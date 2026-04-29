"""Pipeline event types, stage constants, and helper constructors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Stage constants
# ---------------------------------------------------------------------------

STANDARD_STAGES: list[str] = [
    "initialized",
    "architect_running",
    "architect_done",
    "advisor_running",
    "topic_done",
    "researcher_running",
    "literature_done",
    "writer_running",
    "writing_done",
    "reviewer_running",
    "review_done",
    "polisher_running",
    "polish_done",
    "export_done",
    "cancelled",
    "failed",
]

STAGE_PROGRESS: dict[str, int] = {
    "initialized": 0,
    "architect_done": 15,
    "topic_done": 30,
    "literature_done": 45,
    "writing_done": 65,
    "review_done": 85,
    "polish_done": 95,
    "export_done": 100,
    "failed": 100,
    "cancelled": 100,
}

AGENT_LABELS: dict[str, str] = {
    "architect": "🧭 大纲规划",
    "advisor": "🎯 选题分析",
    "researcher": "📚 文献整理",
    "writer": "✍️ 初稿撰写",
    "reviewer": "🔍 审稿反馈",
    "polisher": "✨ 润色定稿",
    "system": "⚙ 系统",
}

# ---------------------------------------------------------------------------
# Event type literal
# ---------------------------------------------------------------------------

EventType = Literal[
    "state",
    "token",
    "message",
    "cost",
    "error",
    "completion",
    "artifact",
    "validation",
    "cancelled",
]

# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------

ERROR_CODES: set[str] = {
    "AGENT_PATH_EMPTY",
    "AGENT_PATH_INVALID",
    "DEPENDENCY_MISSING",
    "API_KEY_MISSING",
    "IMPORT_FAILED",
    "ARCHITECT_FAILED",
    "RUNNER_FAILED",
    "PAPER_NOT_FOUND",
    "BUDGET_EXCEEDED",
    "USER_CANCELLED",
    "IMPORT_TO_EDITOR_FAILED",
}

# ---------------------------------------------------------------------------
# PaperEvent
# ---------------------------------------------------------------------------


@dataclass
class PaperEvent:
    """Unified event type emitted by pipeline runners."""

    type: EventType
    agent: str = ""
    stage: str = ""
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe serialization."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


# ---------------------------------------------------------------------------
# Helper constructors
# ---------------------------------------------------------------------------


def make_state_event(
    stage: str,
    agent: str = "",
    message: str = "",
) -> PaperEvent:
    return PaperEvent(type="state", agent=agent, stage=stage, message=message)


def make_token_event(
    content: str,
    agent: str = "",
    is_final: bool = False,
) -> PaperEvent:
    return PaperEvent(
        type="token",
        agent=agent,
        payload={"content": content, "is_final": is_final},
    )


def make_error_event(
    message: str,
    agent: str = "",
    stage: str = "",
    code: str = "RUNNER_FAILED",
) -> PaperEvent:
    return PaperEvent(
        type="error",
        agent=agent,
        stage=stage,
        message=message,
        payload={"code": code},
    )


def make_completion_event(
    markdown: str = "",
    word_count: int = 0,
    total_cost_cny: float = 0.0,
    session_id: str = "",
) -> PaperEvent:
    return PaperEvent(
        type="completion",
        payload={
            "markdown": markdown,
            "word_count": word_count,
            "total_cost_cny": total_cost_cny,
            "session_id": session_id,
        },
    )


def make_cost_event(
    agent: str,
    cost_cny: float,
    cumulative_cny: float,
    budget_cap_cny: float,
) -> PaperEvent:
    return PaperEvent(
        type="cost",
        agent=agent,
        payload={
            "cost_cny": cost_cny,
            "cumulative_cny": cumulative_cny,
            "budget_cap_cny": budget_cap_cny,
            "budget_pct": (
                cumulative_cny / budget_cap_cny * 100
                if budget_cap_cny > 0
                else 0
            ),
        },
    )


def make_artifact_event(
    agent: str,
    path: str,
    stage: str = "",
) -> PaperEvent:
    return PaperEvent(
        type="artifact",
        agent=agent,
        stage=stage,
        payload={"path": path},
    )
