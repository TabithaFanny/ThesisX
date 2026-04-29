"""CitationVerifierNode — reference verification for academic papers.

Based on citation-verification (claude-scholar).
Core principle: AI-generated citations have ~40% error rate.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

import httpx

from ..models import PaperRequest
from ..prompts.citation_prompts import build_citation_verifier_prompt

logger = logging.getLogger(__name__)


@dataclass
class CitationIssue:
    """A single citation issue."""
    citation_key: str
    status: str  # "verified", "suspicious", "unverifiable"
    issues: list[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class CitationVerificationResult:
    """Result of citation verification."""
    total_citations: int
    verified_count: int
    suspicious_count: int
    unverifiable_count: int
    results: list[CitationIssue] = field(default_factory=list)
    summary: str = ""


class CitationVerifierNode:
    """Verifies citations in academic papers.

    Mock mode: returns a pass result.
    Real mode: calls an OpenAI-compatible API.
    """

    async def run(
        self, paper_text: str, request: PaperRequest
    ) -> CitationVerificationResult:
        """Run citation verification on the given paper text."""
        if request.run_mode == "mock":
            return self._mock_result(paper_text)
        return await self._run_real(paper_text, request)

    def _mock_result(self, paper_text: str) -> CitationVerificationResult:
        """Mock mode: count citations but don't verify."""
        citation_count = len(re.findall(r"\\cite\{[^}]+\}|\[[\d,;\s]+\]", paper_text))
        return CitationVerificationResult(
            total_citations=citation_count,
            verified_count=0,
            suspicious_count=0,
            unverifiable_count=citation_count,
            summary=f"[Mock] 检测到 {citation_count} 处引用，Mock 模式不实际验证",
        )

    async def _run_real(
        self, paper_text: str, request: PaperRequest
    ) -> CitationVerificationResult:
        """Real mode: call API for citation verification."""
        api_key = request.api_key
        base_url = (request.base_url or "https://api.openai.com/v1").rstrip("/")
        model = request.model or "gpt-4o-mini"

        if not api_key:
            logger.warning("CitationVerifier: 无 API Key，跳过引用验证")
            return CitationVerificationResult(
                total_citations=0,
                verified_count=0,
                suspicious_count=0,
                unverifiable_count=0,
                summary="无 API Key，跳过引用验证",
            )

        system_msg, user_msg = build_citation_verifier_prompt(paper_text)

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
                        "temperature": 0.2,
                        "max_tokens": 4000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_result(content)
        except Exception as e:
            logger.error("引用验证 API 调用失败: %s", e)
            return CitationVerificationResult(
                total_citations=0,
                verified_count=0,
                suspicious_count=0,
                unverifiable_count=0,
                summary=f"API 调用失败: {e}",
            )

    @staticmethod
    def _parse_result(content: str) -> CitationVerificationResult:
        """Parse the API response into a CitationVerificationResult."""
        # Try to extract JSON from content
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return CitationVerificationResult(
                        total_citations=0,
                        verified_count=0,
                        suspicious_count=0,
                        unverifiable_count=0,
                        summary=f"解析失败: {content[:200]}",
                    )
            else:
                return CitationVerificationResult(
                    total_citations=0,
                    verified_count=0,
                    suspicious_count=0,
                    unverifiable_count=0,
                    summary=f"未找到 JSON: {content[:200]}",
                )

        results = []
        for item in data.get("results", []):
            results.append(CitationIssue(
                citation_key=item.get("citation_key", ""),
                status=item.get("status", "unverifiable"),
                issues=item.get("issues", []),
                suggestion=item.get("suggestion", ""),
            ))

        return CitationVerificationResult(
            total_citations=data.get("total_citations", 0),
            verified_count=data.get("verified_count", 0),
            suspicious_count=data.get("suspicious_count", 0),
            unverifiable_count=data.get("unverifiable_count", 0),
            results=results,
            summary=data.get("summary", ""),
        )
