"""Editor AI Loop services — Vision 3.4.5 / 3.6.

InsertService: insert knowledge objects into paper outline sections.
DiffView: compute and display diff between old/new text.
UndoManager: undo/redo stack for EditPatch operations.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from app.core.editor.models import EditPatch, OutlineSection


class DiffView:
    """Compute word-level inline diff between two text strings."""

    @staticmethod
    def compute(old: str, new: str) -> list[dict]:
        """Return a list of diff hunks.

        Each hunk: {op: 'equal'|'insert'|'delete', text: str}
        """
        matcher = difflib.SequenceMatcher(None, old, new)
        result: list[dict] = []
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            text = new[j1:j2] if op in ("replace", "insert") else old[i1:i2]
            result.append({"op": op, "text": text})
        return result

    @staticmethod
    def render_markdown(old: str, new: str) -> str:
        """Render diff as a minimal Markdown table."""
        hunks = DiffView.compute(old, new)
        lines = ["### 变更预览\n", "| 操作 | 内容 |", "|------|------|"]
        for hunk in hunks:
            op_label = {"equal": "保留", "delete": "-删除", "insert": "+新增", "replace": "~替换"}.get(
                hunk["op"], hunk["op"]
            )
            snippet = hunk["text"][:60].replace("\n", " ")
            lines.append(f"| {op_label} | {snippet} |")
        return "\n".join(lines)


class UndoManager:
    """Undo/redo stack for EditPatch operations on an OutlineSection."""

    MAX_HISTORY = 50

    def __init__(self, section_id: str) -> None:
        self.section_id = section_id
        self._undo: list[EditPatch] = []
        self._redo: list[EditPatch] = []

    def push(self, patch: EditPatch) -> None:
        """Record a patch and clear redo stack."""
        self._undo.append(patch)
        self._redo.clear()
        if len(self._undo) > self.MAX_HISTORY:
            self._undo.pop(0)

    def undo(self) -> EditPatch | None:
        if not self._undo:
            return None
        patch = self._undo.pop()
        self._redo.append(patch)
        return patch

    def redo(self) -> EditPatch | None:
        if not self._redo:
            return None
        patch = self._redo.pop()
        self._undo.append(patch)
        return patch

    def can_undo(self) -> bool:
        return len(self._undo) > 0

    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def serialize(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "undo": [p.to_dict() for p in self._undo],
            "redo": [p.to_dict() for p in self._redo],
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "UndoManager":
        mgr = cls(data["section_id"])
        mgr._undo = [EditPatch.from_dict(d) for d in data.get("undo", [])]
        mgr._redo = [EditPatch.from_dict(d) for d in data.get("redo", [])]
        return mgr


class InsertService:
    """Insert knowledge objects into paper outline sections.

    Respects section boundaries and provides safe insert with diff preview.
    """

    SECTION_TYPES_WITH_ABSTRACT = {"abstract", "intro", "method", "result", "discussion", "conclusion", "references"}

    @staticmethod
    def find_insert_position(
        section_content: str,
        target_heading: str,
        direction: str = "after",
    ) -> int:
        """Find character position to insert text near a heading.

        direction: 'after' (default) or 'before'
        Returns -1 if heading not found.
        """
        idx = section_content.find(target_heading)
        if idx == -1:
            return -1
        if direction == "after":
            return idx + len(target_heading)
        return idx

    @staticmethod
    def apply_patch(section: OutlineSection, patch: EditPatch) -> str:
        """Apply an EditPatch to section content.

        Supports: insert, delete, replace
        """
        content = section.content
        if patch.operation == "insert" and patch.position is not None:
            pos = min(patch.position, len(content))
            return content[:pos] + patch.new_text + content[pos:]
        elif patch.operation == "delete":
            idx = content.find(patch.old_text)
            if idx != -1:
                return content[:idx] + content[idx + len(patch.old_text):]
            return content
        elif patch.operation == "replace":
            idx = content.find(patch.old_text)
            if idx != -1:
                return content[:idx] + patch.new_text + content[idx + len(patch.old_text):]
            return content
        return content

    @staticmethod
    def preview_insert(
        section: OutlineSection,
        knowledge_text: str,
        position: int | None = None,
    ) -> tuple[str, EditPatch]:
        """Preview inserting knowledge text into a section.

        Returns (new_content, patch).
        """
        if position is None:
            position = len(section.content)
        patch = EditPatch.new(
            section_id=section.id,
            operation="insert",
            position=position,
            new_text=knowledge_text,
        )
        new_content = InsertService.apply_patch(section, patch)
        return new_content, patch

    @staticmethod
    def suggest_positions(section: OutlineSection) -> list[tuple[int, str]]:
        """Suggest safe insert positions within a section.

        Returns list of (position, description).
        """
        positions: list[tuple[int, str]] = []
        content = section.content
        # After section heading
        if section.title:
            idx = content.find(section.title)
            if idx != -1:
                positions.append((idx + len(section.title), "章节标题后"))
        # Before first empty line after heading
        empty_idx = content.find("\n\n")
        if empty_idx > 0:
            positions.append((empty_idx + 2, "段落分隔后"))
        # At end
        positions.append((len(content), "章节末尾"))
        return positions
