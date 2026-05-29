"""EditorBridge — AI-generated paper → Editor structured insertion (Vision 3.6)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import OutlineSection, EditPatch


@dataclass
class InsertPreview:
    """Preview of how an AI section maps to Editor outline."""
    section_title: str
    level: int  # 1-6 heading level
    content: str
    action: str = "append"  # append | replace | skip
    target_section: str = ""  # matching existing section title, if any


class EditorBridge:
    """Parse AI-generated paper and map sections to Editor outline."""

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)

    @staticmethod
    def parse_headings(markdown_text: str) -> list[OutlineSection]:
        """Parse markdown headings into OutlineSection list."""
        matches = list(EditorBridge.HEADING_RE.finditer(markdown_text))
        sections: list[OutlineSection] = []
        for i, m in enumerate(matches):
            level = len(m.group(1))
            title = m.group(2).strip()
            # Content is text between this heading and the next heading (or end)
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
            content = markdown_text[start:end].strip()
            sections.append(OutlineSection.new(
                level=level,
                title=title,
                order=i + 1,
            ))
            # Set content after creation
            sections[-1].content = content
        return sections

    @staticmethod
    def insert_by_section(editor_content: str, section: OutlineSection,
                          position: int | None = None) -> str:
        """Insert a section into editor content at the given position.

        If position is None, append to the end.
        """
        heading_prefix = "#" * min(section.level, 6)
        block = f"\n\n{heading_prefix} {section.title}\n{section.content}\n"

        if position is not None and 0 <= position <= len(editor_content):
            return editor_content[:position] + block + editor_content[position:]
        return editor_content + block

    @staticmethod
    def build_insert_preview(paper_text: str,
                             editor_sections: list[OutlineSection]
                             ) -> list[InsertPreview]:
        """Compare AI paper sections with Editor outline and suggest actions."""
        paper_sections = EditorBridge.parse_headings(paper_text)
        editor_titles = {s.title.strip().lower(): s for s in editor_sections}

        previews: list[InsertPreview] = []
        for ps in paper_sections:
            key = ps.title.strip().lower()
            if key in editor_titles:
                previews.append(InsertPreview(
                    section_title=ps.title,
                    level=ps.level,
                    content=ps.content,
                    action="replace",
                    target_section=editor_titles[key].title,
                ))
            else:
                previews.append(InsertPreview(
                    section_title=ps.title,
                    level=ps.level,
                    content=ps.content,
                    action="append",
                ))
        return previews

    @staticmethod
    def apply_preview(editor_content: str, previews: list[InsertPreview],
                      selected: set[str] | None = None) -> str:
        """Apply selected insertion previews to Editor content.

        Only previews whose section_title is in `selected` are applied.
        If selected is None, apply all non-skip previews.
        """
        result = editor_content
        for p in previews:
            if selected is not None and p.section_title not in selected:
                continue
            if p.action == "skip":
                continue
            section = OutlineSection.new(
                level=p.level,
                title=p.section_title,
                order=0,
            )
            section.content = p.content
            result = EditorBridge.insert_by_section(result, section)
        return result
