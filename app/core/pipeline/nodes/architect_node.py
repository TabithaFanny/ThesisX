"""ArchitectNode — self-built outline planning node.

In mock mode, returns a fixed outline.  In real mode, calls an OpenAI-compatible
API via httpx to generate a structured paper outline.

Enhanced with prompts from:
- research-ideation (claude-scholar): 5W1H framework, gap analysis
- Chinese Academic Restructurer (academic-agents): structural editing
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict
from typing import Any

import httpx

from ..models import ArchitectOutput, PaperRequest
from ..prompts.architect_prompts import (
    ARCHITECT_SYSTEM_PROMPT_V2,
    ARCHITECT_USER_PROMPT_TEMPLATE_V2,
)
from ..prompts.deai_prompts import DEAI_BLACKLIST_EN, DEAI_BLACKLIST_ZH

logger = logging.getLogger(__name__)

# Backward-compatible aliases
ARCHITECT_SYSTEM_PROMPT = ARCHITECT_SYSTEM_PROMPT_V2
ARCHITECT_USER_PROMPT_TEMPLATE = ARCHITECT_USER_PROMPT_TEMPLATE_V2


# ---------------------------------------------------------------------------
# Mock outline
# ---------------------------------------------------------------------------

def _mock_outline(topic: str, journal: str) -> ArchitectOutput:
    """Return a fixed mock outline for demo/testing."""
    return ArchitectOutput(
        paper_title=f"{topic}研究——基于{journal}视角的分析",
        central_argument=f"本研究旨在探讨{topic}的核心问题与优化路径",
        argument_chain=[
            f"{topic}的理论基础与现实背景",
            f"{topic}的现状分析与问题识别",
            f"影响{topic}的关键因素分析",
            f"{topic}的优化策略与路径设计",
        ],
        outline=[
            {
                "section_number": 0,
                "title": "摘要",
                "section_goal": "概述研究背景、方法、发现和结论",
                "target_word_count": 500,
                "key_points": ["研究背景", "研究方法", "主要发现", "结论"],
            },
            {
                "section_number": 1,
                "title": "一、引言",
                "section_goal": "阐述研究背景、研究意义和研究问题",
                "target_word_count": 1500,
                "key_points": [
                    "研究背景与现实需求",
                    "研究目的与研究问题",
                    "研究方法与论文结构",
                ],
            },
            {
                "section_number": 2,
                "title": "二、文献综述与理论基础",
                "section_goal": "梳理相关研究现状，建立理论框架",
                "target_word_count": 2000,
                "key_points": [
                    "国内外研究现状",
                    "理论框架与概念界定",
                    "研究述评与研究空白",
                ],
            },
            {
                "section_number": 3,
                "title": "三、现状分析与问题识别",
                "section_goal": "分析当前状况，识别核心问题",
                "target_word_count": 2500,
                "key_points": [
                    "现状描述与数据呈现",
                    "问题识别与归因分析",
                    "[数据待补充]",
                ],
            },
            {
                "section_number": 4,
                "title": "四、影响因素与机制分析",
                "section_goal": "深入分析影响因素和作用机制",
                "target_word_count": 2500,
                "key_points": [
                    "关键影响因素",
                    "作用机制与路径",
                    "[引用待核查]",
                ],
            },
            {
                "section_number": 5,
                "title": "五、优化策略与路径设计",
                "section_goal": "提出针对性的优化建议和实施路径",
                "target_word_count": 2000,
                "key_points": [
                    "策略设计原则",
                    "具体优化路径",
                    "保障措施与实施建议",
                ],
            },
            {
                "section_number": 6,
                "title": "六、结论与展望",
                "section_goal": "总结研究发现，指出局限性和未来方向",
                "target_word_count": 1000,
                "key_points": [
                    "主要结论",
                    "研究局限",
                    "未来研究方向",
                ],
            },
            {
                "section_number": 7,
                "title": "参考文献",
                "section_goal": "列出引用的文献",
                "target_word_count": 0,
                "key_points": [],
            },
        ],
        missing_materials=[
            "需要补充相关统计数据",
            "需要查阅最新政策文件",
            "[引用待核查] 标记的文献需要人工验证真实性",
        ],
        writer_instructions=(
            "请严格依据以上大纲撰写论文。"
            "不得编造文献、数据、访谈或政策文件。"
            "缺少资料时使用 [引用待核查] 或 [数据待补充] 标记。"
            "本结果为论文初稿，不可直接作为最终提交文本。"
        ),
    )


# ---------------------------------------------------------------------------
# ArchitectNode
# ---------------------------------------------------------------------------

class ArchitectNode:
    """Generates a structured paper outline.

    Mock mode: returns a fixed outline instantly.
    Real mode: calls an OpenAI-compatible API with httpx.
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def run(self, request: PaperRequest) -> ArchitectOutput:
        """Generate an outline based on the request."""
        if request.run_mode == "mock":
            return _mock_outline(request.topic, request.journal)
        return await self._run_real(request)

    async def _run_real(self, request: PaperRequest) -> ArchitectOutput:
        """Call an OpenAI-compatible API to generate the outline."""
        api_key = request.api_key
        base_url = (request.base_url or "https://api.openai.com/v1").rstrip("/")
        model = request.model or "gpt-4o-mini"

        if not api_key:
            logger.warning("Real 模式无 API Key，fallback 到 mock 大纲")
            return _mock_outline(request.topic, request.journal)

        user_prompt = ARCHITECT_USER_PROMPT_TEMPLATE.format(
            topic=request.topic,
            journal=request.journal,
            run_mode=request.run_mode,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_output(content, request.topic, request.journal)
        except Exception as e:
            logger.error("ArchitectNode API 调用失败: %s", e)
            logger.info("Fallback 到 mock 大纲")
            return _mock_outline(request.topic, request.journal)

    @staticmethod
    def _parse_output(
        content: str, topic: str, journal: str
    ) -> ArchitectOutput:
        """Parse LLM JSON output into ArchitectOutput, with fallback."""
        # Strip markdown code block if present
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON from the content
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("无法解析 ArchitectNode 输出，使用 fallback")
                    return _mock_outline(topic, journal)
            else:
                logger.warning("ArchitectNode 输出不含 JSON，使用 fallback")
                return _mock_outline(topic, journal)

        return ArchitectOutput(
            paper_title=data.get("paper_title", topic),
            central_argument=data.get("central_argument", ""),
            argument_chain=data.get("argument_chain", []),
            outline=data.get("outline", []),
            missing_materials=data.get("missing_materials", []),
            writer_instructions=data.get("writer_instructions", ""),
        )


# ---------------------------------------------------------------------------
# Enhanced topic builder
# ---------------------------------------------------------------------------

def build_enhanced_topic(request: PaperRequest, outline: ArchitectOutput) -> str:
    """Build the enhanced topic string to inject into Agent Team's Writer prompt.

    Combines: config + outline + writing boundaries + original topic.
    """
    outline_lines: list[str] = []
    for item in outline.outline:
        num = item.get("section_number", "")
        title = item.get("title", "")
        goal = item.get("section_goal", "")
        words = item.get("target_word_count", 0)
        outline_lines.append(f"{num}. {title} — {goal} ({words}字)")

    sections_text = "\n".join(outline_lines)

    chain_text = " → ".join(outline.argument_chain) if outline.argument_chain else ""

    # Format blacklists from the unified prompt library
    zh_bl = "、".join(DEAI_BLACKLIST_ZH[:25])
    en_bl = ", ".join(DEAI_BLACKLIST_EN[:50])

    enhanced = f"""\
【论文生成任务配置】
生成类型：论文初稿
目标风格：{request.journal}
运行模式：{request.run_mode}

【大纲规划】
论文标题：{outline.paper_title}
中心论点：{outline.central_argument}
论证链：{chain_text}
章节规划：
{sections_text}

【分轮写作策略 — 三轮改稿法】
⚠ 以下策略适用于论文撰写阶段，请严格按三轮分离执行：

第一轮 · 逻辑轮
只看论证结构。每一段的论点是什么？从上一段怎么推导过来？结论能不能从前提自然得出？
不管语言好不好，不管引用准不准，只看逻辑链。
检查项：论点清晰度、段间衔接、因果推导、结论可支撑性。

第二轮 · 理论轮
逻辑过关了，再看理论。概念用对了吗？术语符合领域共识吗？框架套得是否恰当？
检查项：概念准确性、术语一致性、理论框架适配度、文献引用匹配。

第三轮 · 语言轮
最后处理表达。学术风格、句式、用词、段落过渡。
检查项：句式多样性、用词精准度、段落过渡自然度、学术规范。

⚠ 不要试图一轮完成所有工作。每一轮只专注一个维度。

【审稿标准 — 5 维评分】
Reviewer 将按以下 5 个维度评分（每项 1-10 分）：
1. Directness（直接性）：是否有废话？观点是否直击要害？
2. Rhythm（节奏感）：句式是否有变化？长短句是否交替？
3. Trust（信任度）：是否尊重读者智商？是否过度解释？
4. Authenticity（真实感）：读起来像人写的吗？有没有AI腔？
5. Density（密度）：每句话都有信息量吗？有没有可以删掉的？

总分低于 35/50 需要返回修改。

【去 AI 痕迹要求】
⚠ 以下词汇和句式在 AI 输出中异常高频，请主动避免：
中文黑名单：{zh_bl}
英文黑名单：{en_bl}

【写作边界】
不得编造文献、数据、访谈、政策文件。
缺少资料时使用 [引用待核查] 或 [数据待补充] 标记。
本结果为论文初稿，不可直接作为最终提交文本。
{outline.writer_instructions}

【用户原始课题】
{request.topic}"""
    return enhanced
