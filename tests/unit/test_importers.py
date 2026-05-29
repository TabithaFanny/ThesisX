"""Tests for MarkdownImporter and BibTeXImporter (Vision 3.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.knowledge.importers import MarkdownImporter, BibTeXImporter
from app.core.knowledge.models import KnowledgeItem


class TestMarkdownImporter:
    def test_parse_multi_section(self, tmp_path: Path):
        md = tmp_path / "notes.md"
        md.write_text("## Section A\n\nContent A.\n\n## Section B\n\nContent B.", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert len(items) == 2
        assert items[0].title == "Section A"
        assert "Content A" in items[0].content
        assert items[1].title == "Section B"

    def test_parse_single_section_no_headings(self, tmp_path: Path):
        md = tmp_path / "simple.md"
        md.write_text("Just plain text without any headings.", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert len(items) == 1
        assert items[0].item_type == "note"
        assert "plain text" in items[0].content

    def test_parse_empty_file(self, tmp_path: Path):
        md = tmp_path / "empty.md"
        md.write_text("", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert len(items) == 1
        assert items[0].content == ""

    def test_parse_with_frontmatter(self, tmp_path: Path):
        md = tmp_path / "fm.md"
        md.write_text(
            "---\ntags: [ml, ai]\n---\n\n## My Note\n\nContent here.",
            encoding="utf-8",
        )
        items = MarkdownImporter.parse_file(md)
        assert len(items) == 1
        assert "ml" in items[0].tags
        assert "ai" in items[0].tags
        assert items[0].title == "My Note"

    def test_parse_frontmatter_with_list(self, tmp_path: Path):
        md = tmp_path / "fm2.md"
        md.write_text(
            "---\n- research\n- draft\n---\n\nSome content without headings.",
            encoding="utf-8",
        )
        items = MarkdownImporter.parse_file(md)
        assert len(items) == 1
        assert "research" in items[0].tags
        assert "draft" in items[0].tags

    def test_all_items_are_notes(self, tmp_path: Path):
        md = tmp_path / "notes.md"
        md.write_text("## A\n\nBody A.\n\n## B\n\nBody B.", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert all(it.item_type == "note" for it in items)

    def test_source_file_is_set(self, tmp_path: Path):
        md = tmp_path / "src.md"
        md.write_text("## Test\n\nBody.", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert all(str(md) == it.source_file for it in items)

    def test_external_source_is_import(self, tmp_path: Path):
        md = tmp_path / "ext.md"
        md.write_text("Content.", encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert all(it.external_source == "import" for it in items)

    def test_content_truncated_to_5000(self, tmp_path: Path):
        md = tmp_path / "big.md"
        md.write_text("## Big\n\n" + ("x" * 6000), encoding="utf-8")
        items = MarkdownImporter.parse_file(md)
        assert len(items[0].content) <= 5000


class TestBibTeXImporter:
    def test_parse_single_article(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text(
            """@article{smith2020,
  author = {Smith, John and Doe, Jane},
  title = {Machine Learning Approaches},
  journal = {Journal of AI Research},
  year = {2020},
  doi = {10.1234/abc}
}""",
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert len(items) == 1
        item = items[0]
        assert item.item_type == "literature"
        assert item.title == "Machine Learning Approaches"
        assert "Smith, John" in item.content
        assert "2020" in item.content
        assert "Journal of AI Research" in item.content
        assert "10.1234/abc" in item.content

    def test_parse_multiple_entries(self, tmp_path: Path):
        bib = tmp_path / "multi.bib"
        bib.write_text(
            """@article{a1,
  author = {Smith, John},
  title = {Article 1},
  year = {2020}
}

@book{b1,
  author = {Jones, Mary},
  title = {Book 1},
  year = {2019}
}""",
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert len(items) == 2
        titles = {it.title for it in items}
        assert "Article 1" in titles
        assert "Book 1" in titles

    def test_missing_title_falls_back_to_cite_key(self, tmp_path: Path):
        bib = tmp_path / "nottitle.bib"
        bib.write_text(
            """@misc{my_citation_key,
  author = {Anonymous},
  year = {2023}
}""",
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert len(items) == 1
        assert "My Citation Key" in items[0].title

    def test_tags_include_entry_type_and_year(self, tmp_path: Path):
        bib = tmp_path / "tags.bib"
        bib.write_text(
            """@article{test,
  title = {Test},
  year = {2022}
}""",
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert "article" in items[0].tags
        assert "2022" in items[0].tags

    def test_missing_author_defaults_to_unknown(self, tmp_path: Path):
        bib = tmp_path / "noauthor.bib"
        bib.write_text(
            """@article{test,
  title = {No Author Paper},
  year = {2021}
}""",
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert "Authors: Unknown" in items[0].content

    def test_empty_bib_file(self, tmp_path: Path):
        bib = tmp_path / "empty.bib"
        bib.write_text("", encoding="utf-8")
        items = BibTeXImporter.parse_file(bib)
        assert items == []

    def test_external_source_is_import(self, tmp_path: Path):
        bib = tmp_path / "src.bib"
        bib.write_text("@article{test, title = {Test}}", encoding="utf-8")
        items = BibTeXImporter.parse_file(bib)
        assert all(it.external_source == "import" for it in items)

    def test_quoted_field_values(self, tmp_path: Path):
        bib = tmp_path / "quoted.bib"
        bib.write_text(
            '''@article{test,
  author = "Smith, John",
  title = "Quoted Title",
  year = "2020"
}''',
            encoding="utf-8",
        )
        items = BibTeXImporter.parse_file(bib)
        assert len(items) == 1
        assert items[0].title == "Quoted Title"
        assert "Smith, John" in items[0].content
