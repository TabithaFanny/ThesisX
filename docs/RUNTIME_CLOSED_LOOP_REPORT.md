# Vision 2.x — Runtime 最小闭环就绪报告

> **原《Vision 3.0 — 最终可用 Beta 发布报告》已作废。**
> 原报告对产品状态的描述过于乐观。本文档为修正版本。

**日期：** 2026-05-03
**版本：** ThesisX v2.x Runtime Beta（不等于完整产品 Beta）
**分支：** main（14 commits ahead of origin/main）
**测试：** 401/401 passed

---

## 一、版本定性（最重要的一节）

**当前版本的真实定位：Runtime 最小闭环就绪，不是完整论文 AI 工作台。**

"Runtime 最小闭环"意味着：
- AI 生成链路的前置条件（配置、session、记录、诊断）已经打通
- 用户可以跑一次完整的"课题 → 初稿"流程
- 历史记录和诊断有了基础设施

但它不等于：
- 用户可以用它完成真实论文写作工作
- 知识库、文献管理、理论匹配等核心论文工作流已就绪
- 产品达到"用户拿到就能用"的完整度

**为什么不能叫 "Vision 3.0 Beta"：**

真正 Vision 3.0 的标志是"知识库 + 理论匹配 + 文献管理 + 写作闭环 + 导出 + 历史完整"全部落地。现在这些核心模块要么是 preview，要么是计划中。把当前状态称为 3.0 会给后续 agent 和用户造成错误预期。

---

## 二、已完成内容

### 已完成（Runtime 最小闭环）

| 模块 | 文件 | 状态 |
|------|------|------|
| Main Editor | `app/ui/main_window.py` | 真实可用，WYSIWYG，格式工具栏，大纲，预览 |
| Workspace 导航 | `app/ui/pages/workspace.py` + `sidebar_nav.py` | 10 个页面可导航 |
| AgentTeamDialog | `app/ui/agent_team_dialog.py` | 三阶段 UI，Mock+Real 双入口 |
| Mock 模式 | `AgentTeamRunner` | 稳定可演示，每次产出完整 session |
| Real 最小验证 | DeepSeek `deepseek-chat` via `tui_runner` | 一次端到端成功（939 events，¥0.05） |
| SessionStore | `app/core/pipeline/session_store.py` | 持久化到 `~/.wenbiao/runs/<session_id>/` |
| RunHistoryReader | `app/core/pipeline/run_history.py` | 统一扫描所有本地 run |
| RunHistoryPage | `app/ui/pages/run_history_page.py` | 三面板 UI，paper.md/Events/诊断报告 |
| RunDiagnostics | `app/core/pipeline/run_diagnostics.py` | 读 run 并输出健康报告 |
| SkillLoader | `app/core/skills/loader.py` | 纯 stdlib，已加载 2 个本地 skill |
| Config 链路 | `app/core/config.py` | Env > Config > Defaults 统一 |
| Provider 健康检查 | `app/core/providers/detector.py` | `generate_provider_health_report()` |
| CLI 诊断入口 | `scripts/diagnose_runs.py` | 读 run，输出 Markdown/JSON 报告 |
| 测试 | `tests/` | 401/401 passed |

### 完成质量说明

- **Mock 模式**：稳定，每次生成完整 `paper.md` 和 events，可在无网络环境演示
- **Real 模式**：验证了 `DEEPSEEK_API_KEY` 优先级链路能通，但仅验证了单次成功，未验证稳定性
- **SessionStore**：所有 run 数据已持久化，包括 `paper.md`、`events.jsonl`、`messages/`、`metadata.json`、`context_files/`
- **SkillLoader**：已加载 `academic-polish.json`（editing）和 `logic-review.json`（review），并注入到 `selected_skills.md`

---

## 三、未完成内容

以下模块**不是本版本范围**，明确列出以便后续规划：

### 核心论文工作流缺失

| 模块 | 当前状态 | 计划版本 |
|------|----------|----------|
| Knowledge Base 数据层 | 页面有，UI 有，无真实数据接入 | Vision 3.1 |
| RAG 知识库检索 | 未实现 | Vision 3.5 |
| Theory Matcher | 只有数据结构，无 UI，无匹配逻辑 | Vision 3.3 |
| Literature Management | preview/coming soon，Zotero 未接 | Vision 3.2 |
| Evidence Pack / 证据包 | 未实现 | Vision 3.4 |
| Zotero 连接器 | 计划中 | Vision 3.7 |
| Obsidian 连接器 | 计划中 | Vision 3.7 |

### Skill 系统不完整

| 模块 | 当前状态 | 计划版本 |
|------|----------|----------|
| SkillLoader Runtime | 已完成，注入 `selected_skills.md` | — |
| Skill Library 页面 UI | preview，只显示 coming soon | Vision 3.8 |
| Skill 与任务绑定 UI | 未实现 | Vision 3.8 |
| Skill 影响 prompt 质量 | 仅文件注入，无 UI 控制 | Vision 3.8 |

### 写作与编辑器闭环不完整

| 模块 | 当前状态 | 计划版本 |
|------|----------|----------|
| AI 生成结果 → paper.md | 已完成，可查看文本 | — |
| 结构化插入 Main Editor | 未实现（只有"打开到编辑器"，复制全文） | Vision 3.6 |
| 局部文本交给 AI 改写 | 未实现 | Vision 3.6 |
| docx 导出 | 无充分验收 | Vision 3.9 |
| 论文版本历史 | mock/preview | Vision 3.6 |

### Provider 前端不完整

| 模块 | 当前状态 | 计划版本 |
|------|----------|----------|
| Provider 配置链路 | 底层已通（Config 层） | — |
| Provider 页面 UI | Settings 部分字段为 preview | Vision 3.x |
| Local CLI Provider 自动发现 | 无 UI，只在 `detector.py` 有逻辑 | Vision 3.x |
| 多 provider profile 切换 | 未实现 | Vision 3.x |

### 工程交付缺失

| 项目 | 当前状态 |
|------|----------|
| Git push | 凭证问题，需人工处理 |
| Release tag | 未打 |
| USER_GUIDE.md | 缺失 |
| 隐私说明 | 缺失 |
| pipeline_v2 真执行 | 当前是 dry-run，只走 tui_runner |

---

## 四、测试与验证说明

### 401 tests passed 证明什么

- 代码逻辑正确（配置合并、session 持久化、诊断读取、UI 组件）
- 不证明用户流程完整
- 不证明 GUI 可用性（PyQt 测试有限）
- 不证明 Real 模式稳定（只跑了一次）

### Real 模式验证说明

**验证时间：** 2026-05-02 01:16
**路径：** Candidate 4（tui_runner），非 pipeline_v2
**结果：** 单次成功，939 events，¥0.05

这证明：
- `DEEPSEEK_API_KEY` 优先级链路已通
- `get_agent_team_config()` 底层逻辑正确
- tui_runner 契约可执行

不能证明：
- 多次不同 topic 稳定
- 不同模型/预算/网络条件下稳定
- pipeline_v2 真执行可用
- 失败重试、取消、错误恢复正确

---

## 五、与原 Vision 3.0 报告的差异

原报告问题：

1. **标题过于乐观**："最终可用 Beta" 暗示完整产品，实际上只有 Runtime 最小闭环
2. **12 条标准覆盖不全面**：验证的是"能跑"，不是"能用"
3. **Real 模式验证过度解读**：一次成功被描述为"Real 链路打通"，实际只是最小验证
4. **未列出 pipeline_v2 dry-run 限制**：当前 Real 走的是 tui_runner，不是新主线
5. **未充分说明核心功能缺失**：Knowledge Base、RAG、Theory Matcher、Zotero、Obsidian 均未提
6. **Git push 失败未充分说明风险**：代码在本地，远程无备份

---

## 六、当前版本的准确名称

**建议命名为：** `ThesisX v2.x — Runtime Beta`（或 `v2.8 Runtime Beta`）

原因：
- 2.x 意味着它是从 2.x 向 3.0 过渡状态
- Runtime Beta 明确说明这是 Runtime 闭环，不是完整产品
- 给后续 agent 和用户正确的预期

---

## 七、给下一步 agent 的交接说明

1. **不要把 Runtime 闭环当成完整产品交付**
2. **下一阶段的真正重心是 Knowledge Base**，不是继续优化 Runtime 或 UI
3. **所有 preview/coming soon 页面不要接伪真实数据**，等数据层到位
4. **pipeline_v2 真执行和 tui_runner 是两条路径**，需要明确哪个是长期主线
5. **USER_GUIDE.md 是发布前提**，当前缺失

---

*本报告生成时间：2026-05-03*
*基于：CODEX_HANDOFF.md、VISION_3_0_BETA_RELEASE_REPORT.md、当前代码状态*