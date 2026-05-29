from __future__ import annotations

from pathlib import Path

from app.core.agent.feedback_memory import AgentFeedbackMemory


def test_feedback_memory_append_and_summarize(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "agent_feedback.json"
    monkeypatch.setattr(AgentFeedbackMemory, "FILE", file_path)

    store = AgentFeedbackMemory()
    store.append(task_type="quality", accepted=True, signal="计划结构清晰")
    store.append(task_type="quality", accepted=False, signal="步骤太泛")

    summary = store.summarize("quality")

    assert "accepted" in summary
    assert "rejected" in summary
    assert "计划结构清晰" in summary
    assert "步骤太泛" in summary
