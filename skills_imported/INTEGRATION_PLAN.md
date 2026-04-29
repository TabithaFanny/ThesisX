# Skills 融合规划

## 来源仓库

| 仓库 | 文件 | 核心价值 |
|------|------|---------|
| claude-scholar | skills/*.md | 研究全流程 skill（选题/写作/审稿/去AI） |
| academic-agents | agents/*.md | 11 个超专精 Agent，嵌入了 MSRA/PKU/USTC 的实战 prompt |
| awesome-ai-research-writing | README.md | 17 个写作 prompt 模板，80+ 黑名单 |
| Humanizer-zh | SKILL.md | 24 种 AI 模式，两遍处理法 |

## 融合映射表

### Pipeline Node → Skills 来源

| Pipeline Node | 融合的 Skill | 来源 | 优先级 |
|--------------|-------------|------|--------|
| **ArchitectNode** | research-ideation | claude-scholar | P0 |
| **Advisor** (Agent Team) | research-ideation + 选题评估 | claude-scholar | P1 |
| **Writer 逻辑轮** | ml-paper-writing (逻辑部分) | claude-scholar | P0 |
| **Writer 理论轮** | Chinese Academic Restructurer | academic-agents | P0 |
| **Writer 语言轮** | English/Chinese Academic Polisher | academic-agents | P0 |
| **Reviewer** | Peer Review Simulator + paper-self-review | academic-agents + claude-scholar | P0 |
| **Polisher** | Chinese Academic Polisher (保守模式) | academic-agents | P1 |
| **DeAIHumanizer** | AI Writing Decontaminator + writing-anti-ai + Humanizer-zh | academic-agents + claude-scholar + Humanizer-zh | P0 |
| **Logic Auditor** | Logic Auditor | academic-agents | P1 |
| **Caption Writer** | Academic Caption Writer | academic-agents | P2 |
| **Data Specialist** | Experiment Data Specialist | academic-agents | P2 |
| **Illustrator** | Paper Architecture Illustrator | academic-agents | P2 |
| **Translator** | Academic Translator | academic-agents | P1 |
| **Text Optimizer** | Text Length Optimizer | academic-agents | P2 |
| **Citation Verifier** | citation-verification | claude-scholar | P1 |
| **Rebuttal Writer** | review-response | claude-scholar | P1 |
| **Camera-ready** | post-acceptance | claude-scholar | P2 |
| **LaTeX Organizer** | latex-conference-template-organizer | claude-scholar | P2 |

### 融合方式

```
skills_imported/          ← 原始下载（保留原样，不修改）
    academic-agents/
    claude-scholar/
    awesome-writing/
    humanizer/

app/core/pipeline/prompts/  ← 融合后的 prompt 库（从原始文件提取+改写）
    __init__.py
    architect_prompts.py     ← research-ideation → ArchitectNode
    writer_logic_prompts.py  ← ml-paper-writing 逻辑部分
    writer_theory_prompts.py ← academic-agents restructurer
    writer_lang_prompts.py   ← academic-agents polisher
    reviewer_prompts.py      ← Peer Review Simulator + paper-self-review
    deai_prompts.py          ← Decontaminator + writing-anti-ai + Humanizer-zh
    translator_prompts.py    ← Academic Translator（双向中英翻译）
    logic_auditor_prompts.py ← Logic Auditor（红线审查）
    citation_prompts.py      ← Citation Verification（引用验证）
    experiment_prompts.py    ← Experiment Data Specialist（19 种图表 + 分析段落）
    illustrator_prompts.py   ← Paper Architecture Illustrator（架构图 prompt）
    caption_prompts.py       ← Academic Caption Writer（图表标题）
    optimizer_prompts.py     ← Text Length Optimizer（±5-15 词精确调整）
    rebuttal_prompts.py      ← review-response（审稿回复策略+模板+语气）
    camera_ready_prompts.py  ← post-acceptance（演示/海报/推广）
    latex_template_prompts.py← latex-conference-template-organizer（LaTeX 模板整理）

app/core/pipeline/nodes/    ← Agent 节点
    __init__.py
    architect_node.py        ← 自研大纲规划节点
    deai_humanizer.py        ← 去 AI 痕迹节点
    translator_node.py       ← 翻译节点（Batch 2）
    logic_auditor_node.py    ← 逻辑审计节点（Batch 2）
    citation_verifier_node.py← 引用验证节点（Batch 2）
```

## 分批实施计划

### Batch 1（P0，本次实施）
1. ✅ research-ideation → 增强 ArchitectNode 的大纲生成 prompt
2. ✅ ml-paper-writing → 注入 Writer 三轮策略的详细指令
3. ✅ Peer Review Simulator → 替换 Reviewer 的审稿 prompt
4. ✅ AI Writing Decontaminator + Humanizer-zh → 增强 DeAIHumanizer 的检测规则

### Batch 2（P1）
5. ✅ Academic Translator → translator_prompts.py + TranslatorNode
6. ✅ Chinese Academic Restructurer → writer_theory_prompts.py（Writer 理论轮）
7. ✅ citation-verification → citation_prompts.py + CitationVerifierNode
8. ✅ Logic Auditor → logic_auditor_prompts.py + LogicAuditorNode

### Batch 3（P2）
9. ✅ Experiment Data Specialist → experiment_prompts.py（19 种图表 + 实验分析段落）
10. ✅ Paper Architecture Illustrator → illustrator_prompts.py（双语架构图 prompt）
11. ✅ Academic Caption Writer → caption_prompts.py（图/表标题生成）
12. ✅ Text Length Optimizer → optimizer_prompts.py（压缩/扩展 ±5-15 词）

### Batch 4（P1-P2，补充融合）
13. ✅ review-response → rebuttal_prompts.py（审稿回复：分类/策略/模板/语气/会议特化）
14. ✅ post-acceptance → camera_ready_prompts.py（会议准备：幻灯片/海报/推广内容）
15. ✅ latex-conference-template-organizer → latex_template_prompts.py（LaTeX 模板整理：KDD/NeurIPS/ICML/ICLR/CVPR/ACL/AAAI）

### 跳过的低价值文件
- publication-chart-skill → 已被 experiment_prompts.py 覆盖
- results-analysis → 已被 experiment_prompts.py 覆盖
- results-report → 已被 experiment_prompts.py 覆盖
- daily-paper-generator → 功能与 ThesisX 核心无关
- verification-loop → 已被 citation_prompts.py 覆盖

---

## ARIS 融合规划

### 来源仓库

| 仓库 | 核心价值 |
|------|---------|
| ARIS (affaan-m/Auto-claude-code-research-in-sleep) | 68 个 SKILL.md，覆盖学术研究全流程，跨模型对抗审稿，7.7k stars，AAAI 2026 |

### ARIS 融合映射表

| ARIS Skill | ThesisX Prompt 模块 | 新增能力 | 状态 |
|------------|---------------------|---------|------|
| **novelty-check** | `novelty_prompts.py` | 研究查新（4 阶段：提取主张→多源检索→跨模型验证→查新报告） | ✅ Batch 5 |
| **paper-claim-audit** | `claim_audit_prompts.py` | 零上下文数据审计（新鲜审稿人只看论文+原始结果，抓数字膨胀/种子挑选/配置不匹配） | ✅ Batch 5 |
| **auto-review-loop** | `auto_review_prompts.py` | 自动审稿循环（medium/hard/nightmare 三级难度，审稿人记忆，辩论协议） | ✅ Batch 5 |
| **research-lit** | `literature_search_prompts.py` | 多源文献检索（7 源去重，论文评分，综述合成） | ✅ Batch 5 |
| **citation-audit** | `citation_prompts.py` (增强) | 三层引用审计（存在性 + 元数据正确性 + 上下文适当性） | ✅ Batch 5 |
| **paper-write** | 已被 writer_*_prompts.py 覆盖 | LaTeX 论文生成（章节级） | 跳过（重叠） |
| **paper-plan** | 已被 architect_prompts.py 覆盖 | Claims-Evidence Matrix 大纲 | 跳过（重叠） |
| **rebuttal** | 已被 rebuttal_prompts.py 覆盖 | 审稿回复 | 跳过（重叠） |

### Batch 5（ARIS 融合）
16. ✅ novelty-check → novelty_prompts.py（查新报告：主张提取 + 多源检索策略 + 跨模型验证）
17. ✅ paper-claim-audit → claim_audit_prompts.py（零上下文数据审计：7 种失败模式检测）
18. ✅ auto-review-loop → auto_review_prompts.py（三级难度审稿循环 + 审稿人记忆 + 辩论协议）
19. ✅ research-lit → literature_search_prompts.py（7 源文献检索 + 论文评分 + 综述合成）
20. ✅ citation-audit → citation_prompts.py 增强（三层审计：存在性 + 元数据 + 上下文）

---

## 外部工具融合规划

### MinerU PDF 解析（V4 阶段）

| 项目 | 核心能力 | 接入方式 |
|------|---------|---------|
| MinerU (opendatalab/MinerU) | PDF→结构化 Markdown，61.5k stars，109 语言 OCR | `magic-pdf` CLI 或 Python API，作为 Document Parsing Layer 后端 |

**接入计划**：
- V4 阶段引入，作为 `DocumentParser` Protocol 的第一个实现
- 支持文本型 PDF（PyMuPDF）和扫描型 PDF（MinerU VLM/OCR）
- 输出统一 `DocumentMarkdown + StructuredMetadata + Chunks`
- macOS mlx 加速支持

### research-assist Zotero 连接器（V5 阶段）

| 项目 | 核心能力 | 接入方式 |
|------|---------|---------|
| research-assist (TimGuttmann/research-assist) | Zotero→profile→arXiv→rank→digest，6 阶段 Agent 流水线 | 作为 `SourceConnector` Protocol 的 Zotero 实现 |

**接入计划**：
- V5 阶段引入，作为 Source Connector Layer 的 Zotero 连接器
- 复用其双信号评分器（0.30 map_match + 0.70 zotero_semantic）
- 复用 Zotero MCP 集成模式
- 适配 `SourceConnector` Protocol（fetch → parse → score → dedup）

### literature-downloader-skill（V5 阶段）

| 项目 | 核心能力 | 接入方式 |
|------|---------|---------|
| literature-downloader-skill | 零依赖 Python（stdlib only），付费墙检测，合规架构 | 作为 Download Manager 的下载引擎 |

**接入计划**：
- V5 阶段引入，处理合法全文获取
- 遵守 AccessPolicy（open_access → allow_download, restricted → block_download）
- 零依赖优势：无需额外安装
