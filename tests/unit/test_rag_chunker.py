"""Tests for RAG TextChunker and BM25."""

import pytest
from app.core.rag.chunker import TextChunker, BM25, _extract_words


class TestTextChunker:
    def test_chunk_text_empty(self):
        assert TextChunker.chunk_text("") == []
        assert TextChunker.chunk_text("   ") == []

    def test_chunk_text_short(self):
        text = "这是一段比较短的文本。" * 5
        chunks = TextChunker.chunk_text(text)
        assert len(chunks) >= 1
        assert chunks[0]["text"]

    def test_chunk_text_has_required_fields(self):
        chunks = TextChunker.chunk_text("hello world " * 200)
        for c in chunks:
            assert "id" in c
            assert "text" in c
            assert "start_char" in c
            assert "end_char" in c
            assert "chunk_index" in c

    def test_chunk_indices_increment(self):
        chunks = TextChunker.chunk_text("a" * 100 + " b" * 100 + " c" * 100)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_split_paragraphs(self):
        text = "第一段\n\n第二段\n\n第三段"
        parts = TextChunker._split_paragraphs(text)
        assert len(parts) == 3
        assert "第一段" in parts[0]
        assert "第二段" in parts[1]
        assert "第三段" in parts[2]


class TestBM25:
    def test_score_empty_chunks(self):
        bm = BM25()
        results = bm.score(set(), [], avgdl=10)
        assert results == []

    def test_score_no_overlap(self):
        bm = BM25()
        chunks = [{"text": "计算机科学是研究计算机的学科"}]
        results = bm.score({"文学"}, chunks, avgdl=5)
        assert results[0][1] == 0.0

    def test_score_with_overlap(self):
        bm = BM25()
        chunks = [{"text": "人工智能和机器学习是热门研究领域"}]
        # Use decomposed query words (same bigram logic)
        query_words = _extract_words("人工智能机器学习研究")
        results = bm.score(query_words, chunks, avgdl=10)
        assert results[0][1] > 0

    def test_score_sorted_descending(self):
        bm = BM25()
        chunks = [
            {"text": "人工智能研究"},
            {"text": "机器学习研究"},
            {"text": "深度学习研究"},
        ]
        results = bm.score({"研究"}, chunks, avgdl=5)
        scores = [r for _, r in results]
        assert scores == sorted(scores, reverse=True)


class TestExtractWords:
    def test_extract_chinese_bigrams(self):
        from app.core.rag.chunker import _extract_words
        words = _extract_words("人工智能")
        assert "人工" in words or "智能" in words

    def test_extract_english_words(self):
        from app.core.rag.chunker import _extract_words
        words = _extract_words("machine learning")
        assert "machine" in words
        assert "learning" in words

    def test_extract_mixed(self):
        from app.core.rag.chunker import _extract_words
        words = _extract_words("AI学习")
        assert len(words) >= 2
