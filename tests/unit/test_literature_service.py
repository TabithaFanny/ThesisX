"""Tests for LiteratureService — PDF import, BibTeX parsing, CRUD, search, formatters."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.core.literature import LiteratureService, Reference


class TestLiteratureService:
    """Tests for LiteratureService using temp directories."""

    @pytest.fixture
    def svc(self, tmp_path):
        return LiteratureService(base_dir=tmp_path)

    def test_list_references_empty(self, svc):
        assert svc.list_references() == []

    def test_import_pdf_not_found(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.import_pdf("/nonexistent/file.pdf")

    def test_import_bibtex_not_found(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.import_bibtex("/nonexistent/bib.bib")

    def test_import_bibtex_empty(self, svc, tmp_path):
        bib = tmp_path / "empty.bib"
        bib.write_text("", encoding="utf-8")
        refs = svc.import_bibtex(str(bib))
        assert refs == []

    def test_import_bibtex_single_entry(self, svc, tmp_path):
        bib = tmp_path / "test.bib"
        bib.write_text(
            '@article{test2024,\n  author = {张三 and 李四},\n  title = {测试论文},\n  year = {2024},\n  journal = {计算机学报},\n  doi = {10.1234/test}\n}',
            encoding="utf-8",
        )
        refs = svc.import_bibtex(str(bib))
        assert len(refs) == 1
        assert refs[0].title == "测试论文"
        assert refs[0].authors == ["张三", "李四"]
        assert refs[0].year == "2024"
        assert refs[0].journal == "计算机学报"
        assert refs[0].doi == "10.1234/test"

    def test_import_bibtex_multiple_entries(self, svc, tmp_path):
        bib = tmp_path / "multi.bib"
        bib.write_text(
            '@article{a2024,\n  author = {王五},\n  title = {论文A},\n  year = {2024},\n  journal = {A期刊}\n}\n'
            '@book{b2023,\n  author = {赵六},\n  title = {书籍B},\n  year = {2023},\n  booktitle = {B出版社}\n}',
            encoding="utf-8",
        )
        refs = svc.import_bibtex(str(bib))
        assert len(refs) == 2
        titles = {r.title for r in refs}
        assert titles == {"论文A", "书籍B"}

    def test_list_references(self, svc, tmp_path):
        bib = tmp_path / "list.bib"
        bib.write_text(
            '@article{r1,\n  author = {Author One},\n  title = {Paper One},\n  year = {2023}\n}\n'
            '@article{r2,\n  author = {Author Two},\n  title = {Paper Two},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        svc.import_bibtex(str(bib))
        refs = svc.list_references()
        assert len(refs) == 2

    def test_list_references_sorted_by_created_at(self, svc, tmp_path):
        bib = tmp_path / "sort.bib"
        bib.write_text(
            '@article{r1,\n  author = {A},\n  title = {First},\n  year = {2020}\n}\n'
            '@article{r2,\n  author = {B},\n  title = {Second},\n  year = {2021}\n}\n'
            '@article{r3,\n  author = {C},\n  title = {Third},\n  year = {2022}\n}',
            encoding="utf-8",
        )
        svc.import_bibtex(str(bib))
        refs = svc.list_references()
        # Most recently created (imported last) should be first
        created_ats = [r.created_at for r in refs]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_search_references(self, svc, tmp_path):
        bib = tmp_path / "search.bib"
        bib.write_text(
            '@article{s1,\n  author = {研究者A},\n  title = {人工智能研究},\n  year = {2024}\n}\n'
            '@article{s2,\n  author = {研究者B},\n  title = {机器学习应用},\n  year = {2023}\n}\n'
            '@article{s3,\n  author = {研究者C},\n  title = {数据分析方法},\n  year = {2022}\n}',
            encoding="utf-8",
        )
        svc.import_bibtex(str(bib))
        results = svc.search_references("人工智能")
        assert len(results) >= 1
        assert "人工智能" in results[0].title

    def test_search_references_no_query(self, svc):
        assert svc.search_references("") == []
        assert svc.search_references("  ") == []

    def test_search_references_by_author(self, svc, tmp_path):
        bib = tmp_path / "auth.bib"
        bib.write_text(
            '@article{a1,\n  author = {王小明},\n  title = {论文X},\n  year = {2024}\n}\n'
            '@article{a2,\n  author = {张小红},\n  title = {论文Y},\n  year = {2023}\n}',
            encoding="utf-8",
        )
        svc.import_bibtex(str(bib))
        results = svc.search_references("王小明")
        assert len(results) >= 1

    def test_add_tag(self, svc, tmp_path):
        bib = tmp_path / "tag.bib"
        bib.write_text(
            '@article{t1,\n  author = {Test},\n  title = {Tagged Paper},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        [ref] = svc.import_bibtex(str(bib))
        updated = svc.add_tag(ref.id, "AI")
        assert updated is not None
        assert "AI" in updated.tags

    def test_add_duplicate_tag_noop(self, svc, tmp_path):
        bib = tmp_path / "tag2.bib"
        bib.write_text(
            '@article{t2,\n  author = {Test},\n  title = {Tagged Paper 2},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        [ref] = svc.import_bibtex(str(bib))
        svc.add_tag(ref.id, "AI")
        updated = svc.add_tag(ref.id, "AI")  # add same tag again
        assert updated is not None
        assert updated.tags.count("AI") == 1

    def test_remove_tag(self, svc, tmp_path):
        bib = tmp_path / "rtag.bib"
        bib.write_text(
            '@article{rt1,\n  author = {Test},\n  title = {Remove Tag Paper},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        [ref] = svc.import_bibtex(str(bib))
        svc.add_tag(ref.id, "AI")
        updated = svc.remove_tag(ref.id, "AI")
        assert updated is not None
        assert "AI" not in updated.tags

    def test_delete_reference(self, svc, tmp_path):
        bib = tmp_path / "del.bib"
        bib.write_text(
            '@article{d1,\n  author = {Test},\n  title = {Delete Me},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        [ref] = svc.import_bibtex(str(bib))
        assert svc.delete_reference(ref.id) is True
        assert svc.get_reference(ref.id) is None

    def test_delete_nonexistent(self, svc):
        assert svc.delete_reference("nonexistent-id") is False

    def test_update_reference(self, svc, tmp_path):
        bib = tmp_path / "upd.bib"
        bib.write_text(
            '@article{u1,\n  author = {Test},\n  title = {Original Title},\n  year = {2024}\n}',
            encoding="utf-8",
        )
        [ref] = svc.import_bibtex(str(bib))
        ref.title = "Updated Title"
        updated = svc.update_reference(ref)
        assert updated.title == "Updated Title"
        # Verify persistence
        reloaded = svc.get_reference(ref.id)
        assert reloaded is not None
        assert reloaded.title == "Updated Title"


class TestReferenceModel:
    """Tests for Reference model and formatters."""

    def test_reference_new(self):
        ref = Reference.new(title="Test", authors=["A"], year="2024", journal="J")
        assert ref.title == "Test"
        assert ref.authors == ["A"]
        assert ref.year == "2024"
        assert ref.journal == "J"
        assert ref.id is not None

    def test_reference_to_dict(self):
        ref = Reference.new(title="Test", authors=["A", "B"], year="2024", journal="J")
        d = ref.to_dict()
        assert d["title"] == "Test"
        assert d["authors"] == ["A", "B"]
        assert d["year"] == "2024"
        assert d["journal"] == "J"

    def test_reference_from_dict(self):
        data = {
            "id": "abc",
            "title": "From Dict",
            "authors": ["X"],
            "year": "2023",
            "journal": "K",
            "doi": "10.1234/ab",
            "abstract": "Abstract text",
            "file_path": "/path/to/f.pdf",
            "zotero_key": "",
            "tags": ["tag1"],
            "indexed": False,
            "created_at": "2024-01-01T00:00:00",
        }
        ref = Reference.from_dict(data)
        assert ref.id == "abc"
        assert ref.title == "From Dict"
        assert ref.tags == ["tag1"]

    def test_format_gbt7714(self):
        ref = Reference.new(
            title="论文标题",
            authors=["张三", "李四"],
            year="2024",
            journal="计算机学报",
        )
        formatted = ref.format_gbt7714()
        assert "张三" in formatted
        assert "李四" in formatted
        assert "2024" in formatted
        assert "论文标题" in formatted

    def test_format_apa(self):
        ref = Reference.new(
            title="论文标题",
            authors=["王五"],
            year="2023",
            journal="J. of Testing",
        )
        formatted = ref.format_apa()
        assert "王五" in formatted
        assert "2023" in formatted
        assert "J. of Testing" in formatted
