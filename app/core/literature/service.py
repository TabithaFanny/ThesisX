"""Literature management service — import, parse, and search references."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from .models import Reference


class LiteratureService:
    """Manages the local literature library at ~/.wenbiao/literature/."""

    LIT_DIR = Path.home() / ".wenbiao" / "literature"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.lit_dir = Path(base_dir or self.LIT_DIR).expanduser()
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.lit_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Import
    # -------------------------------------------------------------------------

    def import_pdf(self, file_path: str) -> Reference:
        """Extract metadata from a PDF and create a Reference.

        Uses PyMuPDF (fitz) to extract title and first-page text.
        Raises FileNotFoundError if the file doesn't exist.
        """
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        import fitz

        doc = fitz.open(str(path))
        metadata = doc.metadata

        # Extract title from metadata or first heading
        title = metadata.get("title", "").strip()
        if not title:
            title = self._extract_title_from_pdf(doc) or path.stem.replace("-", " ").title()

        # Extract author from metadata
        author_str = metadata.get("author", "")
        authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []

        # Extract year from creation date
        creation_date = metadata.get("creationDate", "")
        year = self._extract_year(creation_date)

        doc.close()

        ref = Reference.new(
            title=title,
            authors=authors,
            year=year,
            file_path=str(path),
        )
        self._save(ref)
        return ref

    def _extract_title_from_pdf(self, doc: "fitz.Document") -> str | None:
        """Try to get title from first non-empty large text block."""
        for page in doc:
            blocks = page.get_text("blocks")
            for block in blocks:
                text = block[4].strip()
                # Look for a line that looks like a title (shorter, no period)
                if text and len(text) < 200 and not text.startswith("@"):
                    return text.split("\n")[0].strip()
        return None

    def _extract_year(self, creation_date: str) -> str:
        """Extract year from PDF creation date string like 'D:20240115120000'."""
        if not creation_date:
            return ""
        # PDF dates are often D:YYYYMMDDHHmmSS
        m = re.search(r"D:(\d{4})", creation_date)
        if m:
            return m.group(1)
        return ""

    def import_bibtex(self, bib_path: str) -> list[Reference]:
        """Parse a BibTeX file and import all entries as References.

        Returns list of imported References.
        Raises FileNotFoundError if the file doesn't exist.
        """
        path = Path(bib_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {bib_path}")

        text = path.read_text(encoding="utf-8")
        refs = self._parse_bibtex(text)
        for ref in refs:
            self._save(ref)
        return refs

    def _parse_bibtex(self, text: str) -> list[Reference]:
        """Simple BibTeX parser for common entry types.

        Handles: article, book, inproceedings, conference, thesis, misc
        Fields: author, title, journal, year, doi, abstract
        """
        refs: list[Reference] = []
        # Match @type{key, ... }
        entry_pattern = re.compile(
            r"@(\w+)\s*\{\s*[^,]*\s*,\s*(.*?)\n\s*\}",
            re.DOTALL | re.IGNORECASE,
        )
        field_pattern = re.compile(
            r"(\w+)\s*=\s*[{\"](.*?)[}\"]",
            re.DOTALL | re.IGNORECASE,
        )

        for entry_match in entry_pattern.finditer(text):
            entry_type = entry_match.group(1).lower()
            fields_text = entry_match.group(2)

            if entry_type not in ("article", "book", "inproceedings", "conference", "thesis", "misc", "phdthesis", "mastersthesis"):
                continue

            field_matches = field_pattern.finditer(fields_text)
            fields: dict[str, str] = {}
            for fm in field_matches:
                key = fm.group(1).lower()
                val = fm.group(2).strip()
                # Remove LaTeX braces
                val = re.sub(r"[{}]", "", val)
                # Unescape common LaTeX
                val = val.replace('\\"', '"').replace("\\&", "&")
                fields[key] = val

            # Parse authors (and .. or and)
            raw_authors = fields.get("author", "")
            authors = re.split(r"\s+and\s+", raw_authors)
            authors = [a.strip() for a in authors if a.strip()]

            year = fields.get("year", "")

            # Journal or booktitle
            journal = fields.get("journal") or fields.get("booktitle") or None

            # Thesis type
            thesis_type = ""
            if entry_type in ("thesis", "phdthesis", "mastersthesis"):
                thesis_type = "PhD" if "phd" in entry_type else "Master"
                journal = journal or f"{thesis_type} Thesis"

            ref = Reference.new(
                title=fields.get("title", "Untitled"),
                authors=authors,
                year=year,
                journal=journal,
                doi=fields.get("doi"),
                abstract=fields.get("abstract"),
            )
            refs.append(ref)

        return refs

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------

    def list_references(self, tag: str | None = None) -> list[Reference]:
        """List all references, optionally filtered by tag."""
        refs: list[Reference] = []
        for path in self.lit_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                ref = Reference.from_dict(data)
                if tag is None or tag in ref.tags:
                    refs.append(ref)
            except Exception:
                continue
        refs.sort(key=lambda r: r.created_at, reverse=True)
        return refs

    def get_reference(self, ref_id: str) -> Reference | None:
        path = self.lit_dir / f"{ref_id}.json"
        if not path.exists():
            return None
        try:
            return Reference.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            return None

    def update_reference(self, ref: Reference) -> Reference:
        """Update an existing reference."""
        self._save(ref)
        return ref

    def delete_reference(self, ref_id: str) -> bool:
        path = self.lit_dir / f"{ref_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def _extract_words(self, text: str) -> set[str]:
        """Extract searchable words from mixed Chinese/English text.

        English: word boundaries. Chinese: character n-grams (2-4 chars).
        """
        words: set[str] = set()
        english_part = re.sub(r"[\u4e00-\u9fff]", "", text.lower())
        english_words = re.findall(r"\b[a-zA-Z]{2,}\b", english_part)
        words.update(english_words)

        chinese_text = re.sub(r"[a-zA-Z0-9]", "", text)
        for n in range(2, 5):
            for i in range(len(chinese_text) - n + 1):
                words.add(chinese_text[i : i + n])
        return words

    def search_references(self, query: str) -> list[Reference]:
        """Full-text search across title, authors, abstract, and tags."""
        query_words = self._extract_words(query)
        if not query_words:
            return []

        results: list[tuple[Reference, int]] = []
        for ref in self.list_references():
            text_fields = " ".join([
                ref.title,
                " ".join(ref.authors),
                ref.journal or "",
                ref.abstract or "",
                " ".join(ref.tags),
            ])
            field_words = self._extract_words(text_fields)
            overlap = len(query_words & field_words)
            if overlap > 0:
                results.append((ref, overlap))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in results]

    def add_tag(self, ref_id: str, tag: str) -> Reference | None:
        """Add a tag to a reference."""
        ref = self.get_reference(ref_id)
        if ref is None:
            return None
        if tag not in ref.tags:
            ref.tags.append(tag)
            self._save(ref)
        return ref

    def remove_tag(self, ref_id: str, tag: str) -> Reference | None:
        """Remove a tag from a reference."""
        ref = self.get_reference(ref_id)
        if ref is None:
            return None
        if tag in ref.tags:
            ref.tags.remove(tag)
            self._save(ref)
        return ref

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _save(self, ref: Reference) -> None:
        path = self.lit_dir / f"{ref.id}.json"
        path.write_text(
            json.dumps(ref.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
