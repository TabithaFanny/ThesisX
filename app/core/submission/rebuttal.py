"""Rebuttal planning — minimal concern extraction and rebuttal plan."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RebuttalPlan:
    """A plan for responding to reviewer concerns."""
    submission_id: str
    concerns: list[str] = field(default_factory=list)
    plans: list[str] = field(default_factory=list)
    done: bool = False


class RebuttalService:
    """Minimal rebuttal plan generator — rule-based concern extraction."""

    # Common reviewer concern patterns (simplified)
    CONCERN_PATTERNS = [
        (re.compile(r"(?:methodology|方法论|方法).{0,30}(?:flaw|问题|不足|weak)"), "方法论"),
        (re.compile(r"(?:literature|文献).{0,30}(?:gap|不足|weak|缺乏)"), "文献综述"),
        (re.compile(r"(?:sample|样本).{0,30}(?:small|少|不足)"), "样本量"),
        (re.compile(r"(?:result|结果).{0,30}(?:lack|不足|novelty)"), "结果创新性"),
        (re.compile(r"(?:writing|写作|表达).{0,30}(?:clarify|clear|improve)"), "写作表达"),
        (re.compile(r"(?:statistical|统计).{0,30}(?:test|检验|method)"), "统计方法"),
        (re.compile(r"(?:ethical|伦理).{0,30}(?:approval|statement)"), "伦理声明"),
        (re.compile(r"(?:figure|图表).{0,30}(?:improve|clarify|better)"), "图表质量"),
    ]

    GENERIC_RESPONSES: dict[str, str] = {
        "方法论": "感谢审稿人对方法论的关注。我们已在正文中补充了方法论部分的详细说明，并引用了相关参考文献支持我们的方法选择。具体修改见第X节。",
        "文献综述": "感谢指出文献综述的不足。我们已补充了相关工作对比分析（见第X节），并进一步阐述了我们研究与现有工作的区别和贡献。",
        "样本量": "感谢对样本量的关注。我们已在附录中补充了样本量计算的依据，并说明在当前研究设计下，该样本量足以支持我们的统计分析。",
        "结果创新性": "感谢审稿人对创新性的关注。我们已在第X节重新梳理了主要贡献点，明确了与现有工作的差异化价值。",
        "写作表达": "感谢对写作质量的建议。我们已对全文进行润色，重点修改了第X节的语言表达，使其更加清晰准确。",
        "统计方法": "感谢对统计方法的建议。我们已在附录中补充了详细的统计检验过程说明，并增加了鲁棒性检验结果。",
        "伦理声明": "感谢提醒。我们已在附录中补充了伦理审查声明，说明本研究所需的伦理批准情况。",
        "图表质量": "感谢审稿人的建议。我们已按要求重新绘制/优化了相关图表，使信息呈现更加清晰直观（见新图X）。",
    }

    def extract_concerns(self, reviewer_text: str) -> list[str]:
        """Extract likely reviewer concern types from free text."""
        concerns = []
        for pattern, label in self.CONCERN_PATTERNS:
            if pattern.search(reviewer_text):
                concerns.append(label)
        return list(dict.fromkeys(concerns))  # dedupe

    def build_plan(self, submission_id: str, reviewer_texts: list[str]) -> RebuttalPlan:
        """Build a rebuttal plan from raw reviewer text(s)."""
        plan = RebuttalPlan(submission_id=submission_id)
        for text in reviewer_texts:
            concerns = self.extract_concerns(text)
            plan.concerns.extend(concerns)
        plan.concerns = list(dict.fromkeys(plan.concerns))  # dedupe

        for concern in plan.concerns:
            plan.plans.append(
                self.GENERIC_RESPONSES.get(concern, f"针对「{concern}」问题，请结合审稿人具体意见逐条回应，补充相关证据和说明。")
            )
        return plan

    def write_plan_markdown(self, plan: RebuttalPlan, output_path: str | Path) -> None:
        """Write a rebuttal plan as a Markdown document."""
        out = Path(output_path)
        lines = [f"# Rebuttal Plan — {plan.submission_id}\n"]
        for i, (concern, response) in enumerate(zip(plan.concerns, plan.plans), 1):
            lines.append(f"\n## {i}. {concern}")
            lines.append(f"\n**审稿人意见：** (待填写具体审稿意见)")
            lines.append(f"\n**回复提纲：**\n{response}")
        lines.append("\n---\n*由 ThesisX RebuttalService 自动生成 — 请结合实际审稿意见修改*")
        out.write_text("\n".join(lines), encoding="utf-8")
