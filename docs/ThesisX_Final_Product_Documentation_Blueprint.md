# ThesisX 最终产品全量文档体系与开发蓝图

> 版本：v1.0  
> 定位：给接管 ThesisX 的 agent / Claude Code / Codex / 开发者使用  
> 目标：让 agent 在不继续误判项目边界、不把局部 Runtime 跑通误判为产品完成的前提下，按最终产品视角建立完整可发布项目的文档体系、技术路线、接口结构、页面映射与执行规则。  
> 注意：本文档不是“立刻就能无脑生成完整产品”的魔法提示词。它是一份**可开发、可拆解、可验收、可交接**的产品与技术总蓝图。agent 拿到后可以立即开始按 Vision 分阶段开发，但仍必须每个阶段 review、测试、汇报、验收。

---

# 0. 自我 Review 结论

## 0.1 这份文档能解决什么

这份文档可以解决：

1. agent 不知道 ThesisX 最终产品到底是什么；
2. agent 把 Runtime 最小闭环误判成“产品可用”；
3. agent 在 UI / SVG / Runtime / Knowledge Base / RAG / Provider 之间来回摇摆；
4. agent 不知道下一步该写文档、写接口、写数据模型，还是写功能代码；
5. agent 不知道哪些功能是真实功能，哪些只是 preview；
6. agent 不知道每个模块该用什么技术；
7. agent 不知道每个页面对应哪个接口、哪个数据对象、哪个服务层；
8. agent 不知道如何拆分 Vision；
9. agent 不知道什么情况下必须停下来等用户确认；
10. agent 不知道如何判断“最终可发布”。

## 0.2 这份文档不能保证什么

这份文档不能保证：

1. agent 一次执行就能写出完整最终产品；
2. 所有技术细节都不需要再根据现有代码调整；
3. 外部 Agent Team、Zotero、Obsidian、Embedding Provider、真实 API 的兼容问题会自动消失；
4. 现有代码不会存在隐藏 bug；
5. 真实发布不需要人工验收。

## 0.3 agent 拿到之后能不能立即开发

可以，但必须按以下方式开发：

```text
先生成文档体系
→ 再建立数据模型
→ 再实现 Knowledge Base
→ 再接 Literature / Theory / Evidence
→ 再做 RAG
→ 再闭环 Editor
→ 再做 Connectors / Skill / Export
→ 最后做 Beta 验收
```

不能直接跳到“完整产品一口气实现”。

## 0.4 是否足够穷尽

本文档覆盖：

- 产品蓝图
- PRD 文档体系
- 技术架构
- 数据模型
- 接口文档
- 前端页面与接口对应关系
- 用户手册
- Agent 执行规则
- Vision Roadmap
- 每个模块的技术路线
- 每个模块的验收标准
- 禁止项
- 发布标准

但真正实现时，每个 Vision 仍需要继续生成更细的子 PRD、测试用例和代码任务清单。

---

# 1. ThesisX 最终产品定义

## 1.1 产品一句话

ThesisX 是一个**本地优先、知识驱动、可追溯、可配置、多 Provider 的论文 AI 工作台**，帮助用户从模糊研究问题出发，完成知识库搭建、文献管理、理论匹配、证据组织、AI 写作、人工编辑、引用导出与历史追踪。

## 1.2 ThesisX 不是

ThesisX 不是：

1. 单次论文生成器；
2. 一个只输入题目就吐出论文的玩具；
3. 一个纯聊天机器人；
4. 一个 Zotero 替代品；
5. 一个 Obsidian 替代品；
6. 一个论文代写器；
7. 一个只有 UI 壳的 demo；
8. 一个只跑通 Runtime 就算完成的项目；
9. 一个所有功能都强依赖云端的 SaaS；
10. 一个不留痕、不追溯、不解释来源的黑箱 AI 工具。

## 1.3 ThesisX 是

ThesisX 是：

1. 本地研究资产管理器；
2. 文献与笔记整理器；
3. 理论匹配器；
4. 证据包构建器；
5. RAG 驱动的 AI 写作引擎；
6. 可编辑论文工作台；
7. Runtime Session 记录系统；
8. Provider 配置与诊断系统；
9. 可导出的学术写作交付工具；
10. 可扩展 Skill / Connector / Agent 平台。

---

# 2. 最终核心主链路

所有功能必须服务于这一条链路：

```text
研究问题
→ 项目空间
→ 知识库
→ 文献管理
→ 理论匹配
→ 证据包
→ RAG 检索
→ AI 写作
→ Main Editor 编辑
→ 引用管理
→ 导出
→ Run / Version / Diagnostics 历史追踪
```

任何不服务这条链路的功能，除非明确标记为未来计划，否则不进入主线。

---

# 3. 最终可发布版本标准

ThesisX 真正达到“最终可用 Beta / 可发布版本”，至少要满足以下标准。

## 3.1 桌面端

1. 用户可以稳定打开桌面端；
2. Main Editor 可以正常编辑；
3. 工具栏、预览、大纲、导出入口不崩；
4. 未完成页面清晰标记 preview；
5. UI 不再追求 SVG 像素级精修，但要一致、可读、可用。

## 3.2 项目与知识库

1. 用户可以创建论文项目；
2. 用户可以输入研究问题；
3. 用户可以导入文献、Markdown、笔记；
4. 用户可以建立项目知识库；
5. 知识对象可搜索、可筛选、可绑定项目；
6. Literature / Note / Theory / Evidence 四类对象结构化保存；
7. 数据存入 SQLite，而不是散乱 JSON。

## 3.3 文献管理

1. 文献可导入；
2. 文献有作者、年份、标题、来源、DOI、citation key；
3. 文献可绑定项目；
4. 文献可产生笔记和证据；
5. 支持 BibTeX / RIS / CSL JSON 基础导入导出；
6. Zotero 连接器可作为后续增强，但最终应支持。

## 3.4 理论匹配

1. 用户输入研究问题；
2. 系统能解析研究对象、变量、场景、机制；
3. 系统能推荐理论；
4. 推荐结果有适配理由；
5. 推荐结果有误用风险；
6. 推荐结果可写入项目知识库；
7. 推荐结果可转成写作框架。

## 3.5 证据包

1. 用户可以创建论点；
2. 用户可以绑定证据；
3. 证据知道来源；
4. 证据知道支撑哪个论点；
5. 证据能记录页码、位置、引用状态；
6. 系统能提示证据缺口；
7. 证据能被 RAG 和写作链路调用。

## 3.6 RAG

1. 支持关键词检索；
2. 支持 FTS5 / BM25；
3. 支持 embedding 检索；
4. 支持 metadata filter；
5. 支持 Context Bundle；
6. Agent 写作时能收到结构化上下文；
7. AI 不得无来源胡编引用；
8. 检索结果可被用户预览。

## 3.7 AI 写作

1. Mock 模式稳定可演示；
2. Real 模式配置完整时可跑；
3. 配置不完整时清楚失败；
4. 任务过程有 state / token / message / cost / error / completion；
5. 结果写入 run session；
6. 结果可以插入 Main Editor；
7. 局部改写可回滚；
8. 每次 AI 操作有快照。

## 3.8 Provider

1. 支持 Local CLI Provider；
2. 支持 Remote API Provider；
3. 支持 Agent Team Provider；
4. 自动发现本地 CLI；
5. 检查 API key 来源；
6. 检查 base_url；
7. 检查 model；
8. 检查 Agent Team 契约；
9. 输出健康报告；
10. 不把 dry-run 伪装成 Real。

## 3.9 Run / History / Diagnostics

1. 每次任务有 session_id；
2. 每次任务写入 request.json；
3. 每次任务写入 metadata.json；
4. 每次任务写入 events.jsonl；
5. 每次任务写入 messages.jsonl；
6. 每次任务写入 paper.md；
7. 每次任务可以诊断；
8. 用户能查看历史；
9. 用户能导出诊断报告；
10. 旧 output/ 兼容，但新 runs/ 是主目录。

## 3.10 导出

1. 支持 Markdown 导出；
2. 支持 DOCX 导出；
3. 支持引用导出；
4. 支持证据包报告；
5. 支持 Run Archive；
6. 支持诊断报告；
7. 支持模板化格式。

## 3.11 安全与隐私

1. 默认本地优先；
2. Zotero / Obsidian 默认只读；
3. API key 不写入普通项目文件；
4. Skill prompt 禁止保存 key；
5. 每次 Real 任务说明会发送什么；
6. 用户可以删除本地 run；
7. 用户可以关闭 Real 模式。

## 3.12 测试与发布

1. 全量测试通过；
2. Mock E2E 通过；
3. Real 最小验证通过；
4. Knowledge Base 测试通过；
5. RAG 测试通过；
6. 导出测试通过；
7. Provider 检测测试通过；
8. 用户手册完整；
9. 隐私说明完整；
10. 版本报告完整。

---

# 4. 文档体系总目录

agent 应该在 `docs/` 下建立以下文档体系。

```text
docs/
  00_PRODUCT/
    PRODUCT_BLUEPRINT.md
    PRODUCT_ROADMAP.md
    INFORMATION_ARCHITECTURE.md
    FINAL_BETA_ACCEPTANCE.md

  01_PRD/
    PRD_OVERVIEW.md
    PRD_KNOWLEDGE_BASE.md
    PRD_LITERATURE_MANAGEMENT.md
    PRD_THEORY_MATCHER.md
    PRD_EVIDENCE_PACK.md
    PRD_RAG.md
    PRD_EDITOR_LOOP.md
    PRD_PROVIDER_SETTINGS.md
    PRD_RUN_HISTORY_DIAGNOSTICS.md
    PRD_SKILL_LIBRARY.md
    PRD_CONNECTORS.md
    PRD_EXPORT_DELIVERY.md

  02_TECHNICAL/
    TECHNICAL_ARCHITECTURE.md
    DATA_MODEL.md
    DATABASE_SCHEMA.md
    RAG_ARCHITECTURE.md
    AGENT_RUNTIME_ARCHITECTURE.md
    PROVIDER_ARCHITECTURE.md
    SECURITY_PRIVACY_ARCHITECTURE.md
    TESTING_STRATEGY.md
    MIGRATION_STRATEGY.md

  03_API/
    API_KNOWLEDGE_STORE.md
    API_LITERATURE.md
    API_THEORY_MATCHER.md
    API_EVIDENCE_PACK.md
    API_RAG.md
    API_EDITOR.md
    API_PROVIDER.md
    API_RUN_HISTORY.md
    API_SKILL.md
    API_EXPORT.md
    API_CONNECTORS.md

  04_FRONTEND/
    FRONTEND_BLUEPRINT.md
    FRONTEND_INTERFACE_MAPPING.md
    UI_STATE_SPEC.md
    PAGE_WORKSPACE_HOME.md
    PAGE_MAIN_EDITOR.md
    PAGE_AI_DRAFT_ASSISTANT.md
    PAGE_KNOWLEDGE_BASE.md
    PAGE_LITERATURE.md
    PAGE_THEORY_MATCHER.md
    PAGE_EVIDENCE_PACK.md
    PAGE_RAG_SEARCH.md
    PAGE_RUN_HISTORY.md
    PAGE_RUNTIME_DIAGNOSTICS.md
    PAGE_PROVIDER_SETTINGS.md
    PAGE_SKILL_LIBRARY.md
    PAGE_EXPORT_CENTER.md
    PAGE_CONNECTORS.md

  05_USER_GUIDES/
    USER_GUIDE.md
    QUICK_START.md
    PRIVACY_GUIDE.md
    PROVIDER_SETUP_GUIDE.md
    CONNECTOR_GUIDE.md
    EXPORT_GUIDE.md
    TROUBLESHOOTING.md

  06_AGENT/
    AGENT_HANDOFF.md
    AGENT_EXECUTION_RULES.md
    AGENT_VISION_ROADMAP.md
    AGENT_REVIEW_CHECKLIST.md
    AGENT_PROMPT_LIBRARY.md
    AGENT_STOP_CONDITIONS.md

  07_REPORTS/
    RUNTIME_CLOSED_LOOP_REPORT.md
    KNOWLEDGE_BASE_REPORT.md
    RAG_REPORT.md
    FINAL_BETA_REPORT.md
```

---

# 5. 产品 PRD 总览

## 5.1 用户角色

### 5.1.1 学生用户

典型需求：毕业论文、课程论文、开题报告、文献综述、答辩准备。

核心痛点：不知道选题怎么展开；不知道理论怎么选；文献看了但不会组织；AI 写作容易空泛；不会形成证据链。

### 5.1.2 研究者

典型需求：管理长期文献；组织研究问题；形成理论框架；维护研究笔记；多项目复用知识资产。

### 5.1.3 教师 / 指导者

典型需求：看学生论文逻辑；检查理论适配；检查证据是否支撑论点；输出修改意见。

### 5.1.4 AI 工具重度用户

典型需求：切换不同模型；本地 CLI / Remote API 混用；保存 run 历史；自定义 Skill；复用 Prompt 模板。

---

## 5.2 核心场景

### 场景 A：从模糊研究问题开始

用户输入：

```text
我想研究社区老年人在数字治理中的参与困境。
```

系统应该：解析研究对象、解析场景、解析问题、推荐理论、推荐文献搜索词、创建初始 Knowledge Base、生成大纲、提示需要哪些证据。

### 场景 B：从已有文献开始

用户导入 20 篇文献。系统应该解析元数据、生成 citation key、自动聚类主题、建议文献综述结构、推荐理论、标记证据片段、支持生成综述段落。

### 场景 C：从 Obsidian 笔记开始

用户选择 vault。系统应该扫描 Markdown、解析 frontmatter、解析双链、识别理论/文献/案例、导入 NoteItem、绑定项目，并且不写回原文，除非用户确认。

### 场景 D：AI 生成论文初稿

用户配置 Provider，选择项目，点击生成。系统应该检查 Provider、构建 Context Bundle、启动 AgentTeamRunner、流式记录 events、输出 paper.md、插入 Main Editor、写 run history、失败时输出 diagnostics。

### 场景 E：局部改写

用户选中一段文字，点击“补理论”。系统应该识别选区、查找相关理论、查找相关证据、生成改写建议、展示 diff、用户确认插入、保存 AI 操作快照、可回滚。

---

# 6. 信息架构

## 6.1 一级导航

```text
Workspace
Editor
AI Assistant
Knowledge
Runtime
Tools
Settings
```

## 6.2 二级页面

```text
Workspace
  - Workspace Home

Editor
  - Main Editor
  - Version History
  - Export Center

AI Assistant
  - AI Draft Assistant
  - AI Chat
  - RAG Search

Knowledge
  - Knowledge Base
  - Literature Management
  - Theory Matcher
  - Evidence Pack
  - Data & Charts

Runtime
  - Run History
  - Runtime Diagnostics
  - Provider Settings

Tools
  - Skill Library
  - Zotero Connector
  - Obsidian Connector
  - Local File Import

Settings
  - General Settings
  - Privacy Settings
  - Provider Settings
  - Storage Settings
```

---

# 7. 前端页面蓝图与接口映射

## 7.1 Workspace Home

页面目标：展示项目概览、最近 run、知识库状态、Provider 健康、待完成任务。

页面模块：项目标题、当前研究问题、Provider 状态、Mock/Real 状态、项目进度、知识库数量、文献数量、理论匹配状态、证据包完整度、最近 Run、最近编辑、当前论文大纲、AI 建议、Provider Health、Runtime Diagnostics、下一步建议。

接口：

```python
ProjectService.get_current_project()
KnowledgeStore.get_project_summary(project_id)
RunHistoryReader.list_runs(limit=5)
ProviderService.generate_provider_health_report()
EvidencePackService.get_gap_summary(project_id)
```

状态：真实功能包括项目摘要、RunHistory、Provider 健康；未接真实模块显示 V3/V4 preview。

## 7.2 Main Editor

页面目标：用户主写作空间，支持编辑、预览、AI 插入、局部改写、版本快照。

页面模块：文档大纲、章节树、字数统计、WYSIWYG 编辑器、Markdown / rich text 内容、光标插入、选区操作、AI 操作面板、知识片段、证据建议、理论建议、局部改写结果。

接口：

```python
EditorOperationService.insert_content()
EditorOperationService.rewrite_selection()
EditorOperationService.create_snapshot()
EditorOperationService.rollback()
RagService.build_context_bundle()
TheoryMatcher.match_theories()
EvidencePackService.get_evidence_for_section()
```

技术：PyQt6 QTextEdit / QTextDocument、Markdown AST、OperationPatch、Undo stack、Diff engine、Run linkage。

关键规则：Main Editor 是真实功能，不能破坏；AI 生成结果不能只是写 paper.md，必须能结构化插入；每次 AI 改写必须可回滚。

## 7.3 AI Draft Assistant

页面目标：发起论文初稿生成任务。

页面模块：输入研究问题、选择 Knowledge / Literature / Theory / Evidence、选择 Provider / Mock / Real、运行任务、查看结果 / 插入编辑器 / 查看 diagnostics。

接口：

```python
AgentTeamRunner.run(request)
ProviderService.health_check()
RagService.build_context_bundle()
SessionStore.create_session()
RunDiagnostics.diagnose_run()
```

技术：PyQt QDialog、Worker Thread、PaperRequest、PaperEvent stream、SessionStore。

## 7.4 Knowledge Base

页面目标：统一管理 Literature / Note / Theory / Evidence。

页面模块：类型筛选、项目筛选、标签筛选、知识对象列表、搜索框、批量操作、对象详情、来源、关系、项目绑定、RAG 可用状态。

接口：

```python
KnowledgeStore.search()
KnowledgeStore.create_object()
KnowledgeStore.update_object()
KnowledgeStore.link_to_project()
KnowledgeStore.get_object_relations()
```

技术：SQLite、FTS5、Markdown parser、Tag system、Object relation graph。

## 7.5 Literature Management

页面目标：管理文献、引用、阅读状态、项目用途。

页面模块：Collection、项目、标签、阅读状态、文献表格、作者、年份、标题、来源、citation key、状态、文献详情、abstract、notes、evidence、citation preview。

接口：

```python
LiteratureService.add_literature()
LiteratureService.import_bibtex()
LiteratureService.import_ris()
LiteratureService.generate_citation_key()
LiteratureService.link_to_project()
```

## 7.6 Theory Matcher

页面目标：根据研究问题推荐理论框架。

页面模块：研究问题输入、学科选择、匹配按钮、推荐理论卡片、fit score、适用理由、误用风险、理论详情、核心概念、经典文献、写作模板、插入大纲。

接口：

```python
TheoryMatcher.parse_research_question()
TheoryMatcher.recall_theories()
TheoryMatcher.rank_theories()
TheoryMatcher.explain_match()
```

## 7.7 Evidence Pack

页面目标：组织论点与证据。

页面模块：Claims、Subclaims、Evidence 列表、证据强度、来源、引用状态、Gap Analysis、缺口类型、建议补充、推荐搜索词。

接口：

```python
EvidencePackService.create_claim()
EvidencePackService.create_evidence()
EvidencePackService.link_evidence()
EvidencePackService.analyze_gaps()
```

## 7.8 RAG Search

页面目标：让用户看到 AI 写作将使用哪些知识。

页面模块：搜索输入、过滤器、结果列表、来源、相关性、引用状态、加入 Context Bundle。

接口：

```python
RagService.search()
RagService.build_context_bundle()
```

## 7.9 Run History

页面目标：查看历史 AI 任务。

页面模块：Run 列表、paper.md 预览、metadata、output files、diagnostics、events、messages。

接口：

```python
RunHistoryReader.list_runs()
RunHistoryReader.get_run()
RunDiagnostics.diagnose_run()
```

## 7.10 Runtime Diagnostics

页面目标：诊断当前 Runtime 状态。

页面模块：Provider Health、Agent Team Contract、Session Health、Missing Files、Errors、Recommended Actions。

接口：

```python
RunDiagnostics.diagnose_latest()
ProviderService.generate_provider_health_report()
AgentTeamCompatAdapter.validate_agent_team_contract()
```

## 7.11 Provider Settings

页面目标：配置 Local CLI、Remote API、Agent Team。

页面模块：codex、claude、openclaw、hermes、opencode、OpenAI、DeepSeek、OpenRouter、Localhost、candidate paths、contract type、supported mode。

接口：

```python
discover_local_clis()
detect_remote_api_config()
detect_agent_team_paths()
save_providers()
load_providers()
```

## 7.12 Skill Library

页面目标：管理本地 Skill 包。

页面模块：skill 分类、skill 卡片、状态、风险、task binding、prompt、input schema、output schema、enabled projects。

接口：

```python
SkillLoader.scan_skills()
SkillLoader.validate_skill()
SkillLoader.enable_skill()
SkillLoader.build_skill_context()
```

## 7.13 Export Center

页面目标：导出论文与相关资产。

页面模块：DOCX、Markdown、BibTeX、RIS、Evidence Pack Report、Run Archive、Diagnostics Report。

接口：

```python
ExportService.export_docx()
ExportService.export_markdown()
ExportService.export_bibtex()
ExportService.export_session_archive()
```

---

# 8. 数据模型

## 8.1 SQLite 主库

最终主库：

```text
~/.wenbiao/thesisx.db
```

主要表：

```text
projects
knowledge_objects
literature_items
note_items
theory_items
evidence_items
claims
claim_evidence_links
project_knowledge_links
object_relations
tags
object_tags
citations
embedding_chunks
index_jobs
skills
skill_bindings
provider_profiles
import_jobs
export_jobs
editor_snapshots
```

## 8.2 projects

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  research_question TEXT,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);
```

## 8.3 knowledge_objects

```sql
CREATE TABLE knowledge_objects (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT,
  content TEXT,
  source_type TEXT,
  source_uri TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);
```

## 8.4 literature_items

```sql
CREATE TABLE literature_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  title TEXT NOT NULL,
  authors_json TEXT,
  year INTEGER,
  venue TEXT,
  doi TEXT,
  isbn TEXT,
  citation_key TEXT UNIQUE,
  abstract TEXT,
  keywords_json TEXT,
  file_path TEXT,
  zotero_key TEXT,
  reading_status TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(object_id) REFERENCES knowledge_objects(id)
);
```

## 8.5 note_items

```sql
CREATE TABLE note_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  source_path TEXT,
  vault_name TEXT,
  note_type TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(object_id) REFERENCES knowledge_objects(id)
);
```

## 8.6 theory_items

```sql
CREATE TABLE theory_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  name TEXT NOT NULL,
  discipline TEXT,
  school TEXT,
  core_concepts_json TEXT,
  assumptions TEXT,
  applicable_questions_json TEXT,
  explanatory_mechanism TEXT,
  boundary_conditions TEXT,
  misuse_risks TEXT,
  writing_templates_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(object_id) REFERENCES knowledge_objects(id)
);
```

## 8.7 evidence_items

```sql
CREATE TABLE evidence_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  project_id TEXT,
  claim_id TEXT,
  content TEXT NOT NULL,
  quote TEXT,
  evidence_type TEXT,
  source_object_id TEXT,
  source_title TEXT,
  source_location TEXT,
  page TEXT,
  reliability INTEGER,
  relevance_score REAL,
  support_strength TEXT,
  counter_evidence INTEGER DEFAULT 0,
  gap_flag INTEGER DEFAULT 0,
  gap_reason TEXT,
  citation_key TEXT,
  citation_status TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(object_id) REFERENCES knowledge_objects(id)
);
```

---

# 9. RAG 架构

## 9.1 检索策略

最终必须是混合检索：FTS5 / BM25 + Embedding + Metadata Filter + Rerank + Context Bundle。

## 9.2 Chunk 策略

```text
Literature abstract：整体 chunk
Literature full text：按 section / paragraph chunk
Note：按 heading chunk
Theory：按 theory concept chunk
Evidence：单条 evidence chunk
```

## 9.3 Context Bundle

```json
{
  "project_id": "project_001",
  "task_type": "draft_section",
  "query": "社区数字治理中的老年人参与困境",
  "literature": [],
  "theories": [],
  "evidence": [],
  "notes": [],
  "citation_constraints": [],
  "forbidden_claims": []
}
```

## 9.4 注入原则

Agent 不能收到一坨无结构文本，而要收到：Relevant Literature、Relevant Theories、Evidence、User Notes、Citation Constraints、Do Not Invent Sources。

---

# 10. Agent Runtime 架构

## 10.1 现有结构

```text
AgentTeamDialog
→ AgentTeamWorker
→ AgentTeamRunner
→ AgentTeamCompatAdapter
→ Provider / External Agent Team
→ PaperEvent
→ SessionStore
→ RunHistoryReader
→ RunDiagnostics
```

## 10.2 最终结构

```text
PaperRequest
  + ProjectContext
  + KnowledgeContext
  + RAGContextBundle
  + SkillContext
  + ProviderProfile
→ RuntimePlan
→ AgentTeamRunner
→ EventStream
→ SessionStore
→ EditorOperation
```

## 10.3 PaperEvent

```text
state
token
message
cost
artifact
error
completion
```

## 10.4 Run 目录

```text
~/.wenbiao/runs/<session_id>/
  request.json
  metadata.json
  context/
    paper_request.md
    runtime_instructions.md
    user_constraints.md
    selected_skills.md
    context_bundle.json
  logs/
    events.jsonl
    messages.jsonl
    errors.log
  output/
    outline.json
    paper.md
    quality_report.json
  artifacts/
    imported_files/
    generated/
```

---

# 11. Provider 架构

## 11.1 Provider 类型

```text
LocalCLIProvider
RemoteAPIProvider
AgentTeamProvider
```

## 11.2 Local CLI

需要发现：codex、claude、openclaw、hermes、opencode。

技术：

```python
shutil.which("codex")
subprocess.run([path, "--version"])
```

## 11.3 Remote API

支持：OpenAI、DeepSeek、OpenRouter、Localhost、Custom。

配置示例：

```json
{
  "provider_id": "deepseek",
  "base_url": "https://api.deepseek.com/v1",
  "model": "deepseek-chat",
  "api_key_source": "env:DEEPSEEK_API_KEY"
}
```

## 11.4 Agent Team

检测：tui_runner、pipeline_v2、pipeline_function、unsupported。

---

# 12. Skill 系统

## 12.1 Skill 包结构

```text
~/.wenbiao/skills/<skill_id>/
  skill.yaml
  prompt.md
  examples.md
  README.md
```

## 12.2 skill.yaml

```yaml
id: academic_polish
name: 学术润色
version: 1.0.0
category: writing
description: 提升论文表达的学术性
input_schema:
  - text
  - target_style
output_schema:
  - revised_text
  - change_summary
risk_level: medium
```

## 12.3 安全规则

1. Skill 中不能写 API key；
2. 导入时扫描 `sk-`、`api_key`、`secret`、`token`；
3. 高置信密钥阻止启用；
4. 中置信密钥 warning；
5. Skill 执行必须写入 run context。

---

# 13. Zotero / Obsidian Connector

## 13.1 Zotero

默认只读。

读取：library、collections、items、tags、notes、attachments metadata。

不默认写回。

## 13.2 Obsidian

默认只读。

读取：Markdown files、frontmatter、wiki links、tags、headings、backlinks。

不默认写回原文件。

## 13.3 写回边界

允许写回：ThesisX 生成的新 note、理论匹配结果 note、证据包索引 note。

禁止默认写回：原始笔记正文、Zotero 原始元数据、删除文件、覆盖 frontmatter。

---

# 14. Export 架构

## 14.1 导出类型

```text
DOCX
Markdown
BibTeX
RIS
CSL JSON
Evidence Pack Report
Runtime Diagnostics Report
Session Archive ZIP
```

## 14.2 DOCX 模板

```text
Default Academic Template
University Thesis Template
Journal Article Template
Custom Template
```

技术：python-docx、style templates、citation style processor。

---

# 15. 用户手册结构

## 15.1 USER_GUIDE.md

章节：ThesisX 是什么、第一次启动、创建论文项目、使用 Main Editor、使用 AI 初稿助手、搭建知识库、导入文献、导入 Obsidian、匹配理论、创建证据包、使用 RAG 写作、局部改写、查看历史、配置 Provider、导出论文、常见问题。

## 15.2 QUICK_START.md

```text
5 分钟快速开始：
1. 新建项目
2. 输入研究问题
3. 导入 3 篇文献
4. 添加一个理论
5. 生成大纲
6. 插入编辑器
7. 导出 markdown/docx
```

## 15.3 PRIVACY_GUIDE.md

必须说明：哪些数据只保存在本地、哪些数据发送远程模型、API key 如何保存、如何关闭 Real 模式、如何删除 runs、如何清理知识库、Zotero / Obsidian 是否写回。

---

# 16. Agent 执行规则

## 16.1 全局规则

```text
1. 不要继续 SVG 精修。
2. 不要把 Runtime 跑通说成产品完成。
3. 不要破坏 Main Editor。
4. 不要破坏 AgentTeamDialog。
5. 不要删除 Mock 分支。
6. 不要删除旧 output/。
7. 不要修改外部 Agent Team 仓库。
8. 不要发真实 API，除非用户明确确认。
9. 不要把 dry-run 说成 Real。
10. 每个 Vision 完成后必须跑测试。
```

## 16.2 每轮执行流程

```text
1. 读取最新文档和代码
2. git status
3. git diff --stat
4. 运行相关测试
5. 输出本轮计划
6. 执行
7. 定向测试
8. 全量测试
9. 输出报告
10. 判断是否进入下一 Vision
```

## 16.3 停止条件

必须停止并汇报：测试失败、需要真实 API、需要删除数据、需要修改外部仓库、需要大改 Main Editor、需要大改 AgentTeamDialog、需要写回 Zotero/Obsidian、需要引入新重依赖。

---

# 17. Vision Roadmap

## Vision 3.1 Knowledge Base

目标：实现 SQLite 主库、KnowledgeObject、LiteratureItem、NoteItem、TheoryItem、EvidenceItem 基础 CRUD。

任务：创建数据库层、创建 schema、创建 KnowledgeStore、创建四类对象模型、创建导入接口、创建搜索接口、创建基础 UI、测试。

验收：能创建项目、能创建知识对象、能搜索、能绑定项目、能持久化。

## Vision 3.2 Literature Management

目标：实现文献管理与 citation key。

任务：LiteratureService、BibTeX import、RIS import、citation key、project binding、literature UI。

## Vision 3.3 Theory Matcher

目标：实现理论库和理论匹配。

任务：内置 30 个理论、TheoryMatcher、研究问题解析、BM25 召回、LLM 解释、UI。

## Vision 3.4 Evidence Pack

目标：实现论点-证据绑定。

任务：claims 表、evidence 表、evidence linking、gap analysis、evidence UI。

## Vision 3.5 RAG

目标：实现混合检索和 Context Bundle。

任务：FTS5、chunking、embedding provider、metadata filter、context bundle、agent injection。

## Vision 3.6 Editor Loop

目标：AI 输出结构化插入 Main Editor。

任务：insert current cursor、replace selection、insert section、diff、rollback、snapshot。

## Vision 3.7 Connectors

目标：接 Zotero / Obsidian。

任务：Zotero read-only import、Obsidian vault scan、ImportJob、conflict preview。

## Vision 3.8 Skill Library

目标：本地 Skill 包加载和注入。

任务：SkillLoader、YAML parse、secret scan、skill binding、context injection。

## Vision 3.9 Export

目标：DOCX / Markdown / Citation / Reports 导出。

任务：DOCX template、Markdown export、BibTeX export、Evidence report、Run archive。

## Vision 4.0 Product Beta

目标：真正可发布 Beta。

验收：用户可以完成完整论文工作流；Knowledge → RAG → AI → Editor → Export 闭环；Mock 和 Real 都有清楚边界；所有 preview 功能不误导；测试全部通过；用户文档完整。

---

# 18. 第一轮 agent 应该做什么

不要直接写功能代码。先生成核心文档。

## 18.1 第一轮文档任务

创建：

```text
docs/00_PRODUCT/PRODUCT_BLUEPRINT.md
docs/00_PRODUCT/PRODUCT_ROADMAP.md
docs/01_PRD/PRD_OVERVIEW.md
docs/02_TECHNICAL/TECHNICAL_ARCHITECTURE.md
docs/02_TECHNICAL/DATA_MODEL.md
docs/01_PRD/PRD_KNOWLEDGE_BASE.md
docs/04_FRONTEND/FRONTEND_INTERFACE_MAPPING.md
docs/03_API/API_KNOWLEDGE_STORE.md
docs/06_AGENT/AGENT_VISION_ROADMAP.md
docs/06_AGENT/AGENT_EXECUTION_RULES.md
```

## 18.2 第一轮验收

```text
10 份文档存在
每份文档不是空壳
每份文档包含最终产品视角
每份文档包含分阶段实现路径
不修改功能代码
不改 UI
不发 API
不删除旧文件
```

---

# 19. 第二轮 agent 应该做什么

开始 Vision 3.1 Knowledge Base。

## 19.1 文件

```text
app/core/knowledge/
  __init__.py
  models.py
  database.py
  store.py
  importers.py
  search.py

tests/unit/
  test_knowledge_store.py
  test_knowledge_models.py
```

## 19.2 不做

```text
不接 RAG
不接 Zotero
不接 Obsidian
不接 UI 大改
不发 API
```

---

# 20. 第三轮 agent 应该做什么

实现 Literature Management。

文件：

```text
app/core/literature/
  models.py
  service.py
  import_bibtex.py
  import_ris.py
  citation_key.py
```

---

# 21. 最终判断

如果 agent 只完成 Runtime，不能叫最终产品。

如果 agent 完成以下闭环，才接近最终产品：

```text
Project
→ Knowledge Base
→ Literature
→ Theory
→ Evidence
→ RAG
→ Agent Writing
→ Editor Insert
→ Export
→ Run History
```

最终可发布版本必须是：

```text
用户能把自己的研究资料放进去
系统能组织它们
AI 能基于这些资料写作
用户能编辑和回滚
结果能导出
全过程能追溯
```

这才是 ThesisX 的最终产品。
