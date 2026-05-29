"""Persistent feedback memory for agent outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentFeedbackRecord:
    task_type: str
    project_id: str
    accepted: bool
    signal: str
    created_at: str


class AgentFeedbackMemory:
    """Store lightweight acceptance/rejection signals for agent tasks."""

    FILE = Path.home() / ".wenbiao" / "agent_feedback.json"

    def load(self) -> list[AgentFeedbackRecord]:
        if not self.FILE.exists():
            return []
        try:
            data = json.loads(self.FILE.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return []
            return [
                AgentFeedbackRecord(
                    task_type=str(item.get("task_type", "")),
                    project_id=str(item.get("project_id", "")),
                    accepted=bool(item.get("accepted", False)),
                    signal=str(item.get("signal", "")),
                    created_at=str(item.get("created_at", "")),
                )
                for item in data
            ]
        except Exception:
            return []

    def save(self, records: list[AgentFeedbackRecord]) -> None:
        self.FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "task_type": item.task_type,
                "project_id": item.project_id,
                "accepted": item.accepted,
                "signal": item.signal,
                "created_at": item.created_at,
            }
            for item in records
        ]
        self.FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def append(self, *, task_type: str, project_id: str = "", accepted: bool, signal: str) -> None:
        records = self.load()
        records.append(
            AgentFeedbackRecord(
                task_type=task_type,
                project_id=project_id,
                accepted=accepted,
                signal=signal.strip(),
                created_at=_now(),
            )
        )
        self.save(records[-50:])

    def summarize(self, task_type: str, project_id: str = "", limit: int = 8) -> str:
        records = [
            item
            for item in self.load()
            if item.task_type == task_type and (not project_id or item.project_id == project_id)
        ][-limit:]
        if not records:
            return ""
        lines = ["Recent feedback memory:"]
        for item in records:
            verdict = "accepted" if item.accepted else "rejected"
            lines.append(f"- {verdict}: {item.signal}")
        return "\n".join(lines)
