"""Tests for the integrated prompt library — validates all prompt modules."""

import pytest

from app.core.pipeline.prompts import (
    ARCHITECT_SYSTEM_PROMPT_V2,
    DEAI_BLACKLIST_EN,
    DEAI_BLACKLIST_ZH,
    DEAI_PATTERNS_ZH,
    DEAI_SYSTEM_PROMPT_V2,
    REVIEWER_SYSTEM_PROMPT,
    SELF_REVIEW_CHECKLIST,
    WRITER_LANG_POLISH_PROMPT_ZH,
    WRITER_LOGIC_SYSTEM_PROMPT,
    WRITER_THEORY_RESTRUCTURE_PROMPT_ZH,
    build_deai_user_prompt,
    build_research_ideation_prompt,
    build_reviewer_user_prompt,
)


class TestArchitectPrompts:
    def test_v2_prompt_contains_5w1h(self):
        assert "What" in ARCHITECT_SYSTEM_PROMPT_V2
        assert "Why" in ARCHITECT_SYSTEM_PROMPT_V2
        assert "How" in ARCHITECT_SYSTEM_PROMPT_V2

    def test_v2_prompt_contains_gap_analysis(self):
        assert "差距分析" in ARCHITECT_SYSTEM_PROMPT_V2

    def test_v2_prompt_contains_smart(self):
        assert "SMART" in ARCHITECT_SYSTEM_PROMPT_V2

    def test_research_ideation_prompt(self):
        prompt = build_research_ideation_prompt("数字治理", "CSSCI")
        assert "数字治理" in prompt
        assert "CSSCI" in prompt
        assert "5W1H" in prompt


class TestWriterPrompts:
    def test_logic_prompt_contains_checklist(self):
        assert "检查清单" in WRITER_LOGIC_SYSTEM_PROMPT
        assert "论点" in WRITER_LOGIC_SYSTEM_PROMPT

    def test_theory_restructure_prompt(self):
        assert "逻辑重组" in WRITER_THEORY_RESTRUCTURE_PROMPT_ZH
        assert "术语" in WRITER_THEORY_RESTRUCTURE_PROMPT_ZH
        assert "Refined Text" in WRITER_THEORY_RESTRUCTURE_PROMPT_ZH

    def test_lang_polish_prompt(self):
        assert "克制修改" in WRITER_LANG_POLISH_PROMPT_ZH
        assert "口语" in WRITER_LANG_POLISH_PROMPT_ZH
        assert "Refined Text" in WRITER_LANG_POLISH_PROMPT_ZH


class TestReviewerPrompts:
    def test_reviewer_prompt_contains_13_dimensions(self):
        assert "选题与问题意识" in REVIEWER_SYSTEM_PROMPT
        assert "AIGC" in REVIEWER_SYSTEM_PROMPT
        assert "verdict" in REVIEWER_SYSTEM_PROMPT

    def test_reviewer_prompt_contains_writing_scores(self):
        assert "Directness" in REVIEWER_SYSTEM_PROMPT
        assert "Rhythm" in REVIEWER_SYSTEM_PROMPT
        assert "Authenticity" in REVIEWER_SYSTEM_PROMPT

    def test_self_review_checklist(self):
        assert "摘要" in SELF_REVIEW_CHECKLIST
        assert "引用" in SELF_REVIEW_CHECKLIST
        assert "AIGC" in SELF_REVIEW_CHECKLIST

    def test_build_reviewer_user_prompt(self):
        prompt = build_reviewer_user_prompt(
            topic="AI治理", journal="CSSCI", paper_text="测试文本"
        )
        assert "AI治理" in prompt
        assert "CSSCI" in prompt


class TestDeAIPrompts:
    def test_zh_blacklist_nonempty(self):
        assert len(DEAI_BLACKLIST_ZH) >= 30

    def test_en_blacklist_nonempty(self):
        assert len(DEAI_BLACKLIST_EN) >= 70

    def test_patterns_nonempty(self):
        assert len(DEAI_PATTERNS_ZH) >= 15

    def test_zh_blacklist_contains_expected(self):
        for word in ["此外", "至关重要", "赋能", "综上所述", "毋庸置疑"]:
            assert word in DEAI_BLACKLIST_ZH

    def test_en_blacklist_contains_expected(self):
        lower_bl = [w.lower() for w in DEAI_BLACKLIST_EN]
        for word in ["leverage", "delve", "pivotal", "nuanced", "scrutinize"]:
            assert word in lower_bl

    def test_deai_system_prompt_v2(self):
        assert "两遍处理法" in DEAI_SYSTEM_PROMPT_V2
        assert "通过信号" in DEAI_SYSTEM_PROMPT_V2
        assert "5 维" in DEAI_SYSTEM_PROMPT_V2

    def test_build_deai_user_prompt_zh(self):
        prompt = build_deai_user_prompt("测试文本", language="zh")
        assert "中文" in prompt
        assert "测试文本" in prompt

    def test_build_deai_user_prompt_en(self):
        prompt = build_deai_user_prompt("test text", language="en")
        assert "English" in prompt or "De-AI" in prompt

    def test_build_deai_user_prompt_auto(self):
        prompt = build_deai_user_prompt("mixed text", language="auto")
        assert "自动检测" in prompt
