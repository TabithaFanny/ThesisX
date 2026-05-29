# ThesisX 最终产品决策基准

> 来源：用户提供的最终产品决策方向文档
> 用途：所有后续 Vision 实现必须服从此文档，不重新争论已决策事项
> 生效日期：2026-05-03

---

## 总决策

ThesisX 最终形态不是"论文生成器"，而是一个**本地优先、知识驱动、可追溯、可配置、多 Provider 的论文 AI 工作台**。

核心链路固定为：

```
研究问题 → 知识库 → 文献管理 → 理论匹配 → 证据包 → RAG 检索 → AI 写作 → Main Editor 编辑 → 引用与导出 → Run/版本历史追踪
```

所有技术决策都服从这条链路。MVP 可以分阶段，但最终架构不能按临时 demo 设计。

---

## Vision 3.0：Research Workspace

### 3.0-D1 Project 数据模型

**决策：采用 Project 容器 + ResearchQuestion/Direction/Goal 模型。**

```
Project（项目容器）
- id（UUID）
- name（项目名称）
- research_question（研究问题）
- discipline（学科领域）
- status（active/archived/completed）
- created_at
- updated_at

ResearchQuestion（研究问题）
- id（UUID）
- project_id（关联 Project）
- question（问题描述）
- keywords（关键词列表）
- discipline（学科领域）
- clarity_score（清晰度评分，4.1）
- created_at
- updated_at

ResearchDirection（研究方向）
- id（UUID）
- project_id（关联 Project）
- direction（方向描述）
- rationale（选择理由）
- status（exploring/selected/rejected）
- created_at

ResearchGoal（研究目标）
- id（UUID）
- project_id（关联 Project）
- goal（目标描述）
- milestone（里程碑）
- deadline（截止日期）
- status（pending/in_progress/completed）
- created_at
```

### 3.0-D2 项目绑定关系

**决策：ProjectKnowledgeLink 和 ProjectRunLink 实现多对多绑定。**

```
ProjectKnowledgeLink（项目-知识绑定）
- project_id
- knowledge_object_id
- role（background/core/method/theory/evidence/section_claim）
- priority
- project_note
- used_in_sections

ProjectRunLink（项目-Run绑定）
- project_id
- run_id
- created_at
```

### 3.0-D3 ResearchQuestion 影响链

**决策：ResearchQuestion 是 Theory Matcher 和 RAG 的输入来源。**

- ResearchQuestion.question → TheoryMatcher.match_research_question()
- ResearchQuestion.keywords → RAG 检索上下文
- ResearchQuestion.discipline → 影响理论推荐范围

---

## Vision 3.1：Knowledge Base

### 3.1-D1 四类对象字段定义

**决策：采用统一 KnowledgeObject 基类 + 专属对象扩展字段。**

```
KnowledgeObject（基类）
- id
- type
- title
- summary
- content
- tags
- source_type
- source_uri
- project_ids
- linked_object_ids
- sync_status（synced/pending/conflict/readonly）
- external_source（zotero/obsidian/manual）
- external_id
- external_uri
- external_updated_at
- external_hash
- verified_status（unverified/partially_verified/verified）
- usable_for_writing（bool）
- usable_for_rag（bool）
- ai_generated（bool）
- human_verified（bool）
- relevance_score
- confidence_score
- created_at
- updated_at
- version
- metadata

LiteratureItem（扩展）
- id
- title
- authors
- year
- venue
- doi
- isbn
- citation_key
- abstract
- keywords
- file_path
- zotero_key
- reading_status
- project_ids
- notes_count
- evidence_count

NoteItem（扩展）
- id
- title
- content
- summary
- source_path
- vault_name
- linked_literature_ids
- linked_theory_ids
- linked_evidence_ids
- tags
- project_ids
- note_type
- created_at
- updated_at

TheoryItem（扩展）
- id
- name
- discipline
- school
- core_concepts
- assumptions
- applicable_questions
- explanatory_mechanism
- boundary_conditions
- misuse_risks
- classic_literature_ids
- related_theory_ids
- writing_templates

EvidenceItem（扩展）
- id
- claim
- subclaim
- content
- evidence_type
- source_object_id
- source_location
- quote
- page
- reliability
- relevance_score
- counter_evidence
- gap_flag
- linked_paragraph_ids
- citation_status
```

**方向要求：** agent 后续实现时，所有知识资产都必须能被统一检索、统一绑定项目、统一追溯来源、统一参与 RAG。不要做四个互不相通的列表页。

### 3.1-D2 存储格式

**决策：SQLite 作为主库，FTS5 做全文检索，向量索引作为增强层，JSON / Markdown 只作为导入导出格式。**

不要选纯 JSON。最终产品一定会有筛选、标签、项目绑定、关系图、检索、引用、RAG、版本历史，JSON 很快会崩。

**最终结构：**
```
~/.wenbiao/
  thesisx.db
  knowledge/
    imports/
    exports/
    files/
    embeddings/
  runs/
  providers.json
```

**数据库层：**
- knowledge_objects
- literature_items
- note_items
- theory_items
- evidence_items
- projects
- project_knowledge_links
- object_relations
- tags
- citations
- embeddings
- import_jobs

**方向要求：** 最终架构必须以 SQLite 为中心。JSON 可以用于导入、导出、备份，但不能作为主数据源。

### 3.1-D3 知识库与项目绑定

**决策：全局知识库 + 项目级 Collection 引用绑定。**

不要"一项目一个独立知识库"，也不要完全混在一起。正确形态是：

```
Global Knowledge Base
  ├── Literature
  ├── Notes
  ├── Theories
  ├── Evidence
  └── Projects
       ├── Project A collection
       ├── Project B collection
       └── Project C collection
```

一篇文献、一个理论、一个笔记可以被多个项目复用。项目只保存绑定关系、使用状态、项目内标签、引用优先级。

**方向要求：** agent 后续不能把知识库做成"当前论文附属文件夹"。它必须是长期研究资产库。

### 3.1-D4 Markdown 导入规范

**决策：自由 Markdown 可导入，frontmatter 强推荐且优先解析。**

最终产品必须兼容 Obsidian，所以不能强制所有用户遵循一个死格式。策略是：

- 有 frontmatter → 精准解析
- 无 frontmatter → 自动推断
- 推断不确定 → 导入后让用户补全

**推荐 frontmatter：**
```yaml
---
type: note
title: 社区治理中的数字化转型
tags: [社区治理, 数字治理]
project: 社区治理论文
source: obsidian
linked_literature:
  - chen2022_governance
linked_theory:
  - collaborative_governance
---
```

**方向要求：** 导入系统必须宽进严出：允许用户自由导入，但进入 ThesisX 内部后要结构化。

---

## Vision 3.2：Literature Management

### 3.2-D1 citation key 格式

**决策：默认使用 authorYearShortTitle，支持 CSL/APA/GB/T/Chicago 导出格式，但 citation key 内部统一。**

内部 citation key 不等于导出格式。内部 key 应稳定、可读、可去重：

```
chen2022_digitalGovernance
ostrom1990_governingCommons
bourdieu1986_formsCapital
```

规则：第一作者姓氏 + 年份 + 标题关键词，冲突时加 a/b/c 或短 hash。

导出时再由 CSL 样式控制 APA、Chicago、GB/T 7714。

**方向要求：** 不要把 APA/Chicago 当成内部 citation key。内部 key 要稳定，外部格式要可切换。

### 3.2-D2 文献-项目绑定粒度

**决策：文献全局唯一，项目内可重复引用，项目保存引用状态和用途。**

一个 LiteratureItem 只存一份，但在不同项目里有不同使用状态：

```sql
project_literature_links
- project_id
- literature_id
- role: background / core / method / theory / evidence / contrast
- reading_status
- priority
- notes
- used_in_sections
```

**方向要求：** agent 不能为每个项目复制一份文献。必须全局唯一 + 项目关系表。

---

## Vision 3.3：Theory Matcher

### 3.3-D1 理论库初始规模

**决策：最终产品应内置 80-120 个跨学科理论；早期实现可以先内置 30 个高频理论，但数据结构按 120+ 设计。**

覆盖领域：社会学、社会工作、公共管理、教育学、心理学、传播学、组织研究、技术与社会、治理理论、政策过程。

**初始优先理论（30个）：** 社会支持理论、赋权理论、生态系统理论、优势视角、社会资本理论、场域理论、结构功能主义、符号互动论、理性选择理论、制度理论、新制度主义、协同治理理论、多中心治理理论、街头官僚理论、政策过程理论、议程设置理论、技术接受模型、创新扩散理论、活动理论、扎根理论方法论、生命历程理论、风险社会理论、社会建构论、依附理论、角色理论、污名理论、社会认同理论、计划行为理论、资源依赖理论、复杂适应系统理论。

**方向要求：** Theory Matcher 不是"理论名词库"，必须包含适用问题、核心机制、误用风险、经典文献、写作模板。

### 3.3-D2 理论匹配策略

**决策：规则检索 + 语义检索 + LLM 解释的混合策略。**

成熟方案：
1. 研究问题解析：抽取对象、场景、变量、机制、学科
2. 候选召回：BM25 + tags + discipline + embedding
3. 重排：适配度评分
4. LLM 解释：为什么适用、为什么不适用、如何写
5. 风险检查：误用理论提醒

**输出必须包括：**
- recommended_theories
- fit_score
- fit_reason
- boundary_warning
- classic_literature
- writing_frame
- misuse_risk

**方向要求：** 理论匹配必须可解释，不能只返回"推荐某理论"。

---

## Vision 3.4：Evidence Pack

### 3.4-D1 EvidenceItem 字段

**决策：EvidenceItem 必须服务于"论点—证据—来源—段落"的完整追溯链。**

最终字段：
```
id
project_id
claim_id
subclaim_id
content
quote
evidence_type
source_object_id
source_title
source_location
page
paragraph
reliability
relevance_score
support_strength
counter_evidence
gap_flag
gap_reason
linked_section_id
linked_paragraph_id
citation_key
citation_status
created_at
updated_at
```

**方向要求：** Evidence Pack 不是资料摘录页，而是论文论证系统。每条证据必须知道它支撑哪个论点、来自哪里、能不能引用、还缺什么。

### 3.4-D2 缺口分析方式

**决策：规则先做硬检查，AI 做解释判断，最终输出可操作缺口。**

**混合策略：**
- 规则检查：每个核心 claim 是否有 1-2 条证据、是否有 citation、source location、是否都是同一来源、是否缺少反方证据、是否缺少方法/数据支撑
- AI 判断：证据是否真的支撑 claim、支撑强度够不够、是否存在概念跳跃、是否需要补理论/案例/数据

**输出：**
```json
{
  "gap_type": "...",
  "severity": "...",
  "missing_evidence_type": "...",
  "suggested_search_query": "...",
  "suggested_literature_type": "...",
  "rewrite_advice": "..."
}
```

**方向要求：** 缺口分析不能只是红黄绿状态，要告诉用户"缺什么、去哪找、怎么补"。

---

## Vision 3.5：RAG

### 3.5-D1 Embedding 方案

**决策：混合检索架构：BM25 / FTS5 + Embedding + Metadata Filter + Rerank。**

最终产品必须混合：
1. 第一层：SQLite FTS5 / BM25，保证关键词、作者、理论名、标题精准命中
2. 第二层：Embedding，解决模糊概念、近义表达、跨语言语义
3. 第三层：Metadata Filter，按项目、类型、年份、标签、来源过滤
4. 第四层：Rerank，按研究问题和写作任务重排

**Embedding Provider：**
- 默认：远程 embedding API
- 可选：本地 embedding model
- 降级：无 embedding 时只用 FTS5/BM25

**方向要求：** agent 不要做"只有向量库"的 RAG。论文场景需要精确引用，必须保留关键词检索和元数据过滤。

### 3.5-D2 索引更新策略

**决策：增量更新为主，手动重建为兜底。**

机制：
- 对象新增/修改 → 标记 dirty
- 后台或手动触发 → 更新 FTS / embedding
- 索引失败 → 保留旧索引并记录错误
- 用户可点击"重建索引"

**数据表：**
- index_jobs
- embedding_chunks
- knowledge_object_index_status

**方向要求：** 最终产品必须可持续使用，不能每次改一条笔记就全库重建。

### 3.5-D3 RAG 结果注入方式

**决策：RAG 结果必须作为结构化 Context Bundle 注入，不要粗暴追加纯文本。**

**结构：**
```json
{
  "query": "...",
  "task_type": "theory_match / literature_review / evidence_support / writing",
  "results": [
    {
      "object_id": "...",
      "object_type": "literature",
      "title": "...",
      "snippet": "...",
      "source_location": "...",
      "citation_key": "...",
      "relevance_score": 0.87,
      "usage_instruction": "可作为理论背景"
    }
  ]
}
```

Agent 收到的不是一坨文本，而是分区：
- Relevant Literature
- Relevant Theories
- Evidence
- User Notes
- Citation Constraints
- Do-not-invent Sources

**方向要求：** 所有 AI 写作必须基于结构化证据包，禁止无来源胡编引用。

---

## Vision 3.6：Editor 闭环

### 3.6-D1 插入方式

**决策：两种模式都要：光标插入 + 大纲章节插入。**

最终编辑器要支持：
1. 插入到当前光标
2. 替换选中文本
3. 新建章节
4. 插入到指定大纲节点
5. 作为批注/建议插入

**方向要求：** 不要只做"覆盖 paper.md"。AI 输出必须能结构化进入 Main Editor。

### 3.6-D2 局部改写配置

**决策：内置任务模板 + 用户自定义模板。**

**内置：** 学术润色、降 AI 痕迹、逻辑压缩、扩写论证、补理论连接、补证据连接、改成 C 刊风格、改成答辩口播

**用户自定义字段：**
```yaml
name
description
prompt_template
input_scope
output_format
risk_warning
```

**方向要求：** 最终产品必须支持用户保存自己的写作习惯，不能只有固定 prompt。

### 3.6-D3 回滚机制

**决策：编辑器 Undo 栈 + AI 操作版本快照双机制。**

普通输入走 Undo。AI 改写必须自动生成快照：
```
before_text
after_text
operation_type
prompt
used_context
timestamp
linked_run_id
```

用户可以：撤销本次 AI 操作、查看 diff、恢复到改写前、保存为版本。

**方向要求：** AI 写作必须可回滚，否则用户不敢用。

---

## Vision 3.7：Zotero / Obsidian

### 3.7-D1 Zotero API Key 配置

**决策：支持 API Key + 环境变量；OAuth 作为后续增强。密钥不明文写入项目数据。**

**优先级：**
1. 环境变量
2. 系统 Keychain / 安全存储
3. 用户配置引用
4. 手动临时输入

**同步字段：** zotero_key、library_id、collection_key、title、authors、year、abstract、tags、attachments、notes

**方向要求：** Zotero 先做安全只读同步，后续可选写回 note，但不能默认写回。

### 3.7-D2 Obsidian 同步策略

**决策：手动同步 + 文件变化检测提示，不做默认自动频繁同步。**

策略：
- 用户选择 vault
- 手动点击同步
- 系统扫描 md 文件
- 识别 frontmatter / 双链 / 标签
- 显示变更预览
- 用户确认导入

**方向要求：** Obsidian 连接器必须尊重用户原始 vault，不擅自写回。

### 3.7-D3 写回边界

**决策：默认只读；写回必须显式开启、逐项确认、永不覆盖原文。**

**允许写回：** ThesisX 生成的摘要 note、文献阅读笔记、理论匹配结果 note、证据包索引 note

**禁止默认写回：** 修改用户原始笔记正文、删除用户文件、覆盖 frontmatter、改 Zotero 原始元数据

**方向要求：** 所有连接器必须本地安全优先，默认只读。

---

## Vision 3.8：Skill Library UI

### 3.8-D1 Skill 配置存储

**决策：Skill 定义用 YAML 文件，启用状态和绑定关系存 SQLite/config。**

**Skill 包结构：**
```
~/.wenbiao/skills/
  academic_polish/
    skill.yaml
    prompt.md
    examples.md
```

**skill.yaml：**
```yaml
id: academic_polish
name: 学术润色
version: 1.0.0
category: writing
description: 提升论文表达的学术性
input_schema: [text, target_style]
output_schema: [revised_text, change_summary]
risk_level: medium
```

**启用状态表：** skill_bindings - skill_id, project_id, task_type, enabled

**方向要求：** Skill 文件要可移植，绑定关系要结构化管理。

### 3.8-D2 敏感信息处理

**决策：Skill prompt 中禁止写 key；系统检测到疑似密钥必须拦截或强警告。**

规则：
- 禁止在 skill.yaml / prompt.md 中保存 API key
- 检测 sk- / api_key / token / secret 等模式
- 导入时给 warning
- 高置信度密钥直接阻止启用

**方向要求：** Skill 是执行能力，必须有安全边界。不能让用户不小心把 key 写进 prompt。

---

## Vision 3.9：导出与交付

### 3.9-D1 docx 格式模板

**决策：支持通用模板 + 学校/期刊可配置模板。**

最终导出系统：
- Default Academic Template
- University Thesis Template
- Journal Article Template
- Custom Template

**模板字段：** title_page、heading_styles、font、line_spacing、citation_style、reference_style、page_number、table_style、figure_caption_style

**方向要求：** 不要只做一个 docx。论文产品最终必须支持模板化导出。

### 3.9-D2 隐私说明内容

**决策：内置清晰隐私说明，按 Provider 和任务级别显示"会发送什么"。**

隐私说明必须写清：
- 哪些数据只保存在本地
- 哪些数据会发送到远程模型
- 什么时候发送、发送给哪个 Provider
- 是否包含文献内容、用户笔记、API key
- 如何关闭 Real 模式
- 如何删除本地 runs
- 如何导出/清理知识库

**每次 Real 任务前显示摘要：**
```
本次将发送：
- 研究问题
- 选中的知识片段
- 任务 prompt
不会发送：
- 未选中的本地文件
- API key
- 整个 Obsidian vault
```

**方向要求：** 隐私说明不是法律作文，而是用户每次使用 AI 前能看懂的数据边界。

---

## 给 agent 的最终推进准则

所有实现必须服从以下最终产品决策：

1. ThesisX 是本地优先的论文 AI 工作台，不是单次论文生成器。
2. 主链路固定为：研究问题 → 知识库 → 文献管理 → 理论匹配 → 证据包 → RAG → AI 写作 → Editor → 导出 → 历史。
3. Knowledge Base 使用 SQLite 主库，JSON/Markdown 只做导入导出。
4. 知识对象全局唯一，项目通过 Collection/Link 绑定，不复制数据。
5. Literature / Note / Theory / Evidence 必须统一建模、统一来源追溯、统一项目绑定。
6. Theory Matcher 必须可解释，输出适配理由、边界和误用风险。
7. Evidence Pack 必须绑定 claim、source、location、citation 和 paragraph。
8. RAG 必须是混合检索：FTS/BM25 + embedding + metadata filter + rerank。
9. AI 写作必须基于结构化 Context Bundle，不允许无来源胡编引用。
10. Main Editor 必须支持结构化插入、局部改写、diff 和回滚。
11. Zotero / Obsidian 默认只读，写回必须显式确认。
12. Skill 使用文件包定义，启用状态和任务绑定结构化存储。
13. Provider / API key / 本地 CLI 配置必须安全、可诊断、可切换。
14. 导出必须支持模板化 docx / markdown / diagnostic report。
15. 所有未完成能力必须保持 preview，不允许假装已接通。

---

*本文档为所有后续 agent 执行的基准，不在此文档范围内的决策才需要重新讨论。*