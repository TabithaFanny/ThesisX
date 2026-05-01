"""Smoke tests for ThesisX CLI — subprocess-based, no API calls."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CLI = [sys.executable, str(Path(__file__).resolve().parent.parent.parent / "cli" / "thesisx.py")]


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        CLI + list(args), capture_output=True, text=True, timeout=30,
    )


class TestCLIHelp:
    def test_no_args_shows_help(self):
        result = run_cli()
        assert result.returncode == 0
        assert "usage:" in (result.stdout + result.stderr).lower()

    def test_help_flag_on_subcommands(self):
        for cmd in (["diagnose", "runs"], ["verify", "contracts"], ["health"], ["migrate"]):
            result = run_cli(*cmd, "--help")
            assert result.returncode == 0


class TestCLIDiagnose:
    def test_diagnose_runs(self):
        result = run_cli("diagnose", "runs")
        assert result.returncode == 0
        assert "Found" in result.stdout


class TestCLIVerify:
    def test_verify_contracts(self):
        result = run_cli("verify", "contracts")
        assert result.returncode == 0
        assert "candidate-1" in result.stdout
        assert "candidate-4" in result.stdout

    def test_verify_providers(self):
        result = run_cli("verify", "providers")
        assert result.returncode == 0
        assert "Local CLIs" in result.stdout or "Local" in result.stdout


class TestCLIHealth:
    def test_health(self):
        result = run_cli("health")
        assert result.returncode == 0
        assert "Overall" in result.stdout

    def test_health_writes_reports(self, tmp_path: Path):
        result = run_cli("health", "--output-dir", str(tmp_path))
        assert result.returncode == 0
        assert (tmp_path / "provider_health.md").exists()
        data = json.loads((tmp_path / "provider_health.json").read_text())
        assert "local_clis" in data
        assert "remote_apis" in data
        assert "agent_teams" in data


class TestCLIRunMock:
    def test_run_mock(self):
        result = run_cli("run", "mock", "CLI mock test topic")
        assert result.returncode == 0
        assert "Done:" in result.stdout
        assert "Session:" in result.stdout
        assert "Paper:" in result.stdout


class TestCLIMigrate:
    def test_migrate_dry_run(self):
        result = run_cli("migrate", "--dry-run")
        assert result.returncode == 0
        assert "DRY RUN" in result.stdout
