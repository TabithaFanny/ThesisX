"""DeAIHumanizer — removes AI writing patterns from generated text.

Based on:
- Humanizer-zh (op7418/Humanizer-zh): 24 AI writing patterns
- awesome-ai-research-writing: 80+ English blacklist, 18+ Chinese blacklist
- academic-agents (AI Writing Decontaminator): 70+ English blacklist, 6-category Chinese patterns
- writing-anti-ai (claude-scholar): 5 core rules, 5-dimension scoring

Two-pass approach:
1. Rewrite pass — replace AI patterns with natural expressions
2. Audit pass — "what makes this obviously AI?" final check
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

from ..models import PaperRequest
from ..prompts.deai_prompts import (
    DEAI_BLACKLIST_EN,
    DEAI_BLACKLIST_ZH,
    DEAI_PATTERNS_ZH,
    DEAI_SYSTEM_PROMPT_V2,
    EN_REPLACEMENTS,
    build_deai_user_prompt,
)

logger = logging.getLogger(__name__)

# Backward-compatible aliases (used by tests)
ZH_AI_BLACKLIST: list[str] = DEAI_BLACKLIST_ZH
EN_AI_BLACKLIST: list[str] = DEAI_BLACKLIST_EN
AI_PATTERNS_ZH: list[tuple[str, str, str]] = DEAI_PATTERNS_ZH

# Legacy aliases for system/user prompts
DEAI_SYSTEM_PROMPT = DEAI_SYSTEM_PROMPT_V2
DEAI_USER_PROMPT = build_deai_user_prompt


@dataclass
class DeAIResult:
    """Result of the De-AI humanization pass."""
    humanized_text: str
    modification_log: str
    passed: bool  # True if text was already natural
    pattern_count: int  # Number of AI patterns detected


class DeAIHumanizer:
    """Removes AI writing patterns from generated paper text.

    Mock mode: returns text unchanged with a pass signal.
    Real mode: calls an OpenAI-compatible API.
    """

    async def run(self, text: str, request: PaperRequest) -> DeAIResult:
        """Run De-AI humanization on the given text."""
        if request.run_mode == "mock":
            return self._mock_result(text)
        return await self._run_real(text, request)

    def _mock_result(self, text: str) -> DeAIResult:
        """Mock mode: count patterns but don't actually rewrite."""
        pattern_count = self._count_patterns(text)
        return DeAIResult(
            humanized_text=text,
            modification_log=f"[Mock] 检测到 {pattern_count} 处 AI 痕迹，Mock 模式不实际改写",
            passed=(pattern_count == 0),
            pattern_count=pattern_count,
        )

    async def _run_real(self, text: str, request: PaperRequest) -> DeAIResult:
        """Real mode: call API to humanize text."""
        api_key = request.api_key
        base_url = (request.base_url or "https://api.openai.com/v1").rstrip("/")
        model = request.model or "gpt-4o-mini"

        if not api_key:
            logger.warning("De-AI: 无 API Key，跳过去 AI 处理")
            return DeAIResult(
                humanized_text=text,
                modification_log="无 API Key，跳过去 AI 处理",
                passed=True,
                pattern_count=0,
            )

        en_blacklist_str = ", ".join(DEAI_BLACKLIST_EN[:40])
        en_replacements_str = "\n".join(
            f"- {k} → {v}" for k, v in list(EN_REPLACEMENTS.items())[:12]
        )

        system_msg = DEAI_SYSTEM_PROMPT_V2.format(
            en_blacklist=en_blacklist_str,
            en_replacements=en_replacements_str,
        )
        user_msg = build_deai_user_prompt(text[:8000])  # Limit length

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 8000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_result(content, text)
        except Exception as e:
            logger.error("De-AI API 调用失败: %s", e)
            return DeAIResult(
                humanized_text=text,
                modification_log=f"API 调用失败: {e}",
                passed=False,
                pattern_count=0,
            )

    @staticmethod
    def _parse_result(content: str, original: str) -> DeAIResult:
        """Parse the API response into a DeAIResult."""
        passed = "[检测通过]" in content

        # Try to split into humanized text and modification log
        parts = content.split("修改日志")
        if len(parts) >= 2:
            humanized = parts[0].strip()
            log = parts[1].strip()
        else:
            # Try splitting by "第二部分"
            parts = content.split("第二部分")
            if len(parts) >= 2:
                humanized = parts[0].strip()
                log = parts[1].strip()
            else:
                humanized = content
                log = "（修改日志未解析）"

        # Remove markdown code blocks if present
        if humanized.startswith("```"):
            lines = humanized.split("\n")
            humanized = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        pattern_count = len(re.findall(r"→|->|改为|替换为", log))

        return DeAIResult(
            humanized_text=humanized if not passed else original,
            modification_log=log,
            passed=passed,
            pattern_count=pattern_count,
        )

    @staticmethod
    def _count_patterns(text: str) -> int:
        """Count AI patterns in the text (for mock mode)."""
        count = 0
        for phrase in ZH_AI_BLACKLIST:
            if phrase in text:
                count += 1
        for word in EN_AI_BLACKLIST:
            if word.lower() in text.lower():
                count += 1
        return count
