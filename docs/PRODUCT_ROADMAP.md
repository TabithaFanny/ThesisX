# ThesisX 真正最终可用产品路线图

> **定位说明：** 本文档是 Vision 3.0 Beta 发布报告的路线图修正版。
> 原路线图（V1-V12）混淆了"Runtime 闭环"和"完整论文 AI 工作台"。本文按真实产品链路重新排序，从 Knowledge Base 开始，不再以 Runtime/UI 为中心。

**当前版本：** ThesisX v2.x Runtime Beta
**目标版本：** ThesisX v5.0 完整论文 AI 工作台
**预计阶段数：** 3.0 → 3.1 → 3.2 → 3.3 → 3.4 → 3.4.5 → 3.5 → 3.5.1 → 3.6 → 3.7 → 3.8 → 3.9 → 3.10 → 4.0 → 4.1-4.7 → 5.0

---

## Vision 3.0：Research Workspace 核心

**目标：** 建立论文项目容器（Project container），定义研究问题/方向/目标模型，作为所有后续功能的基础。

### 用户价值
- 用户有了一个研究空间，可以从模糊想法到清晰项目
- 研究问题和方向被结构化定义，影响后续理论推荐和 RAG
- 项目内 Run、上下文、知识对象全部绑定到同一个项目

### 核心数据模型
- **Project**：论文项目容器（id, name, research_question, discipline, created_at, updated_at）
- **ResearchQuestion**：研究问题（id, project_id, question, keywords, discipline, created_at）
- **ResearchDirection**：研究方向（id, project_id, direction, rationale, status）
- **ResearchGoal**：研究目标（id, project_id, goal, milestone, deadline）

### 涉及后端模块
- `app/core/project/`（新建）：ProjectService, ResearchQuestionService
- SQLite 表：projects, research_questions, research_directions, research_goals

### 禁止事项
- 不做复杂项目依赖管理（先单一项目）
- 不做多项目并行管理（3.0 先专注单项目）

### 验收标准
- [ ] 用户可创建 Project，输入研究问题
- [ ] ResearchQuestion 可被 Theory Matcher 读取
- [ ] 项目内可创建多个 Run，绑定到同一 Project
- [ ] KnowledgeBase 可绑定对象到 Project

---

## Vision 3.1：Knowledge Base 最小可用

**目标：** 建立本地知识库数据模型，用户能看到真实知识条目（文献/笔记/理论/证据），但不先做复杂 RAG。

### 用户价值
- 用户有了自己的研究资料空间
- 手动管理条目，积累研究资产
- 不再只依赖 AI 生成，可以管理真实资料

### 涉及前端页面
- `KnowledgeBasePage`（新建）：条目列表 / 搜索 / 分组 / 标签
- 四类对象详情面板：文献、笔记、理论、证据
- 导入按钮（Markdown 导入 + 手动添加）

### 涉及后端/数据模块
- `app/core/knowledge/`（新建）：数据模型 + 本地存储
- `KnowledgeStore`：增删改查，SQLite/JSON 文件持久化
- 四类对象定义：`LiteratureItem`、`NoteItem`、`TheoryItem`、`EvidenceItem`
- 文件解析：`MarkdownImporter`、`JsonImporter`

### 涉及接口
- `POST /knowledge/items` — 创建条目
- `GET /knowledge/items` — 查询列表
- `DELETE /knowledge/items/<id>` — 删除
- `GET /knowledge/items?type=&tag=` — 筛选

### 需要新增/修改的文件
```
app/core/knowledge/
├── __init__.py
├── models.py          # 四类 dataclass
├── store.py            # KnowledgeStore（增删改查）
├── importers.py        # Markdown / JSON 解析
app/ui/pages/knowledge_base_page.py  # 新建
app/ui/components/knowledge_*.py     # 组件
```

### 禁止事项（当前版本不包含）
- 不做 RAG 检索（3.5 及后续版本规划）
- 不接 Zotero（3.7 及后续版本规划）
- 不接 Obsidian 写回（3.7 及后续版本规划）
- 不做复杂标签系统（先简单标签）
- 不做 PDF 内容解析（3.5.1 及后续版本规划）

### 验收标准
- [ ] 用户可创建/查看/删除知识条目
- [ ] 四类对象可区分（文献/笔记/理论/证据）
- [ ] Markdown 文件可导入
- [ ] 搜索能找到条目标题/标签
- [ ] 知识库面板显示真实数据（不是 mock）

### 必须跑的测试
- `test_knowledge_store.py` — CRUD 正确
- `test_importers.py` — Markdown 解析正确
- 手动验证：导入一个 Markdown 文件，条目出现在列表

### 是否允许自动连续执行
- **否** — 数据模型设计需要用户确认字段和关系后再继续

### 哪些地方必须停下来让我确认
1. 四类对象的完整字段定义（LiteratureItem 需要哪些字段？）
2. 存储格式：SQLite 还是 JSON 文件？
3. 知识库与论文项目的绑定关系（一本书一个 KB，还是共享？）
4. 导入的 Markdown 格式规范是否需要约束？

---

## Vision 3.2：Literature Management 真闭环

**目标：** 在知识库基础上，把文献管理做成完整闭环（标签/摘要/引用/citation key），为 Zotero 接入打基础。

### 用户价值
- 用户可以像管理 Zotero 一样管本地文献
- 可以给文献打标签、写摘要
- citation key 可追溯
- 写作时可引用真实文献

### 涉及前端页面
- `LiteraturePage`（已有壳）：接真实数据，替换 mock
- 文献详情面板：标签、摘要、引用信息、DOI、作者、年份
- 文献分组（项目绑定）

### 涉及后端/数据模块
- `LiteratureService`（扩展 3.1 的 KnowledgeStore）
- `CitationKeyGenerator`：根据年份/作者生成 citation key
- `LiteratureMatcher`：文献与论文项目绑定

### 涉及接口
- `POST /literature` — 添加文献
- `GET /literature` — 列表/筛选
- `PUT /literature/<id>` — 更新标签/摘要
- `GET /literature/<id>/citation` — 获取 citation key

### 需要新增/修改的文件
```
app/core/knowledge/literature.py     # 新建，LiteratureService
app/core/knowledge/citation.py       # 新建，citation key 生成
app/ui/pages/literature.py            # 修改，接真实数据
```

### 禁止事项（当前版本不包含）
- 不做 Zotero 导入（3.7 及后续版本规划）
- 不做 PDF 内容解析（3.5.1 及后续版本规划）
- 不做复杂引用格式（先输出 basic citation）

### 验收标准
- [ ] 文献可添加/编辑/删除
- [ ] 可打标签（多标签支持）
- [ ] 可写摘要（plain text）
- [ ] citation key 格式正确（AuthorYear）
- [ ] 文献与论文项目绑定
- [ ] Literature 页面不再显示 mock 数据

### 必须跑的测试
- `test_literature_service.py`
- `test_citation_key_generator.py`

### 是否允许自动连续执行
- **是** — 逻辑相对独立，可连续实现

### 哪些地方必须停下来让我确认
1. citation key 格式规范（Harvard / APA / Chicago？）
2. 文献与项目的绑定粒度（一个项目一本文献列表？）

---

## Vision 3.3：Theory Matcher 最小可用

**目标：** 用户输入研究问题，系统推荐候选理论，输出适配理由、使用边界、经典文献、误用风险。

### 用户价值
- 不用读大量文献就知道有哪些理论可用
- 得到理论适配性评估，不盲目套用
- 理论写到论文框架时有明确指引

### 涉及前端页面
- `TheoryMatcherPage`（新建）：输入研究问题 → 输出候选理论列表
- 理论详情面板：适配理由 / 使用边界 / 经典文献 / 误用风险
- 理论写入论文框架按钮

### 涉及后端/数据模块
- `TheoryMatcherService`（新建）：研究问题 → 理论候选
- 理论库：`TheoryItem`（从 KnowledgeStore 的 TheoryItem 扩展）
- `KeywordExtractor`：从研究问题抽取关键词/概念/机制/学科方向
- `TheoryRanker`：候选理论排序

### 涉及接口
- `POST /theory/match` — 输入研究问题，返回候选理论列表
- `GET /theory/<id>` — 理论详情
- `POST /theory/apply` — 将理论写入论文框架

### 需要新增/修改的文件
```
app/core/theory/
├── __init__.py
├── matcher.py           # TheoryMatcherService
├── keyword_extractor.py # 研究问题关键词抽取
├── theory_ranker.py     # 候选排序
├── theories/            # 内置理论库（JSON）
app/ui/pages/theory_matcher_page.py  # 新建
```

### 禁止事项（当前版本不包含）
- 不做复杂语义检索（先用关键词匹配）
- 不做理论自动写作（只推荐，不自动写）
- 不做理论库自动更新（先手工维护理论库）
- 不做跨学科理论推荐（第一版先限定学科范围）

### 验收标准
- [ ] 输入研究问题，返回≥3个候选理论
- [ ] 每个理论包含：名称、适配理由、使用边界、经典文献、误用风险
- [ ] 可将理论写入论文框架（作为章节或段落）
- [ ] Theory Matcher 页面不是 mock

### 必须跑的测试
- `test_theory_matcher.py` — 固定研究问题输出可验证的理论
- `test_keyword_extractor.py`

### 是否允许自动连续执行
- **是** — 逻辑独立，可连续

### 哪些地方必须停下来让我确认
1. 理论库初始规模（先内置多少个理论？覆盖哪些学科？）
2. 理论匹配策略：规则引擎 vs 小模型？

---

## Vision 3.4：Evidence Pack / 证据包

**目标：** 建立论点—证据绑定，支持文献摘录、案例材料、数据说明、证据缺口提示。

### 用户价值
- 写作时有可追溯的证据来源
- 不会凭空捏造文献和数据
- 证据缺口能被系统提示

### 涉及前端页面
- `EvidencePackPage`（新建）：证据列表 / 绑定论点 / 来源类型
- 证据详情面板：摘录内容、来源、关联论点、缺口标记

### 涉及后端/数据模块
- `EvidenceService`（新建）：增删改查证据
- `EvidenceItem` dataclass：论点、证据内容、类型（摘录/案例/数据）、来源、缺口标记
- `ClaimBinder`：证据与论文段落绑定

### 涉及接口
- `POST /evidence` — 添加证据
- `GET /evidence?claim=` — 按论点查证据
- `PUT /evidence/<id>/claim` — 绑定到论点
- `GET /evidence/gaps` — 证据缺口分析

### 需要新增/修改的文件
```
app/core/evidence/
├── __init__.py
├── service.py      # EvidenceService
├── models.py       # EvidenceItem
├── binder.py       # ClaimBinder
app/ui/pages/evidence_pack_page.py  # 新建
```

### 禁止事项（当前版本不包含）
- 不做自动证据生成（用户手动添加）
- 不做复杂知识图谱（先简单绑定）
- 不做证据质量自动评分（用户手动标记）

### 验收标准
- [ ] 证据可创建/编辑/删除
- [ ] 证据可绑定到论文中的具体论点
- [ ] 支持来源类型区分（摘录/案例/数据）
- [ ] 缺口标记功能可用
- [ ] Evidence Pack 页面不是 mock

### 必须跑的测试
- `test_evidence_service.py`

### 是否允许自动连续执行
- **是** — 逻辑独立，可连续

### 哪些地方必须停下来让我确认
1. EvidenceItem 的核心字段有哪些？
2. 证据缺口分析的实现方式（规则 vs AI）？

---

## Vision 3.5：RAG 最小可用

**目标：** 对本地知识库做检索，支持模糊概念找文献、研究问题找理论、证据检索。写作时引用可追溯来源，不胡编文献。

### 用户价值
- 输入模糊研究兴趣能找到相关文献
- 不需要精确关键词
- 证据有来源，论文可信

### 涉及前端页面
- `RAGSearchPage`（新建）：自然语言检索框 + 结果列表
- 结果详情：来源文件/文献、相关段落、匹配理由
- 检索历史

### 涉及后端/数据模块
- `RAGService`（新建）：Embedding + 向量检索
- `TextChunker`：长文本分块（知识条目/文献摘要/笔记）
- `EmbeddingIndex`：本地向量索引（SQLite + vector 或简单 BM25 起步）
- `Retriever`：检索 → 重排 → 返回

### 涉及接口
- `POST /rag/index` — 构建索引
- `POST /rag/search` — 检索（自然语言）
- `GET /rag/history` — 检索历史

### 需要新增/修改的文件
```
app/core/rag/
├── __init__.py
├── service.py       # RAGService
├── chunker.py       # TextChunker
├── indexer.py       # EmbeddingIndex（先 BM25，后续可换向量）
├── retriever.py     # Retriever + Re-ranker
app/ui/pages/rag_search_page.py  # 新建
```

### 禁止事项（当前版本不包含）
- 不做复杂知识图谱检索
- 不做跨语言检索（先单一语言）
- 不做实时网络检索
- 不接外部 API（先用本地 Embedding 或纯 BM25）
- RAG-Fusion 等高级检索（4.2 及后续版本规划）

### 验收标准
- [ ] 自然语言检索返回相关结果（不要求完美召回）
- [ ] 结果显示来源（文献名/条目名/段落）
- [ ] 支持按类型筛选（文献/笔记/理论/证据）
- [ ] 构建索引不在主线程（不阻塞 UI）
- [ ] RAG 检索不返回空结果时报错提示清晰

### 必须跑的测试
- `test_rag_service.py` — 固定 corpus + 固定 query 可验证
- `test_chunker.py`

### 是否允许自动连续执行
- **是** — 逻辑独立，但索引构建需要人工验证效果

### 哪些地方必须停下来让我确认
1. Embedding 方案选型：OpenAI API / 本地模型 / BM25？**（这是重大决策点）**
2. 索引更新策略：实时 vs 手动重建？
3. RAG 结果如何注入到写作流程（作为 context 传入 Agent）？

---

## Vision 3.6：AI 写作与 Main Editor 结构化闭环

**目标：** AI 生成结果不只是 paper.md，能按标题层级插入 Main Editor，能从选中文本发起改写，能基于知识库/理论/证据包写作。

### 用户价值
- AI 生成结果直接进入编辑器，不需要复制粘贴
- 可以针对段落/章节继续改写
- 写作时有知识库和理论的上下文支撑

### 涉及前端页面
- `AgentTeamDialog`（已有）：改造结果页，不只是预览，要能选择插入方式
- `MainEditor`（已有）：增强与 AgentTeamDialog 的数据通道
- 新增"局部改写"功能：选中文本 → 发送到 AI → 替换

### 涉及后端/数据模块
- `EditorBridge`（新建）：AI 结果 → 结构化插入编辑器
- `RewriteService`（扩展现有 AgentTeamRunner）：局部文本改写
- `OutlineParser`：解析 paper.md 的标题层级，供插入时选择位置

### 涉及接口
- `POST /editor/insert` — 按标题层级插入章节
- `POST /editor/rewrite` — 局部文本改写
- `GET /editor/outline` — 获取当前文档大纲

### 需要新增/修改的文件
```
app/core/editor/
├── __init__.py
├── bridge.py         # EditorBridge，AI结果→编辑器
├── outline_parser.py # 解析标题层级
├── rewrite.py        # RewriteService，局部改写
app/ui/agent_team_dialog.py  # 修改，结果页接编辑器
app/ui/main_window.py        # 修改，接收插入信号
```

### 禁止事项（当前版本不包含）
- 不做全自动写作（保留用户控制权）
- 不在编辑器里直接调用大模型（通过 AgentTeamRunner）
- 不破坏现有 Main Editor 任何功能
- 不做实时协作编辑

### 验收标准
- [ ] AI 生成结果可按章节插入 Main Editor（不是全文复制）
- [ ] 选中文本可发送给 AI 改写，结果替换原文
- [ ] 插入后保留原有格式（标题层级、粗体、列表）
- [ ] 不破坏现有编辑器功能（每次改后手动验证）

### 必须跑的测试
- `test_editor_bridge.py` — 插入结构正确
- `test_outline_parser.py` — 标题解析正确
- **手动验证**：生成一篇论文，插入编辑器，验证格式完整

### 是否允许自动连续执行
- **是** — 但每次需要手动截图验证编辑器格式

### 哪些地方必须停下来让我确认
1. 插入方式：覆盖当前光标位置 vs 在大纲中新建章节？
2. 局部改写的 prompt 是否需要用户配置？
3. AI 改写结果如果不满意，如何回滚？

---

## Vision 3.7：Zotero / Obsidian 连接器

**目标：** 导入 Zotero 文献、读取 Obsidian vault，建立同步边界，不破坏用户原始数据。先只读，再考虑写回。

### 用户价值
- 直接用已有 Zotero 文献库，不需要手动重建
- 复用 Obsidian 中的研究笔记作为知识库来源
- 数据边界清晰，不破坏原始文件

### 涉及前端页面
- `SettingsPage`（修改）：Zotero / Obsidian 配置面板
- `KnowledgeBasePage`（修改）：显示导入自 Zotero / Obsidian 的条目

### 涉及后端/数据模块
- `ZoteroConnector`（新建）：Zotero API 读取，文献条目同步
- `ObsidianScanner`（已有，部分完成）：vault 扫描，Markdown 文件读取
- `SyncManager`：同步状态管理（只读模式下不写回）

### 涉及接口
- `POST /connectors/zotero/import` — 从 Zotero 导入
- `POST /connectors/obsidian/scan` — 扫描 vault
- `GET /connectors/status` — 连接状态

### 需要新增/修改的文件
```
app/core/connectors/
├── __init__.py
├── zotero.py       # ZoteroConnector
├── obsidian.py     # ObsidianScanner（扩展已有）
app/ui/pages/settings_page.py  # 修改，接配置 UI
```

### 禁止事项（当前版本不包含）
- 第一版不做写回（不修改 Zotero / Obsidian 原始文件）
- 不做实时同步（用户手动触发）
- 不自动解决冲突（显示冲突让用户处理）
- 不在未确认前删除任何用户数据

### 验收标准
- [ ] Zotero API 可读取（需要用户输入 Zotero API Key）
- [ ] Obsidian vault 可扫描（需要用户指定 vault 路径）
- [ ] 导入的条目出现在知识库（文献 / 笔记）
- [ ] 不会误删或修改原始文件
- [ ] 连接状态在 Settings 页面清晰显示

### 必须跑的测试
- `test_zotero_connector.py`（需要 mock Zotero API）
- `test_obsidian_scanner.py`（需要 mock vault）
- **手动验证**：用真实 Zotero 库 / Obsidian vault 测试

### 是否允许自动连续执行
- **否** — 涉及外部数据，需要人工确认数据边界和同步策略

### 哪些地方必须停下来让我确认
1. Zotero API Key 的获取和配置方式？
2. Obsidian vault 的同步策略（定期 vs 手动）？
3. 写回的边界在哪里？哪些可以写回，哪些不能？

---

## Vision 3.8：Skill Library 真实接入

**目标：** SkillLoader 与 Skill Library UI 打通，本地 skill 可启用/禁用，skill 与任务类型绑定，selected_skills.md 影响 prompt 和 run。

### 用户价值
- 用户在 GUI 里管理 skill（不是只靠文件）
- skill 真正影响生成质量（不只是注入 context）
- 不同任务类型可绑定不同 skill

### 涉及前端页面
- `SkillLibraryPage`（已有壳）：接真实 skill 列表，替换 preview
- skill 详情：名称、描述、分类、prompt 预览、启用状态
- skill 绑定配置：哪些 skill 绑定到哪些任务类型（写作/改写/理论匹配）

### 涉及后端/数据模块
- `SkillLoader`（已有）：扩展支持 skill 配置（启用/禁用/优先级）
- `SkillRegistry`：管理 skill 元数据、绑定关系、加载状态
- `SkillPicker`：任务类型 → 激活 skill 列表

### 涉及接口
- `GET /skills` — 列出所有本地 skill
- `PUT /skills/<id>` — 更新启用状态
- `GET /skills?task=` — 按任务类型获取激活 skill
- `POST /skills/bind` — 绑定 skill 到任务类型

### 需要新增/修改的文件
```
app/core/skills/
├── registry.py       # 新建，SkillRegistry
├── picker.py         # 新建，SkillPicker
app/ui/pages/skill_library.py  # 修改，接真实列表
```

### 禁止事项（当前版本不包含）
- 不做远程 skill 市场（只本地）
- 不做 skill 创建 UI（先只管理已有的 skill 文件）
- 不做 skill 版本管理
- 不自动下载新 skill

### 验收标准
- [ ] SkillLibrary 页面显示真实本地 skill（不是 coming soon）
- [ ] 可启用/禁用单个 skill
- [ ] skill 与任务类型绑定后，在 run 中生效
- [ ] selected_skills.md 内容与 UI 状态一致
- [ ] skill prompt 变更后在 run 中反映

### 必须跑的测试
- `test_skill_registry.py`
- `test_skill_picker.py`
- **手动验证**：启用 Logic Review skill，跑一个 run，检查 selected_skills.md 内容

### 是否允许自动连续执行
- **是** — 逻辑独立，可连续

### 哪些地方必须停下来让我确认
1. skill 绑定到任务类型的配置存在哪里（文件 vs config）？
2. skill prompt 中的敏感信息（API key 等）如何处理？

---

## Vision 3.9：导出与交付

**目标：** docx 导出、markdown 导出、session 打包、诊断报告导出、USER_GUIDE.md、隐私说明、release tag。

### 用户价值
- 论文可导出为 docx，提交给导师/期刊
- 运行记录可打包，方便复盘
- 有完整用户说明，不靠猜测使用

### 涉及前端页面
- `MainEditor`（修改）：导出菜单（docx / md）
- `RunHistoryPage`（已有）：导出 session 包按钮

### 涉及后端/数据模块
- `DocxExporter`（已有，需充分验收）：paper.md → docx 转换
- `SessionExporter`：run session → zip 包
- `ReportGenerator`：诊断报告 → Markdown

### 涉及接口
- `POST /export/docx` — 导出当前编辑器内容为 docx
- `POST /export/session/<session_id>` — 打包 session
- `GET /export/report/<session_id>` — 下载诊断报告

### 需要新增/修改的文件
```
app/core/export/
├── __init__.py
├── docx_exporter.py      # 已有，需充分验收
├── session_exporter.py   # 新建
app/ui/main_window.py     # 修改，导出菜单
```

### 禁止事项（当前版本不包含）
- 不做 PDF 导出（后续版本规划）
- 不做复杂格式模板（先保持论文基本格式）
- 不在导出时修改内容（纯转换）

### 验收标准
- [ ] Main Editor 可导出 docx（标题层级、列表、粗体保留）
- [ ] 导出失败有明确错误提示（不是 silent fail）
- [ ] session 包包含 paper.md + events + metadata
- [ ] USER_GUIDE.md 存在且内容完整
- [ ] 隐私说明存在（哪些数据发 API、session 存储位置）
- [ ] Git release tag 已打

### 必须跑的测试
- `test_docx_exporter.py` — 基本导出正确
- `test_session_exporter.py` — 包内容完整
- **手动验收**：导出真实 paper.md，对比格式

### 是否允许自动连续执行
- **是** — 逻辑独立

### 哪些地方必须停下来让我确认
1. docx 格式模板是否需要定制（不同学校/期刊格式不同）？
2. 隐私说明的具体内容（需要用户提供）

---

## Vision 4.0：Final Product Beta

**目标：** 用户能从研究问题开始，完成完整链路：Research Workspace → 知识库 → 文献 → 理论 → 证据 → RAG → AI 写作 → Editor 闭环 → 质量看板 → 导出 → 历史追踪。

### 用户价值
- 一个完整的研究论文写作工具
- 不只是"能跑"，是真的"能用"
- 数据都在本地，不丢失，不被滥用

### 验收标准
- [ ] 从空白项目到完整论文导出，全链路可走通
- [ ] 知识库、文献、理论、证据不全是 mock
- [ ] RAG 检索有实际效果（不是空结果）
- [ ] Skill Library 与 run 真正绑定
- [ ] Zotero/Obsidian 可导入真实数据
- [ ] 导出 docx 格式可用
- [ ] Quality Dashboard 显示真实质量数据
- [ ] USER_GUIDE.md 完整
- [ ] 隐私说明清晰
- [ ] Git release tag 打好
- [ ] 测试覆盖率 ≥ 80%

### 是否允许自动连续执行
- **否** — 必须人工完整验收全链路

---

## Vision 4.1：Research Question Refinement Advanced

**目标：** 智能分析研究问题清晰度，推荐研究方向细化，识别研究空白。

- 研究问题清晰度评分
- 研究方向推荐引擎
- 研究空白识别

---

## Vision 4.2：Advanced RAG / RAG-Fusion

**目标：** 高级 RAG 检索能力，多路召回融合，跨语言检索。

- RAG-Fusion 多路召回
- 跨语言检索（英/中）
- 知识图谱增强检索

---

## Vision 4.3：Cross-lingual Search

**目标：** 跨语言知识检索，翻译辅助阅读，本地化支持。

- 中英双语检索
- 翻译辅助阅读
- 本地化 UI 优化

---

## Vision 4.4：Online Literature Discovery

**目标：** 在线文献发现，Semantic Scholar / arXiv 搜索，RSS 追踪。

- 在线数据库搜索
- 论文发现推荐
- RSS 源追踪

---

## Vision 4.5：Connector Write-back

**目标：** Zotero/Obsidian 双向同步，写回确认流程。

- Zotero 写回（用户确认）
- Obsidian 写回（用户确认）
- 冲突解决 UI

---

## Vision 4.6：Knowledge Graph Visualization

**目标：** 知识图谱可视化，论点-证据关系图，理论关系网络。

- 知识对象关系可视化
- Claim-Evidence 图谱
- 理论关系网络图

---

## Vision 4.7：Template System

**目标：** 用户自定义模板，模板市场（本地），模板分享。

- 自定义模板创建
- 本地模板管理
- 模板变量系统

---

## Vision 5.0：Collaboration / Cloud Optional

**目标：** 协作功能（可选），云端同步（可选），多设备支持。

- 多设备同步（可选）
- 项目分享与协作（可选）
- 云端备份（可选）

---

## 真实建议

### 1. 当前版本应该重新命名为什么

**ThesisX v2.8 — Runtime Beta**

理由：2.x 表示它是从 2.x 向 3.0 过渡的中间状态，不是完整 3.0。"Runtime Beta" 明确说明这是 Runtime 闭环可用，不是产品可用。

---

### 2. 原 Vision 3.0 报告哪里过于乐观

五处：

**第一，标题** — "最终可用 Beta" 暗示完整产品，实际上只是 Runtime 可跑。

**第二，12 条标准的性质** — 验证的是"能打开 / 能编辑 / 能跑 / 能记录"，不是"能用"。这些是 Runtime 前置条件，不是产品功能完整性指标。

**第三，Real 模式验证结论** — 单次成功（939 events）被描述为"Real 模式打通"，但 pipeline_v2 实际还是 dry-run，真正跑的是 tui_runner（旧路径）。这不是完整 Real 链路。

**第四，核心功能缺失未充分说明** — Knowledge Base、RAG、Theory Matcher、Zotero、Obsidian、Evidence Pack 这些核心模块在报告里几乎没提，只在"已知限制"里一句带过。

**第五，产品完整性暗示** — 报告结论是"可以发布 Beta"，但没有 Beta 版应该有的完整功能列表做支撑。Beta 发布报告变成了 Runtime 就绪报告。

---

### 3. 下一步应该优先做 Runtime，还是 Knowledge Base

**优先做 Knowledge Base（Vision 3.1）。**

理由：
- Runtime 已经闭环，继续优化 Runtime 边际收益极低
- Knowledge Base 是论文 AI 工作台的核心差异点，没有它系统只是"AI 生成文本"而不是"知识驱动的论文写作"
- Knowledge Base 优先级高于 RAG（RAG 依赖 Knowledge Base 的数据）
- 3.1 是数据模型层，不依赖 UI，可以快速验证

不要继续在 Runtime 上投入了。当前 Runtime 的核心价值已经在，不再是瓶颈。

---

### 4. 如果目标是最终论文 AI 工作台，下一轮应该从哪个 Vision 开始

**从 Vision 3.1 开始：Knowledge Base 最小可用。**

具体任务是：
1. 定义四类数据对象（LiteratureItem / NoteItem / TheoryItem / EvidenceItem）的字段
2. 实现 KnowledgeStore（增删改查）
3. 实现 Markdown 导入
4. 新建 `KnowledgeBasePage`（替换当前的 preview 页面）
5. 手动验证：导入一个 Markdown 文件，条目出现在列表

**为什么不是 3.2（Literature）开始：** Literature 依赖 Knowledge Base 的基础数据模型，先做 3.1 再扩展到 3.2 更顺。

---

### 5. 哪些任务可以自动执行，哪些必须让我确认

**可自动执行（不需要每次确认）：**

| 任务 | 原因 |
|------|------|
| Vision 3.1 数据模型实现 | 有明确字段定义后，纯实现工作 |
| Vision 3.2 LiteratureService | 逻辑独立，可连续实现 |
| Vision 3.3 TheoryMatcher | 关键词提取 + 规则匹配，可自动 |
| Vision 3.4 EvidenceService | 增删改查，可自动 |
| Vision 3.8 SkillRegistry / SkillPicker | 逻辑独立，可自动 |
| Vision 3.9 SessionExporter / ReportGenerator | 纯实现，可自动 |

**必须让我确认（决策点）：**

| 决策点 | 所在版本 | 原因 |
|--------|----------|------|
| 四类对象完整字段定义 | 3.1 | 数据模型影响后续所有功能 |
| 存储格式（SQLite vs JSON） | 3.1 | 涉及数据结构迁移成本 |
| Embedding 方案选型 | 3.5 | 重大架构决策，影响性能和成本 |
| Zotero API Key 配置方式 | 3.7 | 涉及外部服务认证 |
| Obsidian 同步策略 | 3.7 | 涉及用户数据边界 |
| docx 格式模板 | 3.9 | 涉及输出质量 |
| 隐私说明内容 | 3.9 | 需要用户提供 |
| 全链路人工验收 | 4.0 | 必须人工走完完整流程 |

---

## 附录：当前代码真实状态速查

```
Main Editor:         真实可用（WYSIWYG，格式工具栏，大纲）
Workspace 导航:       10 页面可导航
AgentTeamDialog:     三阶段 UI，Mock 稳定，Real 单次验证
SessionStore:        持久化正常
RunHistoryPage:     三面板 UI 真实可用
RunDiagnostics:      可输出诊断报告
SkillLoader:        Runtime 完成，已加载 2 个 skill
Config 链路:         Env > Config > Defaults 统一
Provider 健康检查:    底层可用，UI 部分
测试:                401/401 passed
Git:                本地 14 commits ahead，remote 未推送
```

---

*本文档生成时间：2026-05-03*
*基于：CODEX_HANDOFF.md、V1/V2 阶段记录、当前代码状态*