"""Mock data for all workspace pages."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------

MOCK_LITERATURE = [
    {
        "title": "Attention Is All You Need",
        "authors": "Vaswani A, Shazeer N, et al.",
        "year": "2017",
        "source": "NeurIPS",
        "tag": "Transformer",
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": "Devlin J, Chang M, et al.",
        "year": "2019",
        "source": "NAACL",
        "tag": "BERT",
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP",
        "authors": "Lewis P, Perez E, et al.",
        "year": "2020",
        "source": "NeurIPS",
        "tag": "RAG",
    },
    {
        "title": "ChatGPT: Optimizing Language Models for Dialogue",
        "authors": "OpenAI",
        "year": "2022",
        "source": "arXiv",
        "tag": "LLM",
    },
]


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

MOCK_SKILL_CATEGORIES = [
    {"name": "全部技能", "count": 86, "active": True},
    {"name": "常用技能", "count": 24, "active": False},
    {"name": "论文写作", "count": 32, "active": False},
    {"name": "审稿优化", "count": 18, "active": False},
    {"name": "文献处理", "count": 8, "active": False},
    {"name": "数据分析", "count": 4, "active": False},
]

MOCK_SKILLS = [
    {
        "name": "论文写作助手",
        "description": "生成结构化论文初稿，适合从研究课题快速产出章节骨架。",
        "category": "论文写作",
        "tags": ["初稿", "结构化"],
        "usage_count": 12400,
        "rating": 4.8,
        "status": "仅预览",
        "status_type": "warning",
        "risk_level": "中",
        "risk_note": "生成内容需人工核查引用与论证边界。",
        "applicability": "适用于论文大纲、初稿铺写、章节骨架生成。",
        "input_schema": "输入：课题 / 目标风格 / 字数范围",
        "output_schema": "输出：章节结构 / 段落草稿 / 风险标记",
        "agent": "Writer / Architect",
    },
    {
        "name": "实验结果分析",
        "description": "解释统计结果与图表，输出面向论文写作的结果描述。",
        "category": "数据分析",
        "tags": ["统计", "结果解释"],
        "usage_count": 8700,
        "rating": 4.7,
        "status": "未接入",
        "status_type": "muted",
        "risk_level": "高",
        "risk_note": "当前不接真实计算，不可替代正式统计分析。",
        "applicability": "适用于结果描述模板、图表说明草稿。",
        "input_schema": "输入：图表摘要 / 指标说明 / 研究问题",
        "output_schema": "输出：结果描述 / 观察点 / 待核查提示",
        "agent": "Analyst",
    },
    {
        "name": "论文逻辑自检",
        "description": "审查论证链条，识别跳步论证、缺证据点和不充分结论。",
        "category": "审稿优化",
        "tags": ["逻辑链", "审稿"],
        "usage_count": 6400,
        "rating": 4.7,
        "status": "仅预览",
        "status_type": "warning",
        "risk_level": "中",
        "risk_note": "提示可辅助排查问题，但不等于正式同行评审。",
        "applicability": "适用于章节自检、结论收缩、答辩前复查。",
        "input_schema": "输入：章节草稿 / 研究主张 / 证据摘要",
        "output_schema": "输出：逻辑问题清单 / 修订建议",
        "agent": "Reviewer",
    },
    {
        "name": "降低模板化表达",
        "description": "减少机械句式，输出更接近人工写作风格的改写建议。",
        "category": "审稿优化",
        "tags": ["润色", "降痕"],
        "usage_count": 6600,
        "rating": 4.5,
        "status": "即将推出",
        "status_type": "info",
        "risk_level": "高",
        "risk_note": "不得用于规避学术规范审查，只能作为表达润色参考。",
        "applicability": "适用于表达去模板化、句式多样化处理。",
        "input_schema": "输入：段落文本 / 风格要求",
        "output_schema": "输出：改写建议 / 风险提醒",
        "agent": "Polisher",
    },
    {
        "name": "相关工作撰写",
        "description": "组织文献综述结构，帮助梳理研究脉络与研究空白。",
        "category": "文献处理",
        "tags": ["综述", "文献"],
        "usage_count": 5800,
        "rating": 4.4,
        "status": "未接入",
        "status_type": "muted",
        "risk_level": "中",
        "risk_note": "当前不接真实文献库，不可假定引用已验证。",
        "applicability": "适用于综述结构草拟、主题聚类说明。",
        "input_schema": "输入：研究主题 / 文献列表摘要",
        "output_schema": "输出：综述提纲 / 主题分组",
        "agent": "Researcher",
    },
    {
        "name": "审稿意见模拟",
        "description": "从审稿人视角找问题，提前暴露结构和表达风险。",
        "category": "审稿优化",
        "tags": ["审稿", "预检"],
        "usage_count": 10800,
        "rating": 4.7,
        "status": "仅预览",
        "status_type": "warning",
        "risk_level": "中",
        "risk_note": "模拟结果仅供参考，不代表真实期刊审稿结论。",
        "applicability": "适用于投稿前预检、回复提纲准备。",
        "input_schema": "输入：论文摘要 / 章节概要 / 目标期刊",
        "output_schema": "输出：模拟问题清单 / 回复方向",
        "agent": "Reviewer",
    },
]

MOCK_SKILL_DETAIL = {
    "title": "论文写作助手",
    "summary": "当前选中技能为写作类 mock 组件，用于展示技能详情、输入输出说明和风险边界，不代表已接通真实 Skill Registry。",
    "status": "仅预览",
    "status_type": "warning",
    "use_cases": [
        "根据研究课题快速生成章节骨架",
        "为摘要、引言、方法部分生成初稿框架",
        "为后续人工改写保留风险标记",
    ],
    "input_schema": [
        "课题描述",
        "目标风格 / 期刊类型",
        "字数范围 / 研究边界",
    ],
    "output_schema": [
        "结构化章节草稿",
        "待核查引用标记",
        "潜在风险说明",
    ],
    "risk_rules": [
        "不得将生成内容视为已验证引用",
        "不得将 mock 状态解释为可运行技能",
        "必须人工复核论证边界和事实来源",
    ],
}


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

MOCK_VERSIONS = [
    {
        "version": "v3",
        "description": "第三稿：修改理论框架，补充案例分析",
        "author": "Magnus",
        "time": "今天 14:30",
    },
    {
        "version": "v2",
        "description": "第二稿：根据导师反馈修改文献综述",
        "author": "Magnus",
        "time": "昨天 09:15",
    },
    {
        "version": "v1",
        "description": "初稿：完成全文初稿",
        "author": "Magnus",
        "time": "3 天前",
    },
]

# Version history timeline — aligned with page_07_version_history.svg
MOCK_VERSION_TIMELINE = [
    {
        "version": "v12",
        "label": "最新版本",
        "active": True,
        "summary": "完成去痕润色并收缩结论表达",
        "source": "AI 润色预览",
        "agent": "润色师",
        "skill": "AI 去痕润色",
        "review": "MINOR_REVISION",
        "cost": "¥1.20",
        "tokens": "1.8k tokens",
        "time": "今天 16:45",
        "risk_notes": [
            "当前页面未接入真实版本持久化与回滚。",
            "Diff 内容为 mock 对比摘要，不代表真实逐字差异。",
            "恢复 / 比较 / 导出按钮仅用于界面预览。",
        ],
    },
    {
        "version": "v11",
        "label": "审稿修改",
        "active": False,
        "summary": "根据 reviewer 意见补充逻辑链与限制说明",
        "source": "审稿修改预览",
        "agent": "审稿专家",
        "skill": "逻辑链审查",
        "review": "MAJOR_REVISION",
        "cost": "¥2.80",
        "tokens": "3.2k tokens",
        "time": "今天 14:30",
        "risk_notes": [
            "仅展示 mock 审稿修改节点。",
            "不连接真实 Git、数据库或历史恢复。",
        ],
    },
    {
        "version": "v10",
        "label": "草稿",
        "active": False,
        "summary": "形成初版章节结构和案例分析草稿",
        "source": "初稿生成预览",
        "agent": "论文写手",
        "skill": "论文结构规划",
        "review": "—",
        "cost": "¥3.50",
        "tokens": "4.6k tokens",
        "time": "昨天 20:10",
        "risk_notes": [
            "内容为 mock 版本轨迹，不代表真实生成记录。",
        ],
    },
    {
        "version": "v9",
        "label": "引用补充",
        "active": False,
        "summary": "补充近三年文献并统一引用格式",
        "source": "引用整理预览",
        "agent": "文献研究员",
        "skill": "引用格式检查",
        "review": "—",
        "cost": "¥0.60",
        "tokens": "0.9k tokens",
        "time": "昨天 18:00",
        "risk_notes": [
            "仅预览引用补充节点，不接真实文献库历史。",
        ],
    },
]

# Version diff blocks — aligned with component_version_diff_card.svg
MOCK_VERSION_DIFFS = {
    "v11→v12": {
        "title": "版本对比 v11 → v12",
        "deletions": [
            "该段直接断言 AI 显著提升效率，证据不足。",
            "引用了未经核查的案例数据。",
        ],
        "additions": [
            "改为\"可能改善分类与资源匹配过程\"。",
            "添加 [引用待核查] 标记，待人工核实。",
        ],
        "reason": "降低过度结论，匹配证据边界。",
    },
    "v10→v11": {
        "title": "版本对比 v10 → v11",
        "deletions": [
            "第三章理论框架概念界定模糊。",
            "文献综述缺少近三年研究进展。",
        ],
        "additions": [
            "明确界定核心概念，引用王五 (2023) 定义。",
            "补充 2022-2024 年数字化治理文献 5 篇。",
        ],
        "reason": "根据审稿意见修改理论框架与文献综述。",
    },
    "v9→v10": {
        "title": "版本对比 v9 → v10",
        "deletions": [
            "[占位] 此前为引用补充版本的差异。",
        ],
        "additions": [
            "完成全文初稿，包含摘要、正文五章、结论。",
            "参考文献格式统一为 GB/T 7714。",
        ],
        "reason": "从引用补充版本扩展为完整初稿。",
    },
}

# Chat conversation history — aligned with page_03_ai_chat.svg
MOCK_CHAT_HISTORY = [
    {"title": "优化论文引言", "time": "今天 14:20", "active": True},
    {"title": "解释 Transformer 架构", "time": "昨天 16:00", "active": False},
    {"title": "润色审稿意见回复", "time": "3 天前", "active": False},
    {"title": "生成文献综述大纲", "time": "上周五", "active": False},
]

# Literature detail — aligned with page_04_literature_management.svg
MOCK_LIT_DETAILS = {
    "abstract": "提出了 Transformer 模型架构，完全基于注意力机制，摒弃了循环和卷积结构。在机器翻译任务上取得了最先进的性能，同时大幅提升了训练效率。",
    "citation_gb": "Vaswani A, Shazeer N, Parmar N, et al. Attention is all you need[C]//Advances in Neural Information Processing Systems. 2017: 5998-6008.",
    "citation_apa": "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. In Advances in Neural Information Processing Systems (pp. 5998-6008).",
    "scores": {
        "相关性": 92,
        "影响力": 98,
        "时效性": 75,
        "可信度": 95,
    },
    "source_status": "已获取全文",
    "tags": ["Transformer", "注意力机制", "NLP", "NeurIPS 2017"],
}


# ---------------------------------------------------------------------------
# Collaboration
# ---------------------------------------------------------------------------

MOCK_COLLABORATION_MSGS = [
    {
        "sender": "导师 · 张教授",
        "content": "第三章的理论框架需要更清晰地界定核心概念，建议参考王五 (2023) 的定义。",
        "time": "2 小时前",
    },
    {
        "sender": "Magnus",
        "content": "收到，我会在今晚前修改完成。另外关于案例选择，您觉得是否需要增加一个对比案例？",
        "time": "1 小时前",
    },
    {
        "sender": "导师 · 张教授",
        "content": "可以考虑加入深圳的案例，他们在这方面做得比较有代表性。",
        "time": "30 分钟前",
    },
]

MOCK_TASKS = [
    {"title": "修改理论框架", "assignee": "Magnus", "priority": "高", "status": "进行中"},
    {"title": "补充政策文献", "assignee": "Magnus", "priority": "中", "status": "待开始"},
    {"title": "格式检查", "assignee": "Magnus", "priority": "低", "status": "待开始"},
]


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

MOCK_SUBMISSION_STATS = [
    {"label": "待投稿", "count": 2},
    {"label": "审稿中", "count": 1},
    {"label": "Rebuttal", "count": 1},
    {"label": "已接收", "count": 1},
]

MOCK_SUBMISSIONS = [
    {
        "journal": "ACL 2024",
        "paper": "Adaptive Review-Aware Thesis Writing",
        "status": "Under Review",
        "status_type": "warning",
        "submitted": "2024-05-10",
        "round": "Round 1",
        "action": "查看",
    },
    {
        "journal": "EMNLP 2024",
        "paper": "Evidence-Scoped Rebuttal Planning for LLM Writing",
        "status": "Rebuttal",
        "status_type": "primary",
        "submitted": "2024-04-20",
        "round": "Reply Due",
        "action": "回复",
    },
    {
        "journal": "AAAI 2024",
        "paper": "Policy-Grounded Multi-Agent Drafting",
        "status": "Rejected",
        "status_type": "error",
        "submitted": "2024-03-15",
        "round": "Decision",
        "action": "查看",
    },
    {
        "journal": "IJCAI 2024",
        "paper": "Human-in-the-Loop Revision Traces",
        "status": "Accepted",
        "status_type": "success",
        "submitted": "2024-02-01",
        "round": "Camera Ready",
        "action": "查看",
    },
    {
        "journal": "中国行政管理",
        "paper": "数字化转型背景下基层治理创新研究",
        "status": "待投稿",
        "status_type": "warning",
        "submitted": "—",
        "round": "待选期刊",
        "action": "提交",
    },
]

MOCK_REBUTTAL_DETAIL = {
    "title": "EMNLP 2024 · Evidence-Scoped Rebuttal Planning for LLM Writing",
    "decision": "Rebuttal Required",
    "decision_type": "warning",
    "main_issues": [
        "实验设置与基线比较描述不充分",
        "对人工审校流程的证据解释不够具体",
        "结论部分对泛化能力表述偏强",
    ],
    "response_plan": [
        "补充 baseline 选择理由与消融结果摘要",
        "收缩关于泛化能力的表述，并增加限制说明",
        "逐条映射 reviewer concern 到修订段落位置",
    ],
    "materials": [
        "补实验表格摘要",
        "修订后结论段草稿",
        "逐条 rebuttal response 模板",
    ],
    "risk_notes": [
        "当前页面不接真实投稿系统，状态仅为 mock",
        "回复计划不代表已生成正式 rebuttal 文本",
        "不得将按钮理解为真实提交、导出或同步功能",
    ],
}


# ---------------------------------------------------------------------------
# AI Chat
# ---------------------------------------------------------------------------

MOCK_AGENTS = [
    {"name": "写作助手", "role": "论文撰写与修改", "status": "在线", "status_type": "success"},
    {"name": "文献顾问", "role": "文献检索与分析", "status": "在线", "status_type": "success"},
    {"name": "审稿专家", "role": "论文审阅与反馈", "status": "离线", "status_type": "muted"},
    {"name": "数据分析师", "role": "数据处理与可视化", "status": "离线", "status_type": "muted"},
]

MOCK_CHAT_MESSAGES = [
    {
        "sender": "user",
        "content": "帮我看看第三章的论证逻辑有没有问题？",
        "time": "14:20",
    },
    {
        "sender": "agent",
        "agent": "写作助手",
        "content": "我仔细阅读了第三章，发现以下逻辑问题：\n\n1. 第二节的论点与第一节的结论之间缺乏过渡\n2. 第三段的案例与论点关联性不够强\n3. 建议在第二节末尾增加一个小结段落",
        "time": "14:21",
    },
    {
        "sender": "user",
        "content": "好的，帮我修改第二节的过渡部分。",
        "time": "14:25",
    },
    {
        "sender": "agent",
        "agent": "写作助手",
        "content": "已为您生成过渡段落草稿，请查看编辑器中的修改建议。注意：生成内容仅供参考，请根据实际研究进行调整。",
        "time": "14:26",
    },
]

MOCK_CHAT_CONTEXT = {
    "current_paper": "数字化转型背景下基层治理创新研究",
    "chapter": "第三章 理论框架",
    "word_count": "12,340 字",
    "last_review": "2024-03-20",
}


# ---------------------------------------------------------------------------
# Data & Charts
# ---------------------------------------------------------------------------

MOCK_DATASET_CATEGORIES = [
    {"name": "全部数据集", "count": 36, "active": True},
    {"name": "问卷数据", "count": 18, "active": False},
    {"name": "分析结果", "count": 12, "active": False},
    {"name": "实验数据", "count": 6, "active": False},
]

MOCK_DATASETS = [
    {
        "name": "education_train.csv",
        "file_type": "CSV",
        "size": "12.4 MB",
        "updated": "2024-03-18",
        "status": "已解析",
        "status_type": "success",
    },
    {
        "name": "model_results.xlsx",
        "file_type": "XLSX",
        "size": "856 KB",
        "updated": "2024-03-15",
        "status": "仅预览",
        "status_type": "warning",
    },
    {
        "name": "survey_summary.csv",
        "file_type": "CSV",
        "size": "3.2 MB",
        "updated": "2024-03-12",
        "status": "待核查",
        "status_type": "muted",
    },
]

MOCK_CHARTS = [
    {
        "title": "居民满意度分布",
        "type": "柱状图",
        "status": "仅预览",
        "status_type": "warning",
        "preview": "bar",
    },
    {
        "title": "治理效能趋势",
        "type": "折线图",
        "status": "仅预览",
        "status_type": "warning",
        "preview": "line",
    },
    {
        "title": "政策来源占比",
        "type": "饼图",
        "status": "仅预览",
        "status_type": "warning",
        "preview": "pie",
    },
    {
        "title": "特征关联热度",
        "type": "热力图",
        "status": "仅预览",
        "status_type": "warning",
        "preview": "heatmap",
    },
]
