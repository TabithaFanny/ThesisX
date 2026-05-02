"""Tests for KnowledgeService."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.core.knowledge import KnowledgeService


@pytest.fixture
def kb_service(tmp_path: Path) -> KnowledgeService:
    """Create a KnowledgeService backed by a temp directory."""
    svc = KnowledgeService(base_dir=tmp_path / "kb")
    return svc


class TestImportFile:
    def test_import_txt_creates_source_and_chunks(self, kb_service: KnowledgeService, tmp_path: Path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a test document.\n\n## Section One\n\nContent here.", encoding="utf-8")

        src = kb_service.import_file(str(txt_file))

        assert src.id is not None
        assert src.title == "Test"
        assert src.source_type == "txt"
        assert src.status == "parsed"
        assert src.chunk_count >= 1

        chunks = kb_service.get_chunks(src.id)
        assert len(chunks) >= 1

    def test_import_md_creates_source(self, kb_service: KnowledgeService, tmp_path: Path):
        md_file = tmp_path / "notes.md"
        md_file.write_text("# Notes\n\nSome notes with **bold** text.", encoding="utf-8")

        src = kb_service.import_file(str(md_file))

        assert src.source_type == "markdown"
        assert src.status == "parsed"

    def test_rejects_unsupported_type(self, kb_service: KnowledgeService, tmp_path: Path):
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("data", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported file type"):
            kb_service.import_file(str(bad_file))

    def test_rejects_nonexistent_file(self, kb_service: KnowledgeService):
        with pytest.raises(FileNotFoundError):
            kb_service.import_file("/nonexistent/file.txt")

    def test_rejects_oversized_file(self, kb_service: KnowledgeService, tmp_path: Path):
        large_file = tmp_path / "large.txt"
        # Write more than MAX_FILE_SIZE_BYTES (50MB)
        large_file.write_bytes(b"x" * (51 * 1024 * 1024))

        with pytest.raises(ValueError, match="File too large"):
            kb_service.import_file(str(large_file))

    def test_import_updates_source_path(self, kb_service: KnowledgeService, tmp_path: Path):
        txt_file = tmp_path / "my_doc.txt"
        txt_file.write_text("Content", encoding="utf-8")

        src = kb_service.import_file(str(txt_file))

        assert src.path == str(txt_file)


class TestListSources:
    def test_list_sources_returns_sorted_list(self, kb_service: KnowledgeService, tmp_path: Path):
        # Import two files
        (tmp_path / "a.txt").write_text("AAA", encoding="utf-8")
        (tmp_path / "b.txt").write_text("BBB", encoding="utf-8")

        kb_service.import_file(str(tmp_path / "a.txt"))
        kb_service.import_file(str(tmp_path / "b.txt"))

        sources = kb_service.list_sources()
        assert len(sources) == 2
        # Most recent first
        assert sources[0].title in ("A", "B")

    def test_list_sources_empty_dir(self, kb_service: KnowledgeService):
        sources = kb_service.list_sources()
        assert sources == []


class TestSearch:
    def test_search_finds_matching_chunks(self, kb_service: KnowledgeService, tmp_path: Path):
        txt_file = tmp_path / "search_test.txt"
        txt_file.write_text("Machine learning is a subset of artificial intelligence.", encoding="utf-8")

        kb_service.import_file(str(txt_file))

        results = kb_service.search("machine learning")
        assert len(results) >= 1
        chunk, score = results[0]
        assert score > 0

    def test_search_returns_empty_for_no_match(self, kb_service: KnowledgeService, tmp_path: Path):
        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("Completely unrelated content.", encoding="utf-8")

        kb_service.import_file(str(txt_file))

        results = kb_service.search("machine learning")
        assert len(results) == 0

    def test_search_handles_empty_query(self, kb_service: KnowledgeService):
        results = kb_service.search("")
        assert results == []


class TestDeleteSource:
    def test_delete_removes_source_and_chunks(self, kb_service: KnowledgeService, tmp_path: Path):
        txt_file = tmp_path / "to_delete.txt"
        txt_file.write_text("Content to delete.", encoding="utf-8")

        src = kb_service.import_file(str(txt_file))
        assert kb_service.get_source(src.id) is not None

        kb_service.delete_source(src.id)

        assert kb_service.get_source(src.id) is None
        assert kb_service.get_chunks(src.id) == []

    def test_delete_nonexistent_id_returns_false(self, kb_service: KnowledgeService):
        result = kb_service.delete_source("nonexistent-id")
        assert result is False
