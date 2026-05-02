"""Data models for the Knowledge Base."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


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
    created_at: str = ""

    @staticmethod
    def new(title: str, source_type: str, path: str) -> "KnowledgeSource":
        return KnowledgeSource(
            id=str(uuid.uuid4())[:8],
            title=title,
            source_type=source_type,
            path=path,
            created_at=datetime.now().isoformat(),
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
    created_at: str = ""

    @staticmethod
    def new(source_id: str, text: str, heading: str | None = None) -> "KnowledgeChunk":
        return KnowledgeChunk(
            id=str(uuid.uuid4())[:12],
            source_id=source_id,
            text=text,
            heading=heading,
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "text": self.text,
            "heading": self.heading,
            "keywords": self.keywords,
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
            created_at=str(data.get("created_at", "")),
        )
