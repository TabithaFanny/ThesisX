# ThesisX 总技术架构

> 定义 ThesisX 全栈技术架构：桌面端、数据层、Runtime、Knowledge Base、RAG、Provider、Agent、Export、安全与隐私、测试。

---

## 1. 桌面端架构（PyQt6）

```
MainWindow
├── _mode_stack（QStackedWidget）
│   ├── [0] Workspace（QWidget）
│   │   ├── SidebarNav（QWidget）
│   │   └── WorkspaceArea（QStackedWidget）— 10+ 页面
│   │       ├── WorkspaceHomePage
│   │       ├── ResearchWorkspacePage（3.0）
│   │       ├── KnowledgeBasePage（3.1）
│   │       ├── LiteraturePage（3.2）
│   │       ├── TheoryMatcherPage（3.3）
│   │       ├── EvidencePackPage（3.4）
│   │       ├── RagSearchPage（3.5）
│   │       ├── QualityDashboardPage（3.10）
│   │       ├── RunHistoryPage
│   │       ├── RuntimeDiagnosticsPage（3.2+）
│   │       ├── ProviderSettingsPage
│   │       ├── SkillLibraryPage（preview）
│   │       ├── ExportCenterPage
│   │       └── SettingsPage
│   └── [1] Editor（QWidget）
│       ├── FormattingToolbar
│       ├── MoreToolbar
│       ├── DocumentCanvas（QTextEdit + QTextDocument）
│       ├── OutlineWidget（QTreeWidget）
│       ├── StatusBar
│       └── PlagiarismPanel / AgentPanel
│
├── AgentTeamDialog（QDialog — AI 论文初稿助手）
│   ├── ConfigPage（8 字段）
│   ├── ProgressPage（6 阶段 + log + cancel）
│   └── ResultPage（preview + quality + 导入选项）
│
└── 菜单栏 / 工具栏
```

**模式切换：** `_mode_stack.setCurrentIndex(0|1)` 控制 Workspace / Editor 切换

**线程模型：**
- UI 主线程：PyQt 事件循环
- Agent 线程：`AgentTeamWorker（QThread）` 驱动 `AgentTeamRunner.run()`
- Async IO：`asyncio` 事件循环在 worker 线程内创建

---

## 2. 数据层架构

### 2.1 SQLite 主库

**路径：** `~/.wenbiao/thesisx.db`

**核心表（按优先级）：**

```sql
-- 项目
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    research_question TEXT,
    discipline TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 统一知识对象基类
CREATE TABLE knowledge_objects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('literature','note','theory','evidence')),
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source_type TEXT,
    source_uri TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);

-- 四类扩展对象
CREATE TABLE literature_items (...);  -- 扩展 literature 专用字段
CREATE TABLE note_items (...);        -- 扩展 note 专用字段
CREATE TABLE theory_items (...);      -- 扩展 theory 专用字段
CREATE TABLE evidence_items (...);    -- 扩展 evidence 专用字段

-- 关系
CREATE TABLE project_knowledge_links (
    project_id TEXT,
    object_id TEXT,
    role TEXT,
    priority INTEGER,
    UNIQUE(project_id, object_id)
);

CREATE TABLE object_relations (
    from_object_id TEXT,
    to_object_id TEXT,
    relation_type TEXT,
    UNIQUE(from_object_id, to_object_id, relation_type)
);

-- 标签
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE object_tags (
    object_id TEXT,
    tag_id TEXT,
    UNIQUE(object_id, tag_id)
);

-- 引用
CREATE TABLE citations (
    id TEXT PRIMARY KEY,
    source_object_id TEXT,
    target_object_id TEXT,
    context TEXT,
    page TEXT,
    FOREIGN KEY (source_object_id) REFERENCES knowledge_objects(id)
);

-- FTS5 全文检索
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    title, summary, content,
    content='knowledge_objects',
    content_rowid='rowid'
);

-- Embedding（未来扩展）
CREATE TABLE embeddings (
    object_id TEXT PRIMARY KEY,
    chunk_index INTEGER,
    embedding BLOB,
    FOREIGN KEY (object_id) REFERENCES knowledge_objects(id)
);

-- Skill
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE skill_bindings (
    skill_id TEXT,
    project_id TEXT,
    task_type TEXT,
    enabled INTEGER DEFAULT 1,
    PRIMARY KEY (skill_id, project_id, task_type)
);

-- Run
CREATE TABLE runs (
    session_id TEXT PRIMARY KEY,
    project_id TEXT,
    run_mode TEXT,
    status TEXT,
    provider_type TEXT,
    model TEXT,
    cost REAL,
    started_at TEXT,
    ended_at TEXT
);
```

### 2.2 本地文件系统

```
~/.wenbiao/
  thesisx.db              ← SQLite 主库
  knowledge/
    imports/              ← 导入的源文件（Markdown/PDF/BibTeX）
    exports/              ← 导出的文件（docx/md/zip）
    files/                ← 附件（PDF等）
    embeddings/           ← 向量索引文件
  runs/
    <session_id>/
      request.json
      metadata.json
      events.jsonl
      messages.jsonl
      paper.md
      outline.json
      quality_report.json
      context/
        selected_skills.md
        knowledge_context.md
        theory_context.md
      artifacts/
  providers.json          ← Provider 配置（不含 key）
  config.json             ← 用户配置
```

---

## 3. Runtime 架构

```
用户触发 AgentTeamDialog
    ↓
PaperRequest（topic, outline_type, skills, ...）
    ↓
AgentTeamWorker（QThread）
    ↓
AgentTeamRunner.run()
    ├── Mock 模式：AgentTeamRunner（内部 Mock 实现）
    └── Real 模式：AgentTeamCompatAdapter
                    ↓
              LocalCLIProvider / RemoteAPIProvider / AgentTeamProvider
                    ↓
              PaperEvent stream（state/token/cost/message/artifact/error/completion）
    ↓
SessionStore.write_event() → JSONL
    ↓
UI 更新（progress signal）
    ↓
Run 完成 → paper.md + 诊断报告
```

**核心组件：**
- `SessionStore`：`~/.wenbiao/runs/<session_id>/` 持久化
- `RunHistoryReader`：读取 `~/.wenbiao/runs/` 所有历史
- `RunDiagnostics`：读 run → 健康报告
- `ProviderDetector`：发现 Local CLI、Remote API、Agent Team
- `Config`：统一配置（Env > Config > Defaults）

---

## 4. Research Workspace 架构（3.0）

```
ProjectService（主接口）
    ├── create_project() / get_project() / update_project() / delete_project()
    ├── create_research_question() / get_research_question()
    ├── link_knowledge_object() / link_run()
    └── list_project_runs() / list_project_knowledge()
            ↓
        SQLite（projects / research_questions / research_directions / research_goals 表）
            ↓
        project_knowledge_links（多对多）
            ↓
        project_run_links（多对多）
```

**核心模块：**
- `app/core/project/` — ProjectService + ResearchQuestionService
- ResearchQuestion 影响 Theory Matcher 和 RAG 检索上下文

---

## 5. Knowledge Base 架构

```
KnowledgeStore（主接口）
    ├── create_object() / update_object() / delete_object()
    ├── get_object() / search()
    ├── link_to_project() / unlink_from_project()
    └── list_by_project()
            ↓
        SQLite（knowledge_objects 表）
            ↓
        FTS5（全文检索）
            ↓
        文件系统（源文件存储）
```

**导入路径：**
- Markdown 导入 → `MarkdownImporter`（frontmatter 解析 + 推断）
- BibTeX 导入 → `BibtexImporter`
- Zotero → `ZoteroConnector`（3.7）
- Obsidian → `ObsidianScanner`（3.7）

---

## 6. RAG 架构

```
用户查询（自然语言）
    ↓
QueryParser（抽取关键词/意图/过滤器）
    ↓
混合检索（4 层）
    ├── Layer 1：FTS5 / BM25（精准关键词）
    ├── Layer 2：Embedding（语义相似度）
    ├── Layer 3：Metadata Filter（项目/类型/年份/标签）
    └── Layer 4：Rerank（按任务相关性重排）
    ↓
ContextBundle 生成
    ├── literature: []
    ├── theories: []
    ├── evidence: []
    ├── notes: []
    ├── citation_constraints: []
    └── forbidden_claims: []
    ↓
注入 PaperRequest.context
```

**Embedding 策略：**
- 默认：远程 embedding API（OpenAI / DeepSeek）
- 可选：本地 embedding model
- 降级：FTS5-only（无 embedding 时）

---

## 7. Provider 架构

```
ProviderService
    ├── discover_local_clis()
    │       └── LocalCLIProvider（codex / claude / openclaw）
    ├── detect_remote_api_config()
    │       └── RemoteAPIProvider（DeepSeek / OpenAI / OpenRouter）
    ├── detect_agent_team_paths()
    │       └── AgentTeamProvider（tui_runner / pipeline_v2 / pipeline_function）
    ├── health_check(profile_id, mode)
    │       └── ProviderHealthReport
    └── set_default_profile(profile_id)

Config（统一配置层）
    └── get_agent_team_config()
            ↓
        Env > providers.json > config.json > Defaults
```

**Provider 健康报告：**
```python
@dataclass
class ProviderHealthReport:
    overall_ok: bool
    providers: list[ProviderStatus]
    issues: list[str]
    recommendations: list[str]
```

---

## 8. Agent 架构

```
AgentTeamDialog
    ├── ConfigPage（PaperRequest 参数配置）
    ├── ProgressPage（6 阶段 progress + token + cost）
    └── ResultPage（paper.md preview + 质量检查 + 导入选项）

AgentTeamWorker（QThread）
    └── AgentTeamRunner.run() → PaperEvent stream
            ↓
        Mock 模式：内部 Mock 实现（固定响应）
        Real 模式：AgentTeamCompatAdapter
            ├── LocalCLIProvider：本地 CLI（codex）
            ├── RemoteAPIProvider：远程 API（DeepSeek / OpenAI）
            └── AgentTeamProvider：外部 Agent Team

AgentTeamCompatAdapter
    └── get_agent_team_config()
            ↓
        DEEPSEEK_API_KEY > OPENAI_API_KEY > AI_API_KEY > custom_ai_api_key
```

---

## 9. Export 架构

```
ExportService
    ├── export_docx(content, template) → docx
    ├── export_markdown(content) → md
    ├── export_bibtex(project_id) → bib
    ├── export_session_archive(session_id) → zip
    └── export_diagnostics_report(run_id) → md

DocxTemplate
    ├── Default Academic Template
    ├── University Thesis Template
    ├── Journal Article Template
    └── Custom Template（用户配置）
```

---

## 10. Quality Dashboard 架构（3.10）

```
QualityService（主接口）
    ├── get_writing_progress() — 字数/章节完成度
    ├── get_claim_coverage() — Claim 覆盖率
    ├── get_evidence_integrity() — 证据完整性
    ├── get_citation_completeness() — 引用完整性
    └── run_export_preflight() — 导出预检
            ↓
        Editor（获取写作进度）
            ↓
        EvidencePack（获取 Claim 和证据数据）
            ↓
        CitationStore（获取引用数据）
```

**核心模块：**
- `app/core/quality/` — QualityService + ClaimTracker + EvidenceChecker + CitationChecker
- 与 Editor、Evidence Pack、CitationStore 集成

---

## 11. 安全与隐私架构

```
本地数据（永不发送）
    ├── thesisx.db
    ├── ~/.wenbiao/runs/（session 数据）
    ├── ~/.wenbiao/knowledge/
    └── providers.json（不含 key）

发送至 Remote API（仅 Real 模式）
    ├── 研究问题 / 大纲 / 写作 prompt
    ├── 选中的知识片段（Context Bundle）
    ├── 模型名称 + base_url
    └── 不发送：未选中的文件 / 整个 vault / API key

API Key 存储优先级
    1. 环境变量（最安全）
    2. 系统 Keychain
    3. 配置文件（不含明文 key）
    4. 用户手动输入（临时）

Skill 安全
    - 导入时扫描 sk- / api_key / token / secret
    - 高置信度阻止启用
    - prompt.md 中禁止写 key
```

---

## 12. 测试架构

```
tests/
├── unit/
│   ├── test_config_unified.py
│   ├── test_knowledge_store.py（3.1）
│   ├── test_literature_service.py（3.2）
│   ├── test_theory_matcher.py（3.3）
│   ├── test_evidence_pack.py（3.4）
│   ├── test_rag_retriever.py（3.5）
│   ├── test_editor_operations.py（3.6）
│   ├── test_provider_detector.py
│   ├── test_skill_loader.py
│   └── test_export_docx.py（3.9）
├── integration/
│   ├── test_run_history.py
│   └── test_session_store.py
└── ui/
    └── （PyQt 冒烟测试）

覆盖率目标：≥ 80%（最终 Beta）
```

---

## 13. 技术栈总结

| 层级 | 技术 | 版本 |
|------|------|------|
| 桌面 UI | PyQt6 | 6.x |
| 主语言 | Python | 3.14 |
| 本地主库 | SQLite + FTS5 | 3.x |
| 向量检索 | sqlite-vec（可选）/ FAISS（可选） | 最新 |
| 文档解析 | markdown-it-py / python-frontmatter / PyYAML | 最新 |
| PDF 元数据 | pypdf | 最新 |
| 导出 | python-docx | 最新 |
| Zotero | pyzotero（3.7） | 最新 |
| 测试 | pytest | 最新 |
| 类型检查 | mypy | 最新 |

---

## 14. 分阶段实现

| 阶段 | 实现内容 |
|------|---------|
| v2.x | PyQt6 UI + SessionStore + RunHistory + Provider 配置链路 |
| v3.1 | SQLite + KnowledgeStore + FTS5 + Markdown 导入 |
| v3.2 | LiteratureService + citation key + CSL |
| v3.3 | TheoryMatcher + 规则+语义混合 |
| v3.4 | EvidencePack + Claim-Evidence 绑定 |
| v3.5 | RAG（4 层检索） + Embedding |
| v3.6 | Editor 闭环（插入+改写+回滚） |
| v3.7 | Zotero + Obsidian 连接器 |
| v3.8 | Skill 文件 + 绑定 UI |
| v3.9 | Export Center（多模板） |
| v4.0 | 完整测试覆盖（≥ 80%） |

---

*本文档与 DATA_MODEL.md、AGENT_RUNTIME_ARCHITECTURE.md 配套。*
*技术决策以 PRODUCT_DECISIONS.md 为准。*