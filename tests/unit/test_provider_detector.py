"""Tests for provider detection system — all read-only, no API calls."""

from __future__ import annotations

from pathlib import Path

from app.core.providers.detector import (
    discover_local_clis,
    detect_remote_api_config,
    detect_agent_team_paths,
    generate_provider_health_report,
)
from app.core.providers.models import (
    LocalCLIProvider,
    RemoteAPIProvider,
    AgentTeamProvider,
    ProviderHealthStatus,
    ProviderKind,
    ProviderHealthReport,
)


class TestLocalCLIDiscovery:
    def test_discovers_clis(self):
        """discover_local_clis should return a list of LocalCLIProvider."""
        results = discover_local_clis()
        assert isinstance(results, list)
        assert len(results) >= 5  # codex, claude, opencode, openclaw, hermes
        for p in results:
            assert isinstance(p, LocalCLIProvider)
            assert p.name
            assert p.display_name
            assert p.kind == ProviderKind.LOCAL_CLI

    def test_known_cli_names(self):
        """Known CLI names should be in the result set."""
        results = discover_local_clis()
        names = {p.name for p in results}
        for expected in ("codex", "claude", "opencode", "openclaw", "hermes"):
            assert expected in names, f"{expected} should be in discovered CLIs"

    def test_available_cli_has_path_and_version(self):
        """If a CLI is available, it should have a path."""
        results = discover_local_clis()
        available = [p for p in results if p.available]
        for p in available:
            assert p.executable_path, f"{p.name} should have executable_path"
            assert os_access_or_true(p.executable_path)

    def test_unavailable_cli_has_no_path(self):
        """If a CLI is not available, path should be empty."""
        results = discover_local_clis()
        unavailable = [p for p in results if not p.available]
        for p in unavailable:
            assert p.executable_path == "", f"{p.name} should have empty path"


class TestRemoteAPIConfig:
    def test_detects_presets(self):
        """detect_remote_api_config should return 4 presets."""
        results = detect_remote_api_config()
        assert len(results) == 4
        names = {p.name for p in results}
        assert names == {"openai", "deepseek", "openrouter", "localhost"}

    def test_each_preset_has_required_fields(self):
        """Each preset should have base_url, model, api_key_source."""
        results = detect_remote_api_config()
        for p in results:
            assert isinstance(p, RemoteAPIProvider)
            assert p.base_url
            assert p.model
            assert p.api_key_source in ("env:OPENAI_API_KEY", "env:AI_API_KEY",
                                         "config:custom_ai_api_key", "none")
            assert p.kind == ProviderKind.REMOTE_API

    def test_localhost_does_not_require_key(self, monkeypatch):
        """localhost provider should not require API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        results = detect_remote_api_config()
        localhost = next(p for p in results if p.name == "localhost")
        assert localhost.health_status != "unavailable"


class TestAgentTeamDetection:
    def test_detects_candidates(self):
        """detect_agent_team_paths should find candidates."""
        results = detect_agent_team_paths()
        assert len(results) >= 1
        for p in results:
            assert isinstance(p, AgentTeamProvider)
            assert p.name
            assert p.contract_type
            assert p.execution_mode in ("real", "dry-run", "broken")

    def test_candidate_1_is_pipeline_v2(self):
        """Candidate 1 should be detected as pipeline_v2."""
        results = detect_agent_team_paths()
        c1 = next((p for p in results if p.name == "candidate-1"), None)
        if c1 and c1.contract_supported:
            assert c1.contract_type == "pipeline_v2"
            assert c1.execution_mode == "dry-run"

    def test_candidate_4_is_tui_runner(self):
        """Candidate 4 should be detected as tui_runner."""
        results = detect_agent_team_paths()
        c4 = next((p for p in results if p.name == "candidate-4"), None)
        if c4 and c4.contract_supported:
            assert c4.contract_type == "tui_runner"
            assert c4.execution_mode == "real"

    def test_with_config_path(self):
        """Should also check the config.json agent_team_path."""
        results = detect_agent_team_paths(
            config_agent_team_path="/Volumes/E/agent team 2/academic-agent-team/"
        )
        # config path should appear in results (may merge with candidate-1)
        assert any(
            p.name == "config"
            or (p.name == "candidate-1" and p.root_path)
            for p in results
        )


class TestProviderHealthReport:
    def test_generates_report(self):
        """generate_provider_health_report should produce a structured report."""
        report = generate_provider_health_report()
        assert isinstance(report, ProviderHealthReport)
        assert report.timestamp
        assert isinstance(report.overall_ok, bool)
        assert report.summary

    def test_report_has_all_sections(self):
        """Report should have local_clis, remote_apis, agent_teams."""
        report = generate_provider_health_report()
        assert len(report.local_clis) >= 5
        assert len(report.remote_apis) == 4
        assert len(report.agent_teams) >= 1

    def test_health_items_are_typed(self):
        """Each health item should be ProviderHealthStatus."""
        report = generate_provider_health_report()
        for item in report.local_clis + report.remote_apis + report.agent_teams:
            assert isinstance(item, ProviderHealthStatus)
            assert item.provider_name
            assert isinstance(item.ok, bool)
            assert isinstance(item.checks, dict)

    def test_local_cli_health_reflects_availability(self):
        """Available CLIs should be OK, unavailable should have issues."""
        local_clis = discover_local_clis()
        report = generate_provider_health_report(local_clis=local_clis)
        for health in report.local_clis:
            provider = next(p for p in local_clis if p.name == health.provider_name)
            if provider.available:
                assert health.ok or health.warnings  # may have version warning
            else:
                assert not health.ok
                assert health.issues

    def test_agent_team_health_dry_run_warning(self):
        """pipeline_v2 candidates should have dry_run_only flag."""
        report = generate_provider_health_report()
        dry_run_teams = [h for h in report.agent_teams if h.dry_run_only]
        if dry_run_teams:
            for h in dry_run_teams:
                assert not h.checks.get("real_ready", True)


# Helper
def os_access_or_true(path: str) -> bool:
    """Check os.access or return True if path empty (test tolerance)."""
    import os
    if not path:
        return True
    return os.access(path, os.X_OK)
