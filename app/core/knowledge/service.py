"""Knowledge Base service — file import, parsing, and search."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Claim, KnowledgeChunk, KnowledgeSource
from .parser import parse_file


class KnowledgeService:
    """Manages the local Knowledge Base at ~/.wenbiao/knowledge/."""

    KB_DIR = Path.home() / ".wenbiao" / "knowledge"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.kb_dir = Path(base_dir or self.KB_DIR).expanduser()
        self.sources_dir = self.kb_dir / "sources"
        self.chunks_dir = self.kb_dir / "chunks"
        self.claims_dir = self.kb_dir / "claims"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.claims_dir.mkdir(parents=True, exist_ok=True)

    # Maximum file size: 50 MB
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

    def import_file(self, file_path: str) -> KnowledgeSource:
        """Import a file into the Knowledge Base.

        Returns the created KnowledgeSource.
        Raises ValueError for unsupported file types.
        Raises FileNotFoundError if the file doesn't exist.
        Raises ValueError if the file exceeds MAX_FILE_SIZE_BYTES.
        """
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                f"Maximum supported size is {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        suffix = path.suffix.lower()
        source_type = {
            ".txt": "txt",
            ".md": "markdown",
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
        }.get(suffix)

        if not source_type:
            raise ValueError(f"Unsupported file type: {suffix}")

        # Create source
        source = KnowledgeSource.new(
            title=path.stem.replace("-", " ").replace("_", " ").title(),
            source_type=source_type,
            path=str(path),
        )
        source.status = "pending"

        # Parse and chunk
        source, chunks = parse_file(source)

        # Save source
        self._save_source(source)

        # Save chunks
        self._save_chunks(source.id, chunks)

        return source

    def list_sources(self) -> list[KnowledgeSource]:
        """List all imported sources."""
        sources: list[KnowledgeSource] = []
        for path in self.sources_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                sources.append(KnowledgeSource.from_dict(data))
            except Exception:
                continue
        sources.sort(key=lambda s: s.created_at, reverse=True)
        return sources

    def get_source(self, source_id: str) -> KnowledgeSource | None:
        """Get a source by ID."""
        path = self.sources_dir / f"{source_id}.json"
        if not path.exists():
            return None
        try:
            return KnowledgeSource.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            return None

    def get_chunks(self, source_id: str) -> list[KnowledgeChunk]:
        """Get all chunks for a source."""
        path = self.chunks_dir / f"{source_id}.jsonl"
        if not path.exists():
            return []
        chunks: list[KnowledgeChunk] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(KnowledgeChunk.from_dict(json.loads(line)))
            except Exception:
                continue
        return chunks

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

    def search(self, query: str, top_k: int = 10) -> list[tuple[KnowledgeChunk, float]]:
        """Simple keyword search across all chunks.

        Returns list of (chunk, score) sorted by relevance score descending.
        No embedding — just keyword overlap scoring.
        """
        query_words = self._extract_words(query)
        if not query_words:
            return []

        results: list[tuple[KnowledgeChunk, float]] = []

        for chunk_path in self.chunks_dir.glob("*.jsonl"):
            for line in chunk_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = KnowledgeChunk.from_dict(json.loads(line))
                except Exception:
                    continue

                chunk_words = self._extract_words(chunk.text)
                overlap = len(query_words & chunk_words)
                if overlap > 0:
                    score = overlap / (len(query_words) + len(chunk_words) - overlap)
                    results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def delete_source(self, source_id: str) -> bool:
        """Delete a source and its chunks. Returns True if deleted."""
        source_path = self.sources_dir / f"{source_id}.json"
        chunks_path = self.chunks_dir / f"{source_id}.jsonl"
        deleted = False
        if source_path.exists():
            source_path.unlink()
            deleted = True
        if chunks_path.exists():
            chunks_path.unlink()
            deleted = True
        return deleted

    def _save_source(self, source: KnowledgeSource) -> None:
        path = self.sources_dir / f"{source.id}.json"
        path.write_text(json.dumps(source.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def export_chunks_as_context(self, source_ids: list[str], output_path: str | Path) -> int:
        """Export chunks from selected sources as a Markdown context file.

        Returns the number of chunks written.
        """
        out = Path(output_path)
        lines: list[str] = ["# Knowledge Context\n"]
        total = 0
        for sid in source_ids:
            src = self.get_source(sid)
            if not src:
                continue
            lines.append(f"\n## {src.title}\n")
            for chunk in self.get_chunks(sid):
                lines.append(f"\n### {chunk.heading or '片段'}\n")
                lines.append(chunk.text)
                total += 1
        out.write_text("\n".join(lines), encoding="utf-8")
        return total

    def _save_chunks(self, source_id: str, chunks: list[KnowledgeChunk]) -> None:
        path = self.chunks_dir / f"{source_id}.jsonl"
        lines = [json.dumps(c.to_dict(), ensure_ascii=False) for c in chunks]
        path.write_text("\n".join(lines), encoding="utf-8")

    # ── Claim extraction (Vision 3.3 Theory Matcher) ──────────────────────

    def extract_claims(
        self,
        source_id: str,
        claim_type: str = "fact",
        min_length: int = 20,
    ) -> list[Claim]:
        """Extract claims from all chunks of a source.

        Simple rule-based extraction: sentences longer than min_length
        that contain factual indicators (实验表明、结果显示、研究发现).
        """
        factual_patterns = [
            "表明", "显示", "发现", "证实", "证明",
            "结果显示", "实验表明", "研究发现",
            "表明了", "证明了",
        ]
        claims: list[Claim] = []
        for chunk in self.get_chunks(source_id):
            sentences = re.split(r"[。；！？\n]", chunk.text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) < min_length:
                    continue
                if any(pat in sent for pat in factual_patterns):
                    claim = Claim.new(
                        source_id=source_id,
                        chunk_id=chunk.id,
                        claim_text=sent,
                        claim_type=claim_type,
                    )
                    claims.append(claim)
        if claims:
            self._save_claims(source_id, claims)
        return claims

    def list_claims(self, source_id: str) -> list[Claim]:
        path = self.claims_dir / f"{source_id}.jsonl"
        if not path.exists():
            return []
        claims: list[Claim] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                claims.append(Claim.from_dict(json.loads(line)))
            except Exception:
                continue
        return claims

    def _save_claims(self, source_id: str, claims: list[Claim]) -> None:
        path = self.claims_dir / f"{source_id}.jsonl"
        lines = [json.dumps(c.to_dict(), ensure_ascii=False) for c in claims]
        path.write_text("\n".join(lines), encoding="utf-8")
