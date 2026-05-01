"""Tests for pipeline_v2 and pipeline_function dry-run adapter paths."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter
from app.core.pipeline.agent_team_runner import AgentTeamRunner
from app.core.pipeline.models import PaperRequest


def _make_compat_check(supported: bool, contract_type: str) -> object:
    """Build a minimal ContractCheckResult-like return for monkeypatching."""

    class _FakeCheck:
        def __init__(self):
            self.supported = supported
            self.contract_type = contract_type
            self.reason = ""
            self.agent_team_root = Path("/fake/path")
            self.error_code = "" if supported else "IMPORT_FAILED"

    return _FakeCheck()


class TestPipelineV2DryRun:
    """Verify dry-run adapter emits complete event flow without real import."""

    def test_pipeline_v2_dry_run_emits_all_stages(self, tmp_path: Path, monkeypatch):
        """pipeline_v2 dry-run should yield state, message, cost, completion events."""
        # Pretend contract detection returns pipeline_v2
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda cls, path: _make_compat_check(True, "pipeline_v2"),
        )

        async def _run():
            adapter = AgentTeamCompatAdapter()
            request = PaperRequest(
                topic="pipeline_v2 dry-run 测试",
                journal="中文核心",
                run_mode="real",
                budget_cap_cny=10.0,
                agent_team_path="/fake/path",
                session_id="test-sess-001",
            )
            return [event async for event in adapter.run_external_agent_team(
                request, base_dir=tmp_path,
            )]

        events = asyncio.run(_run())
        types = [e.type for e in events]

        # Core event types
        assert "state" in types
        assert "message" in types
        assert "cost" in types
        assert "completion" in types
        assert "error" not in types

        # Verify standard stages are represented
        state_stages = {e.stage for e in events if e.type == "state"}
        expected_stages = {
            "advisor_running", "topic_done",
            "researcher_running", "literature_done",
            "writer_running", "writing_done",
            "reviewer_running", "review_done",
            "polisher_running", "polish_done",
            "export_done",
        }
        assert expected_stages.issubset(state_stages)

        # Completion carries dry-run marker
        completion = [e for e in events if e.type == "completion"]
        assert completion
        assert completion[0].payload.get("mode") == "dry-run"
        assert completion[0].payload.get("contract") == "pipeline_v2"
        assert completion[0].payload.get("total_cost_cny") == 0.0

    def test_pipeline_function_dry_run_emits_all_stages(self, tmp_path: Path, monkeypatch):
        """pipeline_function dry-run should yield state, message, cost, completion events."""
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda cls, path: _make_compat_check(True, "pipeline_function"),
        )

        async def _run():
            adapter = AgentTeamCompatAdapter()
            request = PaperRequest(
                topic="pipeline_function dry-run 测试",
                journal="SCI",
                run_mode="real",
                budget_cap_cny=5.0,
                agent_team_path="/fake/path",
                session_id="test-sess-002",
            )
            return [event async for event in adapter.run_external_agent_team(
                request, base_dir=tmp_path,
            )]

        events = asyncio.run(_run())
        types = [e.type for e in events]

        assert "state" in types
        assert "message" in types
        assert "cost" in types
        assert "completion" in types
        assert "error" not in types

        completion = [e for e in events if e.type == "completion"]
        assert completion[0].payload.get("mode") == "dry-run"
        assert completion[0].payload.get("contract") == "pipeline_function"

    def test_unsupported_contract_still_returns_error(self, tmp_path: Path, monkeypatch):
        """unsupported contract should still return an error event, not crash."""
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda self, path: _make_compat_check(False, "unsupported"),
        )

        async def _run():
            adapter = AgentTeamCompatAdapter()
            request = PaperRequest(
                topic="unsupported test",
                run_mode="real",
                agent_team_path="/bad/path",
            )
            return [event async for event in adapter.run_external_agent_team(
                request, base_dir=tmp_path,
            )]

        events = asyncio.run(_run())
        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].payload.get("code") in {"IMPORT_FAILED", "AGENT_PATH_INVALID", "AGENT_PATH_EMPTY"}

    def test_cancel_during_dry_run(self, tmp_path: Path, monkeypatch):
        """Cancelling during dry-run should emit a cancelled state event."""
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda cls, path: _make_compat_check(True, "pipeline_v2"),
        )

        async def _run():
            adapter = AgentTeamCompatAdapter()
            request = PaperRequest(
                topic="cancel test",
                run_mode="real",
                agent_team_path="/fake/path",
            )
            events = []
            async for event in adapter.run_external_agent_team(request, base_dir=tmp_path):
                events.append(event)
                if event.stage == "advisor_running":
                    adapter.cancel()
            return events

        events = asyncio.run(_run())
        assert events[-1].type == "state"
        assert events[-1].stage == "cancelled"

    def test_dry_run_does_not_import_external_module(self, tmp_path: Path, monkeypatch):
        """Verify dry-run never triggers sys.path insertion or real import."""
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda cls, path: _make_compat_check(True, "pipeline_v2"),
        )

        import_was_called = False

        def _fake_import(*args, **kwargs):
            nonlocal import_was_called
            import_was_called = True
            raise ImportError("should not be called")

        # The _run_tui_runner uses `import_agent_team_api` which we don't touch
        # in dry-run paths. Verify dry-run code path never calls it.
        from app.core.pipeline import agent_team_compat_adapter as mod

        monkeypatch.setattr(mod, "import_agent_team_api", _fake_import)

        async def _run():
            adapter = AgentTeamCompatAdapter()
            request = PaperRequest(
                topic="no import test",
                run_mode="real",
                agent_team_path="/fake/path",
            )
            return [event async for event in adapter.run_external_agent_team(
                request, base_dir=tmp_path,
            )]

        events = asyncio.run(_run())
        assert not import_was_called, "dry-run must not call import_agent_team_api"
        assert any(e.type == "completion" for e in events)


class TestAgentTeamRunnerWithDryRun:
    """Verify AgentTeamRunner correctly handles dry-run from CompatAdapter."""

    def test_runner_accepts_dry_run_and_generates_paper_md(self, tmp_path: Path, monkeypatch):
        """Runner in real mode with pipeline_v2 dry-run should produce paper.md."""
        # Create a valid path and mock the safety gate to bypass contract check
        pkg = tmp_path / "fake_agent_team" / "academic_agent_team"
        pkg.mkdir(parents=True)
        (pkg / "pipeline_v2.py").write_text("", encoding="utf-8")
        agent_path = str(tmp_path / "fake_agent_team")

        # Monkeypatch the safety gate to always pass + set compat to use dry-run
        import app.core.pipeline.agent_team_runner as runner_mod
        monkeypatch.setattr(
            runner_mod, "_validate_real_mode_gate",
            lambda request: {"ok": True, "issues": [], "warnings": []},
        )
        monkeypatch.setattr(
            AgentTeamCompatAdapter,
            "validate_agent_team_contract",
            lambda cls, path: _make_compat_check(True, "pipeline_v2"),
        )

        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="Runner dry-run 测试",
                journal="中文核心",
                run_mode="real",
                budget_cap_cny=10.0,
                agent_team_path=agent_path,
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        types = [e.type for e in events]

        assert "completion" in types
        assert "error" not in types

        # Verify session was written
        runs_dir = tmp_path / "runs"
        session_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
        assert len(session_dirs) == 1

        session_dir = session_dirs[0]
        paper_path = session_dir / "output" / "paper.md"
        assert paper_path.exists(), f"paper.md not found at {paper_path}"
        paper_content = paper_path.read_text(encoding="utf-8")
        assert "Runner dry-run 测试" in paper_content

        # Verify metadata was written
        assert (session_dir / "metadata.json").exists()
        metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["status"] == "completed"
        assert metadata["run_mode"] == "real"

        # Verify events and messages
        assert (session_dir / "logs" / "events.jsonl").exists()
        assert (session_dir / "logs" / "messages.jsonl").exists()

    def test_runner_mock_mode_unchanged(self, tmp_path: Path):
        """Mock mode should still work correctly after dry-run changes."""
        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="Mock still works",
                run_mode="mock",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        assert any(e.type == "completion" for e in events)
        assert not any(e.type == "error" for e in events)

        runs_dir = tmp_path / "runs"
        session_dirs = [p for p in runs_dir.iterdir() if p.is_dir()]
        assert session_dirs
        assert (session_dirs[0] / "output" / "paper.md").exists()
