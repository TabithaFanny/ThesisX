"""Tests for OutlinePickerDialog (V3.x → V4.0 Fix 1.3)."""

from __future__ import annotations

import pytest
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QDialog

from app.core.editor.bridge import EditorBridge, InsertPreview


# Skip all tests if no QApplication (headless CI)
@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication exists for dialog tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([""])
    yield app


class TestOutlinePickerDialog:
    def test_creates_with_previews(self, qapp):
        previews = [
            InsertPreview(
                section_title="Introduction",
                level=1,
                content="Some introduction text.",
                action="append",
            ),
            InsertPreview(
                section_title="Methods",
                level=2,
                content="Methodology details.",
                action="replace",
                target_section="Methods",
            ),
        ]
        from app.ui.outline_picker_dialog import OutlinePickerDialog
        dialog = OutlinePickerDialog(previews)
        assert dialog is not None
        # All sections should be selected by default
        dialog.close()

    def test_select_all_deselect_all(self, qapp):
        previews = [
            InsertPreview(
                section_title="Section A",
                level=1,
                content="Content A",
                action="append",
            ),
            InsertPreview(
                section_title="Section B",
                level=2,
                content="Content B",
                action="append",
            ),
        ]
        from app.ui.outline_picker_dialog import OutlinePickerDialog
        dialog = OutlinePickerDialog(previews)
        dialog._deselect_all()
        dialog._on_accept()
        assert len(dialog.selected_titles) == 0
        dialog._select_all()
        dialog._on_accept()
        assert "Section A" in dialog.selected_titles
        assert "Section B" in dialog.selected_titles
        dialog.close()

    def test_returns_selected_titles(self, qapp):
        previews = [
            InsertPreview(
                section_title="Theory",
                level=1,
                content="Theory framework",
                action="append",
            ),
        ]
        from app.ui.outline_picker_dialog import OutlinePickerDialog
        dialog = OutlinePickerDialog(previews)
        dialog._on_accept()
        assert "Theory" in dialog.selected_titles
        dialog.close()
