"""Tests for ZoteroConnector (Vision 3.7)."""

from __future__ import annotations

import pytest
from pathlib import Path

from app.core.connectors.zotero import ZoteroConnector, _parse_ris


# ── RIS parser ──────────────────────────────────────────────────────────────

class TestRISParser:
    def test_parse_single_entry(self):
        ris = "TY  - JOUR\nAU  - Smith, J.\nTI  - Test Title\nPY  - 2023\nER  - \n"
        records = _parse_ris(ris)
        assert len(records) == 1
        assert records[0]["TY"] == "JOUR"
        assert records[0]["TI"] == "Test Title"

    def test_parse_multiple_entries(self):
        ris = (
            "TY  - JOUR\nTI  - First\nER  - \n"
            "TY  - JOUR\nTI  - Second\nER  - \n"
        )
        records = _parse_ris(ris)
        assert len(records) == 2

    def test_parse_empty_text(self):
        records = _parse_ris("")
        assert records == []

    def test_parse_missing_fields(self):
        ris = "TY  - JOUR\nTI  - Only Title\nER  - \n"
        records = _parse_ris(ris)
        assert records[0]["TI"] == "Only Title"
        assert "AU" not in records[0]

    def test_parse_with_comments(self):
        ris = "# Comment line\nTY  - JOUR\nTI  - Title\nER  - \n"
        records = _parse_ris(ris)
        assert len(records) == 1


# ── BibTeX import ───────────────────────────────────────────────────────────

class TestBibTeXImport:
    def test_import_single_entry(self, tmp_path: Path):
        bib = """@article{smith2023,
  author = {Smith, John},
  title = {Important Research},
  year = {2023},
  journal = {Journal of Science},
}
"""
        path = tmp_path / "test.bib"
        path.write_text(bib)
        items = ZoteroConnector.import_bibtex(path)
        assert len(items) == 1
        assert items[0].item_type == "literature"
        assert "Important Research" in items[0].title
        assert items[0].external_source == "zotero"

    def test_import_empty_file(self, tmp_path: Path):
        path = tmp_path / "empty.bib"
        path.write_text("")
        items = ZoteroConnector.import_bibtex(path)
        assert items == []

    def test_import_sets_source_file(self, tmp_path: Path):
        bib = "@article{test, author = {A}, title = {T}, year = {2024}}"
        path = tmp_path / "test.bib"
        path.write_text(bib)
        items = ZoteroConnector.import_bibtex(path)
        assert str(path) in items[0].source_file


# ── RIS import ──────────────────────────────────────────────────────────────

class TestRISImport:
    def test_import_single_entry(self, tmp_path: Path):
        ris = "TY  - JOUR\nAU  - Lee, C.\nTI  - Research\nPY  - 2022\nER  - \n"
        path = tmp_path / "test.ris"
        path.write_text(ris)
        items = ZoteroConnector.import_ris(path)
        assert len(items) >= 1
        assert items[0].item_type == "literature"
        assert items[0].external_source == "zotero"

    def test_import_missing_file_raises(self, tmp_path: Path):
        path = tmp_path / "nonexistent.ris"
        with pytest.raises(FileNotFoundError):
            ZoteroConnector.import_ris(path)

    def test_import_empty_file(self, tmp_path: Path):
        path = tmp_path / "empty.ris"
        path.write_text("")
        items = ZoteroConnector.import_ris(path)
        assert items == []
