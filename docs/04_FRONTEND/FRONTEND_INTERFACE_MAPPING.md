# Frontend Interface Mapping — 页面与服务映射

> 定义 ThesisX 所有页面与后端服务、数据对象的对应关系。
> 每页标注：前端文件 → 后端服务 → 数据对象 → 实现状态。

---

## 映射总表

| 页面 | 前端文件 | 后端服务 | 数据对象 | 实现状态 | 说明 |
|------|---------|---------|---------|---------|------|
| Workspace Home | `workspace_home.py` | RunHistoryReader + Config | RunSummary | **部分真实** | 部分数据已接真实 RunHistory |
| Main Editor | `main_window.py` | QTextDocument | — | **真实可用** | WYSIWYG 编辑器，功能完整 |
| AI Draft Assistant | `agent_team_dialog.py` | AgentTeamRunner + SessionStore | PaperRequest / Run | **真实可用** | Mock 稳定，Real 单次验证 |
| Research Workspace | `research_workspace_page.py` | ProjectService | Project / ResearchQuestion | **3.0 实现** | 新建页面 |
| Knowledge Base | `knowledge_base_page.py` | KnowledgeStore | KnowledgeObject | **3.1 实现** | 当前无 UI 或 preview |
| Literature | `literature.py` | LiteratureService | LiteratureItem | **3.2 实现** | 当前 preview |
| Theory Matcher | `theory_matcher_page.py` | TheoryMatcher | TheoryItem | **3.3 实现** | 当前 preview |
| Evidence Pack | `evidence_pack_page.py` | EvidencePackService | EvidenceItem | **3.4 实现** | 当前 preview |
| RAG Search | `rag_search_page.py` | RagService | — | **3.5 实现** | 当前 preview |
| Quality Dashboard | `quality_dashboard_page.py` | QualityService | — | **3.10 实现** | 新建页面 |
| Run History | `run_history_page.py` | RunHistoryReader | RunSummary / RunDetail | **部分真实** | 三面板 UI 已实现 |
| Runtime Diagnostics | `runtime_diagnostics_page.py` | RunDiagnostics | RunHealth | **部分真实** | CLI 已实现，UI 部分 |
| Provider Settings | `provider_settings_page.py` | ProviderService | ProviderProfile | **部分真实** | 底层检测已实现，UI 部分 |
| Skill Library | `skill_library.py` | SkillLoader | Skill | **preview** | SkillLoader Runtime 已实现，UI 未接 |
| Export Center | `export_center.py` | ExportService | — | **部分真实** | Markdown 导出部分，docx 待充分验收 |
| Data & Charts | `data_charts.py` | — | — | **preview** | 只有 UI 壳 |
| Collaboration | `collaboration.py` | — | — | **preview** | 只有 UI 壳 |
| Version History | `version_history.py` | — | — | **preview** | 只有 UI 壳 |
| Submission | `submission.py` | — | — | **preview** | 只有 UI 壳 |
| AI Chat | `ai_chat_page.py` | — | — | **V2 计划** | 当前 preview |
| Settings | `settings_page.py` | Config | — | **部分真实** | 部分字段已接真实配置 |
| Zotero Connector | `zotero_connector.py` | ZoteroConnector | LiteratureItem | **3.7 实现** | 当前不存在 |
| Obsidian Connector | `obsidian_connector.py` | ObsidianScanner | NoteItem | **3.7 实现** | 当前不存在 |
| Local Import | `local_import.py` | MarkdownImporter | KnowledgeObject | **3.1 的一部分** | 当前无独立 UI |

---

## 状态说明

| 状态 | 含义 | 操作限制 |
|------|------|---------|
| **真实可用** | 底层数据 + UI 全部接通，可正常使用 | 可以正常使用 |
| **部分真实** | 部分功能已接通，部分仍 mock/preview | 注意分辨哪些是真实的 |
| **3.x 实现** | 在路线图中规划，当前为 preview/不存在 | 不要把 preview 说成真实 |
| **V2 计划** | 当前不在 3.x 路线图中 | 搁置 |
| **不存在** | 还没有创建文件 | 后续按 PRD 新建 |

---

## 详细映射

### Workspace Home（真实可用 — 部分）

**前端：** `app/ui/pages/workspace_home.py`
**后端：** `RunHistoryReader` + `generate_provider_health_report()`
**数据：** `RunSummary[]`（已部分接真实数据）

**已接通：**
- Run 历史记录（列表）
- Provider 健康状态摘要
- 进度卡片数据（从 RunHistory 统计）

**仍 mock：**
- 搜索功能
- 待办列表

**分阶段：** 3.1 后完全真实

---

### Main Editor（真实可用）

**前端：** `app/ui/main_window.py`
**后端：** `QTextDocument`（原生 PyQt，无后端服务）
**数据：** 无（文档内容在内存，通过 `contentChanged` signal 管理）

**已接通：** 全部功能
- 格式化工具栏
- 大纲
- 预览同步
- 菜单/快捷键
- 状态栏

**分阶段：** 无需分阶段，持续维护

---

### AI Draft Assistant（真实可用）

**前端：** `app/ui/agent_team_dialog.py`
**后端：** `AgentTeamRunner` + `SessionStore`
**数据：** `PaperRequest` → `Run`（session）

**已接通：**
- Mock 模式（稳定）
- Real 模式（单次验证成功）
- SessionStore 持久化
- RunHistory 记录

**分阶段：** 3.6 增加 Editor 闭环（结构化插入）

---

### Knowledge Base（3.1 实现）

**前端：** `app/ui/pages/knowledge_base_page.py`（待建或 preview）
**后端：** `KnowledgeStore`
**数据：** `KnowledgeObject` / `LiteratureItem` / `NoteItem` / `TheoryItem` / `EvidenceItem`

**当前状态：** 无真实 UI 或 preview 壳
**3.1 实现：**
- 列表/搜索/筛选
- 详情面板
- Markdown 导入
- 项目绑定

---

### Literature（3.2 实现）

**前端：** `app/ui/pages/literature.py`
**后端：** `LiteratureService`
**数据：** `LiteratureItem`

**当前状态：** preview（Coming Soon badge）
**3.2 实现：**
- 文献列表（接真实 KnowledgeStore）
- citation key 生成（authorYearShortTitle）
- 标签/阅读状态
- 项目绑定（role）

---

### Theory Matcher（3.3 实现）

**前端：** `app/ui/pages/theory_matcher_page.py`（待建）
**后端：** `TheoryMatcher`
**数据：** `TheoryItem`

**当前状态：** 不存在
**3.3 实现：**
- 研究问题输入
- 理论推荐输出（附理由/边界/误用风险）
- 理论详情面板

---

### Evidence Pack（3.4 实现）

**前端：** `app/ui/pages/evidence_pack_page.py`（待建）
**后端：** `EvidencePackService`
**数据：** `EvidenceItem` / `Claim`

**当前状态：** 不存在
**3.4 实现：**
- 创建 Claim
- 绑定 EvidenceItem
- 缺口分析
- 导出证据包报告

---

### RAG Search（3.5 实现）

**前端：** `app/ui/pages/rag_search_page.py`（待建）
**后端：** `RagService`
**数据：** —（检索结果）

**当前状态：** 不存在
**3.5 实现：**
- 自然语言查询
- 混合检索（4层）
- Context Bundle 预览
- 注入写作

---

### Run History（部分真实）

**前端：** `app/ui/pages/run_history_page.py`
**后端：** `RunHistoryReader` + `RunDiagnostics`
**数据：** `RunSummary` / `RunDetail` / `RunHealth`

**已接通：**
- Run 列表
- Run 详情（paper.md / events / metadata）
- 诊断报告
- 三面板 UI

**仍缺失：**
- 导出 session 包
- 按 topic/model/date 筛选
- 从历史 run 继续编辑

**分阶段：** 3.9 完善导出，3.6 Editor 闭环后支持继续编辑

---

### Runtime Diagnostics（部分真实）

**前端：** `app/ui/pages/runtime_diagnostics_page.py`（待建或集成）
**后端：** `RunDiagnostics` + `ProviderService`
**数据：** `RunHealth` / `ProviderHealthReport`

**已接通（CLI）：** `scripts/diagnose_runs.py`
**缺失：** 独立 UI 页面（当前集成在 Run History 详情里）

---

### Provider Settings（部分真实）

**前端：** `app/ui/pages/settings_page.py`
**后端：** `ProviderService` + `Config`
**数据：** `ProviderProfile`

**已接通：**
- `get_agent_team_config()` 底层逻辑
- `generate_provider_health_report()`
- Settings 页面部分字段

**缺失：**
- Provider 切换 UI
- 本地 CLI 自动发现 UI
- Remote API 配置测试 UI
- Agent Team 路径选择 UI

**分阶段：** 3.2+ 完善 UI

---

### Skill Library（preview）

**前端：** `app/ui/pages/skill_library.py`
**后端：** `SkillLoader`
**数据：** `Skill` / `SkillBinding`

**已接通（Runtime）：**
- `SkillLoader.load_local_skills()`
- `~/.wenbiao/skills/` 文件扫描
- `selected_skills.md` 注入

**缺失（UI）：**
- Skill 列表页（真实数据）
- 启用/禁用 UI
- 任务类型绑定 UI

**分阶段：** 3.8 实现完整 UI

---

### Export Center（部分真实）

**前端：** `app/ui/pages/export_center.py`（待建）
**后端：** `ExportService`
**数据：** —

**已接通：**
- Markdown 导出（部分）
- `python-docx` 已安装

**缺失：**
- 多模板 docx 导出
- BibTeX / RIS 导出
- Session Archive 打包
- 导出预览

**分阶段：** 3.9 实现完整 Export Center

---

## 前端文件清单（按目录）

```
app/ui/
├── main_window.py          → Main Editor（真实）
├── toolbar.py              → FormattingToolbar / MoreToolbar（真实）
├── preview_widget.py       → WYSIWYG 编辑区（真实）
├── outline_widget.py       → 大纲（真实）
├── status_bar.py           → 状态栏（真实）
├── agent_team_dialog.py    → AI Draft Assistant（真实）
├── pages/
│   ├── workspace_home.py  → Home（部分真实）
│   ├── run_history_page.py → Run History（部分真实）
│   ├── settings_page.py   → Settings（部分真实）
│   ├── knowledge_base_page.py → KB（3.1）
│   ├── literature.py      → Literature（3.2）
│   ├── theory_matcher_page.py → Theory（3.3）
│   ├── evidence_pack_page.py → Evidence（3.4）
│   ├── rag_search_page.py  → RAG（3.5）
│   ├── skill_library.py    → Skill Library（preview）
│   ├── export_center.py    → Export（3.9）
│   ├── data_charts.py      → Data & Charts（preview）
│   ├── collaboration.py   → Collaboration（preview）
│   ├── version_history.py  → Version History（preview）
│   └── submission.py       → Submission（preview）
└── components/
    └── sidebar_nav.py      → 导航（10项，真实）
```

---

## 分阶段实现路径

| 阶段 | 真实可用 | 部分真实 | preview |
|------|---------|---------|---------|
| **当前** | Main Editor, AgentTeamDialog, SidebarNav | Workspace Home, Run History, Settings | Skill Library, Data & Charts, Collaboration, Version History, Submission, AI Chat |
| **v3.1** | Knowledge Base | | |
| **v3.2** | Literature, Runtime Diagnostics, Provider Settings 完善 | | |
| **v3.3** | Theory Matcher | | |
| **v3.4** | Evidence Pack | | |
| **v3.5** | RAG Search | | |
| **v3.6** | Main Editor 闭环增强 | | |
| **v3.7** | Zotero Connector, Obsidian Connector | | |
| **v3.8** | Skill Library | | |
| **v3.9** | Export Center | | |
| **v4.0** | 所有 preview 完成或明确废弃 | | |

---

*本文档是前端实现的映射基准。*
*页面状态以本文档为准，不得擅自将 preview 标为真实可用。*