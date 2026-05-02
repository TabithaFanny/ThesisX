"""Submission management — minimal local storage for submission records."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class SubmissionRecord:
    """A single manuscript submission record."""
    id: str
    paper_title: str
    venue: str
    status: str  # draft | submitted | under_review | revision | accepted | rejected
    submitted_at: str = ""
    rounds: int = 0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "paper_title": self.paper_title,
            "venue": self.venue,
            "status": self.status,
            "submitted_at": self.submitted_at,
            "rounds": self.rounds,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SubmissionRecord":
        return cls(**d)


class SubmissionService:
    """Minimal submission record manager at ~/.wenbiao/submissions/."""

    DIR = Path.home() / ".wenbiao" / "submissions"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.dir = Path(base_dir or self.DIR).expanduser()
        self.dir.mkdir(parents=True, exist_ok=True)

    def add(self, paper_title: str, venue: str) -> SubmissionRecord:
        """Create a new draft submission record."""
        rec = SubmissionRecord(
            id=str(uuid.uuid4())[:8],
            paper_title=paper_title,
            venue=venue,
            status="draft",
        )
        self._save(rec)
        return rec

    def list_all(self) -> list[SubmissionRecord]:
        records = []
        for p in self.dir.glob("*.json"):
            try:
                records.append(SubmissionRecord.from_dict(json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                continue
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def update_status(self, rec_id: str, status: str) -> SubmissionRecord | None:
        rec = self.get(rec_id)
        if rec is None:
            return None
        rec.status = status
        if status == "submitted" and not rec.submitted_at:
            rec.submitted_at = datetime.now().strftime("%Y-%m-%d")
        if status in ("revision", "accepted", "rejected"):
            rec.rounds += 1
        self._save(rec)
        return rec

    def get(self, rec_id: str) -> SubmissionRecord | None:
        p = self.dir / f"{rec_id}.json"
        if not p.exists():
            return None
        try:
            return SubmissionRecord.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            return None

    def delete(self, rec_id: str) -> bool:
        p = self.dir / f"{rec_id}.json"
        if p.exists():
            p.unlink()
            return True
        return False

    def _save(self, rec: SubmissionRecord) -> None:
        p = self.dir / f"{rec.id}.json"
        p.write_text(json.dumps(rec.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
