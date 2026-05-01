# MULTICA / ccswitch 配置体系借鉴报告 + ThesisX Provider 配置方案

> 生成时间：2026-05-01
> 基于：MULTICA 源码审计 + ccswitch 文档审计 + ThesisX Vision 2.1→2.4 现状
> ccswitch 本机未安装。审计基于 https://github.com/farion1231/cc-switch 文档。

---

## 一、MULTICA 配置体系审计

### 1.1 核心发现

| 维度 | 实现方式 |
|------|---------|
| **CLI 发现** | `exec.LookPath()` 扫描 PATH 找 `claude`/`codex`/`opencode`/`openclaw`/`hermes` |
| **自定义路径** | 环境变量 `MULTICA_CLAUDE_PATH` / `MULTICA_CODEX_PATH` 等 |
| **版本检测** | `agent.DetectVersion()` 调 `execPath --version` |
| **Provider 抽象** | `Backend` 接口 (Execute → Session{Messages, Result})，每个 CLI 独立 struct |
| **配置存储** | `~/.multica/config.json`，profiled 版本用 `~/.multica/profiles/<name>/config.json` |
| **配置项** | `server_url`, `app_url`, `workspace_id`, `token`, `watched_workspaces` |
| **优先级** | CLI flag > 环境变量 > 默认值 |
| **Agent Entry** | `{Path, Model}` 结构体，存 daemon config 中 |
| **Profile** | 独立 config 目录 + 独立 workspace root + 独立 health port |
| **执行隔离** | 每任务独立 `workspaces_root/<ws_id>/<task_id>/workdir/` + 独立 CODEX_HOME |
| **Env 管理** | 过滤父 env 中的 agent 特定变量 (CLAUDECODE, CLAUDECODE_*) 后合并 |
| **原子写入** | Temp file + Rename，`0600` 权限 |

### 1.2 适不适合 ThesisX 借鉴？

| 借鉴点 | 适用度 | 说明 |
|--------|--------|------|
| `exec.LookPath()` 自动检测 CLI | **高** | ThesisX 应能自动发现 `codex`/`claude`/`academic_agent_team` |
| Provider Backend 接口抽象 | **高** | ThesisX 已有 `PaperPipelineRunner` Protocol，可扩展为 Provider 层 |
| Profile 目录结构 | **中** | `~/.wenbiao/providers/<name>/` 模式可借鉴 |
| 原子写入 | **中** | Config 写入安全可借鉴 temp+rename 模式 |
| 环境变量优先级 | **已实现** | Vision 2.4 已做 ENV > config.json > 默认值 |
| Daemon/Server/DB 全套 | **太重** | ThesisX 是桌面 App，不需要 daemon 长驻进程 |
| WebSocket/任务队列 | **太重** | ThesisX 不需要分布式任务调度 |
| Workspace agent 注册 | **不适用** | ThesisX 不是多租户平台 |

---

## 二、ccswitch 配置体系审计

### 2.1 核心发现

ccswitch 是一个 Tauri 2 桌面应用（前端 React + 后端 Rust），统一管理 Claude Code / Codex / Gemini CLI / OpenCode / OpenClaw 五个 CLI 工具的配置。

| 维度 | 实现方式 |
|------|---------|
| **Provider 存储** | SQLite `~/.cc-switch/cc-switch.db`（providers, MCP, prompts, skills） |
| **本地设置** | `~/.cc-switch/settings.json`（device-level UI 偏好） |
| **预设** | 50+ 内置 provider 预设（AWS Bedrock, NVIDIA NIM, 社区 relay 等） |
| **切换方式** | 主界面选择 + 系统托盘点击 |
| **本地代理** | 本地 proxy 层做格式转换、故障转移、熔断器、健康监测 |
| **健康检查** | Stream Check 面板覆盖全部 5 个应用，支持延迟测试 |
| **API Key** | 编辑页支持修改、回填机制 |
| **环境变量** | 有冲突检测专门文档 `5.4-env-conflict.md` |
| **云同步** | Dropbox / OneDrive / iCloud / WebDAV |
| **设计哲学** | 最小侵入：卸载后 CLI 工具仍可用（始终保持一个活跃配置） |

### 2.2 适不适合 ThesisX 借鉴？

| 借鉴点 | 适用度 | 说明 |
|--------|--------|------|
| 多 Provider Profile 管理 | **高** | ThesisX 需要"远程 API"和"本地 Agent Team"两种 profile |
| 50+ 预设转为最少配置 | **中** | ThesisX 可做少量内置 preset（OpenAI, DeepSeek, localhost） |
| 健康检查/可用性检测 | **高** | ThesisX 需要不发 API 的配置校验 + 发 API 的模型可用性检测 |
| 环境变量冲突处理 | **高** | 当前 `get_agent_team_config()` 有优先级但无冲突检测 |
| 一键切换 profile | **中** | UI 层面后续支持 |
| 本地 proxy | **重/不适用** | ThesisX 不需要中间人代理 |
| SQLite 数据库 | **重** | ThesisX 有 JSON 文件即够，无需引入 SQLite |
| 云同步 | **不适用** | 当前阶段不做 |
| 5 CLI 全覆盖 | **参考** | ThesisX 可从 2-3 个起 |

---

## 三、ThesisX 当前配置差距分析

### 3.1 当前支持哪些配置？

| 配置项 | 来源 | 当前状态 |
|--------|------|---------|
| `agent_team_path` | config.json | ✓ 单一路径 |
| `api_key` | ENV OPENAI_API_KEY / AI_API_KEY / config.custom_ai_api_key | ✓ Vision 2.4 已统一 |
| `base_url` | ENV OPENAI_BASE_URL / config.custom_ai_api_url | ✓ |
| `model` | ENV OPENAI_MODEL / config.custom_ai_model | ✓ |
| `default_journal` | config.json | ✓ |
| `default_mode` | config.json | ✓ |
| `default_budget_cny` | config.json | ✓ |
| 多 profile | — | ✗ 无 |
| 本地 CLI 检测 | — | ✗ 无 |
| 远程 API provider | — | ✗ 单一 base_url |
| Provider 健康检查 | — | ✗ `_test_configuration()` 只是路径+key 检查 |

### 3.2 差距清单

| # | 差距 | 严重度 |
|---|------|--------|
| 1 | 无法区分"本地 CLI provider"和"远程 API provider" | 高 |
| 2 | 无法自动发现 `codex`/`claude`/`academic_agent_team` | 高 |
| 3 | 无法保存多个 API profile（如 OpenAI + DeepSeek） | 中 |
| 4 | 无法做 provider 级别的健康检查 | 中 |
| 5 | 无法告诉用户"你缺的是 CLI、路径、API key、base_url、model 还是契约不兼容" | 中 |
| 6 | 配置优先级已合理（ENV > config > default），但无冲突检测 | 低 |
| 7 | `_test_configuration()` 能检测路径和 key，但不能检测 agent CLI 是否可用 | 低 |

---

## 四、ThesisX Provider / Model / Agent 配置体系方案

### 4.1 配置对象设计

```python
# ── Provider 类型枚举 ──
class ProviderKind(Enum):
    LOCAL_CLI = "local_cli"         # codex, claude, opencode 等
    REMOTE_API = "remote_api"       # OpenAI, DeepSeek, OpenRouter 等
    AGENT_TEAM = "agent_team"       # academic_agent_team（多 agent 编排）

# ── Local CLI Provider ──
@dataclass
class LocalCLIProvider:
    kind: ProviderKind = ProviderKind.LOCAL_CLI
    name: str                       # "codex", "claude", "opencode"
    display_name: str               # "Codex CLI", "Claude Code"
    executable_path: str            # /usr/local/bin/codex 或自动发现
    version: str                    # "--version" 输出
    available: bool                 # LookPath 结果
    model_override: str             # 环境变量覆盖模型名
    env_vars: dict[str, str]        # 额外环境变量

# ── Remote API Provider ──
@dataclass
class RemoteAPIProvider:
    kind: ProviderKind = ProviderKind.REMOTE_API
    name: str                       # "openai", "deepseek", "openrouter"
    display_name: str               # "OpenAI API", "DeepSeek"
    api_key: str                    # 从 env/config 合并
    base_url: str                   # https://api.openai.com/v1
    model: str                      # gpt-4o
    extra_models: list[str]         # 可选模型列表
    api_key_configured: bool        # 是否有 key
    health_status: str              # "unknown" / "ok" / "unavailable"

# ── Agent Team Provider ──
@dataclass
class AgentTeamProvider:
    kind: ProviderKind = ProviderKind.AGENT_TEAM
    name: str                       # "candidate-1", "candidate-4"
    display_name: str               # "Academic Agent Team (pipeline_v2)"
    root_path: str                  # /Volumes/E/agent team 2/academic-agent-team/
    contract_type: str              # "tui_runner" / "pipeline_v2" / "pipeline_function"
    contract_supported: bool        # CompatAdapter 检测结果
    execution_mode: str             # "dry-run" / "real" / "unsupported"
    needs_api_key: bool             # Real 模式需要
    health_status: str              # "ok" / "dry_run_only" / "broken"

# ── Model Profile ──
@dataclass
class ModelProfile:
    model_id: str                   # "gpt-4o"
    display_name: str               # "GPT-4o"
    provider_name: str              # 属于哪个 RemoteAPIProvider
    context_window: int             # 128000
    max_output_tokens: int          # 16384

# ── Runtime Profile ──
@dataclass
class RuntimeProfile:
    """组合一个 Provider + 一个 Model + 运行参数"""
    name: str                       # "openai-gpt4o", "local-codex"
    provider: str                   # provider name
    model: str                      # model_id
    budget_cap_cny: float           # 10.0
    journal: str                    # "中文核心"
    run_mode: str                   # "mock" / "dry-run" / "real"

# ── 健康状态 ──
@dataclass
class ProviderHealthStatus:
    provider_name: str
    ok: bool
    issues: list[str]               # 阻断性问题
    warnings: list[str]             # 警告
    checks: dict[str, bool]         # path_exists, executable, api_key_set, etc.
    dry_run_only: bool              # 只能 dry-run
```

### 4.2 配置来源优先级

```
远程 API Provider 的 api_key:
  ENV OPENAI_API_KEY   (最高)
  → ENV AI_API_KEY
  → config.json custom_ai_api_key
  → providers.json provider.api_key
  → 空字符串 (最低，表示未配置)

远程 API Provider 的 base_url:
  ENV OPENAI_BASE_URL  (最高)
  → config.json custom_ai_api_url
  → providers.json provider.base_url
  → "https://api.openai.com/v1" (默认)

远程 API Provider 的 model:
  ENV OPENAI_MODEL     (最高)
  → config.json custom_ai_model
  → providers.json provider.default_model
  → "gpt-4o-mini" (默认)

本地 CLI 的 executable_path:
  ENV THESISX_CODEX_PATH / MULTICA_CODEX_PATH  (最高)
  → providers.json provider.executable_path
  → exec.LookPath("codex") / LookPath("claude") (自动检测)

Agent Team 的 root_path:
  config.json agent_team_path  (最高)
  → providers.json provider.root_path
  → 自动发现候选目录 (最低)
```

### 4.3 本地 CLI Provider 设计

参考 MULTICA 的 `exec.LookPath()` + `DetectVersion()` 模式：

```python
# app/core/providers/local_cli.py

def discover_local_clis() -> list[LocalCLIProvider]:
    """自动发现 PATH 中的 AI CLI 工具，不修改任何配置。"""
    results = []
    for cli_name, env_var, display in [
        ("codex", "CODEX_PATH", "Codex CLI"),
        ("claude", "CLAUDE_PATH", "Claude Code"),
        ("opencode", "OPENCODE_PATH", "OpenCode"),
        ("openclaw", "OPENCLAW_PATH", "OpenClaw"),
    ]:
        path = shutil.which(os.environ.get(f"THESISX_{env_var}", cli_name))
        provider = LocalCLIProvider(
            name=cli_name,
            display_name=display,
            executable_path=path or "",
            version=detect_version(path) if path else "",
            available=path is not None,
        )
        results.append(provider)
    return results

def detect_version(exec_path: str) -> str:
    """Run `exec_path --version` and return output."""
    try:
        result = subprocess.run([exec_path, "--version"], capture_output=True,
                                text=True, timeout=10)
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return ""
```

检测类型（不发 API）：
- `PATH 可发现` — `shutil.which()` 非空
- `可执行` — `os.access(path, X_OK)`
- `版本已知` — `--version` 返回正常

### 4.4 远程 API Provider 设计

参考 ccswitch 的 provider preset 模式：

预设列表（只做 3-5 个常用）：
```json
{
  "presets": {
    "openai": {
      "display_name": "OpenAI API",
      "base_url": "https://api.openai.com/v1",
      "default_model": "gpt-4o-mini",
      "requires_api_key": true
    },
    "deepseek": {
      "display_name": "DeepSeek",
      "base_url": "https://api.deepseek.com/v1",
      "default_model": "deepseek-chat",
      "requires_api_key": true
    },
    "openrouter": {
      "display_name": "OpenRouter",
      "base_url": "https://openrouter.ai/api/v1",
      "default_model": "openai/gpt-4o",
      "requires_api_key": true
    },
    "localhost": {
      "display_name": "本地 Ollama / vLLM",
      "base_url": "http://localhost:11434/v1",
      "default_model": "llama3",
      "requires_api_key": false
    }
  }
}
```

检测类型：
- **不发 API**：`api_key_configured`（有非空 key）、`base_url 格式合法`（URL parse 成功）
- **发 API（需用户确认）**：`GET {base_url}/models`（验证 key 有效 + endpoint 可达）

### 4.5 Agent Team Provider 设计

```
发现方式：
1. 读取 config.json agent_team_path
2. 扫描已知候选目录（Candidate 1-4）
3. 对每个路径跑 CompatAdapter.validate_agent_team_contract()
4. 输出 contract_type, supported, execution_mode

契约 → 执行模式映射：
  tui_runner        → "real"（可真实执行）
  pipeline_v2       → "dry-run"（事件流通过，不调 API）
  pipeline_function → "dry-run"（同上）
  unsupported       → "broken"
```

### 4.6 UI 最小配置入口设计

当前 AgentTeamDialog 配置页显示：

```
研究课题: [text input]
生成设置: 生成类型 | 目标风格 | 运行模式 | 预算 | 润色
Agent Team 路径: [未选择] [浏览...]
[检测配置]  ← 已在 Vision 2.4 添加
模式信息: ...
合规声明: ...
[关闭] [开始生成]
```

**建议增加（不修改现有结构，在"Agent Team 路径"卡片下增加折叠区域）：**

```
Agent Team 路径: [未选择] [浏览...]
  └─ 检测到: 未设置 (点击"浏览"或输入路径)
  └─ 契约类型: --
  └─ 执行模式: --
  [检测配置]

▼ 高级 Provider 配置 (折叠，默认隐藏)
  Provider 类型: [本地 CLI ▾] [远程 API ▾] [Agent Team ▾]

  远程 API:
    Provider: [OpenAI ▾] [DeepSeek ▾] [自定义]
    Base URL: [https://api.openai.com/v1]
    Model:     [gpt-4o-mini ▾]
    API Key:   [••••••••] (用环境变量 OPENAI_API_KEY)
    [检测 API 可用性]  ← 需用户确认才发请求

  本地 CLI:
    检测到: codex ✓ (/usr/local/bin/codex, v0.37.0)
            claude ✓ (/opt/homebrew/bin/claude, v2.0.0)
            opencode ✗ (未安装)
    [重新检测]
```

不做的：
- 不把 provider 管理做成全功能面板（太多选项会吓到用户）
- 不做系统托盘切换
- 不做云同步
- 不做 MCP 面板

### 4.7 本地配置文件结构

新建 `~/.wenbiao/providers.json`：

```json
{
  "version": 1,
  "default_provider": "agent-team-candidate-1",
  "last_health_check": "2026-05-01T23:00:00Z",
  "local_clis": [
    {
      "name": "codex",
      "display_name": "Codex CLI",
      "executable_path": "/opt/homebrew/bin/codex",
      "version": "0.37.0",
      "available": true,
      "model_override": "",
      "env_vars": {},
      "last_detected": "2026-05-01T23:00:00Z"
    },
    {
      "name": "claude",
      "display_name": "Claude Code",
      "executable_path": "",
      "version": "",
      "available": false,
      "model_override": "",
      "env_vars": {},
      "last_detected": "2026-05-01T23:00:00Z"
    }
  ],
  "remote_api_providers": [
    {
      "name": "openai",
      "display_name": "OpenAI API",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4o-mini",
      "api_key_source": "env:OPENAI_API_KEY",
      "health_status": "unknown",
      "last_health_check": null
    },
    {
      "name": "deepseek",
      "display_name": "DeepSeek",
      "base_url": "https://api.deepseek.com/v1",
      "model": "deepseek-chat",
      "api_key_source": "env:DEEPSEEK_API_KEY",
      "health_status": "unknown",
      "last_health_check": null
    }
  ],
  "agent_teams": [
    {
      "name": "candidate-1",
      "display_name": "Academic Agent Team (pipeline_v2)",
      "root_path": "/Volumes/E/agent team 2/academic-agent-team/",
      "contract_type": "pipeline_v2",
      "contract_supported": true,
      "execution_mode": "dry-run",
      "health_status": "dry_run_only",
      "last_detected": "2026-05-01T23:00:00Z"
    },
    {
      "name": "candidate-4",
      "display_name": "Academic Agent Team (tui_runner)",
      "root_path": "/Volumes/E/agent team 2/wt-1488343317639991428/",
      "contract_type": "tui_runner",
      "contract_supported": true,
      "execution_mode": "real",
      "health_status": "ok",
      "last_detected": "2026-05-01T23:00:00Z"
    }
  ],
  "runtime_profiles": [
    {
      "name": "default-mock",
      "provider": "none",
      "model": "",
      "budget_cap_cny": 10.0,
      "journal": "中文核心",
      "run_mode": "mock"
    },
    {
      "name": "openai-real",
      "provider": "openai",
      "model": "gpt-4o",
      "budget_cap_cny": 20.0,
      "journal": "CSSCI",
      "run_mode": "real"
    }
  ]
}
```

**API Key 安全规则：**
- `providers.json` **不存明文 API key**。存储 `"api_key_source": "env:OPENAI_API_KEY"` 引用
- 如果用户坚持要存 key（如 `localhost` provider 不需要 env），用 `keyring` 库存储
- providers.json 不进 git（已有 `.gitignore`）
- 当前 config.json 中的 `custom_ai_api_key` 字段保持向后兼容，但标记为 deprecated

---

## 五、实现路线图

### Vision 2.4.1：Provider 配置审计与只读检测

**目标：** 只读扫描本地 CLI、远程 API 配置、Agent Team 路径，输出统一检测报告。

**涉及文件：**
- 新建 `app/core/providers/__init__.py`
- 新建 `app/core/providers/detector.py` — 自动发现 + 检测
- 新建 `app/core/providers/models.py` — Provider 数据模型
- 修改 `scripts/diagnose_runs.py` — 增加 provider 检测命令

**做什么：**
1. 定义 `ProviderKind`, `LocalCLIProvider`, `RemoteAPIProvider`, `AgentTeamProvider`, `ProviderHealthStatus` 数据模型
2. 实现 `discover_local_clis()` — `shutil.which()` 自动发现
3. 实现 `detect_remote_api_config()` — 从 env/config 读取当前 API 配置
4. 实现 `detect_agent_team_paths()` — 扫描候选目录 + contract 检测
5. 实现 `generate_provider_health_report()` — 汇总所有 provider 状态
6. CLI 入口：`scripts/diagnose_runs.py --providers`

**不做什么：**
- 不修改 config.json 结构
- 不写入 providers.json
- 不发 API 请求
- 不修改 UI

**风险：** 极低。纯只读。

**验收标准：**
- `.venv/bin/python scripts/diagnose_runs.py --providers` 输出 provider 状态表
- 能检测 codex / claude 是否在 PATH
- 能输出当前 API 配置状态
- 能检测 Agent Team 候选路径契约
- 331 tests 继续通过

**是否需要确认：** 否，可自动执行。

---

### Vision 2.4.2：本地 CLI 自动发现

**目标：** 启动时自动扫描 PATH 中的 AI CLI，写入 `~/.wenbiao/providers.json`，不影响现有配置。

**涉及文件：**
- `app/core/providers/detector.py` — 增强
- `app/core/config.py` — 新增 `load_providers()` / `save_providers()`
- `scripts/diagnose_runs.py` — 增加 `--discover-local` 命令
- 新建 `tests/unit/test_provider_detector.py`

**做什么：**
1. 增强 `discover_local_clis()` — 支持自定义路径、版本检测、可用性标记
2. 在 Config 类新增 `load_providers()` / `save_providers()` — 读写 `providers.json`
3. 首次启动或手动触发时写 providers.json
4. 命令行入口：`scripts/diagnose_runs.py --discover-local`

**不做什么：**
- 不修改 config.json 中 agent_team_path
- 不修改 UI
- 不发 API 请求

**风险：** 低。新文件写入，不影响旧配置。

**验收标准：**
- `--discover-local` 输出发现的 CLI 列表
- providers.json 写入 local_clis 数组
- 再次运行时，上次结果可被读取
- 331+ tests 继续通过

**是否需要确认：** 否，可自动执行。

---

### Vision 2.4.3：远程 API Profile 配置

**目标：** 支持多个远程 API provider profile（OpenAI, DeepSeek, localhost 等），写入 `providers.json`。

**涉及文件：**
- `app/core/providers/models.py` — 增强 RemoteAPIProvider
- `app/core/providers/detector.py` — 增强预设 + 检测
- `scripts/diagnose_runs.py` — 增加 `--check-api` 命令
- 新建 `tests/unit/test_remote_api_provider.py`

**做什么：**
1. 定义 API Provider 预设（openai, deepseek, openrouter, localhost）
2. 实现 `detect_remote_api_providers()` — 从 env/config 推断当前 API 配置
3. 实现 API 配置校验（不发请求）：base_url 格式、key 是否非空
4. 增加 `--check-api` CLI 命令
5. 写入 providers.json 的 remote_api_providers 段

**不做什么：**
- 不发真实 API 请求（model check 留到 Vision 2.5）
- 不修改 UI
- 不修改 config.json

**风险：** 低。

**验收标准：**
- `--check-api` 输出 API 配置状态
- 支持 4 个预设 provider
- api_key 来源标注（env / config / none）
- 331+ tests 继续通过

**是否需要确认：** 否，可自动执行。

---

### Vision 2.4.4：Agent Team Provider 选择

**目标：** 自动发现 Agent Team 候选路径，写入 `providers.json`，支持多候选选择。

**涉及文件：**
- `app/core/providers/detector.py` — 增强 agent_team 检测
- `app/core/pipeline/agent_team_compat_adapter.py` — 复用 contract 检测
- `scripts/diagnose_runs.py` — 增加 `--detect-agent-teams` 命令

**做什么：**
1. 扫描硬编码候选目录（Candidate 1-4）
2. 同时扫描 `config.json` 中的 `agent_team_path`
3. 对每个候选跑 contract 检测
4. 输出 execution_mode（real / dry-run / broken）
5. 写入 providers.json 的 agent_teams 段
6. 支持候选排序和默认选择

**不做什么：**
- 不修改外部 Agent Team 仓库
- 不发送 API 请求
- 不修改 UI

**风险：** 低。

**验收标准：**
- `--detect-agent-teams` 输出所有候选的 contract 类型和执行模式
- providers.json 有 agent_teams 数组
- Candidate 1 = pipeline_v2/dry-run
- Candidate 4 = tui_runner/real
- 331+ tests 继续通过

**是否需要确认：** 否，可自动执行。

---

### Vision 2.4.5：配置健康报告（聚合）

**目标：** 整合 2.4.1-2.4.4，输出统一 Provider 配置健康报告。

**涉及文件：**
- `app/core/providers/health.py` — 健康报告生成器
- `scripts/diagnose_runs.py` — 增加 `--health` 命令

**做什么：**
1. 实现 `ProviderHealthReport` 数据类
2. 整合 local CLI + remote API + agent team 检测结果
3. 分层输出：阻断性问题 → 警告 → 已就绪
4. 明确告诉用户：缺什么、怎么解决

**不做什么：**
- 不发 API 请求（health check 中的 API 部分仅做 "api_key configured?" 检查）
- 不修改 UI
- 不修改代码

**风险：** 极低。

**验收标准：**
- `--health` 输出完整配置健康报告
- 报告明确分类：issues（阻断）/ warnings（提示）/ ok（就绪）
- 报告包含 actionable 建议（如"请设置 OPENAI_API_KEY 环境变量"）
- 331+ tests 继续通过

**是否需要确认：** 否，可自动执行。**但这是 Vision 2.5 之前的最后一步。**

---

## 六、回答

### 1. ThesisX 最应该从 MULTICA 借鉴什么？

**`exec.LookPath()` 式的本地 CLI 自动发现**。MULTICA 的 daemon 启动时自动检测 PATH 中的 agent CLI，这是 ThesisX 最需要的能力。当前 ThesisX 的 agent_team_path 是手动配置的单个路径，无法知道用户机器上有什么 CLI 可用。

其次值得借鉴的是 **Backend 接口抽象**。MULTICA 把所有 agent CLI 抽象为统一的 `Backend` 接口，输入端保持一致，各 provider 自行处理 stdin/stdout 协议差异。ThesisX 可把 codex/claude/academic_agent_team/openai-api 统一为类似的 Provider 抽象。

### 2. ThesisX 最应该从 ccswitch 借鉴什么？

**多 Provider Profile 管理 + 健康检查分层**。ccswitch 支持 50+ 预设 provider、一键切换、自动故障转移。ThesisX 不需要 50 个，但需要 3-5 个核心 profile（OpenAI/DeepSeek/localhost/academic_agent_team）。

另一个关键是 **健康检查的层次设计**：
- 不发 API：配置格式校验、key 是否非空、路径是否存在
- 发 API（需用户确认）：`GET /models`、模型可用性、延迟

ccswitch 还有"最小侵入"哲学——卸载后 CLI 仍可用。ThesisX 也应保持这个原则：providers.json 附加在 `~/.wenbiao/` 下，不影响用户现有的 `config.json` 和 env 配置。

### 3. 当前应该先做本地 CLI provider，还是远程 API profile？

**先做本地 CLI provider（Vision 2.4.2），再补远程 API profile（Vision 2.4.3）。**

理由：
- 本地 CLI 自动发现是最基础的能力，不需要用户配置就能产出结果
- Agent Team 候选路径检测（Vision 2.4.4）与本地 CLI 发现是同一类操作（文件系统扫描 + 可执行性检查）
- 远程 API profile 需要更多设计（预设、key 来源标注、env 冲突检测）
- 做完本地 CLI + agent team 检测后，再做远程 API，可形成完整的 provider 健康报告

### 4. 哪些配置检测可以不发 API？

| 检测项 | 方式 | 无需 API |
|--------|------|---------|
| CLI 是否在 PATH | `shutil.which()` | ✓ |
| CLI 可执行性 | `os.access(X_OK)` | ✓ |
| CLI 版本 | `subprocess --version` (本地) | ✓ |
| Agent Team 路径存在 | `Path.exists()` | ✓ |
| Agent Team 契约类型 | 文件结构检测（已有） | ✓ |
| API key 是否非空 | 字符串检查 | ✓ |
| Base URL 格式 | URL parse | ✓ |
| 配置文件是否存在 | 文件系统检查 | ✓ |
| 环境变量冲突 | 比较 env vs config vs default | ✓ |

### 5. 哪些配置检测必须用户确认？

| 检测项 | 方式 | 必须确认 |
|--------|------|---------|
| API key 有效性 | `GET {base_url}/models` + 认证 header | ✓ 会产生费用/泄露 key |
| 模型可用性 | 发送最小 API 请求 | ✓ 会产生费用 |
| Agent Team 真实执行 | import + PipelineConfig | ✓ 可能执行副作用 |
| 写入 providers.json | 文件写入 | ✗ 本地文件，无风险 |

### 6. 下一轮最小实现应该从哪个 Vision 开始？

**从 Vision 2.4.1（Provider 配置审计与只读检测）开始，可连续执行到 2.4.5。**

Vision 2.4.1-2.4.5 全部是只读 + 新文件写入，无破坏性，不需用户确认。

建议自动执行的顺序（3 个连续 Vision）：
1. **2.4.1** Provider 配置审计（纯只读，建立数据模型）
2. **2.4.2 + 2.4.3 + 2.4.4** 合并执行（CLI 发现 + API profile + Agent Team 检测）
3. **2.4.5** 配置健康聚合报告

然后在 Vision 2.5 前暂停，等用户确认再进入 Real API 调用。
