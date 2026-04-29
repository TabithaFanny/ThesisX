"""Tests for app.core.pipeline.events — PaperEvent, stage constants, helpers."""

import json
from datetime import datetime

from app.core.pipeline.events import (
    AGENT_LABELS,
    ERROR_CODES,
    STAGE_PROGRESS,
    STANDARD_STAGES,
    PaperEvent,
    make_artifact_event,
    make_completion_event,
    make_cost_event,
    make_error_event,
    make_state_event,
    make_token_event,
)


class TestStageConstants:
    def test_standard_stages_is_nonempty(self):
        assert len(STANDARD_STAGES) > 0
        assert "initialized" in STANDARD_STAGES
        assert "export_done" in STANDARD_STAGES
        assert "cancelled" in STANDARD_STAGES
        assert "failed" in STANDARD_STAGES

    def test_stage_progress_covers_terminal_stages(self):
        for stage in ("export_done", "failed", "cancelled"):
            assert stage in STAGE_PROGRESS
            assert STAGE_PROGRESS[stage] == 100

    def test_stage_progress_starts_at_zero(self):
        assert STAGE_PROGRESS["initialized"] == 0

    def test_agent_labels_covers_all_agents(self):
        for agent in ("architect", "advisor", "researcher", "writer", "reviewer", "polisher"):
            assert agent in AGENT_LABELS

    def test_error_codes_is_nonempty(self):
        assert len(ERROR_CODES) > 0
        assert "RUNNER_FAILED" in ERROR_CODES


class TestPaperEvent:
    def test_default_construction(self):
        ev = PaperEvent(type="state")
        assert ev.type == "state"
        assert ev.agent == ""
        assert ev.stage == ""
        assert ev.message == ""
        assert ev.payload == {}
        assert isinstance(ev.timestamp, datetime)

    def test_to_dict(self):
        ev = PaperEvent(type="token", agent="writer", payload={"content": "hello"})
        d = ev.to_dict()
        assert d["type"] == "token"
        assert d["agent"] == "writer"
        assert d["payload"]["content"] == "hello"
        assert isinstance(d["timestamp"], str)  # ISO format

    def test_to_dict_timestamp_is_iso(self):
        ev = PaperEvent(type="state")
        d = ev.to_dict()
        # Should be parseable
        datetime.fromisoformat(d["timestamp"])


class TestMakeStateEvent:
    def test_basic(self):
        ev = make_state_event("architect_running", agent="architect", message="starting")
        assert ev.type == "state"
        assert ev.agent == "architect"
        assert ev.stage == "architect_running"
        assert ev.message == "starting"


class TestMakeTokenEvent:
    def test_basic(self):
        ev = make_token_event("hello world", agent="writer")
        assert ev.type == "token"
        assert ev.payload["content"] == "hello world"
        assert ev.payload["is_final"] is False

    def test_final(self):
        ev = make_token_event("", is_final=True)
        assert ev.payload["is_final"] is True


class TestMakeErrorEvent:
    def test_basic(self):
        ev = make_error_event("something failed", code="ARCHITECT_FAILED")
        assert ev.type == "error"
        assert ev.message == "something failed"
        assert ev.payload["code"] == "ARCHITECT_FAILED"


class TestMakeCompletionEvent:
    def test_basic(self):
        ev = make_completion_event(markdown="# Hello", word_count=100, total_cost_cny=1.5, session_id="abc")
        assert ev.type == "completion"
        assert ev.payload["markdown"] == "# Hello"
        assert ev.payload["word_count"] == 100
        assert ev.payload["total_cost_cny"] == 1.5
        assert ev.payload["session_id"] == "abc"


class TestMakeCostEvent:
    def test_basic(self):
        ev = make_cost_event("writer", 0.5, 2.0, 10.0)
        assert ev.type == "cost"
        assert ev.payload["cost_cny"] == 0.5
        assert ev.payload["cumulative_cny"] == 2.0
        assert ev.payload["budget_pct"] == 20.0

    def test_zero_budget(self):
        ev = make_cost_event("writer", 0.5, 2.0, 0.0)
        assert ev.payload["budget_pct"] == 0


class TestMakeArtifactEvent:
    def test_basic(self):
        ev = make_artifact_event("architect", "/tmp/outline.json", "architect_done")
        assert ev.type == "artifact"
        assert ev.agent == "architect"
        assert ev.payload["path"] == "/tmp/outline.json"
        assert ev.stage == "architect_done"
