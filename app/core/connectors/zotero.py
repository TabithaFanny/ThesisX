"""ZoteroConnector — BibTeX / RIS file import (Vision 3.7).

Delegates to MarkdownImporter and BibTeXImporter from knowledge module.
Supports file-based import without network access.
"""

from __future__ import annotations

from pathlib import Path

from app.core.knowledge.models import KnowledgeItem


class ZoteroConnector:
    """Import Zotero-exported files (BibTeX, RIS) into the knowledge base."""

    @staticmethod
    def import_bibtex(filepath: Path) -> list[KnowledgeItem]:
        """Parse a BibTeX file and return KnowledgeItem list.

        Delegates to the BibTeXImporter in knowledge module.
        """
        from app.core.knowledge.importers import BibTeXImporter

        entries = BibTeXImporter.parse_file(filepath)
        items: list[KnowledgeItem] = []
        for entry in entries:
            # entry is already a KnowledgeItem — tag it as zotero source
            entry.external_source = "zotero"
            if not entry.source_file:
                entry.source_file = str(filepath)
            items.append(entry)
        return items

    @staticmethod
    def import_ris(filepath: Path) -> list[KnowledgeItem]:
        """Parse a RIS file and return KnowledgeItem list."""
        if not filepath.exists():
            raise FileNotFoundError(f"RIS file not found: {filepath}")

        text = filepath.read_text(encoding="utf-8", errors="replace")
        records = _parse_ris(text)
        items: list[KnowledgeItem] = []
        for rec in records:
            title = rec.get("TI", filepath.stem)
            content_parts = []
            if rec.get("AB"):
                content_parts.append(rec["AB"])
            authors = rec.get("AU", "")
            if authors:
                content_parts.insert(0, f"Authors: {authors}")
            items.append(KnowledgeItem.create(
                item_type="literature",
                title=title,
                content="\n".join(content_parts),
                source_file=str(filepath),
                tags=_extract_keywords_from_ris(rec),
                external_source="zotero",
            ))
        return items


# ── RIS parser ───────────────────────────────────────────────────────────────

def _parse_ris(text: str) -> list[dict]:
    """Parse RIS format into a list of record dicts."""
    records: list[dict] = []
    current: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("TY  -"):
            if current and "TY" in current:
                records.append(current)
            current = {"TY": line[5:].strip()}
            continue
        if line.startswith("ER  -"):
            if current:
                records.append(current)
            current = {}
            continue
        if "  - " in line and current:
            tag, value = line.split("  - ", 1)
            tag = tag.strip()
            if tag not in current:
                current[tag] = value.strip()
            else:
                existing = current[tag]
                if isinstance(existing, list):
                    existing.append(value.strip())
                else:
                    current[tag] = [existing, value.strip()]
            continue
    if current and "TY" in current:
        records.append(current)
    return records


def _extract_keywords_from_ris(rec: dict) -> list[str]:
    """Extract keyword tags from RIS record fields."""
    tags: list[str] = []
    kw = rec.get("KW")
    if kw:
        if isinstance(kw, list):
            tags.extend(kw)
        else:
            tags.append(str(kw))
    return tags
