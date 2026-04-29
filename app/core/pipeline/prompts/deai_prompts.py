"""De-AI prompts — from AI Writing Decontaminator + writing-anti-ai + Humanizer-zh.

Integrates three sources:
1. academic-agents/academic-ai-decontaminator: 70+ English blacklist, 6-category Chinese patterns, dual-language mode
2. claude-scholar/writing-anti-ai: 5 core rules, 5-dimension scoring, Wikipedia-based pattern detection
3. Humanizer-zh: 24 AI writing pattern categories, two-pass (rewrite + audit) approach

Key design decisions:
- Two-pass approach: rewrite pass + audit pass
- Pass signal: [检测通过] when text is already natural
- Modify-only-when-needed philosophy
- Preserve technical terms, [引用待核查], [数据待补充] markers
"""

# ---------------------------------------------------------------------------
# Complete Chinese AI blacklist (merged from all sources)
# ---------------------------------------------------------------------------

DEAI_BLACKLIST_ZH: list[str] = [
    # Emotional rendering (情感渲染)
    "毋庸置疑", "不可磨灭", "颠覆性", "令人惊叹", "至关重要",
    "深入探讨", "持久的", "充满活力的", "不可忽视",
    # Buzzword inflation (术语膨胀)
    "范式转移", "耦合内聚", "切中要害", "本质", "赋能",
    "多措并举", "提质增效", "建立健全",
    # Mechanical connectors (机械连接)
    "此外", "综上所述", "显著提升", "充分体现", "深刻表明",
    # Template phrases (模板句式)
    "随着时代的发展", "在新时代背景下",
    "具有重要理论意义和现实意义",
    "不是……而是……", "不仅……更……",
    # Pattern categories (模式类)
    "增强", "培养", "格局", "获得", "突出",
    "相互作用", "复杂性", "关键性的", "展示", "织锦", "证明", "宝贵的",
]

# ---------------------------------------------------------------------------
# Complete English AI blacklist (70+ words from decontaminator)
# ---------------------------------------------------------------------------

DEAI_BLACKLIST_EN: list[str] = [
    "Accentuate", "Ador", "Amass", "Ameliorate", "Amplify", "Alleviate",
    "Ascertain", "Advocate", "Articulate", "Bear", "Bolster", "Bustling",
    "Cherish", "Conceptualize", "Conjecture", "Consolidate", "Convey",
    "Culminate", "Decipher", "Demonstrate", "Depict", "Devise", "Delineate",
    "Delve", "Delve Into", "Diverge", "Disseminate", "Elucidate", "Endeavor",
    "Engage", "Enumerate", "Envision", "Enduring", "Exacerbate", "Expedite",
    "Foster", "Galvanize", "Harmonize", "Hone", "Innovate", "Inscription",
    "Integrate", "Interpolate", "Intricate", "Lasting", "Leverage", "Manifest",
    "Mediate", "Nurture", "Nuance", "Nuanced", "Obscure", "Opt", "Originates",
    "Perceive", "Perpetuate", "Permeate", "Pivotal", "Ponder", "Prescribe",
    "Prevailing", "Profound", "Recapitulate", "Reconcile", "Rectify",
    "Rekindle", "Reimagine", "Scrutinize", "Substantiate", "Tailor",
    "Testament", "Transcend", "Traverse", "Underscore", "Unveil", "Vibrant",
    "Tapestry", "Landscape", "Multifaceted", "Comprehensive", "Robust",
]

# ---------------------------------------------------------------------------
# 24 AI writing pattern categories (from Humanizer-zh)
# ---------------------------------------------------------------------------

DEAI_PATTERNS_ZH: list[tuple[str, str, str]] = [
    # (pattern_name, detection_hint, fix_instruction)
    ("意义膨胀", "里程碑、重大意义、深远影响", "用事实陈述替代宏大叙事"),
    ("媒体堆砌", "据XX报道、XX指出", "具体引用来源、日期和研究"),
    ("表面分析", "象征着……反映了……展示了", "删除空洞分析或补充真实来源"),
    ("推销语言", "风景如画、令人惊叹", "使用中性客观描述"),
    ("模糊归因", "专家认为、研究表明", "具名来源、日期和研究"),
    ("模板挑战句", "尽管面临挑战……仍持续", "陈述具体挑战和事实"),
    ("AI常用词", "此外、至关重要、深入探讨", "使用更简单的同义词"),
    ("系动词回避", "充当、具备代替是/有", "直接用是/有"),
    ("否定对比", "不只是X，而是Y", "直接陈述观点"),
    ("三项列举", "创新、启发与洞见", "使用自然的列举长度"),
    ("同义词轮换", "同一概念反复换词", "重复使用最清晰的术语"),
    ("破折号滥用", "过多——破折号", "改用逗号或句号"),
    ("粗体滥用", "每个关键词都加粗", "删除不必要的粗体"),
    ("空洞结论", "未来一片光明、前景广阔", "提供具体计划或事实"),
    ("填充短语", "为了能够、由于这样的事实", "缩短为为了、因为"),
    ("过度对冲", "也许可能大概或许", "使用单一对冲词"),
]

# ---------------------------------------------------------------------------
# Common English replacements
# ---------------------------------------------------------------------------

EN_REPLACEMENTS: dict[str, str] = {
    "Leverage": "Use",
    "Delve into": "Investigate, Examine",
    "Elucidate": "Explain, Clarify",
    "Pivotal": "Important, Key",
    "Unveil": "Present, Introduce",
    "Intricate": "Complex",
    "Endeavor": "Attempt, Effort",
    "Underscore": "Highlight, Emphasize",
    "Substantiate": "Support, Confirm",
    "Ameliorate": "Improve",
    "Scrutinize": "Examine",
    "Depict": "Show",
    "Nuanced": "Subtle",
    "Foster": "Encourage",
    "Bolster": "Support",
    "Robust": "Strong, Reliable",
    "Comprehensive": "Thorough, Complete",
    "Multifaceted": "Complex, Multi-dimensional",
}

# ---------------------------------------------------------------------------
# V2 System Prompt — merged from all three sources
# ---------------------------------------------------------------------------

DEAI_SYSTEM_PROMPT_V2 = """\
你是 ThesisX 学术文本去 AI 痕迹专家。你是一位取证语言学家，能够像鉴定伪造笔迹一样\
识别和消除机器生成的文本模式。你同时支持中文学术文本和英文学术文本。

【核心原则】
1. 保留原意、引用、证据链和 LaTeX 命令
2. 不增加未经验证的内容
3. 改写时保持学术严谨性
4. 如果某段已经很自然，不要强行修改 — 最好的编辑是你不做的编辑
5. 保留专业术语，不为风格原因替换领域专有名词
6. 保留 [引用待核查] 和 [数据待补充] 标记

【两遍处理法】
第一遍 · 重写：扫描全文，替换所有 AI 痕迹明显的词汇和句式
第二遍 · 审计：以"这段文字哪里一看就是 AI 写的？"为标准，做最终检查

【中文检测规则 — 6 类模式】
1. 情感渲染：毋庸置疑、不可磨灭、颠覆性、令人惊叹 → 替换为客观描述
2. 术语膨胀：范式转移、耦合内聚、切中要害 → 替换为具体术语
3. 翻译腔句式：一个...的...的...的 → 拆分为短句
4. 过度被动：...被用来优化... → 采用...优化...
5. 机械列举：首先...其次...最后... → 融合为连贯段落
6. 痛点行话：解决这一痛点 → 针对上述问题

【英文检测规则】
以下英文词汇在 AI 输出中异常高频，替换为更简单的同义词：
{en_blacklist}

常用替换表：
{en_replacements}

【人性化原则】
1. 有观点 — 对事实有反应，不只是报告
2. 变节奏 — 长短句混合，不要每句同长度
3. 承认复杂性 — 真实的人有细腻的感受
4. 适当使用第一人称（中文学术写作中可酌情使用"本文""本研究"）
5. 允许一些不完美 — 完美结构显得机械
6. 用具体细节替代抽象概括

【自检清单 — 交付前必须确认】
1. 自然度：读起来像人类研究者写的吗？
2. 必要性：每处修改都真的提升了可读性吗？如果只是换词，请还原
3. 技术准确性：有没有误替专业术语？
4. 格式合规：英文 LaTeX 是否完整？中文是否有 Markdown 残留？
5. 通过信号：如果原文已经干净，是否发出了正确的通过信号？

【通过信号】
- 英文：[检测通过] 原文表达地道自然，无明显 AI 味，建议保留。
- 中文：[检测通过] 原文表达严谨自然，无明显 AI 痕迹，建议保留。

【输出格式】
第一部分：改写后的完整论文文本（如无需修改则输出原文）
第二部分：修改日志（格式为"原文→改后"，如无需修改则输出通过信号）
第三部分：5 维写作质量评分
  - Directness（直接性）：/10
  - Rhythm（节奏感）：/10
  - Trust（信任度）：/10
  - Authenticity（真实感）：/10
  - Density（密度）：/10

【禁止行为】
- 不得编造文献、数据或引用
- 不得删除 [引用待核查] 或 [数据待补充] 标记
- 不得改变论文的核心论点和结论
- 不得引入 Markdown 格式（中文输出必须是纯文本）
- 不得为了换词而换词 — 每处修改必须有明确理由"""


def build_deai_user_prompt(paper_text: str, language: str = "zh") -> str:
    """Build the user prompt for the De-AI humanizer.

    Args:
        paper_text: The paper text to humanize.
        language: "zh" for Chinese, "en" for English, "auto" for auto-detect.
    """
    lang_instruction = {
        "zh": "请对以下中文学术论文进行去 AI 痕迹处理：",
        "en": "Please de-AI the following English academic text:",
        "auto": "请自动检测语言，并对以下学术文本进行去 AI 痕迹处理：",
    }.get(language, "请对以下学术文本进行去 AI 痕迹处理：")

    return f"""\
{lang_instruction}

---
{paper_text[:8000]}
---

请按照系统提示中的两遍处理法：
第一遍：重写所有 AI 痕迹明显的段落
第二遍：审计全文，检查是否还有明显 AI 生成的痕迹

最后给出 5 维写作质量评分。"""
