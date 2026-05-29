"""KnowledgeStore — SQLite CRUD for KnowledgeItem catalog (Vision 3.1)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import KnowledgeItem, ITEM_TYPES

_DB_PATH = Path.home() / ".wenbiao" / "thesisx.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_knowledge_items_table() -> None:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            item_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            source_file TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            project_id TEXT,
            external_source TEXT DEFAULT 'manual',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    # Index for filtering by type and searching by title
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ki_item_type
        ON knowledge_items(item_type)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ki_project
        ON knowledge_items(project_id)
    """)
    conn.commit()
    conn.close()


class KnowledgeStore:
    """SQLite CRUD for catalog-level KnowledgeItem objects.

    Separate from KnowledgeService which manages file-parsed sources + chunks.
    """

    def __init__(self):
        _init_knowledge_items_table()

    # ── CRUD ──────────────────────────────────────────────────────────────

    def add(self, item: KnowledgeItem) -> KnowledgeItem:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO knowledge_items
                (id, item_type, title, content, source_file, tags,
                 project_id, external_source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id, item.item_type, item.title, item.content,
                item.source_file, json.dumps(item.tags, ensure_ascii=False),
                item.project_id, item.external_source,
                item.created_at, item.updated_at,
            ),
        )
        conn.commit()
        conn.close()
        return item

    def get(self, item_id: str) -> KnowledgeItem | None:
        conn = _get_conn()
        row = conn.execute(
            "SELECT * FROM knowledge_items WHERE id = ?", (item_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_item(dict(row))

    def update(self, item_id: str, patch: dict) -> KnowledgeItem | None:
        item = self.get(item_id)
        if item is None:
            return None
        upd = item.to_dict()
        upd.update(patch)
        from .models import _now
        upd["updated_at"] = _now()
        new_item = KnowledgeItem.from_dict(upd)
        conn = _get_conn()
        conn.execute(
            """
            UPDATE knowledge_items
            SET item_type=?, title=?, content=?, source_file=?, tags=?,
                project_id=?, external_source=?, updated_at=?
            WHERE id=?
            """,
            (
                new_item.item_type, new_item.title, new_item.content,
                new_item.source_file, json.dumps(new_item.tags, ensure_ascii=False),
                new_item.project_id, new_item.external_source,
                new_item.updated_at, new_item.id,
            ),
        )
        conn.commit()
        conn.close()
        return new_item

    def delete(self, item_id: str) -> bool:
        conn = _get_conn()
        cur = conn.execute(
            "DELETE FROM knowledge_items WHERE id = ?", (item_id,)
        )
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted

    def list(
        self,
        item_type: str | None = None,
        project_id: str | None = None,
        tag: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeItem]:
        conn = _get_conn()
        where: list[str] = []
        params: list = []
        if item_type and item_type in ITEM_TYPES:
            where.append("item_type = ?")
            params.append(item_type)
        if project_id:
            where.append("project_id = ?")
            params.append(project_id)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        params.extend([limit, offset])
        rows = conn.execute(
            f"SELECT * FROM knowledge_items {clause} "
            "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()
        conn.close()

        items = [self._row_to_item(dict(r)) for r in rows]
        if tag:
            items = [it for it in items if tag in it.tags]
        return items

    def search(self, query: str, limit: int = 20) -> list[KnowledgeItem]:
        conn = _get_conn()
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM knowledge_items
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY updated_at DESC LIMIT ?
            """,
            (like, like, limit),
        ).fetchall()
        conn.close()
        return [self._row_to_item(dict(r)) for r in rows]

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_item(d: dict) -> KnowledgeItem:
        d["tags"] = json.loads(d.get("tags", "[]"))
        return KnowledgeItem.from_dict(d)
