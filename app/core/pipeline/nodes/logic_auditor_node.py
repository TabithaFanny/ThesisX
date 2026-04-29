"""LogicAuditorNode — final-pass red-line logic check.

Based on Logic Auditor (academic-agents).
High tolerance: only flags fatal contradictions, terminology swaps, and severe grammar errors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from ..models import PaperRequest
from ..prompts.logic_auditor_prompts import build_logic_auditor_prompt

logger = logging.getLogger(__name__)


@dataclass
class LogicAuditResult:
    """Result of a logic audit pass."""
    passed: bool  # True if no fatal issues found
    issues: list[str]  # List of issues found
    raw_output: str


class LogicAuditorNode:
    """Final-pass logic auditor for near-final manuscripts.

    Mock mode: always passes.
    Real mode: calls an OpenAI-compatible API.
    """

    async def run(self, paper_text: str, request: PaperRequest) -> LogicAuditResult:
        """Run logic audit on the given paper text."""
        if request.run_mode == "mock":
            return LogicAuditResult(
                passed=True,
                issues=[],
                raw_output="[Mock] 逻辑审计跳过",
            )
        return await self._run_real(paper_text, request)

    async def _run_real(
        self, paper_text: str, request: PaperRequest
    ) -> LogicAuditResult:
        """Real mode: call API for logic audit."""
        api_key = request.api_key
        base_url = (request.base_url or "https://api.openai.com/v1").rstrip("/")
        model = request.model or "gpt-4o-mini"

        if not api_key:
            logger.warning("LogicAuditor: 无 API Key，跳过逻辑审计")
            return LogicAuditResult(
                passed=True,
                issues=[],
                raw_output="无 API Key，跳过逻辑审计",
            )

        system_msg, user_msg = build_logic_auditor_prompt(paper_text)

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
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
                        "temperature": 0.2,
                        "max_tokens": 2000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_result(content)
        except Exception as e:
            logger.error("逻辑审计 API 调用失败: %s", e)
            return LogicAuditResult(
                passed=False,
                issues=[f"API 调用失败: {e}"],
                raw_output=str(e),
            )

    @staticmethod
    def _parse_result(content: str) -> LogicAuditResult:
        """Parse the API response into a LogicAuditResult."""
        passed = "检测通过" in content or "无实质性问题" in content

        issues: list[str] = []
        if not passed:
            # Split by bullet points or newlines
            for line in content.strip().split("\n"):
                line = line.strip()
                if line and (line.startswith("-") or line.startswith("·") or line.startswith("•")):
                    issues.append(line.lstrip("-·• "))
                elif line and not line.startswith("["):
                    issues.append(line)

        return LogicAuditResult(
            passed=passed,
            issues=issues,
            raw_output=content,
        )
