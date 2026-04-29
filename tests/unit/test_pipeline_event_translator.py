"""Tests for the Agent Team → PaperEvent translator."""

from unittest.mock import MagicMock

from app.core.pipeline.agent_team_runner import _translate_event
from app.core.pipeline.events import PaperEvent


# Create mock event classes to simulate Agent Team events
class MockTokenStreamEvent:
    def __init__(self, agent="writer", content="hello", is_final=False):
        self.agent = agent
        self.content = content
        self.is_final = is_final


class MockStateUpdateEvent:
    def __init__(self, from_stage="a", to_stage="b", agent="writer"):
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.agent = agent


class MockCostUpdateEvent:
    def __init__(self, agent="writer", cost_cny=0.5, cumulative_cny=2.0, budget_cap_cny=10.0):
        self.agent = agent
        self.cost_cny = cost_cny
        self.cumulative_cny = cumulative_cny
        self.budget_cap_cny = budget_cap_cny


class MockAgentMessageEvent:
    def __init__(self, agent="writer", stage="writing", raw_content="done", token_count=100, is_handoff=False):
        self.agent = agent
        self.stage = stage
        self.raw_content = raw_content
        self.token_count = token_count
        self.is_handoff = is_handoff


class MockErrorEvent:
    def __init__(self, agent="writer", stage="writing", message="failed"):
        self.agent = agent
        self.stage = stage
        self.message = message


class MockCompletionEvent:
    def __init__(self, session_id="abc", word_count=5000, total_cost_cny=3.5, output_path="/tmp/paper.md"):
        self.session_id = session_id
        self.word_count = word_count
        self.total_cost_cny = total_cost_cny
        self.output_path = output_path


class MockHumanInterruptEvent:
    def __init__(self, command="/pause"):
        self.command = command


def _make_api():
    """Build a mock API dict with the mock event classes."""
    return {
        "TokenStreamEvent": MockTokenStreamEvent,
        "StateUpdateEvent": MockStateUpdateEvent,
        "CostUpdateEvent": MockCostUpdateEvent,
        "AgentMessageEvent": MockAgentMessageEvent,
        "ErrorEvent": MockErrorEvent,
        "CompletionEvent": MockCompletionEvent,
        "HumanInterruptEvent": MockHumanInterruptEvent,
    }


class TestTranslateTokenStreamEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockTokenStreamEvent(agent="writer", content="hello world", is_final=False)
        ev = _translate_event(raw, api)
        assert ev.type == "token"
        assert ev.agent == "writer"
        assert ev.payload["content"] == "hello world"
        assert ev.payload["is_final"] is False

    def test_final(self):
        api = _make_api()
        raw = MockTokenStreamEvent(is_final=True)
        ev = _translate_event(raw, api)
        assert ev.payload["is_final"] is True


class TestTranslateStateUpdateEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockStateUpdateEvent(from_stage="topic", to_stage="literature", agent="researcher")
        ev = _translate_event(raw, api)
        assert ev.type == "state"
        assert ev.stage == "literature"
        assert ev.agent == "researcher"


class TestTranslateCostUpdateEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockCostUpdateEvent(agent="writer", cost_cny=1.0, cumulative_cny=5.0, budget_cap_cny=10.0)
        ev = _translate_event(raw, api)
        assert ev.type == "cost"
        assert ev.payload["cost_cny"] == 1.0
        assert ev.payload["cumulative_cny"] == 5.0


class TestTranslateAgentMessageEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockAgentMessageEvent(agent="writer", raw_content="Writing complete")
        ev = _translate_event(raw, api)
        assert ev.type == "message"
        assert ev.agent == "writer"
        assert "Writing complete" in ev.message


class TestTranslateErrorEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockErrorEvent(message="API timeout")
        ev = _translate_event(raw, api)
        assert ev.type == "error"
        assert "API timeout" in ev.message


class TestTranslateCompletionEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockCompletionEvent(session_id="xyz", word_count=8000, total_cost_cny=2.5)
        ev = _translate_event(raw, api)
        assert ev.type == "completion"
        assert ev.payload["session_id"] == "xyz"
        assert ev.payload["word_count"] == 8000


class TestTranslateHumanInterruptEvent:
    def test_basic(self):
        api = _make_api()
        raw = MockHumanInterruptEvent(command="/pause")
        ev = _translate_event(raw, api)
        assert ev.type == "message"
        assert "pause" in ev.message


class TestTranslateUnknownEvent:
    def test_unknown_type(self):
        api = _make_api()
        raw = "some random object"
        ev = _translate_event(raw, api)
        assert ev.type == "message"
        assert ev.agent == "system"

    def test_none_fields_safe(self):
        """If an event class exists but has missing attrs, should not crash."""
        api = _make_api()
        raw = MockTokenStreamEvent()
        raw.content = None  # simulate missing
        raw.agent = None
        ev = _translate_event(raw, api)
        assert ev.type == "token"
