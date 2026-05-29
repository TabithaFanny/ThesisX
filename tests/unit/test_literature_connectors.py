"""Tests for Literature Intelligence connectors (Zotero RIS, Obsidian scanner)."""

import pytest
from pathlib import Path
from app.core.literature.zotero_connector import ZoteroConnector
from app.core.literature.obsidian_scanner import ObsidianVaultScanner, ObsidianNote


class TestZoteroConnectorRISParser:
    """Tests for the RIS format parser in ZoteroConnector."""

    def test_parse_ris_single_record(self):
        connector = ZoteroConnector()
        ris_text = """
TY  - JOUR
TI  - Deep Learning for Natural Language Processing
AU  - John Smith
PY  - 2023
JO  - AI Journal
AB  - This paper presents a new approach.
ER  -
"""
        refs = connector._parse_ris(ris_text)
        assert len(refs) == 1
        assert refs[0].title == "Deep Learning for Natural Language Processing"
        assert refs[0].authors == ["John Smith"]
        assert refs[0].year == "2023"

    def test_parse_ris_multiple_authors(self):
        connector = ZoteroConnector()
        ris_text = """
TY  - JOUR
TI  - Multi-Agent Systems
AU  - Alice Wang
AU  - Bob Chen
PY  - 2024
ER  -
"""
        refs = connector._parse_ris(ris_text)
        assert len(refs) == 1
        assert refs[0].authors == ["Alice Wang", "Bob Chen"]

    def test_parse_ris_multiple_records(self):
        connector = ZoteroConnector()
        ris_text = """
TY  - JOUR
TI  - Paper One
PY  - 2022
ER  -
TY  - BOOK
TI  - Paper Two
PY  - 2021
ER  -
"""
        refs = connector._parse_ris(ris_text)
        assert len(refs) == 2
        assert refs[0].title == "Paper One"
        assert refs[1].title == "Paper Two"

    def test_parse_ris_missing_fields(self):
        connector = ZoteroConnector()
        ris_text = """
TY  - JOUR
TI  - Minimal Paper
ER  -
"""
        refs = connector._parse_ris(ris_text)
        assert len(refs) == 1
        assert refs[0].title == "Minimal Paper"
        assert refs[0].authors == []


class TestObsidianNote:
    def test_obsidian_note_fields(self):
        note = ObsidianNote(
            path="/vault/notes/test.md",
            title="Test Note",
            tags=["#AI", "#Research"],
            links=["other_note"],
            backlinks=["backlink_note"],
            content="# Test\n\nThis is test content.",
        )
        assert note.title == "Test Note"
        assert "#AI" in note.tags
        assert "other_note" in note.links


class TestObsidianVaultScanner:
    def test_scanner_requires_directory(self, tmp_path):
        with pytest.raises(ValueError):
            ObsidianVaultScanner(str(tmp_path / "nonexistent"))

    def test_scan_empty_vault(self, tmp_path):
        scanner = ObsidianVaultScanner(str(tmp_path))
        notes = scanner.scan()
        assert notes == []
