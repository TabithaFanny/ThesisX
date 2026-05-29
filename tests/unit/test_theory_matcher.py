"""Tests for TheoryMatcher."""

import pytest
from app.core.theory.matcher import TheoryMatcher, TheoryCandidate


class TestTheoryMatcher:
    def test_extract_keywords_english(self):
        m = TheoryMatcher()
        kw = m.extract_keywords("How do college students use AI tools for learning?")
        assert "ai" in kw or "learning" in kw

    def test_extract_keywords_chinese(self):
        m = TheoryMatcher()
        kw = m.extract_keywords("大学生使用短视频进行社交的动机是什么")
        # Should contain meaningful Chinese n-grams
        assert len(kw) > 0

    def test_extract_keywords_deduplication(self):
        m = TheoryMatcher()
        kw = m.extract_keywords("AI AI AI")
        assert len(kw) == len(set(kw))

    def test_match_returns_theory_candidates(self):
        m = TheoryMatcher()
        results = m.match("How do college students use AI tools for learning?")
        assert len(results) <= 5
        for r in results:
            assert isinstance(r, TheoryCandidate)
            assert r.match_score >= 0

    def test_match_scores_sorted(self):
        m = TheoryMatcher()
        results = m.match("How do college students use AI tools for learning?")
        if len(results) > 1:
            scores = [r.match_score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_match_empty_query(self):
        m = TheoryMatcher()
        results = m.match("")
        assert results == []

    def test_match_tam_keyword(self):
        m = TheoryMatcher()
        # TAM: 技术接受, 感知有用性, 感知易用性
        results = m.match("学生对在线教育平台的接受度和使用意愿")
        assert len(results) > 0
        assert any(r.id == "tam" for r in results)

    def test_theory_candidates_have_required_fields(self):
        m = TheoryMatcher()
        results = m.match("社区治理中的数字化转型", top_k=3)
        for r in results:
            assert r.name_zh
            assert r.name_en
            assert r.discipline
            assert r.core_concepts
            assert r.explanation


    def test_theory_count_at_least_30(self):
        m = TheoryMatcher()
        assert len(m.theories) >= 30, f"Only {len(m.theories)} theories, need 30+"


class TestTheoryCandidate:
    def test_theory_candidate_creation(self):
        c = TheoryCandidate(
            id="test",
            name_zh="测试理论",
            name_en="Test Theory",
            discipline=["教育学"],
            core_concepts=["概念A", "概念B"],
            applicable_topics=["应用话题"],
            explanation="解释",
            limitations=["局限1"],
            match_score=0.85,
        )
        assert c.id == "test"
        assert c.match_score == 0.85
