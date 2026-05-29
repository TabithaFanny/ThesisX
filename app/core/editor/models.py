"""Editor AI Loop data models — Vision 3.4.5 / 3.6.

Supports: OutlineParser, InsertService, RewriteService,
UndoManager, DiffView. Integrates with KnowledgeObject
(binding) and ProjectService (context).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Edit operation types
# ----------------------------------------------------------------------

# Valid edit operations for EditPatch
EDIT_OPERATIONS = frozenset(["insert", "delete", "replace", "rewrite", "move"])


@dataclass
class OutlineSection:
    """A single section within a paper outline.

    Used by Editor AI Loop to track per-section edit status.
    """
    id: str
    level: int  # 1=h1, 2=h2, ...
    title: str
    order: int  # position in outline
    content: str = ""  # rendered text
    word_count: int = 0
    edit_status: str = "pending"  # pending | in_progress | done | rejected
    linked_ko_ids: list[str] = field(default_factory=list)  # ProjectKnowledgeLink ids
    section_type: str = "body"  # abstract | intro | method | result | discussion | conclusion | references
    created_at: str = ""

    @staticmethod
    def new(level: int, title: str, order: int, section_type: str = "body") -> "OutlineSection":
        return OutlineSection(
            id=str(uuid.uuid4())[:12],
            level=level,
            title=title,
            order=order,
            section_type=section_type,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "title": self.title,
            "order": self.order,
            "content": self.content,
            "word_count": self.word_count,
            "edit_status": self.edit_status,
            "linked_ko_ids": self.linked_ko_ids,
            "section_type": self.section_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OutlineSection":
        return cls(
            id=data["id"],
            level=int(data.get("level", 1)),
            title=str(data.get("title", "")),
            order=int(data.get("order", 0)),
            content=str(data.get("content", "")),
            word_count=int(data.get("word_count", 0)),
            edit_status=str(data.get("edit_status", "pending")),
            linked_ko_ids=list(data.get("linked_ko_ids", [])),
            section_type=str(data.get("section_type", "body")),
            created_at=str(data.get("created_at", _now())),
        )


@dataclass
class EditPatch:
    """A single edit operation on an OutlineSection.

    Supports insert / delete / replace / rewrite / move.
    """
    id: str
    section_id: str
    operation: str  # insert|delete|replace|rewrite|move
    position: int | None = None  # char offset for insert/replace
    old_text: str = ""
    new_text: str = ""
    # For move: source_section_id is stored in old_text (as string)
    target_section_id: str | None = None
    applied: bool = False
    undone: bool = False
    created_at: str = ""

    @staticmethod
    def new(
        section_id: str,
        operation: str,
        position: int | None = None,
        old_text: str = "",
        new_text: str = "",
        target_section_id: str | None = None,
    ) -> "EditPatch":
        return EditPatch(
            id=str(uuid.uuid4())[:12],
            section_id=section_id,
            operation=operation,
            position=position,
            old_text=old_text,
            new_text=new_text,
            target_section_id=target_section_id,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "section_id": self.section_id,
            "operation": self.operation,
            "position": self.position,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "target_section_id": self.target_section_id,
            "applied": self.applied,
            "undone": self.undone,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EditPatch":
        return cls(
            id=data["id"],
            section_id=str(data.get("section_id", "")),
            operation=str(data.get("operation", "")),
            position=data.get("position"),
            old_text=str(data.get("old_text", "")),
            new_text=str(data.get("new_text", "")),
            target_section_id=data.get("target_section_id"),
            applied=bool(data.get("applied", False)),
            undone=bool(data.get("undone", False)),
            created_at=str(data.get("created_at", _now())),
        )
