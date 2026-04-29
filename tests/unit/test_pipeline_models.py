"""Tests for app.core.pipeline.models — dataclass construction and defaults."""

from pathlib import Path

from app.core.pipeline.models import (
    ArchitectOutput,
    PaperRequest,
    PaperResult,
    QualityCheckResult,
)


class TestPaperRequest:
    def test_defaults(self):
        req = PaperRequest(topic="test")
        assert req.topic == "test"
        assert req.generation_type == "paper_draft"
        assert req.journal == "中文核心"
        assert req.run_mode == "mock"
        assert req.runner_kind == "sequential"
        assert req.auto_polish is False
        assert req.budget_cap_cny == 10.0
        assert req.agent_team_path == ""
        assert req.base_dir is None
        assert req.api_key == ""
        assert req.base_url == ""
        assert req.model == ""
        assert req.session_id is None

    def test_custom_values(self):
        req = PaperRequest(
            topic="AI governance",
            journal="CSSCI",
            run_mode="real",
            budget_cap_cny=50.0,
            agent_team_path="/opt/agent-team",
            api_key="sk-xxx",
        )
        assert req.topic == "AI governance"
        assert req.journal == "CSSCI"
        assert req.run_mode == "real"
        assert req.budget_cap_cny == 50.0
        assert req.api_key == "sk-xxx"


class TestArchitectOutput:
    def test_defaults(self):
        out = ArchitectOutput()
        assert out.paper_title == ""
        assert out.central_argument == ""
        assert out.argument_chain == []
        assert out.outline == []
        assert out.missing_materials == []
        assert out.writer_instructions == ""

    def test_with_values(self):
        out = ArchitectOutput(
            paper_title="Test Paper",
            central_argument="This is the argument",
            argument_chain=["a", "b"],
            outline=[{"section_number": 1, "title": "Intro"}],
        )
        assert out.paper_title == "Test Paper"
        assert len(out.argument_chain) == 2
        assert len(out.outline) == 1


class TestQualityCheckResult:
    def test_defaults(self):
        q = QualityCheckResult()
        assert q.word_count == 0
        assert q.has_abstract is False
        assert q.warnings == []

    def test_with_values(self):
        q = QualityCheckResult(
            word_count=5000,
            has_abstract=True,
            citation_warning_count=3,
            warnings=["warning 1"],
        )
        assert q.word_count == 5000
        assert q.has_abstract is True
        assert q.citation_warning_count == 3
        assert len(q.warnings) == 1


class TestPaperResult:
    def test_defaults(self):
        r = PaperResult()
        assert r.markdown == ""
        assert r.word_count == 0
        assert r.total_cost_cny == 0.0
        assert r.run_mode == "mock"
