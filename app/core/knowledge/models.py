"""Data models for the Knowledge Base."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class KnowledgeSource:
    """A single imported knowledge source file."""

    id: str
    title: str
    source_type: str  # "pdf" | "docx" | "markdown" | "txt"
    path: str
    status: str = "pending"  # "pending" | "parsed" | "indexed" | "failed"
    author: list[str] = field(default_factory=list)
    year: str | None = None
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    chunk_count: int = 0
    # --- Vision 3.1 sync fields ---
    sync_status: str = "local"  # local | synced | modified | conflict
    external_source: str | None = None  # zotero | obsidian | manual
    external_id: str | None = None
    external_uri: str | None = None
    external_updated_at: str | None = None
    external_hash: str | None = None
    # --- Vision 3.1 verification ---
    verified_status: str = "unverified"  # unverified | suggested | verified | rejected
    usable_for_writing: bool = True
    usable_for_rag: bool = True
    ai_generated: bool = False
    human_verified: bool = False
    created_at: str = ""

    @staticmethod
    def new(title: str, source_type: str, path: str) -> "KnowledgeSource":
        return KnowledgeSource(
            id=str(uuid.uuid4())[:8],
            title=title,
            source_type=source_type,
            path=path,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "source_type": self.source_type,
            "path": self.path,
            "status": self.status,
            "author": self.author,
            "year": self.year,
            "tags": self.tags,
            "summary": self.summary,
            "chunk_count": self.chunk_count,
            "sync_status": self.sync_status,
            "external_source": self.external_source,
            "external_id": self.external_id,
            "external_uri": self.external_uri,
            "external_updated_at": self.external_updated_at,
            "external_hash": self.external_hash,
            "verified_status": self.verified_status,
            "usable_for_writing": self.usable_for_writing,
            "usable_for_rag": self.usable_for_rag,
            "ai_generated": self.ai_generated,
            "human_verified": self.human_verified,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeSource":
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            source_type=str(data.get("source_type", "")),
            path=str(data.get("path", "")),
            status=str(data.get("status", "pending")),
            author=list(data.get("author", [])),
            year=data.get("year"),
            tags=list(data.get("tags", [])),
            summary=str(data.get("summary", "")),
            chunk_count=int(data.get("chunk_count", 0)),
            sync_status=str(data.get("sync_status", "local")),
            external_source=data.get("external_source"),
            external_id=data.get("external_id"),
            external_uri=data.get("external_uri"),
            external_updated_at=data.get("external_updated_at"),
            external_hash=data.get("external_hash"),
            verified_status=str(data.get("verified_status", "unverified")),
            usable_for_writing=bool(data.get("usable_for_writing", True)),
            usable_for_rag=bool(data.get("usable_for_rag", True)),
            ai_generated=bool(data.get("ai_generated", False)),
            human_verified=bool(data.get("human_verified", False)),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class KnowledgeChunk:
    """A chunk of text extracted from a KnowledgeSource."""

    id: str
    source_id: str
    text: str
    heading: str | None = None
    keywords: list[str] = field(default_factory=list)
    # --- Vision 3.1 scoring ---
    relevance_score: float | None = None
    confidence_score: float | None = None
    created_at: str = ""

    @staticmethod
    def new(source_id: str, text: str, heading: str | None = None) -> "KnowledgeChunk":
        return KnowledgeChunk(
            id=str(uuid.uuid4())[:12],
            source_id=source_id,
            text=text,
            heading=heading,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "text": self.text,
            "heading": self.heading,
            "keywords": self.keywords,
            "relevance_score": self.relevance_score,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeChunk":
        return cls(
            id=str(data.get("id", "")),
            source_id=str(data.get("source_id", "")),
            text=str(data.get("text", "")),
            heading=data.get("heading"),
            keywords=list(data.get("keywords", [])),
            relevance_score=data.get("relevance_score"),
            confidence_score=data.get("confidence_score"),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class Claim:
    """A structured claim extracted from a knowledge source.

    Used by Theory Matcher (Vision 3.3) to build evidence chains.
    """
    id: str
    source_id: str
    chunk_id: str
    claim_text: str
    claim_type: str = "fact"  # fact | finding | method | limitation | assumption
    discipline: str = ""
    extracted_by: str = "rule"  # rule | semantic | llm
    created_at: str = ""

    @staticmethod
    def new(source_id: str, chunk_id: str, claim_text: str, claim_type: str = "fact") -> "Claim":
        return Claim(
            id=str(uuid.uuid4())[:12],
            source_id=source_id,
            chunk_id=chunk_id,
            claim_text=claim_text,
            claim_type=claim_type,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "chunk_id": self.chunk_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "discipline": self.discipline,
            "extracted_by": self.extracted_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Claim":
        return cls(
            id=str(data.get("id", "")),
            source_id=str(data.get("source_id", "")),
            chunk_id=str(data.get("chunk_id", "")),
            claim_text=str(data.get("claim_text", "")),
            claim_type=str(data.get("claim_type", "fact")),
            discipline=str(data.get("discipline", "")),
            extracted_by=str(data.get("extracted_by", "rule")),
            created_at=str(data.get("created_at", "")),
        )


# ── KnowledgeItem — catalog-level item (Vision 3.1) ──────────────────────

ITEM_TYPES = frozenset(["literature", "note", "theory", "evidence"])


@dataclass
class KnowledgeItem:
    """A catalog-level knowledge item — manual entry or lightweight reference.

    Different from KnowledgeSource (which is a parsed file with chunks).
    KnowledgeItem represents a single catalog entry: a literature reference,
    a note, a theory description, or an evidence snippet.
    """

    id: str
    item_type: str  # "literature" | "note" | "theory" | "evidence"
    title: str
    content: str = ""
    source_file: str = ""
    tags: list[str] = field(default_factory=list)
    project_id: str | None = None
    external_source: str = "manual"  # "manual" | "zotero" | "obsidian" | "import"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = _now()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if self.item_type not in ITEM_TYPES:
            raise ValueError(
                f"item_type must be one of {sorted(ITEM_TYPES)}, got {self.item_type!r}"
            )

    @classmethod
    def create(
        cls,
        item_type: str,
        title: str,
        content: str = "",
        **kwargs,
    ) -> "KnowledgeItem":
        return cls(
            id=str(uuid.uuid4())[:12],
            item_type=item_type,
            title=title,
            content=content,
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "item_type": self.item_type,
            "title": self.title,
            "content": self.content,
            "source_file": self.source_file,
            "tags": self.tags,
            "project_id": self.project_id,
            "external_source": self.external_source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeItem":
        return cls(
            id=str(data.get("id", "")),
            item_type=str(data.get("item_type", "note")),
            title=str(data.get("title", "")),
            content=str(data.get("content", "")),
            source_file=str(data.get("source_file", "")),
            tags=list(data.get("tags", [])),
            project_id=data.get("project_id"),
            external_source=str(data.get("external_source", "manual")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )
