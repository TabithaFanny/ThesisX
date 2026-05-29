"""RAG Context Engine — Vision 3.5.

TextChunker: splits text into overlapping chunks (512 tokens, 25% overlap).
ContextBundle: assembled context for injection into writing prompts.
SearchHistory: tracks recent searches for deduplication.
BM25: keyword-overlap scorer.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Optional


MAX_TOKENS = 512
OVERLAP_RATIO = 0.25  # 25% overlap


def _token_count(text: str) -> int:
    """Approximate token count (chars / 2 for Chinese, whitespace-split for English)."""
    chinese = re.sub(r"[a-zA-Z0-9\s]", "", text)
    english = re.sub(r"[\u4e00-\u9fff]", "", text)
    return len(chinese) + len(english.split())


def _extract_words(text: str) -> set[str]:
    """Extract searchable words from mixed Chinese/English text.

    English: word boundaries. Chinese: character 2-grams.
    """
    words: set[str] = set()
    english_part = re.sub(r"[\u4e00-\u9fff]", "", text.lower())
    english_words = re.findall(r"\b[a-zA-Z]{2,}\b", english_part)
    words.update(english_words)
    chinese_text = re.sub(r"[a-zA-Z0-9]", "", text)
    for i in range(len(chinese_text) - 1):
        words.add(chinese_text[i:i + 2])
    return words


class TextChunker:
    """Split text into overlapping chunks of ~MAX_TOKENS tokens.

    Overlap is OVERLAP_RATIO of the chunk size.
    Tries to break at paragraph or sentence boundaries.
    """

    PARAGRAPH_SEPARATORS = ["\n\n", "\r\n\r\n"]
    SENTENCE_ENDINGS = re.compile(r"[。！？.!?]\s*")

    @classmethod
    def chunk_text(cls, text: str, max_tokens: int = MAX_TOKENS) -> list[dict]:
        """Split text into overlapping chunks.

        Returns list of dicts with: id, text, start_char, end_char, chunk_index.
        """
        chunks: list[dict] = []
        if not text:
            return chunks

        # Split into paragraphs first
        paragraphs = cls._split_paragraphs(text)
        if not paragraphs:
            paragraphs = [text]

        overlap_tokens = int(max_tokens * OVERLAP_RATIO)
        overlap_chars = overlap_tokens * 2  # approximate

        current = ""
        char_positions: list[tuple[int, int]] = []  # (start, end) in original text
        chunk_index = 0

        i = 0
        while i < len(paragraphs):
            para = paragraphs[i]
            para_len = len(para)

            if _token_count(current) + _token_count(para) <= max_tokens:
                char_start = text.find(para, 0 if i == 0 else char_positions[-1][1])
                if char_start < 0:
                    char_start = char_positions[-1][1] if char_positions else 0
                char_end = char_start + para_len
                char_positions.append((char_start, char_end))
                current += para
                i += 1
            else:
                # Emit current chunk
                if current.strip():
                    chunks.append({
                        "id": f"chunk_{chunk_index}",
                        "text": current.strip(),
                        "start_char": char_positions[0][0],
                        "end_char": char_positions[-1][1],
                        "chunk_index": chunk_index,
                    })
                    chunk_index += 1

                # Build overlap window (last overlap_chars of current)
                overlap_text = current[-overlap_chars:] if len(current) > overlap_chars else current
                # Find sentence/paragraph boundary within overlap
                overlap_start = current.find(overlap_text)
                remaining = text[char_positions[-1][1]:]

                # Restart with overlap text + remaining paragraphs
                current = overlap_text
                char_positions = [(char_positions[-1][1] - len(overlap_text), char_positions[-1][1])]
            # Guard against infinite loop
            if _token_count(current) > max_tokens * 2:
                break

        # Last chunk
        if current.strip() and _token_count(current) > 0:
            chunks.append({
                "id": f"chunk_{chunk_index}",
                "text": current.strip(),
                "start_char": char_positions[0][0] if char_positions else 0,
                "end_char": char_positions[-1][1] if char_positions else len(text),
                "chunk_index": chunk_index,
            })

        return chunks

    @classmethod
    def _split_paragraphs(cls, text: str) -> list[str]:
        for sep in cls.PARAGRAPH_SEPARATORS:
            if sep in text:
                parts = text.split(sep)
                return [p + sep for p in parts[:-1]] + [parts[-1]]
        return [text]


class BM25:
    """Simple BM25 scorer for keyword search over text chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._avgdl = 0.0

    def score(self, query_words: set[str], chunks: list[dict], avgdl: float = 0.0) -> list[tuple[dict, float]]:
        """Score chunks by BM25 keyword overlap.

        Args:
            query_words: set of query keyword strings
            chunks: list of dicts with "text" key
            avgdl: average document length (in words)

        Returns:
            List of (chunk, score) sorted descending.
        """
        if avgdl > 0:
            self._avgdl = avgdl
        results: list[tuple[dict, float]] = []
        for chunk in chunks:
            text = chunk.get("text", "")
            words = _extract_words(text)
            word_count = len(words)
            overlap = len(query_words & words)
            if overlap == 0:
                results.append((chunk, 0.0))
                continue
            # Simplified BM25
            rsv = overlap * (self.k1 + 1) / (overlap + self.k1 * (1 - self.b + self.b * word_count / max(self._avgdl, 1)))
            results.append((chunk, rsv))
        results.sort(key=lambda x: x[1], reverse=True)
        return results
