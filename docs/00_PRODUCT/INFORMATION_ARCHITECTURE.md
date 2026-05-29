# Information Architecture — ThesisX 页面地图与导航结构

> 定义 ThesisX 所有页面、页面关系、导航结构。
> 每页标注：功能定位、核心任务、状态（真实/preview/待实现）。

---

## 1. 页面总表

### 一级入口（SidebarNav）

| 页面 | 文件 | 功能定位 | 核心任务 | 状态 |
|------|------|---------|---------|------|
| Workspace Home | `workspace_home.py` | 项目入口、状态总览 | 查看进度、跳转其他页面 | **真实可用** |
| Main Editor | `main_window.py` | 真实 WYSIWYG 编辑器 | 论文写作、编辑、排版 | **真实可用** |
| AI Draft Assistant | `agent_team_dialog.py` | AI 论文初稿生成 | 配置→生成→预览→插入编辑器 | **真实可用（Mock+Real）** |
| Knowledge Base | `knowledge_base_page.py` | 全局知识资产库 | 管理文献/笔记/理论/证据 | **3.1 最小可用** |
| Literature | `literature.py` | 文献管理 | 导入、标签、摘要、引用 | **3.2** |
| Theory Matcher | `theory_matcher_page.py` | 理论推荐 | 研究问题→理论推荐→写入框架 | **3.3** |
| Evidence Pack | `evidence_pack_page.py` | 证据包 | Claim-Evidence 绑定、缺口分析 | **3.4** |
| RAG Search | `rag_search_page.py` | 混合检索 | 模糊查询→结构化结果→注入写作 | **3.5** |
| Run History | `run_history_page.py` | 运行历史 | 查看历史 Run、paper.md、诊断 | **部分真实** |
| Runtime Diagnostics | `runtime_diagnostics_page.py` | 诊断报告 | 输出健康报告、错误解释 | **3.2+** |
| Provider Settings | `provider_settings_page.py` | Provider 配置 | 检测/配置/切换 Provider | **部分真实** |
| Skill Library | `skill_library.py` | Skill 管理 | 启用/禁用/绑定 Skill | **preview** |
| Export Center | `export_center.py` | 导出管理 | docx/md/BibTeX/Session打包 | **部分真实** |
| Data & Charts | `data_charts.py` | 数据图表 | 数据集管理、图表生成 | **preview** |
| Collaboration | `collaboration.py` | 协作 | 讨论、任务、审稿流 | **preview** |
| Version History | `version_history.py` | 版本历史 | 快照、diff、回滚 | **preview** |
| Submission | `submission.py` | 投稿管理 | 稿件状态、rebuttal | **preview** |
| Settings | `settings_page.py` | 全局设置 | Theme、Connectors、About | **部分真实** |
| AI Chat | `ai_chat_page.py` | 对话 | 与 AI 对话（V2 计划） | **preview（V2）** |

### 连接器（从属页面）

| 页面 | 文件 | 功能定位 | 状态 |
|------|------|---------|------|
| Zotero Connector | `zotero_connector.py` | Zotero 导入 | **3.7** |
| Obsidian Connector | `obsidian_connector.py` | Obsidian vault 扫描 | **3.7** |
| Local Files Import | `local_import.py` | 本地文件导入 | **3.1 的一部分** |
| Markdown Import | `markdown_import.py` | Markdown 批量导入 | **3.1 的一部分** |

### 导出（从属页面）

| 页面 | 文件 | 功能定位 | 状态 |
|------|------|---------|------|
| DOCX Export | 集成在 Export Center | 模板化导出 | **3.9** |
| Markdown Export | 集成在 Export Center | Markdown 导出 | **部分真实** |
| Session Archive | 集成在 Run History | 运行记录打包 | **部分真实** |
| Diagnostics Report | 集成在 Runtime | 诊断报告导出 | **部分真实** |

---

## 2. 导航结构

```
ThesisX 主窗口
├── 菜单栏
│   ├── 文件：新建 / 打开 / 保存 / 导出 / 关闭
│   ├── 编辑：撤销 / 重做 / 剪切 / 复制 / 粘贴
│   ├── 视图：Main Editor / Workspace / Dark Mode
│   ├── 工具：AI 论文初稿助手 / Runtime 诊断
│   ├── 帮助：关于 / 隐私说明 / 用户手册
│   └── 返回工作台（Editor 模式下）
│
├── Workspace 模式（SidebarNav + QStackedWidget）
│   └── SidebarNav（左侧导航）
│       ├── 🏠 Workspace Home
│       ├── 📝 Main Editor
│       ├── 🤖 AI Draft Assistant
│       ├── 📚 知识库（展开）
│       │   ├── Knowledge Base（总览）
│       │   ├── Literature
│       │   ├── Theory Matcher
│       │   └── Evidence Pack
│       ├── 🔍 RAG Search
│       ├── 📊 Runtime（展开）
│       │   ├── Run History
│       │   ├── Runtime Diagnostics
│       │   └── Provider Settings
│       ├── 🛠 工具（展开）
│       │   ├── Skill Library
│       │   ├── Export Center
│       │   └── Data & Charts
│       └── ⚙️ Settings
│
└── Editor 模式（Toolbar + QTextEdit + Outline + AgentPanel）
    ├── FormattingToolbar
    ├── MoreToolbar
    ├── Document Canvas（QTextDocument）
    ├── OutlineWidget（QTreeWidget）
    └── StatusBar
```

---

## 3. 页面关系图

```
用户启动 → Workspace Home
  │
  ├─→ 创建新项目 → Main Editor（空白文档）
  │
  ├─→ AI Draft Assistant → 生成 paper.md → [可选择]
  │                                    │
  │                                    └→ 插入 Main Editor（按章节）
  │
  ├─→ 知识库 → [Literature / Theory Matcher / Evidence Pack]
  │           │
  │           ├─→ RAG Search → 查询知识库 → 结果注入 AI 写作
  │           │
  │           └─→ 连接器 → Zotero / Obsidian / 本地文件
  │
  ├─→ Main Editor（直接进入，手动写作）
  │           │
  │           └─→ 选中文本 → AI 局部改写 → diff / 回滚
  │
  ├─→ Runtime → Run History → 查看历史 paper.md
  │           │
  │           ├─→ Runtime Diagnostics → 健康报告
  │           │
  │           └─→ Provider Settings → 切换/配置 Provider
  │
  ├─→ 工具 → Skill Library → 管理 Skill 启用/禁用
  │         │
  │         ├─→ Export Center → docx / md / BibTeX 导出
  │         │
  │         └─→ Data & Charts（V2）
  │
  └─→ Settings → Connectors（Zotero/Obsidian）
              └─→ Theme / About
```

---

## 4. 每个页面的核心任务

### Workspace Home
**核心任务：** 项目入口总览，显示进度卡片、最近文件、快捷操作。
**真实/preview：** 真实可用（部分数据已接真实 RunHistory）
**跳转关系：** 所有页面的入口，可快速跳转

### Main Editor
**核心任务：** 真实 WYSIWYG 编辑，手动写作和编辑已 AI 生成的 paper.md
**真实/preview：** 真实可用
**跳转关系：** 可被 AI Draft Assistant 插入内容；选中文本可发送给 AI 改写

### AI Draft Assistant
**核心任务：** 配置任务参数 → 执行 Run → 预览 paper.md → 插入 Editor
**真实/preview：** 真实可用（Mock 稳定，Real 单次验证）
**跳转关系：** 结果可插入 Main Editor；进度可查看 Run History

### Knowledge Base
**核心任务：** 查看/搜索/管理所有知识对象（文献/笔记/理论/证据）
**真实/preview：** 3.1 实现最小可用
**跳转关系：** 可跳转 Literature/Theory Matcher/Evidence Pack；可调用 RAG Search

### Literature
**核心任务：** 文献列表、详情、标签、citation key、摘要、项目用途
**真实/preview：** 3.2 实现
**跳转关系：** 文献可绑定到 Evidence Pack；可从 Zotero/Obsidian 导入

### Theory Matcher
**核心任务：** 输入研究问题 → 输出理论推荐（附理由）→ 写入论文框架
**真实/preview：** 3.3 实现
**跳转关系：** 匹配的理论可写入 Main Editor 大纲；推荐文献可跳转 Literature

### Evidence Pack
**核心任务：** 创建 Claim → 绑定 Evidence → 分析缺口 → 导出证据包报告
**真实/preview：** 3.4 实现
**跳转关系：** Evidence 可来自 Literature；Claim 可绑定到 Editor 段落

### RAG Search
**核心任务：** 自然语言查询 → 混合检索结果 → Context Bundle → 注入 AI 写作
**真实/preview：** 3.5 实现
**跳转关系：** 结果注入 AI Draft Assistant 或局部改写

### Run History
**核心任务：** 列表查看所有 Run → 查看 paper.md/events/metadata → 诊断报告
**真实/preview：** 部分真实（列表和详情已实现，导出功能部分）
**跳转关系：** 点击 Run 可打开 session 文件夹；可跳转 Runtime Diagnostics

### Runtime Diagnostics
**核心任务：** 生成 Provider 健康报告、Run 诊断报告
**真实/preview：** 3.2+ 实现
**跳转关系：** 从 Run History 进入；报告可导出

### Provider Settings
**核心任务：** 发现/配置/测试/切换 Provider
**真实/preview：** 部分真实（底层 Provider 检测已实现，UI 部分）
**跳转关系：** 健康状态影响 AI Draft Assistant 的 Real 模式可用性

### Skill Library
**核心任务：** 显示本地 Skill 列表 → 启用/禁用 → 绑定任务类型
**真实/preview：** preview（SkillLoader Runtime 已实现，UI 未接）
**跳转关系：** 启用的 Skill 注入 AI Draft Assistant 的 context

### Export Center
**核心任务：** 导出 docx/md/BibTeX/Session Archive
**真实/preview：** 部分真实（markdown 导出部分，docx 需 3.9 充分验收）
**跳转关系：** 从 Main Editor 或 Run History 进入

---

## 5. 状态判断规则

每页必须按以下规则标注状态：

| 状态 | 定义 |
|------|------|
| **真实可用** | 底层数据和逻辑已接通，UI 可操作，结果可信 |
| **部分真实** | 部分功能已接通，部分仍为 mock 或 preview |
| **preview** | 有 UI 壳，标注 "Coming Soon" 或 "仅预览"，不代表功能已实现 |
| **3.x** | 在 PRODUCT_ROADMAP 中规划，当前未实现 |
| **V2** | 未来版本，当前不在 3.x 路线图中 |

**强制规则：**
- 未接真实功能必须显示 preview / coming soon badge
- 真实功能失败必须清晰报错，不能假装成功
- Provider 未配置必须显示缺什么

---

## 6. 分阶段实现

| 阶段 | 实现页面 |
|------|---------|
| **当前（v2.x）** | Workspace Home（部分真实）、Main Editor、AgentTeamDialog、RunHistoryPage（部分）、Settings（部分） |
| **v3.1** | Knowledge Base（最小）、Local/Markdown Import |
| **v3.2** | Literature、Runtime Diagnostics 完善、Provider Settings 完善 |
| **v3.3** | Theory Matcher |
| **v3.4** | Evidence Pack |
| **v3.5** | RAG Search |
| **v3.6** | Editor 闭环（结构化插入+局部改写+回滚） |
| **v3.7** | Zotero Connector、Obsidian Connector |
| **v3.8** | Skill Library UI（接真实 SkillLoader） |
| **v3.9** | Export Center（多模板 docx） |
| **v4.0** | 所有 preview 页面完成或明确废弃 |

---

*本文档与 FRONTEND_INTERFACE_MAPPING.md 配套。*
*页面状态以本文档为准，后续实现不得擅自将 preview 页面标为真实可用。*