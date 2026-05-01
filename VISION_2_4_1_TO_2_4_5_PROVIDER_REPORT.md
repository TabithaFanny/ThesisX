# Vision 2.4.1-2.4.5 Provider 配置体系实现报告

> 执行时间：2026-05-01
> 执行范围：Vision 2.4.1 → 2.4.5（连续自动）
> 最终测试：347 passed

---

## 1. 修改/新增文件

### 新增

| 文件 | 行数 | 职责 |
|------|------|------|
| `app/core/providers/__init__.py` | 28 | 包初始化 + 导出 |
| `app/core/providers/models.py` | 115 | 6 个数据模型：ProviderKind, LocalCLIProvider, RemoteAPIProvider, AgentTeamProvider, RuntimeProfile, ProviderHealthStatus, ProviderHealthReport |
| `app/core/providers/detector.py` | 285 | 发现引擎：`discover_local_clis()`, `detect_remote_api_config()`, `detect_agent_team_paths()`, `generate_provider_health_report()` |
| `tests/unit/test_provider_detector.py` | 143 | 16 个测试覆盖全部检测和健康检查路径 |

### 修改

| 文件 | 改动 | 说明 |
|------|------|------|
| `app/core/config.py` | +26 行 | 新增 `load_providers()` / `save_providers()`（原子写入） |
| `scripts/diagnose_runs.py` | +140 行 | 新增 6 个命令：--providers, --discover-local, --check-api, --detect-agent-teams, --health, --save-providers |

---

## 2. providers.json 最终结构

`~/.wenbiao/providers.json` 已写入：

```json
{
  "version": 1,
  "local_clis": [...5 entries...],       // codex, claude, opencode, openclaw, hermes
  "remote_api_providers": [...4 entries...], // openai, deepseek, openrouter, localhost
  "agent_teams": [...4 entries...],         // candidate-1~4
  "runtime_profiles": [...1 entry...]       // default-mock
}
```

- 无明文 API key（存储 `api_key_source` 引用）
- 原子写入（temp file + os.replace）

---

## 3. 检测到的本地 CLI

| CLI | 状态 | 路径 | 版本 |
|-----|------|------|------|
| codex | ✓ | `~/.nvm/.../bin/codex` | codex-cli 0.125.0 |
| claude | ✓ | `/Applications/cmux.app/.../bin/claude` | 2.1.63 (Claude Code) |
| opencode | ✗ | not found | — |
| openclaw | ✓ | `~/.nvm/.../bin/openclaw` | 2026.2.25 |
| hermes | ✓ | `~/.local/bin/hermes` | Hermes Agent v0.8.0 |

4/5 CLIs available. Only OpenCode missing.

---

## 4. 检测到的远程 API profile

| Profile | Base URL | Model | Key | Health |
|---------|----------|-------|-----|--------|
| OpenAI API | https://api.openai.com/v1 | gpt-4o-mini | ✗ | unavailable |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat | ✗ | unavailable |
| OpenRouter | https://openrouter.ai/api/v1 | openai/gpt-4o | ✗ | unavailable |
| Local Ollama | http://localhost:11434/v1 | llama3 | N/A | unknown |

3/4 need API key configuration. localhost doesn't require key.

---

## 5. 检测到的 Agent Team 候选

| Candidate | 路径 | 契约 | 执行模式 |
|-----------|------|------|---------|
| candidate-1 | `/Volumes/E/agent team 2/academic-agent-team/` | pipeline_v2 | dry-run |
| candidate-2 | `/Volumes/E/agent team 2/academic-agent-team-work/` | pipeline_function | dry-run |
| candidate-3 | `~/.codex_work/agent-team-2/academic-agent-team/` | unsupported | broken |
| candidate-4 | `/Volumes/E/agent team 2/wt-1488343317639991428/` | tui_runner | **real** |

**仅 candidate-4 支持真实执行。**

---

## 6. Provider Health 报告

路径：
- `/Users/magnus/.wenbiao/runs/_diagnostics/provider_health.md`
- `/Users/magnus/.wenbiao/runs/_diagnostics/provider_health.json`

摘要：
```
本地 CLI: 4 ready, 1 issues — codex(✓), claude(✓), opencode(✗), openclaw(✓), hermes(✓)
远程 API: 1 ready, 3 issues — openai(✗), deepseek(✗), openrouter(✗), localhost(✓)
Agent Team: 3 ready, 1 issues — candidate-1(✓), candidate-2(✓), candidate-3(✗), candidate-4(✓)
```

---

## 7. 所有新增命令

```bash
.venv/bin/python scripts/diagnose_runs.py --providers          # 全部 provider 扫描
.venv/bin/python scripts/diagnose_runs.py --discover-local      # 本地 CLI 发现
.venv/bin/python scripts/diagnose_runs.py --check-api           # 远程 API 检测
.venv/bin/python scripts/diagnose_runs.py --detect-agent-teams  # Agent Team 检测
.venv/bin/python scripts/diagnose_runs.py --health              # 健康聚合报告
```

---

## 8. 测试结果

| 测试文件 | 数量 | 结果 |
|---------|------|------|
| tests/unit/test_provider_detector.py | 16 | ✓ all passed |
| 全量测试 | **347** | ✓ all passed |

---

## 9. 是否仍未进入 Vision 2.5？

**是。Vision 2.5（Real Agent Team 最小可验证）尚未执行。**

当前所有操作均为：
- 只读检测（shutil.which, Path.exists, urlparse）
- 新文件写入（providers.json, health reports）
- 无 API 调用
- 无 Agent Team import
- 无 Main Editor / AgentTeamDialog UI 修改

---

## 10. 下一步是否可以进入 Real Agent Team 最小可验证？

**技术上可以，但需要用户确认：**

### 前置条件（已满足）：
- ✓ Provider 检测系统完整（本次实现）
- ✓ providers.json 持久化（本次实现）
- ✓ 健康检查分层（本次实现）
- ✓ pipeline_v2 dry-run 适配（Vision 2.3）
- ✓ 统一配置链路（Vision 2.4）
- ✓ 本地 Agent Team 契约检测（Candidate 4 = tui_runner, real-ready）
- ✓ 347 tests passing

### 需要用户提供/确认：
1. API Key —— 当前 OPENAI_API_KEY 未设置
2. Agent Team 路径 —— Candidate 4 可用于真实执行，但需要确认
3. 是否接受 API 费用
4. 是否先测试 dry-run（Candidate 1, pipeline_v2）再切 real（Candidate 4, tui_runner）

### 建议的最小路径：
1. 用户设置 `OPENAI_API_KEY` 环境变量
2. 跑 `diagnose_runs.py --health` 确认配置就绪
3. Vision 2.5：以 Candidate 1 + pipeline_v2 + dry-run 模式生成一篇 mock 论文，验证端到端事件流
4. 如果 dry-run 正常，切 Candidate 4 + tui_runner + real 模式发出最少 API 调用
