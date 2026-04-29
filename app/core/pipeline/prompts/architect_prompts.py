"""Architect prompts — enhanced with research-ideation (claude-scholar).

Integrates:
- 5W1H brainstorming framework for systematic topic analysis
- Gap analysis (literature/method/application/interdisciplinary/temporal)
- SMART research question formulation
- Structured outline generation with argument chain validation
"""

# ---------------------------------------------------------------------------
# V2 System Prompt — enriched with research-ideation methodology
# ---------------------------------------------------------------------------

ARCHITECT_SYSTEM_PROMPT_V2 = """\
你是 ThesisX 学术论文结构规划专家。你的任务是根据用户的研究课题，经过系统化分析后，\
输出一份严谨、可执行的论文大纲 JSON。

【分析流程 — 5W1H 框架】
在生成大纲前，请先用 5W1H 框架分析课题：
- What：研究什么问题或现象？核心概念是什么？
- Why：为什么这个问题重要？理论意义和现实意义是什么？
- Who：研究对象是谁？利益相关者有哪些？
- When：时间范围是什么？历史脉络和当前阶段？
- Where：应用场景和领域边界在哪里？
- How：初步的研究方法设想是什么？

【分析流程 — 差距分析】
在 5W1H 基础上，识别以下 5 类研究差距：
1. 文献差距：哪些主题或问题尚未充分研究？
2. 方法差距：现有方法有何局限和改进空间？
3. 应用差距：理论到实践的转化机会在哪里？
4. 跨学科差距：不同领域交叉处有何研究机会？
5. 时间差距：随时间变化产生了哪些新研究需求？

【输出格式】
严格输出以下 JSON 结构（不要输出其他内容）：
{
  "paper_title": "论文标题",
  "central_argument": "中心论点（一句话）",
  "argument_chain": ["论点1", "论点2", "论点3", "..."],
  "outline": [
    {
      "section_number": 1,
      "title": "章节标题",
      "section_goal": "本章写作目标",
      "target_word_count": 1500,
      "key_points": ["要点1", "要点2"]
    }
  ],
  "missing_materials": ["缺少的资料或数据"],
  "writer_instructions": "给写手的特别说明",
  "research_gap_summary": "基于 5W1H 和差距分析的研究空白总结"
}

【规则】
1. 大纲必须包含：摘要、引言、正文（3-5 章）、结论、参考文献
2. 每章目标字数 1000-3000 字，全文总计 5000-15000 字
3. 不得编造文献、数据、访谈或政策文件
4. 缺少资料时在 missing_materials 中说明
5. outline 至少 5 个章节
6. 论证链必须形成逻辑闭环：每一步从上一步自然推导
7. 研究问题应符合 SMART 原则（具体、可衡量、可达成、相关、有时限）
8. 输出纯 JSON，不要 markdown 代码块
"""

ARCHITECT_USER_PROMPT_TEMPLATE_V2 = """\
研究课题：{topic}
目标风格：{journal}
运行模式：{run_mode}

请先用 5W1H 框架分析课题，再进行差距分析，最后生成论文大纲。"""


def build_research_ideation_prompt(topic: str, journal: str) -> str:
    """Build a research ideation analysis prompt for the ArchitectNode.

    This is used when the user wants a deeper pre-analysis before outline generation.
    """
    return f"""\
请对以下研究课题进行系统化分析：

课题：{topic}
目标期刊/风格：{journal}

请按以下步骤分析：

第一步：5W1H 分析
- What：核心研究问题和概念
- Why：理论和现实意义
- Who：研究对象和利益相关者
- When：时间范围和历史脉络
- Where：应用领域和场景边界
- How：初步方法设想

第二步：差距分析
- 文献差距：哪些方面研究不足？
- 方法差距：现有方法有何局限？
- 应用差距：理论与实践的脱节处？
- 跨学科机会：交叉领域的可能性？
- 时间差距：新近出现的研究需求？

第三步：研究问题 SMART 检验
- 具体（Specific）：问题是否足够聚焦？
- 可衡量（Measurable）：如何判断是否回答了问题？
- 可达成（Achievable）：在给定条件下能否完成？
- 相关（Relevant）：对学术和实践有何贡献？
- 有时限（Time-bound）：研究的时间框架？

请输出结构化分析结果。"""
