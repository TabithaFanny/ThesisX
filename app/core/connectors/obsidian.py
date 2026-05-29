"""ObsidianScanner — scan an Obsidian vault for notes (Vision 3.7).

Extracts markdown notes with YAML frontmatter and [[wikilinks]].
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.knowledge.models import KnowledgeItem


class ObsidianScanner:
    """Scan an Obsidian vault directory for markdown notes."""

    def __init__(self, vault_path: Path):
        self._vault_path = Path(vault_path).expanduser()
        if not self._vault_path.is_dir():
            raise NotADirectoryError(f"Vault not found: {self._vault_path}")

    def scan(self, max_files: int = 200) -> list[KnowledgeItem]:
        """Scan vault for .md files and convert to KnowledgeItem list."""
        items: list[KnowledgeItem] = []
        for md_file in self._vault_path.rglob("*.md"):
            if len(items) >= max_files:
                break
            item = self._parse_file(md_file)
            if item:
                items.append(item)
        return items

    def _parse_file(self, filepath: Path) -> KnowledgeItem | None:
        """Parse a single Obsidian note into a KnowledgeItem."""
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

        if not text.strip():
            return None

        # Skip binary-looking content
        if "\x00" in text:
            return None

        # Extract YAML frontmatter
        tags: list[str] = []
        title = filepath.stem
        body_start = 0

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body_start = len(parts[0]) + len(parts[1]) + 6  # "---\n" × 2
                tags = self._parse_frontmatter_tags(frontmatter)
                title_match = re.search(r"(?:title|Title):\s*(.+)", frontmatter)
                if title_match:
                    title = title_match.group(1).strip().strip('"').strip("'")

        # Extract [[wikilinks]] as additional tags
        wikilinks = re.findall(r"\[\[(.+?)\]\]", text)
        for link in wikilinks:
            alias = link.split("|")[0].strip() if "|" in link else link.strip()
            if alias and alias not in tags:
                tags.append(alias)

        body = text[body_start:] if body_start > 0 else text

        return KnowledgeItem.create(
            item_type="note",
            title=title,
            content=body.strip(),
            source_file=str(filepath),
            tags=tags,
            external_source="obsidian",
        )

    @staticmethod
    def _parse_frontmatter_tags(frontmatter: str) -> list[str]:
        """Extract tags from YAML frontmatter."""
        tags: list[str] = []
        for line in frontmatter.splitlines():
            line = line.strip()
            if line.startswith("tags:") or line.startswith("Tags:"):
                tag_part = line.split(":", 1)[1].strip()
                # [tag1, tag2] or tag1
                if tag_part.startswith("["):
                    raw = tag_part.strip("[]")
                    for t in raw.split(","):
                        t = t.strip().strip('"').strip("'")
                        if t:
                            tags.append(t)
                else:
                    for t in tag_part.split():
                        t = t.strip('"').strip("'")
                        if t:
                            tags.append(t)
            elif ": " in line:
                continue
        return tags
