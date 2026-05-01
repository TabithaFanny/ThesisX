# ThesisX Vision 2.1 → 2.4 连续执行完成报告

> 执行时间：2026-05-01
> 执行范围：Vision 2.1 ~ 2.4（连续自动）
> 最终测试：331 passed

---

## 总体摘要

| Vision | 名称 | 状态 | 新建文件 | 修改文件 | 新增测试 |
|--------|------|------|---------|---------|---------|
| 2.1 | Runtime 诊断工具化 | ✓ 完成 | `scripts/diagnose_runs.py` | 无 | 0 |
| 2.2 | 本地历史统一与旧 output 兼容 | ✓ 完成 | `scripts/migrate_sessions.py` | 无 | 0 |
| 2.3 | Agent Team pipeline_v2 dry-run 适配 | ✓ 完成 | `tests/unit/test_pipeline_v2_dry_run.py` | `agent_team_compat_adapter.py`, `agent_team_runner.py` | 7 |
| 2.4 | Real 配置链路打通 | ✓ 完成 | `tests/unit/test_config_unified.py`, `docs/CONFIG_GUIDE.md` | `config.py`, `agent_team_bridge.py`, `agent_team_dialog.py` | 10 |

**测试结果：331 passed (314 基线 + 17 新增)**

---

## Vision 2.1 产出

### 新建
- `scripts/diagnose_runs.py` — CLI 诊断入口

### 成果
- 扫描 `~/.wenbiao/output/` 下 11 个旧 session 并输出诊断报告
- 生成 `~/.wenbiao/runs/_diagnostics/` 下 22 个报告文件（每 session .md + .json + latest.md + latest.json）
- 检测 4 个外部 Agent Team 候选路径的契约类型
- 关键发现：Candidate 4 (wt-*) 仍保留 `tui_runner` 契约

---

## Vision 2.2 产出

### 新建
- `scripts/migrate_sessions.py` — 旧 output → 新 runs 迁移脚本

### 成果
- 11 个旧 session 全部迁移到 `~/.wenbiao/runs/` 下
- 每个新目录含：request.json, metadata.json, output/, context/, artifacts/
- 旧 `~/.wenbiao/output/` 原封不动
- 5 个 session 的 metadata.json 为自动生成（原无此文件）

---

## Vision 2.3 产出

### 修改
- `app/core/pipeline/agent_team_compat_adapter.py`：
  - `run_external_agent_team()` 新增 `pipeline_v2` 和 `pipeline_function` 路由
  - 新增 `_run_pipeline_v2_dry()` — pipeline_v2 6 阶段 dry-run
  - 新增 `_run_pipeline_function_dry()` — pipeline_function 5 阶段 dry-run
- `app/core/pipeline/agent_team_runner.py`：
  - 新增 `compat_dry_run` 标记检测
  - 新增 dry-run 模式下自动生成 mock paper.md 逻辑

### 新建
- `tests/unit/test_pipeline_v2_dry_run.py` — 7 个测试覆盖

### 成果
- `pipeline_v2` 和 `pipeline_function` 契约不再返回"不支持"错误
- Dry-run 产生完整 PaperEvent 流（state + message + cost + completion）
- Dry-run + Runner 组合产生完整 `runs/<session>/` 记录（含 paper.md）
- 不 import 外部模块，不发真实 API
- 不修改 Mock 模式行为
- 不修改 tui_runner 路径

---

## Vision 2.4 产出

### 修改
- `app/core/config.py`：
  - 新增 `get_agent_team_config()` — 统一配置读取（ENV > config.json > 默认值）
  - 新增 `get_agent_team_config_health()` — 只读配置健康检查
- `app/core/pipeline/agent_team_bridge.py`：
  - `sync_api_keys()` 接受 Config 对象，通过 `get_agent_team_config()` 读取
  - 保持旧路径兼容（无 Config 时回退到 env）
- `app/ui/agent_team_dialog.py`：
  - 配置页新增"检测配置"按钮
  - 新增 `_test_configuration()` 方法

### 新建
- `tests/unit/test_config_unified.py` — 10 个测试覆盖
- `docs/CONFIG_GUIDE.md` — 用户配置指南

### 成果
- 配置读取优先级明确：ENV > config.json > defaults
- "检测配置"按钮在对话框中可用，输出友好的配置诊断
- 不破坏 Mock 模式
- 不破坏 AgentTeamDialog 三阶段结构
- 不破坏 `custom_ai_*` 向后兼容字段
- 不发真实 API

---

## 禁止项遵守情况

| # | 禁止项 | 状态 |
|---|--------|------|
| 1 | 不要继续 SVG 精修 | ✓ 遵守 |
| 2 | 不要改 Main Editor | ✓ 遵守 |
| 3 | 不要破坏 AgentTeamDialog 三阶段结构 | ✓ 遵守（仅新增按钮） |
| 4 | 不要发真实 API 请求 | ✓ 遵守 |
| 5 | 不要修改外部 Agent Team 仓库 | ✓ 遵守 |
| 6 | 不要删除或覆盖 ~/.wenbiao/output/ | ✓ 遵守 |
| 7 | 不要接 RAG / Zotero / Git | ✓ 遵守 |
| 8 | 不要新增 Runtime Server | ✓ 遵守 |
| 9 | 不要把 dry-run 说成 Real | ✓ 遵守 |
| 10 | 不要跳过测试 | ✓ 遵守 |

---

## 下一步

Vision 2.4 已完成。根据 Vision Roadmap，**此处停止**。下一阶段是 Vision 2.5（Real Agent Team 最小可验证），需要用户确认：
1. 提供有效的 API Key
2. 确认 Agent Team 路径（Candidate 1 或 Candidate 4）
3. 同意承担 API 费用
