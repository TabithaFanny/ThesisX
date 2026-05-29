"""Tests for RewriteService (Vision 3.6)."""

from __future__ import annotations

import pytest

from app.core.editor.rewrite import RewriteService, RewriteResult


@pytest.fixture
def svc():
    return RewriteService()


# ── polish ──────────────────────────────────────────────────────────────────

class TestPolish:
    def test_polish_changes_text(self, svc):
        result = svc.rewrite("This is a very important result.", "polish")
        assert result.original != result.rewritten
        assert "very important" not in result.rewritten

    def test_polish_preserves_meaningful_content(self, svc):
        text = "The experiment showed significant improvement."
        result = svc.rewrite(text, "polish")
        assert "experiment" in result.rewritten

    def test_polish_returns_patch(self, svc):
        result = svc.rewrite("test content", "polish")
        assert result.patch is not None
        assert result.patch.operation == "replace"
        assert result.patch.old_text == "test content"


# ── expand ──────────────────────────────────────────────────────────────────

class TestExpand:
    def test_expand_adds_content(self, svc):
        text = "This is a finding"
        result = svc.rewrite(text, "expand")
        assert len(result.rewritten) > len(result.original)

    def test_expand_returns_rewrite_result(self, svc):
        result = svc.rewrite("test", "expand")
        assert isinstance(result, RewriteResult)
        assert result.mode == "expand"

    def test_expand_chinese_text(self, svc):
        text = "这项研究表明"
        result = svc.rewrite(text, "expand")
        assert len(result.rewritten) > len(result.original)


# ── add_theory ──────────────────────────────────────────────────────────────

class TestAddTheory:
    def test_add_theory_adds_block(self, svc):
        text = "This is a claim."
        result = svc.rewrite(text, "add_theory")
        assert "理论视角" in result.rewritten
        assert result.rewritten.startswith(text)

    def test_add_theory_preserves_original(self, svc):
        text = "Original claim text."
        result = svc.rewrite(text, "add_theory")
        assert text in result.rewritten


# ── add_evidence ─────────────────────────────────────────────────────────────

class TestAddEvidence:
    def test_add_evidence_adds_block(self, svc):
        text = "A finding needs support."
        result = svc.rewrite(text, "add_evidence")
        assert "证据支撑" in result.rewritten

    def test_add_evidence_returns_patch(self, svc):
        result = svc.rewrite("claim", "add_evidence")
        assert result.patch is not None


# ── error handling ──────────────────────────────────────────────────────────

class TestErrors:
    def test_invalid_mode_raises(self, svc):
        with pytest.raises(ValueError):
            svc.rewrite("text", "nonexistent_mode")

    def test_valid_modes_accepted(self, svc):
        for mode in RewriteService.REWRITE_MODES:
            result = svc.rewrite("text", mode)
            assert isinstance(result, RewriteResult)

    def test_run_mode_is_mock(self, svc):
        assert svc.run_mode == "mock"

    def test_empty_text(self, svc):
        result = svc.rewrite("", "polish")
        assert result.rewritten == ""
