# ThesisX Codex 交接文档

> 生成时间：2026-04-30
> 当前分支状态：前端视觉壳基本完成 + V1 AI 论文初稿助手 Dialog 已实现 + Runtime 未接入

---

## 1. 项目当前一句话状态

ThesisX 当前处于 **"前端视觉壳基本完成 + V1 AI 论文初稿助手 Dialog 已实现 + Runtime 未接入"** 阶段：Workspace 10 个页面全部可导航可截图，V1 Dialog 三阶段 UI 完整且提供 Mock/Real 双模式入口，但 Real 模式入口/配置存在并不等于真实 Agent Team 链路已验证可用；SVG 经过 4 轮对齐修复达到约 60-75%，但真实 Agent Team Runtime 链路（SequentialRunner 驱动、事件流、session 持久化）尚未在 GUI 中跑通，除 Main Editor 外的未来功能页面大多仍为 mock / preview。

---

## 2. 当前已完成内容

### 2.1 V1 AI 论文初稿助手 Dialog

- 三阶段 QStackedWidget：配置页（8 字段）→ 进度页（6 阶段 + 费用 + 日志 + 取消）→ 结果页（预览 + 质量检查 + 审稿意见 + 合规声明 + 导入编辑器）
- `AgentTeamWorker`（QThread）驱动 `AgentTeamRunner.run()`，asyncio event loop 在线程内创建
- Mock / Real 双模式，Real 模式前置校验 API Key / Agent Team 路径；但 Real 模式入口/配置存在并不等于真实 Agent Team 链路已验证可用
- 三种导入模式：new / replace / append（insert_cursor 灰显）
- 预算控制（>80% 警告，>100% 停止）
- 取消任务（`asyncio.Task.cancel`）、关闭清理（`disconnect + deleteLater`）
- 合规声明 3 条（通用 / Mock / 文献核查）
- 文件：`app/ui/agent_team_dialog.py`（1163 行）

### 2.2 Workspace 全量视觉壳

- 10 个页面全部有可导航 UI 实现：Home / AI Chat / Literature / Data Charts / Skills / Versions / Collaboration / Submission / Settings
- 左侧导航栏 `SidebarNav`（10 项，emoji 图标，`page_selected` 信号）
- `Workspace` 容器（SidebarNav + QStackedWidget）
- 主窗口 `_mode_stack`（0=Workspace，1=Editor），菜单 "返回工作台" + Ctrl+Shift+W
- Workspace 新页面基本使用 `design_tokens.py`；旧 Dialog / Toolbar 仍可能保留硬编码颜色
- Mock 数据集中在 `app/ui/mock/workspace_data.py` 和 `app/ui/mock/pages_data.py`

### 2.3 SVG 对齐轮次

| 轮次 | 修复页面 | 修复内容 |
|------|----------|----------|
| Round 1 | AI Chat / Workspace Home / Literature | 气泡色（User=#EEF5FF, AI=#2563EB）、首页搜索/进度卡/复选框、文献分类侧栏/导入按钮/表格行 |
| Round 2 | Version History / AI Chat / Literature | 版本面板+diff 视图+版本信息、对话历史列表、文献详情面板（摘要/引用/评分/标签） |
| Round 3 | Main Editor (Page 02) | 文档信息栏+大纲样式+Agent 建议面板（安全增强，不破坏真实编辑） |

### 2.4 主编辑器 Page 02 安全视觉增强

- 新增 `_enhance_editor_visuals()` 方法（~120 行），在 `_init_ui()` 之后调用
- 文档信息栏：ThesisX 品牌 + "论文初稿.docx" pill + "已保存" + AI 提示条
- 大纲样式：选中项 #EEF5FF 高亮、圆角、间距优化
- Agent 建议面板：右侧 220px，3 条 mock 建议 + "仅预览" badge + 拖拽占位区
- `_switch_to_editor` / `_switch_to_workspace` 管理 agent_panel 可见性
- **未修改**：`FormattingToolbar`、`MoreToolbar`、`PreviewWidget`、`OutlineWidget` 功能、`StatusBar` 功能、所有信号连接

### 2.5 Design Token / Theme 系统

- `app/ui/design_tokens.py`：Light / Dark 颜色类、FontSize（7 级）、Radius（7 级）、Spacing（6 级）
- `app/styles.py`：`MAIN_STYLE` / `DARK_STYLE` 全局样式表，使用 design tokens
- Workspace 新页面和新增组件基本使用 design tokens；旧 Dialog、旧 Toolbar 与历史 UI 代码中仍可能存在硬编码 hex

### 2.8 真功能 / mock / preview 边界表

| 区域 / 界面 | 当前性质 | 说明 |
|-------------|----------|------|
| Main Editor | 真实功能页 | 真实 WYSIWYG 编辑器、工具栏、预览/内容同步、菜单/快捷键等都在实际工作，不可按静态 SVG 反向裁剪 |
| Workspace Home | 导航入口 + mock 信息 | 负责入口、状态摘要、快捷跳转；卡片与列表内容为 mock 展示 |
| AI Chat | 前端壳 / mock / preview | 可导航、可截图，但不代表真实 Agent 对话链路已接通 |
| Literature | 前端壳 / mock / preview | 可导航、可截图，但不代表真实文献库、Zotero、检索、解析已接通 |
| Data & Charts | 前端壳 / mock / preview | 可导航、可截图，但不代表真实数据上传、图表生成已接通 |
| Skill Library | 前端壳 / mock / preview | 可导航、可截图，但不代表真实 Skill Registry / 调用链路已接通 |
| Version History | 前端壳 / mock / preview | 可导航、可截图，但不代表真实版本持久化 / diff / 回滚已接通 |
| Collaboration | 前端壳 / mock / preview | 可导航、可截图，但不代表真实协作消息、权限、任务流已接通 |
| Submission | 前端壳 / mock / preview | 可导航、可截图，但不代表真实投稿管理 / rebuttal 工作流已接通 |
| Settings | 前端壳 / mock / preview | 可导航、可截图，但不代表所有表单项都已接真实配置或外部连接器 |
| `AgentTeamDialog` | UI 完整，链路待验证 | Mock/Real 模式入口都存在；Real 模式入口/配置存在，但真实 Agent Team 链路仍需下一阶段诊断，不得视为已验证可用 |
| `AiDialog` | 真实旧对话框 | 历史 AI 写作助手，属于真实旧功能界面，但不是本轮 SVG 对齐对象 |
| 其他旧 Dialog | 真实功能或历史功能 | 如 `settings_dialog.py`、`skills_dialog.py`、`chart_dialog.py` 等，存在真实功能或历史功能属性，但不在本轮 SVG 对齐范围内 |

### 2.6 Mock / Preview / Coming Soon 标记

| 页面 | 标记 |
|------|------|
| AI Chat | `ComingSoonBadge("V2 计划")` + 输入栏 "仅预览" |
| Literature | `ComingSoonBadge("V3 计划")` + 详情面板 "仅预览" |
| Data & Charts | `ComingSoonBadge("V2 计划")` |
| Version History | `ComingSoonBadge("V2 计划")` |
| Collaboration | `ComingSoonBadge("V3 计划")` |
| Submission | `ComingSoonBadge("V3 计划")` |
| Settings Connectors | `ComingSoonBadge("V3 计划")` x 4 |
| 编辑器 Agent 面板 | "仅预览" QLabel |
| V1 Dialog Mock | 合规声明 3 条 |

### 2.7 测试

- 283 tests 全部通过
- 命令：`.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="`
- 注意：`pyproject.toml` 中有 `--cov` 参数但 `pytest-cov` 在 Python 3.14 下可能不可用，需用 `--override-ini="addopts="` 跳过

---

## 3. 当前没有完成的内容

以下功能 **全部未实现**，当前只有文件结构或 mock 壳：

| 功能 | 当前状态 | 计划版本 |
|------|----------|----------|
| Runtime Server（Agent Team 真实链路在 GUI 中跑通） | 未实现 | V1 下一阶段 |
| CLI Adapter | 未实现 | V1 下一阶段 |
| PaperPipelineRunner / AgentTeamRunner 真实驱动 GUI | 文件存在但 GUI 未连通 | V1 下一阶段 |
| Skill Registry 真实加载 | 未实现 | V2 |
| 本地 messages/events/artifacts JSONL 保存 | 未实现 | V1 下一阶段 |
| RAG 论文库 | 未实现 | V4 |
| 证据链 (Claim-Evidence-Citation) | 未实现 | V7 |
| Zotero / 外部文献库 | 未实现 | V5 |
| Git 真实版本控制 | 未实现 | V10 |
| 真实 diff 对比 | 未实现 | V2 |
| 真实图表生成 | 未实现 | V11 |
| 真实文献检索 (CrossRef/OpenAlex/Semantic Scholar) | 未实现 | V5 |
| PDF/DOCX/OCR 解析 | 未实现 | V4 |
| Agent 协作打回机制 | 未实现 | V8 |
| Graph 工作流 (AutoGen GraphFlow / LangGraph) | 未实现 | V8 |
| 编辑器深度融合（选区操作/Agent 面板） | 未实现 | V9 |

---

## 4. 当前 SVG 对齐真实状态

### 4.1 各页面对齐度

| 页面 | 对齐度 | 说明 |
|------|--------|------|
| Workspace Home (01) | ~80% | 搜索/进度卡/复选框/最近编辑/待办已对齐，快速操作区为额外保留 |
| Main Editor (02) | ~65% | 安全增强（信息栏/大纲样式/Agent 面板），但工具栏结构差异大；这只表示外层视觉结构参考，不代表编辑器内部交互与 SVG 完全一致 |
| AI Chat (03) | ~70% | 对话历史+气泡色+上下文面板已对齐，但整体是 mock |
| Literature (04) | ~75% | 分类侧栏+搜索+导入+表格行+详情面板已对齐，但整体是 mock |
| Data & Charts (05) | ~60% | 基本结构对齐，细节差距较大 |
| Skill Library (06) | ~55% | 分类过滤+卡片网格，SVG 细节未完全还原 |
| Version History (07) | ~75% | 版本面板+diff 视图+版本信息已对齐，但整体是 mock |
| Collaboration (08) | ~55% | 讨论+任务板双栏，SVG 细节未完全还原 |
| Submission (09) | ~50% | 状态概览+表格，SVG 细节差距较大 |
| Settings (10) | ~50% | 分区表单+ComingSoon，SVG 细节差距较大 |
| V1 Dialog | N/A | 独立三阶段 UI，不参照 SVG |

### 4.2 已比较接近 SVG 的页面

- Workspace Home：结构高度对齐
- Version History：3 列布局 + diff 色块对齐
- Literature：分类侧栏 + 表格行 + 详情面板对齐
- AI Chat：对话历史 + 气泡色 + 上下文面板对齐

### 4.3 仍然差距较大的页面

- Data & Charts：缺少 SVG 中的图表可视化占位
- Skill Library：卡片样式未完全对齐 SVG 的 `component_skill_cards.svg`
- Collaboration：任务板样式未完全对齐
- Submission：表格行样式未完全对齐
- Settings：Connectors 区域样式未完全对齐

### 4.4 缺失的 SVG 组件

当前已实现参照的 SVG 组件：
- `component_outline_tree.svg` → 大纲样式已参照
- `component_version_diff_card.svg` → diff 视图已参照
- `component_agent_chat_panel.svg` → 气泡色已参照

尚未专门参照的 SVG 组件：
- `component_skill_cards.svg`（Skill Library 卡片）
- `component_editor_toolbar.svg`（工具栏结构，因保护真实功能未强行对齐）
- `component_wysiwyg_editor_canvas.svg`（编辑区画布，因保护真实编辑器未强行对齐）
- `component_navigation_index.svg`（导航索引组件）

### 4.5 SVG 真源优先级

1. `page_*.svg` 画面本身是页面级第一真源。
2. `component_*.svg` 画面本身是组件级第一真源。
3. `components_manifest.json`、`page_prompts.md`、`reconstruction_guide.md` 是补充说明，不高于 SVG 实际画面。
4. 如果 SVG 画面、manifest、prompt、现有代码冲突，以 SVG 实际画面为准。
5. 如果 SVG 与真实功能安全冲突，以保护真实功能为先，并在报告中明确写出偏离原因。

### 4.6 Main Editor 特殊约束

- `page_02_main_editor.svg` 只能作为视觉参考，不能反向裁剪真实编辑器能力。
- 当前真实结构不是 SVG 的静态复刻；SVG 只能指导外层布局和视觉层级，不能要求删除真实编辑器能力。
- `PreviewWidget` 是真实 `contentEditable` 核心，不能替换成普通 mock canvas。
- `FormattingToolbar` / `MoreToolbar` 是真实工具栏，不能为了 SVG 简化而删除、裁剪或降级。
- 右侧 Agent 建议面板只是 preview 壳，不是已接通的 Agent 工作区。
- Inline AI prompt 不能直接插入正文污染真实文档，因此当前只允许采用不污染文档内容的安全视觉表达。
- 图片/图表拖拽区目前只是视觉 placeholder，不是上传功能，不得对外描述为真实可用。

### 4.7 因真实功能保护而未完全按 SVG 改的区域

- **Main Editor 工具栏**：SVG 仅 5 个简化 pill 按钮，实际有 28+ 格式化按钮，不能简化
- **Main Editor 编辑区**：SVG 是占位条，实际是真实 contentEditable WYSIWYG
- **Main Editor 右侧**：SVG 是"实时预览"，实际 Agent 面板是 mock（PreviewWidget 是中间的编辑器）
- **Main Editor AI 提示**：SVG 嵌入正文中间，实际放在文档信息栏（避免污染真实内容）

### 4.8 仍需核对但本轮不实现的 SVG 组件清单

- `component_skill_cards.svg`：未专门精准对齐
- `component_navigation_index.svg`：未实现
- `component_editor_toolbar.svg`：未精准对齐，原因是保护真实工具栏
- `component_wysiwyg_editor_canvas.svg`：未精准对齐，原因是保护真实编辑器
- `component_agent_chat_panel.svg`：部分对齐
- `component_version_diff_card.svg`：部分对齐
- `component_outline_tree.svg`：部分对齐

### 4.9 后续需要专门做一轮「逐页面 SVG 精准对齐」

当前 4 轮修复是结构性对齐，后续需要逐页面逐组件精准对齐，尤其是：
- Skill Library 卡片样式
- Data & Charts 图表占位
- Collaboration 任务板
- Submission 表格
- Settings Connectors

---

## 5. 关键文件结构

### 5.1 UI 层

| 文件 | 职责 |
|------|------|
| `app/ui/design_tokens.py` | Light/Dark 颜色、FontSize、Radius、Spacing 常量 |
| `app/styles.py` | MAIN_STYLE / DARK_STYLE 全局样式表 |
| `app/ui/components/base.py` | 14+ 可复用组件（PageHeader, StatusBadge, ComingSoonBadge, AgentCard, TaskCard, SkillCard, LiteratureCard, VersionCard 等） |
| `app/ui/components/sidebar_nav.py` | 10 项侧栏导航，page_selected 信号 |
| `app/ui/pages/workspace.py` | Workspace 容器（SidebarNav + QStackedWidget） |
| `app/ui/pages/workspace_home.py` | 首页（问候/搜索/进度卡/最近编辑/待办/快捷操作） |
| `app/ui/pages/ai_chat_page.py` | AI Chat（对话历史+气泡+上下文+Agent 列表） |
| `app/ui/pages/literature.py` | 文献管理（分类侧栏+搜索+表格+详情面板） |
| `app/ui/pages/data_charts.py` | 数据图表（数据集列表+图表卡片） |
| `app/ui/pages/skill_library.py` | 技能库（分类过滤+卡片网格） |
| `app/ui/pages/version_history.py` | 版本历史（版本面板+diff 视图+版本信息） |
| `app/ui/pages/collaboration.py` | 协作（讨论+任务板） |
| `app/ui/pages/submission.py` | 投稿管理（状态概览+表格） |
| `app/ui/pages/settings_page.py` | 设置中心（API/模型/主题/连接器） |
| `app/ui/mock/workspace_data.py` | 首页 mock 数据（进度卡/最近文件/待办/文献分类） |
| `app/ui/mock/pages_data.py` | 全量 mock 数据（文献/技能/版本/协作/投稿/聊天/数据集） |
| `app/ui/agent_team_dialog.py` | V1 AI 论文初稿助手（三阶段 UI + Worker） |
| `app/ui/main_window.py` | 主窗口（3369 行，模式切换/菜单/工具栏/编辑器布局） |

### 5.2 Pipeline 层（文件已存在，但 GUI 未连通）

| 文件 | 职责 | 行数 |
|------|------|------|
| `app/core/pipeline/__init__.py` | 包初始化 | 37 |
| `app/core/pipeline/events.py` | PaperEvent + 阶段常量 + 事件类型 | 201 |
| `app/core/pipeline/models.py` | PaperRequest, ArchitectOutput, QualityCheckResult | 96 |
| `app/core/pipeline/runner.py` | PaperPipelineRunner Protocol | 28 |
| `app/core/pipeline/agent_team_bridge.py` | 路径/依赖/API Key/Agent Team import | 169 |
| `app/core/pipeline/agent_team_runner.py` | V1 Runner Adapter（ArchitectNode + SequentialRunner） | 425 |
| `app/core/pipeline/quality_checks.py` | 静态质量检查 | 88 |
| `app/core/pipeline/nodes/architect_node.py` | 自研大纲规划节点 | 324 |
| `app/core/pipeline/nodes/citation_verifier_node.py` | 引用验证节点 | 169 |
| `app/core/pipeline/nodes/deai_humanizer.py` | AI 去痕润色节点 | 177 |
| `app/core/pipeline/nodes/logic_auditor_node.py` | 逻辑审查节点 | 112 |
| `app/core/pipeline/nodes/translator_node.py` | 翻译节点 | 126 |
| `app/core/pipeline/prompts/` | 20+ prompt 文件（architect, reviewer, writer, optimizer 等） | — |

### 5.3 其他关键文件

| 文件 | 职责 |
|------|------|
| `app/core/config.py` | 配置管理（含 agent_team_path 等字段） |
| `app/ui/toolbar.py` | FormattingToolbar + MoreToolbar（627 行） |
| `app/ui/preview_widget.py` | QWebEngineView + contentEditable WYSIWYG 编辑器 |
| `app/ui/outline_widget.py` | QTreeWidget 大纲 |
| `app/ui/status_bar.py` | StatusBar（字数/字符/行号/编码） |
| `app/ui/plagiarism_panel.py` | 查重面板 |
| `requirements.txt` | 依赖（含 httpx/pydantic/python-dotenv 可选） |

### 5.4 SVG 参照

| 路径 | 内容 |
|------|------|
| `/Users/magnus/Desktop/thesisx_svg_components/svg/` | 18 个 SVG 文件（10 页面 + 7 组件 + 1 总览） |
| `/Users/magnus/Desktop/thesisx_svg_components/specs/` | components_manifest.json + page_prompts.md + reconstruction_guide.md |
| `/Users/magnus/.claude/plans/bubbly-tumbling-valiant.md` | 完整 V1-V12 路线图计划文件 |

---

## 6. 主要技术决策

| # | 决策 |
|---|------|
| 1 | V1 先做 AI 论文初稿助手，跑通"课题→初稿→预览→导入"闭环 |
| 2 | Pipeline 为主，不用 CrewAI |
| 3 | 三层抽象：GUI → Orchestration → Agent Nodes → Skills |
| 4 | Protocol 抽象（`PaperPipelineRunner`），不绑定框架 |
| 5 | V1 使用 Agent Team SequentialRunner |
| 6 | ArchitectNode 是前置规划节点（自研，Mock 返回固定大纲，Real 调 OpenAI 兼容 API） |
| 7 | V1 不做自动重写（MAJOR_REVISION/REJECT 时展示问题给用户） |
| 8 | V1 不做 RAG / 证据链 / Zotero |
| 9 | 前端未来功能只能 mock / preview / coming soon |
| 10 | sys.path 不应 insert(0)，应 append 且防重复 |
| 11 | Mock 模式不需要 API Key |
| 12 | Real 模式需要 API Key / base_url / model 前置检查 |
| 13 | 预算控制不能撤回已发生费用，只能阻止后续阶段 |
| 14 | Agent Team import 延迟到运行时，不影响主程序启动 |
| 15 | 增强 topic 拼接格式：配置+大纲+写作边界+原始课题 |
| 16 | 强制保留 `[引用待核查]` / `[数据待补充]` 风险标记 |

---

## 7. 当前运行与测试方式

### 7.1 启动项目

```bash
cd /Volumes/E/ThesisX
.venv/bin/python main.py
```

### 7.2 运行测试

```bash
cd /Volumes/E/ThesisX
.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="
```

注意：`pyproject.toml` 中配置了 `--cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=10`，但 `pytest-cov` 在 Python 3.14 下可能不可用，必须用 `--override-ini="addopts="` 跳过。

当前结果：283 passed in ~2s。

### 7.3 截图验证 UI

```bash
cd /Volumes/E/ThesisX && .venv/bin/python -c "
import sys, os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView  # 必须在 QApplication 之前
app = QApplication(sys.argv)
from app.ui.main_window import MainWindow
win = MainWindow()
win.resize(1400, 900)
pix = win.grab()
pix.save('/tmp/test.png')
"
```

### 7.4 进入 Workspace

启动后默认在 Workspace 模式（`_mode_stack.setCurrentIndex(0)`）。

### 7.5 进入编辑器

菜单 "文件" 打开文件，或从 Workspace 触发 `open_editor` 信号。`_switch_to_editor()` 设置 `_mode_stack.setCurrentIndex(1)` 并显示工具栏。

### 7.6 打开 AI 论文初稿助手

菜单 "工具" → "AI 论文初稿助手..."，或 Workspace 首页 "AI 初稿助手" 按钮。调用 `_show_agent_paper_dialog()`。

### 7.7 Python 环境

- venv 路径：`/Volumes/E/ThesisX/.venv/bin/python`
- Python 版本：3.14
- PyQt6 已安装

---

## 8. 当前风险与技术债

| # | 风险 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | 测试覆盖率低 | 中 | 当前 ~11%，大量 UI 代码未覆盖 |
| 2 | 旧 Dialog 硬编码颜色 | 低 | toolbar.py 中部分 QPushButton 样式用硬编码 hex |
| 3 | Dark mode 一致性 | 低 | 6/11 页面有 Dark 截图验证，其余未验证 |
| 4 | QMessageBox 自动化阻塞 | 低 | 部分 QMessageBox 可能阻塞自动化测试 |
| 5 | Mock 数据只是展示 | 低 | 每页 3-6 条，足够演示但不够真实 |
| 6 | main_window.py 体量 | 中 | 3369 行，模式切换逻辑需持续注意回归 |
| 7 | 编辑器 Agent 面板布局 | 低 | Agent 面板 + PlagiarismPanel 共存于 splitter |
| 8 | SVG 未完全精准对齐 | 低 | 结构性对齐完成，逐组件精准对齐待做 |
| 9 | Runtime 未接入 | 高 | Agent Team 真实链路尚未在 GUI 中跑通 |
| 10 | AgentTeamDialog 真实运行未验证 | 高 | Mock 模式可用，Real 模式是否真跑 Agent Team 需诊断 |

### 8.1 文档表述边界提醒

- “可导航 UI 实现” 不等于 “真实功能已完成”。
- “支持 Real 模式” 不等于 “真实 Agent Team 链路已验证可用”。
- “SVG 对齐度” 仅表示视觉壳接近程度，不代表交互、数据链路、状态机或后端能力已实现。

---

## 9. 推荐给 Codex 的下一步任务

### 第一阶段：上下文接管与代码阅读（不写代码）

1. 阅读本交接文档
2. 阅读计划文件 `/Users/magnus/.claude/plans/bubbly-tumbling-valiant.md`
3. 阅读关键文件：`main_window.py`（_init_ui / _enhance_editor_visuals / _switch_to_editor）、`agent_team_dialog.py`、`design_tokens.py`、`styles.py`
4. 跑测试：`.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="`
5. 启动项目：`.venv/bin/python main.py`
6. 确认 10 页面可导航、V1 Dialog 可打开、编辑器可使用
7. 重新截图保存到项目目录内

### 第二阶段：SVG 精准对齐规划（不急写代码）

1. 逐页对照 SVG（`/Users/magnus/Desktop/thesisx_svg_components/svg/`）
2. 输出页面清单、组件清单、差异清单
3. 按 P0/P1/P2 排序
4. 由用户确认后再修

### 第三阶段：Runtime 诊断（只诊断不重构）

1. 检查 Agent Team 路径配置
2. 检查 `PipelineConfig` / `SequentialRunner` / events 是否可 import
3. 检查当前 `AgentTeamDialog` Mock 模式是否真走 `AgentTeamRunner`
4. 检查 Real 模式的 API Key / base_url / model 前置校验
5. 输出诊断报告，由用户决定下一步

**当前用户倾向**：先继续详细拆分界面，再对齐 SVG 组件。Codex 接手后应优先等待用户选择：
- A. SVG 精准对齐
- B. Runtime 诊断

不要自行决定先做哪个。

---

## 10. 给 Codex 的执行原则

1. **不要把 mock 说成真实功能**。AI Chat / Literature / Version History 等页面是 mock preview，不是真实功能。
2. **不要破坏 V1 AI 论文初稿助手 Dialog**。修改任何文件前先确认不影响 `agent_team_dialog.py`。
3. **不要破坏 WYSIWYG 编辑器**。`PreviewWidget`、`FormattingToolbar`、`MoreToolbar`、所有信号连接不能动。
4. **不要破坏 283 tests**。每次修改后跑测试。
5. **使用 design_tokens.py**。不要新增硬编码颜色。
6. **Mock 数据集中管理**。在 `app/ui/mock/` 下维护，不要分散到页面文件中。
7. **SVG 参照路径**：`/Users/magnus/Desktop/thesisx_svg_components/svg/` 和 `specs/`。
8. **计划文件路径**：`/Users/magnus/.claude/plans/bubbly-tumbling-valiant.md`。
9. **不要自行决定架构变更**。Pipeline 层已有完整实现，不要重写。
10. **截图保存到项目目录内**，不要依赖 `/tmp`。

### 10.1 后续 Codex 执行禁止项

- 不要把 mock 页接成伪真实功能。
- 不要把按钮接到假数据写入 / 假历史 / 假回滚。
- 不要在 SVG 对齐轮中顺手做 Runtime、CLI、RAG、Zotero、Git 版本控制。
- 不要为追 SVG 改坏 `PreviewWidget`、`FormattingToolbar`、`MoreToolbar`。
- 不要打印 API Key。
- 不要跳过测试。
- 不要把“可导航 UI”描述成“真实功能已完成”。
