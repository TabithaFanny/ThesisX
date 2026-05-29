"""RagService — BM25 search over KnowledgeStore chunks (Vision 3.5).

Builds a chunk index from KnowledgeStore items, then scores chunks by
BM25 keyword overlap for retrieval-augmented generation.
"""

from __future__ import annotations

import uuid
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .chunker import TextChunker, BM25, _extract_words


@dataclass
class RagResult:
    """A single search result with source attribution."""

    chunk_id: str
    source_title: str
    source_id: str
    text: str
    score: float
    item_type: str = ""
    start_char: int = 0
    end_char: int = 0


class RagService:
    """BM25-powered retrieval over KnowledgeStore items.

    Builds an in-memory chunk index from KnowledgeStore, then scores
    chunks against queries using the BM25 keyword-overlap scorer.
    """

    def __init__(self, knowledge_store=None):
        # Lazy import to avoid circular dependency at module load
        from app.core.knowledge.store import KnowledgeStore, _DB_PATH
        self._store = knowledge_store or KnowledgeStore()
        self._chunker = TextChunker
        self._bm25 = BM25()
        self._index: list[dict] = []
        self._db_path = _DB_PATH
        self._persistent = knowledge_store is None
        if self._persistent:
            self._init_index_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_index_table(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rag_chunks (
                chunk_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_title TEXT NOT NULL,
                item_type TEXT NOT NULL,
                project_id TEXT,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_char INTEGER DEFAULT 0,
                end_char INTEGER DEFAULT 0,
                search_terms TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_source
            ON rag_chunks(source_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_project
            ON rag_chunks(project_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_item_type
            ON rag_chunks(item_type)
        """)
        conn.commit()
        conn.close()

    # ── index lifecycle ───────────────────────────────────────────────────

    def build_index(
        self,
        item_type: str | None = None,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> int:
        """Rebuild chunk index from all (or type-filtered) KnowledgeStore items.

        Returns total chunk count.
        """
        if object_id:
            item = self._store.get(object_id)
            items = [item] if item is not None else []
        else:
            list_kwargs = {"item_type": item_type}
            if project_id is not None:
                list_kwargs["project_id"] = project_id
            items = self._store.list(**list_kwargs)

        items = [
            item for item in items
            if item is not None
            and (not item_type or item.item_type == item_type)
            and (not project_id or item.project_id == project_id)
        ]
        self._index = []
        for item in items:
            if not item.content:
                continue
            chunks = self._chunker.chunk_text(item.content)
            for chunk in chunks:
                chunk["source_id"] = item.id
                chunk["source_title"] = item.title
                chunk["item_type"] = item.item_type
                chunk["project_id"] = item.project_id
                self._index.append(chunk)

        if self._persistent:
            self._replace_persistent_chunks(item_type=item_type, project_id=project_id, object_id=object_id)
        return len(self._index)

    def _replace_persistent_chunks(
        self,
        item_type: str | None = None,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> None:
        conn = self._get_conn()
        where: list[str] = []
        params: list[str] = []
        if object_id:
            where.append("source_id = ?")
            params.append(object_id)
        if item_type:
            where.append("item_type = ?")
            params.append(item_type)
        if project_id:
            where.append("project_id = ?")
            params.append(project_id)
        clause = " AND ".join(where) if where else "1=1"
        conn.execute(f"DELETE FROM rag_chunks WHERE {clause}", params)

        conn.executemany(
            """
            INSERT INTO rag_chunks (
                chunk_id, source_id, source_title, item_type, project_id,
                chunk_index, text, start_char, end_char, search_terms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f"{chunk['source_id']}:{chunk.get('chunk_index', i)}",
                    chunk.get("source_id", ""),
                    chunk.get("source_title", ""),
                    chunk.get("item_type", ""),
                    chunk.get("project_id"),
                    int(chunk.get("chunk_index", i)),
                    chunk.get("text", ""),
                    int(chunk.get("start_char", 0)),
                    int(chunk.get("end_char", 0)),
                    json.dumps(sorted(_extract_words(chunk.get("text", ""))), ensure_ascii=False),
                )
                for i, chunk in enumerate(self._index)
            ],
        )
        conn.commit()
        conn.close()

    def index_size(
        self,
        item_type: str | None = None,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> int:
        """Return current number of indexed chunks."""
        if self._persistent:
            conn = self._get_conn()
            where: list[str] = []
            params: list[str] = []
            if object_id:
                where.append("source_id = ?")
                params.append(object_id)
            if item_type:
                where.append("item_type = ?")
                params.append(item_type)
            if project_id:
                where.append("project_id = ?")
                params.append(project_id)
            clause = ("WHERE " + " AND ".join(where)) if where else ""
            row = conn.execute(f"SELECT COUNT(*) AS count FROM rag_chunks {clause}", params).fetchone()
            conn.close()
            return int(row["count"] if row else 0)
        return len(self._index)

    # ── search ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        item_type: str | None = None,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> list[RagResult]:
        """Score chunks against query via BM25 and return top-k results."""
        candidates = self._load_candidates(
            item_type=item_type,
            project_id=project_id,
            object_id=object_id,
        )
        if not candidates:
            return []

        query_words = _extract_words(query)
        if not query_words:
            return []

        avgdl = sum(len(c.get("text", "")) for c in candidates) / max(len(candidates), 1)
        scored = self._bm25.score(query_words, candidates, avgdl)

        results: list[RagResult] = []
        for chunk, score in scored[:top_k]:
            if score <= 0:
                continue
            results.append(RagResult(
                chunk_id=chunk.get("id", str(uuid.uuid4())[:8]),
                source_title=chunk.get("source_title", ""),
                source_id=chunk.get("source_id", ""),
                text=chunk.get("text", ""),
                score=round(score, 4),
                item_type=chunk.get("item_type", ""),
                start_char=chunk.get("start_char", 0),
                end_char=chunk.get("end_char", 0),
            ))
        return results

    def _load_candidates(
        self,
        item_type: str | None = None,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> list[dict]:
        if not self._persistent:
            candidates = self._index
            if item_type:
                candidates = [c for c in candidates if c.get("item_type") == item_type]
            if project_id:
                candidates = [c for c in candidates if c.get("project_id") == project_id]
            if object_id:
                candidates = [c for c in candidates if c.get("source_id") == object_id]
            return candidates

        where: list[str] = []
        params: list[str] = []
        if item_type:
            where.append("item_type = ?")
            params.append(item_type)
        if project_id:
            where.append("project_id = ?")
            params.append(project_id)
        if object_id:
            where.append("source_id = ?")
            params.append(object_id)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        conn = self._get_conn()
        rows = conn.execute(
            f"""
            SELECT chunk_id, source_title, source_id, text, item_type,
                   start_char, end_char, chunk_index, project_id
            FROM rag_chunks
            {clause}
            ORDER BY source_title, chunk_index
            """,
            params,
        ).fetchall()
        conn.close()
        return [
            {
                "id": row["chunk_id"],
                "source_title": row["source_title"],
                "source_id": row["source_id"],
                "text": row["text"],
                "item_type": row["item_type"],
                "start_char": row["start_char"],
                "end_char": row["end_char"],
                "chunk_index": row["chunk_index"],
                "project_id": row["project_id"],
            }
            for row in rows
        ]

    # ── context bundle ────────────────────────────────────────────────────

    def get_context_bundle(
        self,
        query: str,
        top_k: int = 5,
        project_id: str | None = None,
        object_id: str | None = None,
    ) -> str:
        """Pack top results as a Markdown context block for AI writing injection."""
        results = self.search(query, top_k=top_k, project_id=project_id, object_id=object_id)
        if not results:
            return "<!-- 无相关知识库上下文 -->"

        lines = ["## 相关知识库上下文\n"]
        for i, r in enumerate(results):
            lines.append(f"### [{i+1}] {r.source_title} (相关度: {r.score:.2f})")
            snippet = r.text[:300].replace("\n", " ")
            lines.append(f"> {snippet}...")
            lines.append("")
        return "\n".join(lines)

    # ── context file (for AgentTeamDialog) ────────────────────────────────

    def export_context_file(self, query: str, top_k: int = 5,
                            output_dir: Path | None = None) -> Path:
        """Build context bundle and write to a markdown file.

        Returns path to the written file.
        """
        bundle = self.get_context_bundle(query, top_k=top_k)
        out_dir = output_dir or (Path.home() / ".wenbiao" / "runs" / "_context")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "rag_context.md"
        out_path.write_text(bundle, encoding="utf-8")
        return out_path
