"""Tests for DiffPreviewDialog (V3.x → V4.0 Fix 2.3)."""

from __future__ import annotations

import pytest

from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([""])
    yield app


class TestDiffPreviewDialog:
    def test_creates_dialog(self, qapp):
        from app.ui.diff_preview_dialog import DiffPreviewDialog
        dialog = DiffPreviewDialog("original text", "rewritten text", "润色")
        assert dialog is not None
        assert not dialog.is_accepted
        dialog.close()

    def test_accept_sets_flag(self, qapp):
        from app.ui.diff_preview_dialog import DiffPreviewDialog
        dialog = DiffPreviewDialog("old", "new", "扩写")
        dialog._on_accept()
        assert dialog.is_accepted
        dialog.close()

    def test_reject_keeps_flag_false(self, qapp):
        from app.ui.diff_preview_dialog import DiffPreviewDialog
        dialog = DiffPreviewDialog("old", "new", "润色")
        assert not dialog.is_accepted
        dialog.reject()
        assert not dialog.is_accepted
        dialog.close()
