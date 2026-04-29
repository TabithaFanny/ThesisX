"""Multi-source literature search prompts — from research-lit (ARIS).

Seven-source search (Zotero → Obsidian → Local PDFs → Web → Semantic
Scholar → DeepXiv → Exa) with configurable source selection, de-dup,
and structured paper analysis.
"""

LITERATURE_SEARCH_SYSTEM_PROMPT = """\
你是 ThesisX 文献检索专家。你的任务是围绕研究主题进行多源文献检索、
去重、分析和综合。

【数据源优先级】
1. Zotero（用户已有文献库）—— 如可用
2. Obsidian（用户研究笔记）—— 如可用
3. 本地 PDF（papers/ 或 literature/ 目录）
4. Web 搜索（arXiv、Google Scholar、Semantic Scholar）
5. Semantic Scholar API（已发表会议/期刊论文，需显式请求）
6. DeepXiv（渐进式论文检索，需显式请求）
7. Exa（AI 驱动广泛网页搜索，需显式请求）

【分析维度】（对每篇相关论文）
- Problem: 解决什么问题？
- Method: 核心技术贡献（1-2 句）
- Results: 关键数字/声明
- Relevance: 与我们工作的关系
- Source: 在哪里找到的

【输出要求】
1. 结构化文献表格：
   | 论文 | 会议 | 方法 | 关键结果 | 与我们的相关性 | 来源 |
2. 叙事性综述（3-5 段）：按主题/方法分组，共识 vs 分歧，研究空白
3. BibTeX 引用（如可用）

【去重规则】
- 按 arXiv ID 匹配
- 按 DOI 匹配
- 按归一化标题匹配
- 同一论文出现在多个来源时，保留最丰富的元数据版本"""


LITERATURE_ANALYSIS_PROMPT = """\
请分析以下论文与研究主题 "{topic}" 的相关性。

【论文信息】
标题: {title}
作者: {authors}
年份: {year}
摘要: {abstract}
来源: {source}

【分析要求】
1. 判断相关程度：HIGHLY_RELATED / RELATED / TANGENTIALLY / UNRELATED
2. 提取核心贡献（1-2 句）
3. 与研究主题的具体关联
4. 对我们工作的启发或参考价值

【输出格式】
JSON:
{{
  "relevance": "HIGHLY_RELATED|RELATED|TANGENTIALLY|UNRELATED",
  "core_contribution": "",
  "connection_to_topic": "",
  "insights": "",
  "should_include": true
}}"""


LITERATURE_SYNTHESIS_PROMPT = """\
请基于以下已分析的文献，撰写文献综述。

【研究主题】
{topic}

【已分析的文献列表】
{papers_summary}

【综述要求】
1. 按方法/主题分组（非按论文逐篇罗列）
2. 识别共识 vs 分歧
3. 发现研究空白（gaps）
4. 指出我们的工作可以填补哪些空白
5. 3-5 段，每段聚焦一个子主题

【禁止】
- 不要罗列式综述（"A 做了 X，B 做了 Y"）
- 不要简单堆砌摘要
- 要有分析、比较和定位"""


PAPER_SCORING_PROMPT = """\
请对以下论文进行质量评分。

【论文信息】
标题: {title}
作者: {authors}
年份: {year}
会议/期刊: {venue}
被引次数: {citations}
摘要: {abstract}

【评分维度】（每项 0-10）
1. metadata_score: 元数据完整度
2. relevance_score: 与主题相关度
3. credibility_score: 可信度（同行评审？被引？）
4. access_score: 可获取性（OA？有全文？）

【输出格式】
JSON:
{{
  "metadata_score": 0,
  "relevance_score": 0,
  "credibility_score": 0,
  "access_score": 0,
  "overall_score": 0,
  "flags": ["has_doi", "peer_reviewed", "open_access"]
}}"""


def build_literature_search_system_prompt() -> str:
    """Return the multi-source literature search system prompt."""
    return LITERATURE_SEARCH_SYSTEM_PROMPT


def build_literature_analysis_prompt(
    topic: str,
    title: str,
    authors: str,
    year: str,
    abstract: str,
    source: str = "web",
) -> str:
    """Build prompt for analyzing a single paper's relevance."""
    return LITERATURE_ANALYSIS_PROMPT.format(
        topic=topic[:500],
        title=title[:300],
        authors=authors[:300],
        year=year,
        abstract=abstract[:2000],
        source=source,
    )


def build_literature_synthesis_prompt(
    topic: str,
    papers_summary: str,
) -> str:
    """Build prompt for synthesizing a literature review."""
    return LITERATURE_SYNTHESIS_PROMPT.format(
        topic=topic[:500],
        papers_summary=papers_summary[:6000],
    )


def build_paper_scoring_prompt(
    title: str,
    authors: str,
    year: str,
    venue: str,
    citations: str,
    abstract: str,
) -> str:
    """Build prompt for scoring paper quality."""
    return PAPER_SCORING_PROMPT.format(
        title=title[:300],
        authors=authors[:300],
        year=year,
        venue=venue or "未知",
        citations=citations or "未知",
        abstract=abstract[:1500],
    )
