"""Tests for EditorBridge (Vision 3.6)."""

from __future__ import annotations

import pytest

from app.core.editor.bridge import EditorBridge, InsertPreview
from app.core.editor.models import OutlineSection


def _make_section(title: str, level: int = 2, content: str = "") -> OutlineSection:
    s = OutlineSection.new(level=level, title=title, order=0)
    s.content = content
    return s


# ── parse_headings ──────────────────────────────────────────────────────────

class TestParseHeadings:
    def test_simple_headings(self):
        md = "# Title\nContent.\n## Section 1\nMore.\n## Section 2\nEnd."
        sections = EditorBridge.parse_headings(md)
        assert len(sections) == 3
        assert sections[0].title == "Title"
        assert sections[0].level == 1
        assert sections[1].title == "Section 1"
        assert sections[1].level == 2

    def test_nested_headings(self):
        md = "## H2\nBody.\n### H3\nSub.\n## H2 B\nMore."
        sections = EditorBridge.parse_headings(md)
        assert len(sections) == 3
        assert sections[0].level == 2
        assert sections[1].level == 3

    def test_no_headings(self):
        md = "Just plain text without any headings."
        sections = EditorBridge.parse_headings(md)
        assert sections == []

    def test_content_between_headings(self):
        md = "# A\ncontent of A\n## B\ncontent of B"
        sections = EditorBridge.parse_headings(md)
        assert "content of A" in sections[0].content
        assert "content of B" in sections[1].content

    def test_headings_with_special_chars(self):
        md = "## 研究方法\n方法描述。\n### 数据收集\n数据来源。"
        sections = EditorBridge.parse_headings(md)
        assert sections[0].title == "研究方法"
        assert sections[1].title == "数据收集"


# ── insert_by_section ───────────────────────────────────────────────────────

class TestInsertBySection:
    def test_insert_at_end(self):
        editor = "Existing content."
        section = OutlineSection.new(level=2, title="New", order=0)
        section.content = "New content."
        result = EditorBridge.insert_by_section(editor, section)
        assert "Existing content." in result
        assert "## New" in result
        assert "New content." in result

    def test_insert_at_position(self):
        editor = "AAA\nBBB"
        section = OutlineSection.new(level=1, title="Inserted", order=0)
        section.content = "Inserted."
        result = EditorBridge.insert_by_section(editor, section, position=4)
        # "AAA\n" = position 4
        assert result.startswith("AAA\n")
        assert "# Inserted" in result
        assert "BBB" in result

    def test_insert_preserves_existing_content(self):
        editor = "Original text."
        section = OutlineSection.new(level=3, title="Added", order=0)
        section.content = "Added text."
        result = EditorBridge.insert_by_section(editor, section)
        assert "Original text." in result


# ── build_insert_preview ────────────────────────────────────────────────────

class TestBuildInsertPreview:
    def test_new_sections_are_append(self):
        paper = "## New Topic\nNew content."
        editor_sections = [_make_section("Existing", level=2, content="Old.")]
        previews = EditorBridge.build_insert_preview(paper, editor_sections)
        assert len(previews) == 1
        assert previews[0].action == "append"
        assert previews[0].section_title == "New Topic"

    def test_matching_sections_are_replace(self):
        paper = "## Introduction\nNew intro content."
        editor_sections = [_make_section("Introduction", level=2, content="Old.")]
        previews = EditorBridge.build_insert_preview(paper, editor_sections)
        assert len(previews) == 1
        assert previews[0].action == "replace"
        assert previews[0].target_section == "Introduction"

    def test_mixed_preview(self):
        paper = "## Abstract\nNew abstract.\n## New Section\nNew content."
        editor_sections = [
            _make_section("Abstract", level=2, content="Old."),
        ]
        previews = EditorBridge.build_insert_preview(paper, editor_sections)
        assert len(previews) == 2
        actions = {p.section_title: p.action for p in previews}
        assert actions["Abstract"] == "replace"
        assert actions["New Section"] == "append"


# ── apply_preview ───────────────────────────────────────────────────────────

class TestApplyPreview:
    def test_apply_selected_only(self):
        editor = "Original."
        previews = [
            InsertPreview(section_title="A", level=2, content="A content", action="append"),
            InsertPreview(section_title="B", level=2, content="B content", action="append"),
        ]
        result = EditorBridge.apply_preview(editor, previews, selected={"A"})
        assert "A content" in result
        assert "B content" not in result

    def test_skip_action_not_applied(self):
        editor = "Original."
        previews = [
            InsertPreview(section_title="Skip me", level=2, content="Skipped", action="skip"),
        ]
        result = EditorBridge.apply_preview(editor, previews)
        assert "Skipped" not in result

    def test_apply_all_when_selected_is_none(self):
        editor = "Original."
        previews = [
            InsertPreview(section_title="A", level=2, content="A content", action="append"),
            InsertPreview(section_title="B", level=3, content="B content", action="append"),
        ]
        result = EditorBridge.apply_preview(editor, previews)
        assert "A content" in result
        assert "B content" in result
