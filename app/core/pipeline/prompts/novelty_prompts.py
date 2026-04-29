"""Novelty verification prompts — from novelty-check (ARIS).

Four-phase workflow: extract claims → multi-source search → cross-model
verification → novelty report. Prevents months of wasted effort on
non-novel ideas.
"""

NOVELTY_CLAIM_EXTRACTION_PROMPT = """\
你是 ThesisX 查新专家。请从以下研究方案中提取 3-5 个核心技术主张，
这些主张需要在文献中验证其新颖性。

【研究方案】
{method_description}

【提取维度】
对每个核心主张，明确：
1. 方法是什么？（技术机制）
2. 解决什么问题？（应用场景）
3. 与显而易见的 baseline 有何不同？（差异化）

【输出格式】
JSON 数组：
[
  {{
    "claim_id": 1,
    "method": "技术机制描述",
    "problem": "解决的问题",
    "mechanism": "核心工作原理",
    "differentiator": "与 baseline 的差异点"
  }}
]

【规则】
- 聚焦真正可能构成新颖性的技术点
- "将 X 应用于 Y" 除非揭示了出人意料的发现，否则不算新颖
- 同时考虑方法和实验设置的新颖性"""


NOVELTY_SEARCH_PROMPT = """\
请为以下技术主张设计多源文献检索策略。

【技术主张】
{claim_json}

【检索要求】
1. 为每个主张设计至少 3 种不同的查询表述
2. 覆盖以下来源：
   - arXiv 预印本（2024-2026）
   - ICLR/NeurIPS/ICML/CVPR/ACL 最近两届
   - Google Scholar / Semantic Scholar
3. 查询应包含具体技术术语，避免过于宽泛

【输出格式】
JSON 对象：
{{
  "claim_id": {claim_id},
  "queries": [
    {{"query": "检索式", "source": "arxiv|scholar|venue", "rationale": "为何用此表述"}}
  ],
  "target_venues": ["ICLR 2026", "NeurIPS 2025"],
  "year_range": "2024-2026"
}}"""


NOVELTY_VERIFICATION_PROMPT = """\
你是跨模型新颖性审查员。请判断以下研究方案是否具有新颖性。

【研究方案】
{method_description}

【核心主张】
{claims_json}

【检索到的相关文献】
{search_results}

【审查要求】
1. 对每个核心主张，判断新颖性等级：HIGH / MEDIUM / LOW
2. 找出最接近的先前工作（prior work）
3. 明确本方案与先前工作的关键差异（delta）
4. 给出整体新颖性评分（X/10）
5. 给出建议：PROCEED / PROCEED_WITH_CAUTION / ABANDON

【特别注意】
- "将 X 应用于 Y" 通常不算新颖，除非应用揭示了出人意料的发现
- 同时检查方法和实验设置的新颖性
- 如果方法不新颖但发现可能新颖，明确指出
- 最近 6 个月的 arXiv 必须覆盖——领域变化极快

【输出格式】
JSON 对象：
{{
  "claim_assessments": [
    {{
      "claim_id": 1,
      "novelty": "HIGH|MEDIUM|LOW",
      "closest_work": "最接近的论文标题",
      "delta": "关键差异"
    }}
  ],
  "overall_score": 7,
  "recommendation": "PROCEED|PROCEED_WITH_CAUTION|ABANDON",
  "key_differentiator": "本方案的独特之处",
  "risk": "审稿人可能引用的先前工作",
  "suggested_positioning": "如何定位贡献以最大化新颖性感知"
}}"""


NOVELTY_REPORT_TEMPLATE = """\
## 查新报告

### 研究方案
{method_description}

### 核心主张评估
{claim_assessments_table}

### 最接近的先前工作
| 论文 | 年份 | 会议 | 重叠度 | 关键差异 |
|------|------|------|--------|----------|
{prior_work_table}

### 整体新颖性评估
- **评分**: {score}/10
- **建议**: {recommendation}
- **关键差异化**: {key_differentiator}
- **风险**: {risk}

### 定位建议
{suggested_positioning}
"""


def build_claim_extraction_prompt(method_description: str) -> str:
    """Build prompt for extracting core technical claims from a method."""
    return NOVELTY_CLAIM_EXTRACTION_PROMPT.format(
        method_description=method_description[:4000],
    )


def build_novelty_search_prompt(claim_json: str, claim_id: int = 1) -> str:
    """Build prompt for designing search queries for a claim."""
    return NOVELTY_SEARCH_PROMPT.format(
        claim_json=claim_json[:2000],
        claim_id=claim_id,
    )


def build_novelty_verification_prompt(
    method_description: str,
    claims_json: str,
    search_results: str,
) -> str:
    """Build prompt for cross-model novelty verification."""
    return NOVELTY_VERIFICATION_PROMPT.format(
        method_description=method_description[:3000],
        claims_json=claims_json[:2000],
        search_results=search_results[:4000],
    )


def build_novelty_report(
    method_description: str,
    score: int,
    recommendation: str,
    key_differentiator: str,
    risk: str,
    suggested_positioning: str,
    claim_assessments_table: str = "",
    prior_work_table: str = "",
) -> str:
    """Build the final novelty report from parsed results."""
    return NOVELTY_REPORT_TEMPLATE.format(
        method_description=method_description[:500],
        claim_assessments_table=claim_assessments_table or "（待填充）",
        prior_work_table=prior_work_table or "（待填充）",
        score=score,
        recommendation=recommendation,
        key_differentiator=key_differentiator,
        risk=risk,
        suggested_positioning=suggested_positioning,
    )
