"""Tests for Real mode safety gate — no API calls, config validation only."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.pipeline.agent_team_runner import AgentTeamRunner, _validate_real_mode_gate
from app.core.pipeline.models import PaperRequest


class TestRealModeSafetyGate:
    """Verify _validate_real_mode_gate catches all missing config."""

    def test_empty_agent_path(self):
        """Empty agent_team_path should fail."""
        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path="",
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is False
        assert any(issue["code"] == "AGENT_PATH_EMPTY" for issue in result["issues"])

    def test_weixuanze_agent_path(self):
        """'未选择' agent_team_path should fail."""
        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path="未选择",
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is False
        assert any("AGENT_PATH_EMPTY" in issue["code"] for issue in result["issues"])

    def test_invalid_path(self):
        """Non-existent path should fail."""
        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path="/nonexistent/path/xyz",
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is False
        assert any("AGENT_PATH_INVALID" in issue["code"] for issue in result["issues"])

    def test_unsupported_contract(self, tmp_path: Path, monkeypatch):
        """Contract that IS supported but not tui_runner should warn, not fail."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        pkg = tmp_path / "academic_agent_team"
        pkg.mkdir(parents=True)
        (pkg / "pipeline_v2.py").write_text("", encoding="utf-8")

        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path=str(tmp_path),
        )
        result = _validate_real_mode_gate(request)
        # pipeline_v2 is supported → should not be blocked
        # but api_key is missing → should fail on that
        assert result["ok"] is False
        assert any("API_KEY_MISSING" in issue["code"] for issue in result["issues"])
        # Should warn about dry-run only
        assert any("dry-run" in w for w in result["warnings"])

    def test_missing_api_key_with_valid_path(self, tmp_path: Path, monkeypatch):
        """Valid tui_runner path but no API key."""
        pkg = tmp_path / "academic_agent_team" / "tui"
        pkg.mkdir(parents=True)
        (pkg / "runner.py").write_text("", encoding="utf-8")
        (pkg / "events.py").write_text("", encoding="utf-8")

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path=str(tmp_path),
            api_key="",  # explicitly empty
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is False
        assert any("API_KEY_MISSING" in issue["code"] for issue in result["issues"])

    def test_all_ok_with_tui_runner_and_key(self, tmp_path: Path, monkeypatch):
        """Valid tui_runner + API key should pass."""
        pkg = tmp_path / "academic_agent_team" / "tui"
        pkg.mkdir(parents=True)
        (pkg / "runner.py").write_text("", encoding="utf-8")
        (pkg / "events.py").write_text("", encoding="utf-8")

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-1234")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")

        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path=str(tmp_path),
            api_key="sk-test-1234",
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
            budget_cap_cny=10.0,
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is True
        assert len(result["issues"]) == 0

    def test_missing_model_warns_but_passes(self, tmp_path: Path, monkeypatch):
        """Missing model should warn but not fail the gate."""
        pkg = tmp_path / "academic_agent_team" / "tui"
        pkg.mkdir(parents=True)
        (pkg / "runner.py").write_text("", encoding="utf-8")
        (pkg / "events.py").write_text("", encoding="utf-8")

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)

        request = PaperRequest(
            topic="test",
            run_mode="real",
            agent_team_path=str(tmp_path),
            api_key="sk-test",
        )
        result = _validate_real_mode_gate(request)
        assert result["ok"] is True
        assert any("模型" in w for w in result["warnings"])


class TestAgentTeamRunnerSafetyGate:
    """Verify AgentTeamRunner halts on real mode with bad config."""

    def test_runner_stops_on_empty_path(self, tmp_path: Path, monkeypatch):
        """Runner should emit error events and stop, not run mock pipeline."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="bad config",
                run_mode="real",
                agent_team_path="",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        types = [e.type for e in events]
        assert "error" in types
        assert "completion" not in types
        assert not any(e.type == "completion" for e in events)

    def test_runner_emits_clear_error_code(self, tmp_path: Path, monkeypatch):
        """Error events should have a machine-readable code."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="error code test",
                run_mode="real",
                agent_team_path="未选择",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        errors = [e for e in events if e.type == "error"]
        assert errors
        assert errors[0].payload.get("code") == "AGENT_PATH_EMPTY"

    def test_mock_mode_unaffected_by_safety_gate(self, tmp_path: Path):
        """Mock mode should not trigger the safety gate."""
        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="mock bypass",
                run_mode="mock",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        assert any(e.type == "completion" for e in events)
        assert not any(e.payload.get("code") == "AGENT_PATH_EMPTY" for e in events if e.type == "error")
