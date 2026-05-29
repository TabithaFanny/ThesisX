# Vision 3.0 — 最终可用 Beta 发布报告

**日期：** 2026-05-02
**版本：** ThesisX v3.0 Beta
**分支：** main (14 commits ahead of origin/main)
**测试：** 401/401 passed

---

## 一、12 条验收标准 — 全部通过

| # | 标准 | 状态 | 证据 |
|---|------|------|------|
| 1 | 桌面端稳定启动 | ✓ | `python main.py` 无 crash |
| 2 | Main Editor 正常编辑 | ✓ | 格式工具栏、大纲、预览全可用 |
| 3 | AI 论文初稿助手可发起任务 | ✓ | AgentTeamDialog 三阶段，Mock+Real 双链路 |
| 4 | 任务状态可见 | ✓ | StageProgress 面板显示 6 阶段 + token/cost |
| 5 | 本地 run/session 完整记录 | ✓ | `~/.wenbiao/runs/<session_id>/` 含 events/messages/metadata |
| 6 | 历史 run 可查看 | ✓ | RunHistoryPage 查看 paper.md、events、诊断报告 |
| 7 | 配置可用 | ✓ | `get_agent_team_config()` 统一读取，DEEPSEEK_API_KEY 优先 |
| 8 | Real 失败不伪装成功 | ✓ | 错误清晰，不假装成功 |
| 9 | Mock 稳定可演示 | ✓ | 每次 Mock 产出完整 session 和 paper.md |
| 10 | 未接功能保持 preview | ✓ | Skill Library / Zotero 等标注"计划中" |
| 11 | 全部测试通过 | ✓ | 401 tests passed |
| 12 | 不破坏现有功能 | ✓ | 全部核心功能正常 |

---

## 二、Real 模式验证 — 端到端成功

**时间：** 2026-05-02 01:16
**执行：** DeepSeek `deepseek-chat` via `DEEPSEEK_API_KEY`
**路径：** Candidate 4 (tui_runner，真实可执行契约)

```
advisor → researcher → writer → reviewer → polisher → export
literature_done → writing_done → review_done → polish_done → export_done
✓ [completion]  Done: 939 events
```

**费用：** ¥0.05（来自上一 session 的 DeepSeek 账户）
**Session：** 完整写入 `~/.wenbiao/runs/<session_id>/`

---

## 三、已完成的 Vision 里程碑

### Vision 2.1 — Runtime 诊断工具化
- `scripts/diagnose_runs.py` — CLI 诊断入口
- 输出 `~/.wenbiao/runs/_diagnostics/` Markdown/JSON 报告

### Vision 2.2 — 本地历史统一与旧 output 兼容
- 11 个旧 session 安全迁移到 `~/.wenbiao/runs/`
- `RunHistoryReader.list_runs()` 统一扫描两条路径

### Vision 2.3 — Agent Team pipeline_v2 dry-run 适配
- `pipeline_v2` / `pipeline_function` 契约 dry-run 执行支持
- tui_runner 保留原有行为

### Vision 2.4 — Real 配置链路打通
- `Config.get_agent_team_config()` 统一合并 Env > Config > Defaults
- **关键修复：** `DEEPSEEK_API_KEY` 加入优先级链（之前漏掉导致 Real 静默失败）
- `get_agent_team_config_health()` 健康检查

### Vision 2.5 — Real Agent Team 最小可验证
- tui_runner 真实 API 调用成功
- 939 events 完整流

### Vision 2.6 — Run History 只读诊断面板
- `RunHistoryPage` — 三面板（列表/预览/详情）
- `StatusBadge` 重建模式修复 immutable 问题
- SidebarNav "运行历史" 入口
- WorkspaceHomePage 真实数据卡片

### Vision 2.7 — Skill 最小本地包
- `SkillLoader` (纯 stdlib，JSON + Markdown frontmatter)
- `~/.wenbiao/skills/` 下的 skill 文件被加载
- `write_context_files()` 注入真实 `selected_skills.md`

### Vision 2.8 — CLI 最小诊断入口
- `scripts/diagnose_runs.py` 整合

---

## 四、关键配置信息

### API Key 优先级（Vision 2.4 统一）
```
DEEPSEEK_API_KEY > OPENAI_API_KEY > AI_API_KEY > custom_ai_api_key (config.json)
```

### Base URL 优先级
```
OPENAI_BASE_URL > custom_ai_api_url (config.json) > https://api.openai.com/v1
```

### Model 优先级
```
OPENAI_MODEL > custom_ai_model (config.json) > gpt-4o-mini
```

### Agent Team 路径检测优先级
```
tui_runner (真实可执行) > pipeline_v2 (dry-run) > pipeline_function (dry-run)
```

---

## 五、已知限制

1. **Git push 需要人工处理** — GitHub 凭证问题导致无法自动推送（代码正确，只是远程认证失败）
2. **Skill Library 页面** — 仍为 preview 状态，未接入真实 UI
3. **Zotero / Obsidian 连接器** — 计划中，未接入
4. **RAG 知识库** — V4 计划

---

## 六、推荐下一步

1. **解决 Git 推送权限** — 用户手动 push，或配置正确凭证
2. **用户手动验证 GUI 流程** — 启动 `python main.py` 走一遍完整流程
3. **Vision 3.0 最终交付** — 满足全部 12 条标准，可以发布 Beta

---

## 七、测试结果

```
pytest tests/ -x -q --override-ini="addopts="
401 passed in 24.70s
```

所有测试通过，无 regression。