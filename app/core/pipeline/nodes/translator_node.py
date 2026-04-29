"""TranslatorNode — bidirectional CN/EN academic translation.

Based on Academic Translator (academic-agents).
Supports mock mode (returns original text) and real mode (API call).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from ..models import PaperRequest
from ..prompts.translator_prompts import build_translator_prompt

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of a translation pass."""
    translated_text: str
    back_translation: str  # CN→EN: Chinese back-translation for verification
    direction: str  # "c2e" or "e2c"
    modification_log: str


class TranslatorNode:
    """Bidirectional CN/EN academic translator.

    Mock mode: returns original text unchanged.
    Real mode: calls an OpenAI-compatible API.
    """

    async def run(
        self,
        text: str,
        request: PaperRequest,
        direction: str = "auto",
    ) -> TranslationResult:
        """Translate text between Chinese and English."""
        if request.run_mode == "mock":
            return TranslationResult(
                translated_text=text,
                back_translation="[Mock] 不实际翻译",
                direction="auto",
                modification_log="[Mock] 翻译节点跳过",
            )
        return await self._run_real(text, request, direction)

    async def _run_real(
        self,
        text: str,
        request: PaperRequest,
        direction: str,
    ) -> TranslationResult:
        """Real mode: call API for translation."""
        api_key = request.api_key
        base_url = (request.base_url or "https://api.openai.com/v1").rstrip("/")
        model = request.model or "gpt-4o-mini"

        if not api_key:
            logger.warning("Translator: 无 API Key，跳过翻译")
            return TranslationResult(
                translated_text=text,
                back_translation="",
                direction=direction,
                modification_log="无 API Key，跳过翻译",
            )

        system_msg, user_msg = build_translator_prompt(text, direction)

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
                return self._parse_result(content, direction)
        except Exception as e:
            logger.error("翻译 API 调用失败: %s", e)
            return TranslationResult(
                translated_text=text,
                back_translation="",
                direction=direction,
                modification_log=f"API 调用失败: {e}",
            )

    @staticmethod
    def _parse_result(content: str, direction: str) -> TranslationResult:
        """Parse the API response into a TranslationResult."""
        # Try to split into Part 1 and Part 2
        parts = content.split("Part 2")
        if len(parts) >= 2:
            translated = parts[0].replace("Part 1", "").strip()
            # Remove [LaTeX] or [Translation] labels
            for label in ["[LaTeX]", "[Translation]", "[Refined Text]"]:
                translated = translated.replace(label, "").strip()
                parts[1] = parts[1].replace(label, "").strip()
            back = parts[1].strip()
        else:
            translated = content.strip()
            back = ""

        return TranslationResult(
            translated_text=translated,
            back_translation=back,
            direction=direction,
            modification_log="翻译完成",
        )
