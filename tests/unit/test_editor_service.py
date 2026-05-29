"""Tests for Editor AI Loop services."""

import pytest
from app.core.editor.models import EditPatch, OutlineSection
from app.core.editor.service import DiffView, InsertService, UndoManager


class TestDiffView:
    def test_compute_equal(self):
        result = DiffView.compute("hello world", "hello world")
        ops = [r["op"] for r in result]
        assert ops == ["equal"]

    def test_compute_insert(self):
        result = DiffView.compute("hello", "hello world")
        ops = [r["op"] for r in result]
        assert "insert" in ops

    def test_compute_delete(self):
        result = DiffView.compute("hello world", "hello")
        ops = [r["op"] for r in result]
        assert "delete" in ops

    def test_compute_replace(self):
        result = DiffView.compute("机器学习", "深度学习")
        ops = [r["op"] for r in result]
        assert "replace" in ops

    def test_render_markdown(self):
        md = DiffView.render_markdown("hello", "hello world")
        assert "新增" in md
        assert "保留" in md


class TestUndoManager:
    def test_push_and_undo(self):
        mgr = UndoManager("s-1")
        p1 = EditPatch.new("s-1", "insert", new_text="Hello")
        mgr.push(p1)
        assert mgr.can_undo()
        undone = mgr.undo()
        assert undone is not None
        assert undone.new_text == "Hello"

    def test_redo_after_undo(self):
        mgr = UndoManager("s-2")
        p1 = EditPatch.new("s-2", "insert", new_text="World")
        mgr.push(p1)
        mgr.undo()
        assert mgr.can_redo()
        redone = mgr.redo()
        assert redone is not None
        assert redone.new_text == "World"

    def test_cannot_undo_empty(self):
        mgr = UndoManager("s-empty")
        assert not mgr.can_undo()

    def test_serialize_deserialize(self):
        mgr = UndoManager("s-3")
        mgr.push(EditPatch.new("s-3", "insert", new_text="Test"))
        data = mgr.serialize()
        mgr2 = UndoManager.deserialize(data)
        assert mgr2.can_undo()


class TestInsertService:
    def test_apply_patch_insert(self):
        sec = OutlineSection.new(level=2, title="方法", order=1)
        sec.content = "本研完采用实证研究方法"
        patch = EditPatch.new(sec.id, "insert", position=5, new_text="究")
        result = InsertService.apply_patch(sec, patch)
        assert "研究" in result

    def test_apply_patch_delete(self):
        sec = OutlineSection.new(level=2, title="方法", order=1)
        sec.content = "本研完采用实证研究方法"
        patch = EditPatch.new(sec.id, "delete", old_text="本研完")
        result = InsertService.apply_patch(sec, patch)
        assert "本研完" not in result

    def test_apply_patch_replace(self):
        sec = OutlineSection.new(level=2, title="方法", order=1)
        sec.content = "本研完采用实证研究方法"
        patch = EditPatch.new(sec.id, "replace", old_text="本研完", new_text="本研究")
        result = InsertService.apply_patch(sec, patch)
        assert "本研究采用" in result

    def test_preview_insert(self):
        sec = OutlineSection.new(level=2, title="背景", order=0)
        sec.content = "人工智能正在改变教育"
        new_content, patch = InsertService.preview_insert(sec, "，尤其是大模型", position=8)
        assert "大模型" in new_content
        assert patch.operation == "insert"

    def test_suggest_positions(self):
        sec = OutlineSection.new(level=2, title="方法", order=1)
        sec.content = "方法\n\n第一段内容\n\n第二段内容"
        positions = InsertService.suggest_positions(sec)
        assert len(positions) >= 2


class TestOutlineSection:
    def test_new(self):
        s = OutlineSection.new(level=2, title="研究背景", order=1, section_type="intro")
        assert s.level == 2
        assert s.title == "研究背景"
        assert s.edit_status == "pending"
        assert s.section_type == "intro"

    def test_to_dict_round_trip(self):
        s = OutlineSection.new(level=1, title="摘要", order=0, section_type="abstract")
        s.content = "这是一段摘要内容"
        s.word_count = 50
        d = s.to_dict()
        s2 = OutlineSection.from_dict(d)
        assert s2.title == s.title
        assert s2.word_count == 50

    def test_linked_ko_ids(self):
        s = OutlineSection.new(level=3, title="实验结果", order=2)
        s.linked_ko_ids = ["ko-1", "ko-2"]
        d = s.to_dict()
        s2 = OutlineSection.from_dict(d)
        assert s2.linked_ko_ids == ["ko-1", "ko-2"]
