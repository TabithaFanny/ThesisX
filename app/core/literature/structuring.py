"""Structured literature summary service.

Transforms a single literature reference into multiple catalog-level
KnowledgeItem nodes that are easier to search, connect, and promote into
evidence/theory workflows.
"""

from __future__ import annotations

import re

from app.core.knowledge.models import KnowledgeItem
from app.core.literature.models import Reference


class LiteratureStructuringService:
    """Create structured summary nodes from a literature reference."""

    def build_items(
        self,
        reference: Reference,
        project_id: str | None = None,
    ) -> list[KnowledgeItem]:
        source_file = reference.file_path or reference.doi or reference.zotero_key or ""
        base_tags = list(dict.fromkeys([
            "literature-structured",
            *reference.tags,
            *(["zotero"] if reference.zotero_key else []),
            *(["doi"] if reference.doi else []),
        ]))

        sections = [
            (
                "note",
                f"{reference.title} · Overview",
                self._build_overview(reference),
                base_tags + ["overview"],
            ),
            (
                "note",
                f"{reference.title} · Background",
                self._build_background(reference),
                base_tags + ["background"],
            ),
            (
                "theory",
                f"{reference.title} · Method / Theory",
                self._build_method(reference),
                base_tags + ["method", "theory"],
            ),
            (
                "note",
                f"{reference.title} · Findings",
                self._build_findings(reference),
                base_tags + ["findings"],
            ),
            (
                "evidence",
                f"{reference.title} · Evidence Snippet",
                self._build_evidence(reference),
                base_tags + ["evidence"],
            ),
        ]

        items: list[KnowledgeItem] = []
        for item_type, title, content, tags in sections:
            if not content.strip():
                continue
            items.append(
                KnowledgeItem.create(
                    item_type=item_type,
                    title=title,
                    content=content,
                    source_file=source_file,
                    tags=tags,
                    project_id=project_id,
                    external_source=reference.external_source or "literature",
                )
            )
        return items

    def _build_overview(self, reference: Reference) -> str:
        lines = [
            f"Title: {reference.title}",
            f"Authors: {', '.join(reference.authors) if reference.authors else 'Unknown'}",
            f"Year: {reference.year or 'n.d.'}",
        ]
        if reference.journal:
            lines.append(f"Venue: {reference.journal}")
        if reference.doi:
            lines.append(f"DOI: {reference.doi}")
        if reference.zotero_key:
            lines.append(f"Zotero Key: {reference.zotero_key}")
        if reference.abstract:
            lines.extend(["", "Abstract:", reference.abstract.strip()])
        return "\n".join(lines).strip()

    def _build_background(self, reference: Reference) -> str:
        abstract = (reference.abstract or "").strip()
        if not abstract:
            return f"{reference.title} currently lacks an abstract. Review the source PDF and summarize the research background and motivation here."
        first_sentences = self._take_sentences(abstract, 2)
        return (
            "Research Background\n"
            f"{first_sentences}\n\n"
            "Working Notes\n"
            "- What problem space does this paper respond to?\n"
            "- Which prior assumptions or gaps does it challenge?\n"
            "- Where does it sit in the literature line?"
        ).strip()

    def _build_method(self, reference: Reference) -> str:
        abstract = (reference.abstract or "").strip()
        method_hint = self._take_sentences(abstract, 2) if abstract else ""
        if not method_hint:
            method_hint = "Method details are not yet extracted from the source. Add theory, method, dataset, and evaluation setup after reading the paper."
        return (
            "Method / Theory Frame\n"
            f"{method_hint}\n\n"
            "Extraction Slots\n"
            "- Core method or framework:\n"
            "- Input / data source:\n"
            "- Evaluation design:\n"
            "- Theory lens (if any):"
        ).strip()

    def _build_findings(self, reference: Reference) -> str:
        abstract = (reference.abstract or "").strip()
        findings = self._take_sentences(abstract, 3) if abstract else ""
        if not findings:
            findings = "No abstract-derived findings are available yet. Add the key experimental or argumentative outcomes after reading the source."
        return (
            "Key Findings\n"
            f"{findings}\n\n"
            "Follow-up Questions\n"
            "- Which result is most reusable for the current project?\n"
            "- Which limitation or contrast should be tracked?"
        ).strip()

    def _build_evidence(self, reference: Reference) -> str:
        abstract = (reference.abstract or "").strip()
        evidence_text = self._take_sentences(abstract, 1) if abstract else reference.title
        source_bits = []
        if reference.zotero_key:
            source_bits.append(f"zotero_key={reference.zotero_key}")
        if reference.doi:
            source_bits.append(f"doi={reference.doi}")
        if reference.file_path:
            source_bits.append(f"file={reference.file_path}")
        source_line = " | ".join(source_bits) if source_bits else "source metadata pending"
        return (
            f"Claim-support candidate from {reference.title}\n"
            f"{evidence_text}\n\n"
            f"Trace: {source_line}\n"
            "Use this item as a starting evidence snippet, then replace it with page-level or annotation-level support."
        ).strip()

    @staticmethod
    def _take_sentences(text: str, count: int) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
          return ""
        parts = re.split(r"(?<=[.!?。！？])\s+", cleaned)
        selected = [part.strip() for part in parts if part.strip()][:count]
        return " ".join(selected).strip()
