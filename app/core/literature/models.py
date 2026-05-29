"""Reference data model for literature management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Reference:
    """An academic reference imported from PDF, BibTeX, or manual entry."""

    id: str
    title: str
    authors: list[str]
    year: str
    journal: str | None
    doi: str | None
    abstract: str | None
    file_path: str | None
    zotero_key: str | None
    tags: list[str]
    indexed: bool
    created_at: str
    # --- Vision 3.2 sync fields ---
    sync_status: str = "local"
    external_source: str | None = None
    external_id: str | None = None
    external_uri: str | None = None
    external_updated_at: str | None = None
    # --- Vision 3.2 verification ---
    verified_status: str = "unverified"
    usable_for_writing: bool = True
    ai_generated: bool = False
    human_verified: bool = False

    @staticmethod
    def new(
        title: str,
        authors: list[str] | None = None,
        year: str = "",
        journal: str | None = None,
        doi: str | None = None,
        abstract: str | None = None,
        file_path: str | None = None,
        zotero_key: str | None = None,
        tags: list[str] | None = None,
    ) -> "Reference":
        """Create a new Reference with generated id and timestamps."""
        return Reference(
            id=str(uuid.uuid4())[:12],
            title=title,
            authors=authors or [],
            year=year,
            journal=journal,
            doi=doi,
            abstract=abstract,
            file_path=file_path,
            zotero_key=zotero_key,
            tags=tags or [],
            indexed=False,
            created_at=_now(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "abstract": self.abstract,
            "file_path": self.file_path,
            "zotero_key": self.zotero_key,
            "tags": self.tags,
            "indexed": self.indexed,
            "created_at": self.created_at,
            "sync_status": self.sync_status,
            "external_source": self.external_source,
            "external_id": self.external_id,
            "external_uri": self.external_uri,
            "external_updated_at": self.external_updated_at,
            "verified_status": self.verified_status,
            "usable_for_writing": self.usable_for_writing,
            "ai_generated": self.ai_generated,
            "human_verified": self.human_verified,
        }

    @staticmethod
    def from_dict(data: dict) -> "Reference":
        return Reference(
            id=data["id"],
            title=data["title"],
            authors=data.get("authors", []),
            year=data.get("year", ""),
            journal=data.get("journal"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            file_path=data.get("file_path"),
            zotero_key=data.get("zotero_key"),
            tags=data.get("tags", []),
            indexed=data.get("indexed", False),
            created_at=data.get("created_at", _now()),
            sync_status=data.get("sync_status", "local"),
            external_source=data.get("external_source"),
            external_id=data.get("external_id"),
            external_uri=data.get("external_uri"),
            external_updated_at=data.get("external_updated_at"),
            verified_status=data.get("verified_status", "unverified"),
            usable_for_writing=data.get("usable_for_writing", True),
            ai_generated=data.get("ai_generated", False),
            human_verified=data.get("human_verified", False),
        )

    def format_gbt7714(self) -> str:
        """Format as GB/T 7714-2015 numeric citation."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = self.year or "n.d."
        title_str = self.title
        if self.journal:
            return f"{authors_str}. {title_str}[J]. {self.journal}, {year_str}."
        return f"{authors_str}. {title_str}[J]. {year_str}."

    def format_apa(self) -> str:
        """Format as APA 7th edition reference."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = f"({self.year})" if self.year else "(n.d.)"
        title_str = self.title
        if self.journal:
            return f"{authors_str} {year_str}. {title_str}. *{self.journal}*."
        return f"{authors_str} {year_str}. {title_str}."
