"""Zotero connector — minimal import via BibTeX export.

Phase 1: Read Zotero BibTeX/RIS export files.
Phase 2 (future): Zotero Web API / Local API integration.
"""

from __future__ import annotations

from pathlib import Path

from app.core.literature import LiteratureService


class ZoteroConnector:
    """Connect to Zotero via exported BibTeX or RIS files."""

    def __init__(self) -> None:
        self._svc = LiteratureService()

    def import_from_bibtex(self, bib_path: str) -> list[dict]:
        """Import references from a Zotero-exported BibTeX file.

        Zotero exports via: File > Export Library > BibTeX
        """
        refs = self._svc.import_bibtex(bib_path)
        return [r.to_dict() for r in refs]

    def import_from_ris(self, ris_path: str) -> list[dict]:
        """Import references from a Zotero-exported RIS file.

        Zotero exports via: File > Export Library > RIS
        """
        path = Path(ris_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {ris_path}")

        refs = self._parse_ris(path.read_text(encoding="utf-8"))
        imported: list[dict] = []
        for ref in refs:
            self._svc._save(ref)  # pylint: disable=protected-access
            imported.append(ref.to_dict())
        return imported

    def _parse_ris(self, text: str) -> list:
        """Simple RIS format parser.

        RIS format is tag-led: each line is TY  - value or ER  - (end record)
        Common tags: TY (type), AU (author), TI (title), JO/JF (journal),
                     PY (year), DO (doi), AB (abstract)
        """
        from app.core.literature.models import Reference

        refs: list[Reference] = []
        current: dict = {}

        for line in text.split("\n"):
            if not line.strip():
                continue
            if line.startswith("ER"):
                if current:
                    ref = Reference.new(
                        title=current.get("TI", "Untitled"),
                        authors=current.get("AU", []),
                        year=current.get("PY", ""),
                        journal=current.get("JO") or current.get("JF"),
                        doi=current.get("DO"),
                        abstract=current.get("AB"),
                    )
                    refs.append(ref)
                    current = {}
                continue

            if " - " in line:
                tag, _, val = line.partition(" - ")
                tag = tag.strip()
                val = val.strip()

                if tag == "AU":
                    current.setdefault("AU", []).append(val)
                elif tag == "TI":
                    current["TI"] = val
                elif tag == "PY":
                    # RIS year may include date portion
                    current["PY"] = val[:4]
                elif tag in ("JO", "JF"):
                    current["JO"] = val
                elif tag == "DO":
                    current["DO"] = val
                elif tag == "AB":
                    current["AB"] = val

        return refs
