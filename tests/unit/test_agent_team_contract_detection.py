"""Tests for AgentTeamCompatAdapter contract detection and path validation."""

from pathlib import Path

from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter


class TestContractDetection:
    def test_detect_tui_runner_contract(self, tmp_path: Path):
        pkg = tmp_path / "academic_agent_team" / "tui"
        pkg.mkdir(parents=True)
        (pkg / "runner.py").write_text("", encoding="utf-8")
        (pkg / "events.py").write_text("", encoding="utf-8")

        result = AgentTeamCompatAdapter.detect_contract(tmp_path)
        assert result.contract_type == "tui_runner"
        assert result.supported is True

    def test_detect_pipeline_v2_contract(self, tmp_path: Path):
        pkg = tmp_path / "academic_agent_team"
        pkg.mkdir(parents=True)
        (pkg / "pipeline_v2.py").write_text("", encoding="utf-8")

        result = AgentTeamCompatAdapter.detect_contract(tmp_path)
        assert result.contract_type == "pipeline_v2"
        assert result.supported is True

    def test_invalid_agent_team_path(self):
        for raw in ("", "未选择", "/path/that/does/not/exist"):
            result = AgentTeamCompatAdapter.validate_agent_team_contract(raw)
            assert result.supported is False
            assert result.contract_type == "unsupported"
            assert result.error_code in {"AGENT_PATH_EMPTY", "AGENT_PATH_INVALID"}
            assert "/Volumes/E/ThesisX/未选择" not in result.reason
