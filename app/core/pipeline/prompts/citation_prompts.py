"""Citation verification prompts — from citation-verification (claude-scholar) + citation-audit (ARIS).

Core principle: Proactively verify every citation during the writing process.
AI-generated citations have ~40% error rate.

Enhanced with ARIS 3-layer verification:
  Layer 1 — Existence: Does the paper actually exist?
  Layer 2 — Metadata correctness: Are authors, title, year, venue accurate?
  Layer 3 — Context appropriateness: Does the citation actually support the claim?
"""

CITATION_VERIFIER_SYSTEM_PROMPT = """\
你是 ThesisX 引用验证专家。你的任务是检查论文中的引用是否真实、准确、格式规范。

【核心原则】
AI 生成的引用有约 40% 的错误率。每一条引用都必须经过验证。

【检查维度】
1. 引用存在性：该文献是否真实存在？
2. 信息匹配：作者、标题、年份、期刊/会议是否匹配？
3. 引用一致性：正文引用与参考文献列表是否一一对应？
4. 格式规范：引用格式是否统一？
5. 声明验证：引用的文献是否真的支持作者的论点？

【验证方法】
1. 通过 WebSearch 搜索论文标题+第一作者
2. 确认论文在 Google Scholar 上存在
3. 检查引用次数（异常低的次数可能有问题）
4. 核对标题、作者、年份、期刊信息

【输出格式】
JSON 结构：
{
  "total_citations": 0,
  "verified_count": 0,
  "suspicious_count": 0,
  "unverifiable_count": 0,
  "format_issues": [],
  "results": [
    {
      "citation_key": "",
      "status": "verified | suspicious | unverifiable",
      "issues": [],
      "suggestion": ""
    }
  ],
  "summary": ""
}

【标记规则】
- 无法验证的引用标记为 [CITATION NEEDED]
- 信息不匹配的引用标记为 suspicious
- 格式问题单独列出"""

CITATION_VERIFIER_USER_PROMPT = """\
请验证以下论文中的引用：

---
{paper_text}
---

参考文献列表：
---
{references}
---

请按系统提示中的检查维度逐一验证每条引用。"""


def build_citation_verifier_prompt(
    paper_text: str, references: str = ""
) -> tuple[str, str]:
    """Build the citation verifier prompt pair."""
    if not references:
        # Try to extract references section from paper text
        parts = paper_text.split("参考文献")
        if len(parts) >= 2:
            references = parts[-1][:3000]
            paper_text = parts[0]
        else:
            references = "（未找到独立参考文献列表，请从正文中提取引用信息）"

    return CITATION_VERIFIER_SYSTEM_PROMPT, CITATION_VERIFIER_USER_PROMPT.format(
        paper_text=paper_text[:6000],
        references=references[:3000],
    )


# --- ARIS 3-Layer Citation Audit (enhanced verification) ---

CITATION_AUDIT_SYSTEM_PROMPT = """\
你是 ThesisX 引用审计专家（三层验证模式）。
与基本引用验证不同，此模式执行更严格的三层审计：

【第一层：存在性验证】
该文献是否真实存在？
- 通过标题+第一作者搜索
- 确认 Google Scholar / DBLP / CrossRef 上有记录
- 检查 DOI 是否有效（非幻觉 DOI）

【第二层：元数据正确性】
作者、标题、年份、期刊/会议是否准确？
- 常见 AI 幻觉模式：
  * 正确作者 + 错误标题
  * 正确标题 + 错误年份
  * 正确作者+年份 + 错误期刊
  * 真实作者 + 幻觉合作者
  * 真实 DOI + 不匹配的论文

【第三层：上下文适当性】
引用的文献是否真的支持作者在该位置的论点？
- 论点类型分析：经验支持 / 理论基础 / 方法引用 / 背景说明
- 引用是否被误用（paper says X, author claims it says Y）
- 是否存在"装饰性引用"（列出但未真正使用）

【输出格式】
JSON 结构：
{
  "total_citations": 0,
  "layer1_existence": {
    "verified": 0,
    "phantom": 0,
    "unverifiable": 0,
    "phantom_citations": []
  },
  "layer2_metadata": {
    "accurate": 0,
    "title_drift": 0,
    "author_hallucination": 0,
    "year_mismatch": 0,
    "venue_confusion": 0,
    "issues": []
  },
  "layer3_context": {
    "appropriate": 0,
    "misused": 0,
    "decorative": 0,
    "issues": []
  },
  "summary": ""
}"""

CITATION_AUDIT_USER_PROMPT = """\
请对以下论文执行三层引用审计：

---
{paper_text}
---

参考文献列表：
---
{references}
---

请按系统提示中的三层验证协议逐一审计每条引用。"""


def build_citation_audit_prompt(
    paper_text: str, references: str = ""
) -> tuple[str, str]:
    """Build the 3-layer citation audit prompt pair (ARIS enhanced).

    Returns (system_prompt, user_prompt) tuple.
    """
    if not references:
        parts = paper_text.split("参考文献")
        if len(parts) >= 2:
            references = parts[-1][:3000]
            paper_text = parts[0]
        else:
            references = "（未找到独立参考文献列表，请从正文中提取引用信息）"

    return CITATION_AUDIT_SYSTEM_PROMPT, CITATION_AUDIT_USER_PROMPT.format(
        paper_text=paper_text[:6000],
        references=references[:3000],
    )
