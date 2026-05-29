"""CitationExporter — export references as BibTeX, RIS, CSL JSON (Vision 3.9)."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class Ref:
    """Minimal reference for export."""
    key: str
    title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    doi: str = ""
    abstract: str = ""
    cite_key: str = ""


class CitationExporter:
    """Export reference lists to common formats."""

    @staticmethod
    def to_bibtex(refs: list[Ref]) -> str:
        """Convert reference list to BibTeX format."""
        entries: list[str] = []
        for r in refs:
            key = r.cite_key or r.key
            entries.append(f"@article{{{key},")
            if r.authors:
                entries.append(f"  author = {{{r.authors}}},")
            if r.title:
                entries.append(f"  title = {{{r.title}}},")
            if r.journal:
                entries.append(f"  journal = {{{r.journal}}},")
            if r.year:
                entries.append(f"  year = {{{r.year}}},")
            if r.doi:
                entries.append(f"  doi = {{{r.doi}}},")
            if r.abstract:
                entries.append(f"  abstract = {{{r.abstract}}},")
            entries.append("}\n")
        return "\n".join(entries)

    @staticmethod
    def to_ris(refs: list[Ref]) -> str:
        """Convert reference list to RIS format."""
        records: list[str] = []
        for r in refs:
            records.append("TY  - JOUR")
            if r.authors:
                for author in r.authors.split(" and "):
                    records.append(f"AU  - {author.strip()}")
            if r.title:
                records.append(f"TI  - {r.title}")
            if r.year:
                records.append(f"PY  - {r.year}")
            if r.journal:
                records.append(f"JO  - {r.journal}")
            if r.doi:
                records.append(f"DO  - {r.doi}")
            if r.abstract:
                records.append(f"AB  - {r.abstract}")
            records.append("ER  - \n")
        return "\n".join(records)

    @staticmethod
    def to_csl_json(refs: list[Ref]) -> str:
        """Convert reference list to CSL JSON format."""
        items: list[dict] = []
        for r in refs:
            item: dict = {
                "id": r.key,
                "type": "article-journal",
                "title": r.title,
                "DOI": r.doi,
            }
            if r.authors:
                item["author"] = [
                    {"literal": a.strip()} for a in r.authors.split(" and ")
                ]
            if r.year:
                item["issued"] = {"date-parts": [[int(r.year)]]}
            if r.journal:
                item["container-title"] = r.journal
            if r.abstract:
                item["abstract"] = r.abstract
            items.append(item)
        return json.dumps(items, ensure_ascii=False, indent=2)
