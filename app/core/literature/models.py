"""Reference data model for literature management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


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
        import datetime

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
            created_at=datetime.datetime.now().isoformat(),
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
            created_at=data.get("created_at", ""),
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
