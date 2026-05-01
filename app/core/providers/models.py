"""Provider data models for ThesisX configuration system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Provider kind
# ---------------------------------------------------------------------------

class ProviderKind(str, Enum):
    LOCAL_CLI = "local_cli"       # codex, claude, opencode 等
    REMOTE_API = "remote_api"     # OpenAI, DeepSeek, OpenRouter 等
    AGENT_TEAM = "agent_team"     # academic_agent_team（多 agent 编排）


# ---------------------------------------------------------------------------
# Local CLI Provider
# ---------------------------------------------------------------------------

@dataclass
class LocalCLIProvider:
    """A locally-installed AI coding CLI discovered on PATH."""

    name: str                     # "codex", "claude", "opencode", "openclaw", "hermes"
    display_name: str             # "Codex CLI", "Claude Code"
    executable_path: str = ""     # /usr/local/bin/codex or empty if not found
    version: str = ""             # output of --version
    available: bool = False       # shutil.which() result
    model_override: str = ""      # env var override for model
    env_vars: dict[str, str] = field(default_factory=dict)
    last_detected: str = ""       # ISO timestamp

    kind: ProviderKind = ProviderKind.LOCAL_CLI


# ---------------------------------------------------------------------------
# Remote API Provider
# ---------------------------------------------------------------------------

@dataclass
class RemoteAPIProvider:
    """An OpenAI-compatible remote API endpoint."""

    name: str                     # "openai", "deepseek", "openrouter", "localhost"
    display_name: str             # "OpenAI API", "DeepSeek"
    base_url: str = ""            # https://api.openai.com/v1
    model: str = ""               # gpt-4o-mini
    extra_models: list[str] = field(default_factory=list)
    api_key_source: str = ""      # "env:OPENAI_API_KEY" / "config:custom_ai_api_key" / "none"
    api_key_configured: bool = False
    health_status: str = "unknown"  # "unknown" / "ok" / "unavailable"
    last_health_check: str = ""

    kind: ProviderKind = ProviderKind.REMOTE_API


# ---------------------------------------------------------------------------
# Agent Team Provider
# ---------------------------------------------------------------------------

@dataclass
class AgentTeamProvider:
    """An external academic_agent_team installation."""

    name: str                     # "candidate-1", "candidate-4", "custom"
    display_name: str             # "Academic Agent Team (pipeline_v2)"
    root_path: str = ""           # /Volumes/E/agent team 2/academic-agent-team/
    contract_type: str = ""       # "tui_runner" / "pipeline_v2" / "pipeline_function" / "unsupported"
    contract_supported: bool = False
    execution_mode: str = ""      # "real" / "dry-run" / "broken"
    needs_api_key: bool = True
    health_status: str = "unknown"  # "ok" / "dry_run_only" / "broken"
    last_detected: str = ""

    kind: ProviderKind = ProviderKind.AGENT_TEAM


# ---------------------------------------------------------------------------
# Runtime Profile — joins a Provider + Model + run parameters
# ---------------------------------------------------------------------------

@dataclass
class RuntimeProfile:
    name: str                     # "default-mock", "openai-real"
    provider: str = ""            # provider name
    model: str = ""               # model_id
    budget_cap_cny: float = 10.0
    journal: str = "中文核心"
    run_mode: str = "mock"        # "mock" / "dry-run" / "real"


# ---------------------------------------------------------------------------
# Health status
# ---------------------------------------------------------------------------

@dataclass
class ProviderHealthStatus:
    """Aggregate health check for a single provider."""
    provider_name: str
    kind: ProviderKind
    ok: bool = False
    issues: list[str] = field(default_factory=list)    # blocking
    warnings: list[str] = field(default_factory=list)   # non-blocking
    checks: dict[str, bool] = field(default_factory=dict)
    dry_run_only: bool = False


@dataclass
class ProviderHealthReport:
    """Aggregate health check for all detected providers."""
    timestamp: str = ""
    local_clis: list[ProviderHealthStatus] = field(default_factory=list)
    remote_apis: list[ProviderHealthStatus] = field(default_factory=list)
    agent_teams: list[ProviderHealthStatus] = field(default_factory=list)
    overall_ok: bool = False
    summary: str = ""
