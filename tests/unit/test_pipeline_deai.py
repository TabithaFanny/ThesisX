"""Tests for DeAIHumanizer — De-AI humanization node."""

import pytest

from app.core.pipeline.models import PaperRequest
from app.core.pipeline.nodes.deai_humanizer import (
    EN_AI_BLACKLIST,
    ZH_AI_BLACKLIST,
    AI_PATTERNS_ZH,
    DeAIHumanizer,
    DeAIResult,
)


class TestBlacklists:
    def test_zh_blacklist_nonempty(self):
        assert len(ZH_AI_BLACKLIST) >= 18

    def test_en_blacklist_nonempty(self):
        assert len(EN_AI_BLACKLIST) >= 30

    def test_ai_patterns_nonempty(self):
        assert len(AI_PATTERNS_ZH) >= 10

    def test_zh_blacklist_contains_expected(self):
        for word in ["此外", "至关重要", "赋能", "综上所述"]:
            assert word in ZH_AI_BLACKLIST

    def test_en_blacklist_contains_expected(self):
        for word in ["Leverage", "Delve", "Nuanced", "Pivotal"]:
            assert word in EN_AI_BLACKLIST


class TestDeAIHumanizerMock:
    @pytest.mark.asyncio
    async def test_clean_text_passes(self):
        humanizer = DeAIHumanizer()
        req = PaperRequest(topic="test", run_mode="mock")
        text = "这是一段正常的学术论文文本，没有任何AI痕迹。"
        result = await humanizer.run(text, req)
        assert isinstance(result, DeAIResult)
        assert result.pattern_count == 0
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_dirty_text_detected(self):
        humanizer = DeAIHumanizer()
        req = PaperRequest(topic="test", run_mode="mock")
        text = "此外，这项研究至关重要，具有深远的影响和充满活力的发展格局。"
        result = await humanizer.run(text, req)
        assert result.pattern_count > 0
        # Mock mode doesn't actually rewrite, so passed depends on pattern count
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_en_blacklist_detected(self):
        humanizer = DeAIHumanizer()
        req = PaperRequest(topic="test", run_mode="mock")
        text = "This paper aims to leverage and delve into the nuanced landscape."
        result = await humanizer.run(text, req)
        assert result.pattern_count > 0

    @pytest.mark.asyncio
    async def test_mock_returns_original_text(self):
        humanizer = DeAIHumanizer()
        req = PaperRequest(topic="test", run_mode="mock")
        text = "原始文本"
        result = await humanizer.run(text, req)
        assert result.humanized_text == text


class TestDeAIHumanizerRealNoKey:
    @pytest.mark.asyncio
    async def test_real_mode_no_key_skips(self):
        humanizer = DeAIHumanizer()
        req = PaperRequest(topic="test", run_mode="real", api_key="")
        text = "test text"
        result = await humanizer.run(text, req)
        assert result.passed is True
        assert "跳过" in result.modification_log


class TestDeAIResult:
    def test_defaults(self):
        r = DeAIResult(
            humanized_text="text",
            modification_log="log",
            passed=True,
            pattern_count=0,
        )
        assert r.humanized_text == "text"
        assert r.passed is True
        assert r.pattern_count == 0


class TestCountPatterns:
    def test_clean_text(self):
        count = DeAIHumanizer._count_patterns("正常学术文本无AI痕迹")
        assert count == 0

    def test_dirty_text(self):
        count = DeAIHumanizer._count_patterns("此外这个研究至关重要leverage了nuanced方法")
        assert count >= 3
