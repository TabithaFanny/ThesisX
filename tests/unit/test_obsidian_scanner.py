"""Tests for ObsidianScanner (Vision 3.7)."""

from __future__ import annotations

import pytest
from pathlib import Path

from app.core.connectors.obsidian import ObsidianScanner


# ── scan vault ──────────────────────────────────────────────────────────────

class TestScanVault:
    def test_scan_empty_vault(self, tmp_path: Path):
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert items == []

    def test_scan_single_note(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_text("# My Note\n\nContent here.")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert len(items) == 1
        assert items[0].title == "note"
        assert "Content here" in items[0].content
        assert items[0].external_source == "obsidian"

    def test_scan_respects_max_files(self, tmp_path: Path):
        for i in range(10):
            (tmp_path / f"note_{i}.md").write_text(f"# Note {i}")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan(max_files=3)
        assert len(items) == 3

    def test_scan_skips_empty_files(self, tmp_path: Path):
        (tmp_path / "empty.md").write_text("")
        (tmp_path / "real.md").write_text("# Real")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert len(items) == 1


# ── frontmatter parsing ─────────────────────────────────────────────────────

class TestFrontmatter:
    def test_extracts_title_from_frontmatter(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_text("---\ntitle: \"Custom Title\"\ntags: [research]\n---\n# Body")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert items[0].title == "Custom Title"

    def test_extracts_tags_from_frontmatter(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_text("---\ntags: [research, theory, paper]\n---\n# Content")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert "research" in items[0].tags
        assert "theory" in items[0].tags

    def test_no_frontmatter_uses_filename(self, tmp_path: Path):
        note = tmp_path / "my-note.md"
        note.write_text("# Just a heading\n\nContent.")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert items[0].title == "my-note"


# ── wikilinks ────────────────────────────────────────────────────────────────

class TestWikilinks:
    def test_extracts_wikilinks_as_tags(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_text("See [[institutional theory]] and [[path dependence]].")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert "institutional theory" in items[0].tags
        assert "path dependence" in items[0].tags

    def test_wikilinks_with_aliases(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_text("See [[institutional theory|IT theory]] for details.")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert "institutional theory" in items[0].tags


# ── errors ──────────────────────────────────────────────────────────────────

class TestErrors:
    def test_nonexistent_vault_raises(self, tmp_path: Path):
        bad_path = tmp_path / "does_not_exist"
        with pytest.raises(NotADirectoryError):
            ObsidianScanner(bad_path)

    def test_binary_file_skipped(self, tmp_path: Path):
        note = tmp_path / "note.md"
        note.write_bytes(b"\x00\x01\x02")
        scanner = ObsidianScanner(tmp_path)
        items = scanner.scan()
        assert items == []  # Should not crash
