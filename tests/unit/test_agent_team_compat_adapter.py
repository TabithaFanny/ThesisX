"""Tests for AgentTeamCompatAdapter and AgentTeamRunner mock-path stability."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter
from app.core.pipeline.models import PaperRequest
from app.core.pipeline.agent_team_runner import AgentTeamRunner


class TokenStreamEvent:
    def __init__(self, agent="writer", content="hello", is_final=False):
        self.agent = agent
        self.content = content
        self.is_final = is_final


class StateUpdateEvent:
    def __init__(self, from_stage="topic_done", to_stage="writing_done", agent="writer"):
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.agent = agent


class CostUpdateEvent:
    def __init__(self, agent="writer", cost_cny=0.5, cumulative_cny=1.0, budget_cap_cny=10.0):
        self.agent = agent
        self.cost_cny = cost_cny
        self.cumulative_cny = cumulative_cny
        self.budget_cap_cny = budget_cap_cny


class AgentMessageEvent:
    def __init__(self, agent="writer", stage="writing_done", raw_content="done", token_count=10, is_handoff=False):
        self.agent = agent
        self.stage = stage
        self.raw_content = raw_content
        self.token_count = token_count
        self.is_handoff = is_handoff
        self.handoff_target = ""


class ErrorEvent:
    def __init__(self, agent="writer", stage="writing_done", message="failed"):
        self.agent = agent
        self.stage = stage
        self.message = message


class CompletionEvent:
    def __init__(self, session_id="abc", word_count=1234, total_cost_cny=2.0, output_path="/tmp/out"):
        self.session_id = session_id
        self.word_count = word_count
        self.total_cost_cny = total_cost_cny
        self.output_path = output_path


class HumanInterruptEvent:
    def __init__(self, command="/pause"):
        self.command = command


class TestTuiEventTranslation:
    def test_tui_event_translation(self):
        token = AgentTeamCompatAdapter.translate_tui_event(TokenStreamEvent())
        assert token.type == "token"
        assert token.payload["content"] == "hello"

        state = AgentTeamCompatAdapter.translate_tui_event(StateUpdateEvent())
        assert state.type == "state"
        assert state.stage == "writing_done"

        cost = AgentTeamCompatAdapter.translate_tui_event(CostUpdateEvent())
        assert cost.type == "cost"
        assert cost.payload["cumulative_cny"] == 1.0

        msg = AgentTeamCompatAdapter.translate_tui_event(AgentMessageEvent())
        assert msg.type == "message"
        assert msg.message == "done"

        err = AgentTeamCompatAdapter.translate_tui_event(ErrorEvent())
        assert err.type == "error"
        assert err.message == "failed"

        completion = AgentTeamCompatAdapter.translate_tui_event(CompletionEvent())
        assert completion.type == "completion"
        assert completion.payload["session_id"] == "abc"

        interrupt = AgentTeamCompatAdapter.translate_tui_event(HumanInterruptEvent())
        assert interrupt.type == "message"
        assert "pause" in interrupt.message


class TestMockModeUnchanged:
    def test_mock_mode_unchanged(self, tmp_path: Path, monkeypatch):
        async def _unexpected_call(*args, **kwargs):
            raise AssertionError("Compat adapter should not be used in mock mode")
            yield  # pragma: no cover

        monkeypatch.setattr(AgentTeamCompatAdapter, "run_external_agent_team", _unexpected_call)

        async def _run():
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="mock mode test",
                run_mode="mock",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        event_types = [event.type for event in events]

        assert "completion" in event_types
        assert (tmp_path / "output").exists()
        assert (tmp_path / "runs").exists()
        session_dirs = [p for p in (tmp_path / "output").iterdir() if p.is_dir()]
        assert session_dirs
        session_dir = session_dirs[0]
        assert (session_dir / "request.json").exists()
        assert (session_dir / "outline.json").exists()
        assert (session_dir / "paper.md").exists()
        assert (session_dir / "metadata.json").exists()
