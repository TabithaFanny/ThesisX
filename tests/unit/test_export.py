"""Tests for export module (Vision 3.9)."""

from __future__ import annotations

import pytest
import zipfile
from pathlib import Path

from app.core.export.docx_exporter import DocxExporter
from app.core.export.citation_export import CitationExporter, Ref
from app.core.export.session_exporter import SessionExporter


# ── DocxExporter ────────────────────────────────────────────────────────────

class TestDocxExporter:
    def test_export_creates_file(self, tmp_path: Path):
        md = "# 标题\n\n段落内容。\n\n- 列表项1\n- 列表项2\n"
        out = tmp_path / "test.docx"
        result = DocxExporter.export(md, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_empty_markdown(self, tmp_path: Path):
        out = tmp_path / "empty.docx"
        DocxExporter.export("", out)
        assert out.exists()

    def test_export_with_bold_text(self, tmp_path: Path):
        md = "This is **bold** text."
        out = tmp_path / "bold.docx"
        DocxExporter.export(md, out)
        assert out.exists()

    def test_export_with_italic_text(self, tmp_path: Path):
        md = "This is *italic* text."
        out = tmp_path / "italic.docx"
        DocxExporter.export(md, out)
        assert out.exists()

    def test_export_with_headings(self, tmp_path: Path):
        md = "# H1\n## H2\n### H3\nContent."
        out = tmp_path / "headings.docx"
        DocxExporter.export(md, out)
        assert out.exists()

    def test_export_with_blockquote(self, tmp_path: Path):
        md = "> This is a quote."
        out = tmp_path / "quote.docx"
        DocxExporter.export(md, out)
        assert out.exists()

    def test_export_with_ordered_list(self, tmp_path: Path):
        md = "1. First\n2. Second"
        out = tmp_path / "ordered.docx"
        DocxExporter.export(md, out)
        assert out.exists()

    def test_export_with_custom_title(self, tmp_path: Path):
        md = "Content"
        out = tmp_path / "custom.docx"
        DocxExporter.export(md, out, title="自定义标题")
        assert out.exists()


# ── CitationExporter ────────────────────────────────────────────────────────

@pytest.fixture
def sample_refs() -> list[Ref]:
    return [
        Ref(
            key="smith2020deep",
            title="Deep Learning Approaches",
            authors="Smith, John and Jones, Mary",
            year="2020",
            journal="Journal of AI Research",
            doi="10.1234/jair.2020.1",
            abstract="A comprehensive study of deep learning methods.",
            cite_key="smith2020dla",
        ),
        Ref(
            key="lee2019ml",
            title="Machine Learning Basics",
            authors="Lee, Chen",
            year="2019",
            journal="ML Journal",
            cite_key="lee2019mlb",
        ),
    ]


class TestCitationExporter:
    def test_to_bibtex_format(self, sample_refs):
        result = CitationExporter.to_bibtex(sample_refs)
        assert "@article{" in result
        assert "smith2020dla" in result
        assert "Deep Learning Approaches" in result
        assert "Smith, John and Jones, Mary" in result

    def test_to_bibtex_multiple_entries(self, sample_refs):
        result = CitationExporter.to_bibtex(sample_refs)
        entries = result.count("@article{")
        assert entries == 2

    def test_to_ris_format(self, sample_refs):
        result = CitationExporter.to_ris(sample_refs)
        assert "TY  - JOUR" in result
        assert "ER  -" in result
        assert "Deep Learning Approaches" in result

    def test_to_ris_has_authors(self, sample_refs):
        result = CitationExporter.to_ris(sample_refs)
        assert "AU  - Smith, John" in result
        assert "AU  - Jones, Mary" in result

    def test_to_csl_json_format(self, sample_refs):
        import json
        result = CitationExporter.to_csl_json(sample_refs)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "Deep Learning Approaches"

    def test_to_csl_json_has_author_literals(self, sample_refs):
        import json
        result = CitationExporter.to_csl_json(sample_refs)
        data = json.loads(result)
        assert "author" in data[0]
        assert any(a["literal"] == "Smith, John" for a in data[0]["author"])

    def test_empty_refs(self):
        assert CitationExporter.to_bibtex([]) == ""
        assert CitationExporter.to_ris([]) == ""
        import json
        assert json.loads(CitationExporter.to_csl_json([])) == []

    def test_ris_required_fields(self):
        ref = Ref(key="test", title="Test Title", year="2023")
        result = CitationExporter.to_ris([ref])
        assert "PY  - 2023" in result
        assert "TI  - Test Title" in result


# ── SessionExporter ─────────────────────────────────────────────────────────

class TestSessionExporter:
    def test_archive_creates_zip(self, tmp_path: Path):
        # Create a fake session dir
        session_dir = tmp_path / "fake_session"
        session_dir.mkdir(parents=True)
        (session_dir / "events.jsonl").write_text('{"stage": "test"}\n')
        (session_dir / "output").mkdir(parents=True, exist_ok=True)
        (session_dir / "output" / "paper.md").write_text("# Test")

        out = tmp_path / "archive.zip"

        # Patch SESSIONS_DIR
        import app.core.export.session_exporter as m
        import unittest.mock
        with unittest.mock.patch.object(m.SessionExporter, "SESSIONS_DIR", tmp_path):
            result = m.SessionExporter.archive("fake_session", out)

        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

        # Verify zip contents
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            assert "events.jsonl" in names
            assert "output/paper.md" in names

    def test_archive_missing_session_raises(self):
        with pytest.raises(FileNotFoundError):
            SessionExporter.archive("nonexistent_session_12345")

    def test_list_sessions(self, tmp_path: Path):
        import app.core.export.session_exporter as m
        import unittest.mock

        with unittest.mock.patch.object(m.SessionExporter, "SESSIONS_DIR", tmp_path):
            (tmp_path / "sess1").mkdir()
            (tmp_path / "sess2").mkdir()
            (tmp_path / "_context").mkdir()  # should be excluded
            sessions = m.SessionExporter.list_sessions()
            assert "sess1" in sessions
            assert "sess2" in sessions
            assert "_context" not in sessions

    def test_csl_json_valid_structure(self):
        ref = Ref(key="test", title="Test", year="2023", doi="10.0/1")
        result = CitationExporter.to_csl_json([ref])
        import json
        data = json.loads(result)
        assert data[0]["type"] == "article-journal"
        assert "issued" in data[0]
