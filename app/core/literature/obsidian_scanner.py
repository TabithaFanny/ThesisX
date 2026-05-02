"""Obsidian vault scanner — import Obsidian notes as KnowledgeSources."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.knowledge import KnowledgeService


@dataclass
class ObsidianNote:
    """A single Obsidian markdown note."""
    path: str
    title: str
    tags: list[str]
    links: list[str]
    backlinks: list[str]
    content: str


class ObsidianVaultScanner:
    """Scan an Obsidian vault and import notes into the Knowledge Base."""

    def __init__(self, vault_path: str) -> None:
        self.vault_path = Path(vault_path).expanduser().resolve()
        if not self.vault_path.is_dir():
            raise ValueError(f"Obsidian vault path is not a directory: {vault_path}")
        self._kb = KnowledgeService()

    def scan(self) -> list[ObsidianNote]:
        """Scan all .md files in the vault (non-recursive top-level only)."""
        notes: list[ObsidianNote] = []
        for md_path in self.vault_path.glob("*.md"):
            try:
                note = self._parse_note(md_path)
                notes.append(note)
            except Exception:
                continue
        return notes

    def scan_recursive(self) -> list[ObsidianNote]:
        """Recursively scan all .md files in the vault."""
        notes: list[ObsidianNote] = []
        for md_path in self.vault_path.rglob("*.md"):
            if md_path.is_file():
                try:
                    note = self._parse_note(md_path)
                    notes.append(note)
                except Exception:
                    continue
        return notes

    def _parse_note(self, md_path: Path) -> ObsidianNote:
        """Parse a single markdown note.

        Extracts:
        - YAML frontmatter (title, tags, aliases)
        - Headings
        - Wiki-links [[...]]
        - Tags #tag
        """
        text = md_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        frontmatter: dict = {}
        if text.startswith("---"):
            end = text.find("\n---\n", 3)
            if end != -1:
                fm_text = text[4:end]
                frontmatter = self._parse_frontmatter(fm_text)
                text = text[end + 5:]

        # Title from frontmatter or first heading or filename
        title = frontmatter.get("title", "")
        if not title:
            first_line = text.lstrip().split("\n")[0] if text.strip() else ""
            if first_line.startswith("# "):
                title = first_line[2:].strip()
        if not title:
            title = md_path.stem.replace("-", " ").replace("_", " ").title()

        # Tags: from frontmatter + inline #tags
        fm_tags: list[str] = frontmatter.get("tags", [])
        if isinstance(fm_tags, str):
            fm_tags = [fm_tags]
        inline_tags = re.findall(r"(?<!&)#([a-zA-Z\u4e00-\u9fff][a-zA-Z0-9\u4e00-\u9fff_-]*)", text)
        all_tags = list(dict.fromkeys(fm_tags + inline_tags))  # preserve order, dedupe

        # Wiki-links [[...]]
        wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text)

        # Extract headings for chunking
        headings: dict[str, str] = {}
        current_heading = ""
        current_content: list[str] = []
        for line in text.split("\n"):
            m = re.match(r"^(#{1,6})\s+(.+)$", line)
            if m:
                if current_heading and current_content:
                    headings[current_heading] = "\n".join(current_content).strip()
                current_heading = m.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        if current_heading and current_content:
            headings[current_heading] = "\n".join(current_content).strip()

        return ObsidianNote(
            path=str(md_path),
            title=title,
            tags=all_tags,
            links=list(set(wiki_links)),
            backlinks=[],  # computed separately by cross-ref analysis
            content=text.strip(),
        )

    def _parse_frontmatter(self, fm_text: str) -> dict:
        """Parse YAML-like frontmatter (key: value pairs, no nested)."""
        result: dict = {}
        current_key: str | None = None
        current_val: list[str] = []

        for line in fm_text.split("\n"):
            line = line.rstrip()
            if not line:
                continue
            # Key: value
            m = re.match(r"^(\w+):\s*(.*)$", line)
            if m:
                if current_key is not None and current_val:
                    val_str = " ".join(current_val)
                    if "," in val_str:
                        result[current_key] = [v.strip() for v in val_str.split(",")]
                    else:
                        result[current_key] = val_str.strip('" \' ')
                current_key = m.group(1)
                rest = m.group(2).strip()
                if rest:
                    current_val = [rest]
                else:
                    current_val = []
            elif current_key is not None and line.startswith("-"):
                current_val.append(line[1:].strip())
            elif current_key is not None:
                current_val.append(line.strip('" \' '))

        if current_key is not None and current_val:
            val_str = " ".join(current_val)
            # Handle inline list: [item1, item2, item3]
            if val_str.startswith("[") and val_str.endswith("]"):
                inner = val_str[1:-1]
                result[current_key] = [v.strip() for v in inner.split(",")]
            elif "," in val_str and not any(c in val_str for c in "{}[]"):
                result[current_key] = [v.strip() for v in val_str.split(",")]
            else:
                result[current_key] = val_str.strip('" \' ')

        return result

    def import_all(self) -> list[dict]:
        """Scan vault and import all notes into Knowledge Base.

        Returns list of dicts with note title and source_id.
        """
        notes = self.scan_recursive()
        imported: list[dict] = []
        for note in notes:
            try:
                src = self._kb.import_file(note.path)
                src_id = src.id if hasattr(src, "id") else src.get("id")
                imported.append({"title": note.title, "source_id": src_id, "tags": note.tags})
            except Exception:
                continue
        return imported
