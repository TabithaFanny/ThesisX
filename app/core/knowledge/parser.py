"""File parser for Knowledge Base import.

Supports: .txt, .md (native), .pdf (PyMuPDF + pdfminer), .docx (python-docx).
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import KnowledgeSource, KnowledgeChunk


def parse_file(source: KnowledgeSource) -> tuple[KnowledgeSource, list[KnowledgeChunk]]:
    """Parse a file and return updated source + extracted chunks.

    Raises ValueError for unsupported file types.
    """
    path = Path(source.path)
    suffix = path.suffix.lower()

    text: str
    if suffix == ".txt":
        text = _parse_txt(path)
    elif suffix == ".md":
        text = _parse_md(path)
    elif suffix == ".pdf":
        text = _parse_pdf(path)
    elif suffix in (".docx", ".doc"):
        text = _parse_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Update summary (first 300 chars)
    source.summary = text[:300].strip()
    source.status = "parsed"

    # Chunk by sections (### heading or double newline)
    chunks = _chunk_text(source.id, text)

    source.chunk_count = len(chunks)
    return source, chunks


def _parse_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_md(path: Path) -> str:
    content = path.read_text(encoding="utf-8", errors="replace")
    # Strip YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    return content


def _parse_pdf(path: Path) -> str:
    """Extract text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz

        doc = fitz.open(str(path))
        pages: list[str] = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)
    except Exception:
        pass

    # Fallback to pdfminer
    try:
        from pdfminer.high_level import extract_text

        return extract_text(str(path))
    except Exception:
        return ""


def _parse_docx(path: Path) -> str:
    """Extract text from .docx using python-docx."""
    try:
        import docx

        doc = docx.Document(str(path))
        paragraphs: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n\n".join(paragraphs)
    except Exception:
        return ""


def _chunk_text(source_id: str, text: str, max_chars: int = 800) -> list[KnowledgeChunk]:
    """Split text into chunks by heading or by character limit.

    Prefers splitting at markdown headings (##, ###) for semantic coherence.
    """
    chunks: list[KnowledgeChunk] = []

    # Split by markdown headings first
    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    current_body: list[str] = []

    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            # Save previous section
            if current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = line.lstrip("#").strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body:
        sections.append((current_heading, "\n".join(current_body)))

    for heading, body in sections:
        body = body.strip()
        if not body:
            continue

        # If section is small enough, make one chunk
        if len(body) <= max_chars:
            chunks.append(KnowledgeChunk.new(source_id, body, heading))
        else:
            # Split by paragraphs within section
            for para in body.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                if len(para) <= max_chars:
                    chunks.append(KnowledgeChunk.new(source_id, para, heading))
                else:
                    # Split by sentence or line
                    for i in range(0, len(para), max_chars):
                        sub = para[i : i + max_chars].strip()
                        if sub:
                            chunks.append(KnowledgeChunk.new(source_id, sub, heading))

    # Extract keywords from chunks (simple approach: significant words)
    for chunk in chunks:
        chunk.keywords = _extract_keywords(chunk.text)

    return chunks


def _extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract simple keywords: most common non-stopword tokens."""
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "this", "that", "these", "those",
        "it", "its", "as", "we", "our", "you", "your", "he", "she", "they",
        "them", "their", "what", "which", "who", "when", "where", "how", "why",
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "没有", "看", "好", "自己", "这",
    }
    words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]{2,}\b", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]
