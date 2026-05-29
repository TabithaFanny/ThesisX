"""Knowledge importers — batch import from Markdown / BibTeX files (Vision 3.1)."""

from __future__ import annotations

import re
from pathlib import Path

from .models import KnowledgeItem


class MarkdownImporter:
    """Parse Markdown files into KnowledgeItem entries.

    Strategies:
    - With ## headings: each heading section becomes a separate item.
    - Without headings: the whole file becomes one item.
    - Frontmatter (YAML) is extracted as tags / metadata.
    """

    @staticmethod
    def parse_file(filepath: Path) -> list[KnowledgeItem]:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        tags: list[str] = []
        body = text

        # Extract YAML frontmatter if present
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1].strip()
                body = parts[2].strip()
                tags = MarkdownImporter._parse_frontmatter_tags(fm)

        stem = filepath.stem.replace("-", " ").replace("_", " ").title()

        # Split by ## headings (including at start of string)
        sections = re.split(r"(?:^|\n)(?=## )", body)
        sections = [s for s in sections if s.strip()]
        items: list[KnowledgeItem] = []

        if len(sections) <= 1:
            # Single-section document — check for heading at start of body
            heading_match = re.match(r"^## (.+)", body)
            if heading_match:
                title = heading_match.group(1).strip()
                section_body = body[heading_match.end():].strip()
            else:
                title = stem
                section_body = body.strip()
            items.append(KnowledgeItem.create(
                item_type="note",
                title=title,
                content=section_body[:5000],
                source_file=str(filepath),
                tags=tags,
                external_source="import",
            ))
        else:
            for i, section in enumerate(sections):
                section = section.strip()
                if not section:
                    continue
                heading_match = re.match(r"^## (.+)", section)
                if heading_match:
                    heading = heading_match.group(1).strip()
                    section_body = section[heading_match.end():].strip()
                else:
                    heading = f"{stem} ({i + 1})"
                    section_body = section
                items.append(KnowledgeItem.create(
                    item_type="note",
                    title=heading,
                    content=section_body[:5000],
                    source_file=str(filepath),
                    tags=tags,
                    external_source="import",
                ))
        return items

    @staticmethod
    def _parse_frontmatter_tags(fm: str) -> list[str]:
        tags: list[str] = []
        for line in fm.splitlines():
            line = line.strip()
            if line.startswith("tags:"):
                tag_part = line[len("tags:"):].strip()
                # Handle YAML list: [a, b, c] or - a \n - b
                if tag_part.startswith("["):
                    raw = tag_part.strip("[]")
                    tags.extend(t.strip().strip("'\"") for t in raw.split(",") if t.strip())
            elif line.startswith("- "):
                tags.append(line[2:].strip().strip("'\""))
        return tags


class BibTeXImporter:
    """Parse BibTeX files into KnowledgeItem (literature) entries."""

    _HEADER_RE = re.compile(r"@(\w+)\s*\{\s*([^,]+)\s*,")
    _FIELD_RE = re.compile(r"(\w+)\s*=\s*[{\"](.+?)[}\"]")

    @staticmethod
    def parse_file(filepath: Path) -> list[KnowledgeItem]:
        text = filepath.read_text(encoding="utf-8", errors="replace")
        items: list[KnowledgeItem] = []

        # Split by @ to get individual entries (avoid greedy/lazy DOTALL issues)
        raw_blocks = re.split(r"\n(?=@)", text)
        for block in raw_blocks:
            block = block.strip()
            if not block.startswith("@"):
                continue

            header = BibTeXImporter._HEADER_RE.match(block)
            if not header:
                continue
            entry_type = header.group(1)
            cite_key = header.group(2).strip()

            # Extract all field=value pairs from the full block
            fields: dict[str, str] = {}
            for fm in BibTeXImporter._FIELD_RE.finditer(block):
                fields[fm.group(1).lower()] = fm.group(2).strip()

            author = fields.get("author", "Unknown")
            year = fields.get("year", "")
            title = fields.get("title", cite_key.replace("_", " ").title())

            content_lines = [
                f"Authors: {author}",
                f"Year: {year}" if year else "",
                f"Journal: {fields.get('journal', '')}" if fields.get("journal") else "",
                f"DOI: {fields.get('doi', '')}" if fields.get("doi") else "",
            ]
            content = "\n".join(l for l in content_lines if l)

            tags = [entry_type]
            if year:
                tags.append(year)

            items.append(KnowledgeItem.create(
                item_type="literature",
                title=title,
                content=content,
                source_file=str(filepath),
                tags=tags,
                external_source="import",
            ))

        return items
