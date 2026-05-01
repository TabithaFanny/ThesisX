"""Provider detector — read-only probing for local CLIs, remote APIs, Agent Teams.

All functions are read-only. No API calls. No side effects.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .models import (
    AgentTeamProvider,
    LocalCLIProvider,
    ProviderHealthReport,
    ProviderHealthStatus,
    ProviderKind,
    RemoteAPIProvider,
    RuntimeProfile,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KNOWN_CLIS = [
    ("codex", "CODEX_PATH", "Codex CLI"),
    ("claude", "CLAUDE_PATH", "Claude Code"),
    ("opencode", "OPENCODE_PATH", "OpenCode"),
    ("openclaw", "OPENCLAW_PATH", "OpenClaw"),
    ("hermes", "HERMES_PATH", "Hermes"),
]

_API_PRESETS: dict[str, dict] = {
    "openai": {
        "display_name": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "requires_api_key": True,
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "requires_api_key": True,
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o",
        "requires_api_key": True,
    },
    "localhost": {
        "display_name": "Local Ollama / vLLM",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3",
        "requires_api_key": False,
    },
}

_AGENT_TEAM_CANDIDATES = [
    ("candidate-1", "/Volumes/E/agent team 2/academic-agent-team/"),
    ("candidate-2", "/Volumes/E/agent team 2/academic-agent-team-work/"),
    ("candidate-3", "/Users/magnus/.codex_work/agent-team-2/academic-agent-team/"),
    ("candidate-4", "/Volumes/E/agent team 2/wt-1488343317639991428/"),
]


# ---------------------------------------------------------------------------
# Local CLI detection
# ---------------------------------------------------------------------------

def discover_local_clis() -> list[LocalCLIProvider]:
    """Scan PATH for AI coding CLIs. Read-only, no network calls."""
    now = datetime.now(timezone.utc).isoformat()
    results: list[LocalCLIProvider] = []
    for name, env_suffix, display in _KNOWN_CLIS:
        # Priority: THESISX_<NAME>_PATH > MULTICA_<NAME>_PATH > shutil.which
        thesisx_env = os.environ.get(f"THESISX_{env_suffix}", "")
        multica_env = os.environ.get(f"MULTICA_{env_suffix}", "")
        custom_path = thesisx_env or multica_env or name

        found_path = shutil.which(custom_path)
        available = found_path is not None
        version = _detect_version(found_path) if available else ""

        provider = LocalCLIProvider(
            name=name,
            display_name=display,
            executable_path=found_path or "",
            version=version,
            available=available,
            model_override=os.environ.get(f"MULTICA_{name.upper()}_MODEL", ""),
            last_detected=now,
        )
        results.append(provider)
    return results


def _detect_version(exec_path: str) -> str:
    """Run `exec_path --version` and return first line of output."""
    try:
        result = subprocess.run(
            [exec_path, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        out = result.stdout.strip() or result.stderr.strip()
        return out.split("\n")[0][:200] if out else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Remote API detection
# ---------------------------------------------------------------------------

def detect_remote_api_config() -> list[RemoteAPIProvider]:
    """Build RemoteAPIProvider list from presets + env/config. No API calls."""
    now = datetime.now(timezone.utc).isoformat()
    results: list[RemoteAPIProvider] = []

    for name, preset in _API_PRESETS.items():
        # Determine actual base_url / model / api_key from environment + preset defaults
        base_url = (
            os.environ.get("OPENAI_BASE_URL", "")
            or preset["base_url"]
        )
        model = (
            os.environ.get("OPENAI_MODEL", "")
            or preset["default_model"]
        )
        api_key = _resolve_api_key()
        api_key_configured = bool(api_key)

        # Detect API key source
        if os.environ.get("OPENAI_API_KEY", ""):
            source = "env:OPENAI_API_KEY"
        elif os.environ.get("AI_API_KEY", ""):
            source = "env:AI_API_KEY"
        elif api_key_configured:
            source = "config:custom_ai_api_key"
        else:
            source = "none"

        # Determine health status (without API call)
        health = _classify_api_health(name, base_url, api_key_configured)

        provider = RemoteAPIProvider(
            name=name,
            display_name=preset["display_name"],
            base_url=base_url,
            model=model,
            api_key_source=source,
            api_key_configured=api_key_configured,
            health_status=health,
            last_health_check=now,
        )
        results.append(provider)
    return results


def _resolve_api_key() -> str:
    """Resolve API key from all sources without logging it."""
    return (
        os.environ.get("OPENAI_API_KEY", "")
        or os.environ.get("AI_API_KEY", "")
    )


def _classify_api_health(name: str, base_url: str, key_configured: bool) -> str:
    """Classify health status based on static checks only (no API call)."""
    issues: list[str] = []
    # Check base_url format
    try:
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            issues.append(f"base_url 格式无效: {base_url}")
    except Exception:
        issues.append(f"base_url 无法解析: {base_url}")

    # Check API key
    if _API_PRESETS.get(name, {}).get("requires_api_key", True) and not key_configured:
        issues.append("API key 未配置")

    if issues:
        return "unavailable"
    return "unknown"  # can't confirm without real API call


# ---------------------------------------------------------------------------
# Agent Team detection
# ---------------------------------------------------------------------------

def detect_agent_team_paths(config_agent_team_path: str = "") -> list[AgentTeamProvider]:
    """Detect Agent Team installations at known candidate paths plus config.json path.

    Uses AgentTeamCompatAdapter.validate_agent_team_contract() for contract
    detection — no imports of external packages.
    """
    from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter

    now = datetime.now(timezone.utc).isoformat()
    results: list[AgentTeamProvider] = []
    seen_paths: set[str] = set()

    # Collect paths: config.json first, then hardcoded candidates
    paths_to_check: list[tuple[str, str]] = []
    if config_agent_team_path and config_agent_team_path.strip() and config_agent_team_path.strip() != "未选择":
        paths_to_check.append(("config", config_agent_team_path.strip()))
    for name, path in _AGENT_TEAM_CANDIDATES:
        paths_to_check.append((name, path))

    for source_name, raw_path in paths_to_check:
        resolved = str(Path(raw_path).expanduser().resolve())
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)

        check = AgentTeamCompatAdapter.validate_agent_team_contract(raw_path)

        if check.contract_type == "tui_runner":
            exec_mode = "real"
            health = "ok"
        elif check.supported:
            exec_mode = "dry-run"
            health = "dry_run_only"
        else:
            exec_mode = "broken"
            health = "broken"

        display = _agent_team_display(source_name, check.contract_type)

        provider = AgentTeamProvider(
            name=source_name,
            display_name=display,
            root_path=str(check.agent_team_root) if check.agent_team_root else resolved,
            contract_type=check.contract_type,
            contract_supported=check.supported,
            execution_mode=exec_mode,
            needs_api_key=(check.contract_type == "tui_runner"),
            health_status=health,
            last_detected=now,
        )
        results.append(provider)

    return results


def _agent_team_display(source: str, contract: str) -> str:
    contract_label = {
        "tui_runner": "tui_runner (真实执行)",
        "pipeline_v2": "pipeline_v2 (dry-run)",
        "pipeline_function": "pipeline_function (dry-run)",
        "unsupported": "不支持",
    }.get(contract, contract)
    return f"Agent Team {source} [{contract_label}]"


# ---------------------------------------------------------------------------
# Health report
# ---------------------------------------------------------------------------

def generate_provider_health_report(
    local_clis: list[LocalCLIProvider] | None = None,
    remote_apis: list[RemoteAPIProvider] | None = None,
    agent_teams: list[AgentTeamProvider] | None = None,
) -> ProviderHealthReport:
    """Generate a unified health report for all providers."""
    if local_clis is None:
        local_clis = discover_local_clis()
    if remote_apis is None:
        remote_apis = detect_remote_api_config()
    if agent_teams is None:
        agent_teams = detect_agent_team_paths()

    now = datetime.now(timezone.utc).isoformat()

    cli_health = [_health_for_local_cli(p) for p in local_clis]
    api_health = [_health_for_remote_api(p) for p in remote_apis]
    team_health = [_health_for_agent_team(p) for p in agent_teams]

    all_ok = all(
        h.ok for h in cli_health + api_health + team_health
    )

    # Build human-readable summary
    summary_lines = [_summarize_section("本地 CLI", cli_health),
                     _summarize_section("远程 API", api_health),
                     _summarize_section("Agent Team", team_health)]
    summary = "\n".join(line for line in summary_lines if line)

    return ProviderHealthReport(
        timestamp=now,
        local_clis=cli_health,
        remote_apis=api_health,
        agent_teams=team_health,
        overall_ok=all_ok,
        summary=summary,
    )


def _health_for_local_cli(p: LocalCLIProvider) -> ProviderHealthStatus:
    checks = {
        "on_path": p.available,
        "executable": p.available and os.access(p.executable_path, os.X_OK) if p.executable_path else False,
    }
    issues: list[str] = []
    warnings: list[str] = []
    if not checks["on_path"]:
        issues.append(f"{p.display_name} 未在 PATH 中找到")
    if p.available and not p.version:
        warnings.append(f"{p.display_name} 版本检测失败")
    return ProviderHealthStatus(
        provider_name=p.name,
        kind=ProviderKind.LOCAL_CLI,
        ok=len(issues) == 0,
        issues=issues,
        warnings=warnings,
        checks=checks,
    )


def _health_for_remote_api(p: RemoteAPIProvider) -> ProviderHealthStatus:
    checks: dict[str, bool] = {}
    issues: list[str] = []
    warnings: list[str] = []

    # base_url validity
    try:
        parsed = urlparse(p.base_url)
        checks["base_url_valid"] = bool(parsed.scheme and parsed.netloc)
    except Exception:
        checks["base_url_valid"] = False
    if not checks.get("base_url_valid"):
        issues.append(f"{p.display_name} base_url 无效: {p.base_url}")

    # API key
    checks["api_key_set"] = p.api_key_configured
    if _API_PRESETS.get(p.name, {}).get("requires_api_key", True) and not checks["api_key_set"]:
        issues.append(f"{p.display_name} API key 未设置")

    # Conflicts: if env has OPENAI_API_KEY but a provider-specific env is also set
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_BASE_URL"):
        env_model = os.environ.get("OPENAI_MODEL", "")
        if env_model and env_model != p.model:
            warnings.append(
                f"OPENAI_MODEL={env_model} 与 provider {p.name} 默认 "
                f"model={p.model} 不一致（env 优先）"
            )

    return ProviderHealthStatus(
        provider_name=p.name,
        kind=ProviderKind.REMOTE_API,
        ok=len(issues) == 0,
        issues=issues,
        warnings=warnings,
        checks=checks,
    )


def _health_for_agent_team(p: AgentTeamProvider) -> ProviderHealthStatus:
    checks = {
        "path_exists": Path(p.root_path).exists() if p.root_path else False,
        "contract_detected": p.contract_supported,
        "real_ready": p.execution_mode == "real",
    }
    issues: list[str] = []
    warnings: list[str] = []
    dry_run_only = False

    if not checks["path_exists"]:
        issues.append(f"{p.display_name} 路径不存在")
    if not checks["contract_detected"]:
        issues.append(f"{p.display_name} 契约不支持: {p.contract_type}")
    if checks["contract_detected"] and not checks["real_ready"]:
        warnings.append(f"{p.display_name} 仅支持 dry-run，不支持真实执行")
        dry_run_only = True

    return ProviderHealthStatus(
        provider_name=p.name,
        kind=ProviderKind.AGENT_TEAM,
        ok=len(issues) == 0,
        issues=issues,
        warnings=warnings,
        checks=checks,
        dry_run_only=dry_run_only,
    )


def _summarize_section(title: str, items: list[ProviderHealthStatus]) -> str:
    if not items:
        return f"  {title}: 无"
    ok_count = sum(1 for h in items if h.ok)
    issue_count = sum(1 for h in items if not h.ok)
    parts = [f"{ok_count} ready"]
    if issue_count:
        parts.append(f"{issue_count} issues")
    names = ", ".join(
        f"{h.provider_name}({'✓' if h.ok else '✗'})" for h in items
    )
    return f"  {title}: {', '.join(parts)} — {names}"
