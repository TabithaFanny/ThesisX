"""Read-only local run history access for ThesisX runtime sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunHealth:
    status: str
    missing_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RunSummary:
    session_id: str
    created_at: str = ""
    updated_at: str = ""
    topic: str = ""
    journal: str = ""
    run_mode: str = ""
    status: str = "unknown"
    has_paper: bool = False
    has_events: bool = False
    has_messages: bool = False
    has_errors: bool = False
    run_dir: str = ""
    legacy_output_dir: str = ""


@dataclass(frozen=True)
class RunDetail:
    summary: RunSummary
    request: dict[str, Any]
    metadata: dict[str, Any]
    output_files: dict[str, str]
    event_count: int
    message_count: int
    health: RunHealth


class RunHistoryReader:
    """Read-only scanner for ThesisX local run history."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or (Path.home() / ".wenbiao")).expanduser()
        self.runs_root = self.base_dir / "runs"
        self.output_root = self.base_dir / "output"

    def list_runs(self, limit: int | None = None) -> list[RunSummary]:
        session_ids = self._collect_session_ids()
        summaries = [self._build_summary(session_id) for session_id in session_ids]
        summaries.sort(
            key=lambda item: (item.updated_at or item.created_at or "", item.session_id),
            reverse=True,
        )
        if limit is not None:
            return summaries[:limit]
        return summaries

    def get_run(self, session_id: str) -> RunDetail:
        summary = self._build_summary(session_id)
        request = self.read_request(session_id)
        metadata = self.read_metadata(session_id)
        events = self.read_events(session_id)
        messages = self.read_messages(session_id)
        health = self.detect_run_health(session_id)
        output_files = self.read_output_files(session_id)
        return RunDetail(
            summary=summary,
            request=request,
            metadata=metadata,
            output_files=output_files,
            event_count=len(events),
            message_count=len(messages),
            health=health,
        )

    def read_metadata(self, session_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(session_id)
        metadata = self._read_json(run_dir / "metadata.json")
        if metadata:
            return metadata
        legacy_dir = self._legacy_dir(session_id)
        return self._read_json(legacy_dir / "metadata.json")

    def read_request(self, session_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(session_id)
        request = self._read_json(run_dir / "request.json")
        if request:
            return request
        legacy_dir = self._legacy_dir(session_id)
        return self._read_json(legacy_dir / "request.json")

    def read_events(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        run_dir = self._resolve_run_dir(session_id)
        events = self._read_jsonl(run_dir / "logs" / "events.jsonl", limit=limit)
        return events

    def read_messages(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        run_dir = self._resolve_run_dir(session_id)
        messages = self._read_jsonl(run_dir / "logs" / "messages.jsonl", limit=limit)
        return messages

    def read_output_files(self, session_id: str) -> dict[str, str]:
        run_dir = self._resolve_run_dir(session_id)
        output_dir = run_dir / "output"
        legacy_dir = self._legacy_dir(session_id)
        files: dict[str, str] = {}
        candidates = {
            "outline_json": output_dir / "outline.json",
            "paper_md": output_dir / "paper.md",
            "quality_report_json": output_dir / "quality_report.json",
        }
        legacy_candidates = {
            "outline_json": legacy_dir / "outline.json",
            "paper_md": legacy_dir / "paper.md",
            "quality_report_json": legacy_dir / "quality_report.json",
        }
        for key, path in candidates.items():
            if path.exists():
                files[key] = str(path)
            elif legacy_candidates[key].exists():
                files[key] = str(legacy_candidates[key])
        return files

    def detect_run_health(self, session_id: str) -> RunHealth:
        summary = self._build_summary(session_id)
        missing_files: list[str] = []
        notes: list[str] = []

        request = self.read_request(session_id)
        metadata = self.read_metadata(session_id)
        if not request:
            missing_files.append("request.json")
        if not metadata:
            missing_files.append("metadata.json")
            notes.append("缺少 metadata.json，已尝试从目录结构推断基础信息。")
        if not summary.has_paper:
            missing_files.append("paper.md")
        if not summary.has_events:
            missing_files.append("logs/events.jsonl")
            notes.append("未发现事件日志。旧 output 历史可能本来就没有该文件。")
        if not summary.has_messages:
            missing_files.append("logs/messages.jsonl")
            notes.append("未发现消息日志。旧 output 历史可能本来就没有该文件。")

        if missing_files:
            status = "broken" if "request.json" in missing_files else "warning"
        elif summary.has_errors:
            status = "warning"
            notes.append("存在错误日志，建议人工复核该 run。")
        else:
            status = "ok"

        if summary.legacy_output_dir and not summary.run_dir:
            notes.append("该 run 来自旧 output 兼容目录。")

        return RunHealth(status=status, missing_files=missing_files, notes=notes)

    def _collect_session_ids(self) -> list[str]:
        ids: set[str] = set()
        if self.runs_root.exists():
            ids.update(path.name for path in self.runs_root.iterdir() if path.is_dir())
        if self.output_root.exists():
            ids.update(path.name for path in self.output_root.iterdir() if path.is_dir())
        return sorted(ids)

    def _build_summary(self, session_id: str) -> RunSummary:
        run_dir = self._resolve_run_dir(session_id)
        legacy_dir = self._legacy_dir(session_id)
        metadata = self.read_metadata(session_id)
        request = self.read_request(session_id)
        output_files = self.read_output_files(session_id)

        created_at = str(metadata.get("created_at") or request.get("created_at") or "")
        updated_at = str(metadata.get("completed_at") or metadata.get("updated_at") or created_at)
        topic = str(metadata.get("topic") or request.get("topic") or "")
        journal = str(metadata.get("journal") or request.get("journal") or "")
        run_mode = str(metadata.get("run_mode") or request.get("run_mode") or "")
        status = str(metadata.get("status") or self._infer_status(output_files))

        has_events = (run_dir / "logs" / "events.jsonl").exists()
        has_messages = (run_dir / "logs" / "messages.jsonl").exists()
        has_errors = (run_dir / "logs" / "errors.log").exists() and (run_dir / "logs" / "errors.log").stat().st_size > 0
        has_paper = "paper_md" in output_files

        is_new_run = run_dir.parent == self.runs_root and self._is_new_run_dir(run_dir)
        run_dir_value = str(run_dir) if is_new_run else ""
        legacy_dir_value = str(legacy_dir) if legacy_dir.exists() else ""
        if metadata.get("run_dir"):
            run_dir_value = str(metadata["run_dir"])
        if metadata.get("legacy_output_dir"):
            legacy_dir_value = str(metadata["legacy_output_dir"])

        return RunSummary(
            session_id=session_id,
            created_at=created_at,
            updated_at=updated_at,
            topic=topic,
            journal=journal,
            run_mode=run_mode,
            status=status,
            has_paper=has_paper,
            has_events=has_events,
            has_messages=has_messages,
            has_errors=has_errors,
            run_dir=run_dir_value,
            legacy_output_dir=legacy_dir_value,
        )

    def _resolve_run_dir(self, session_id: str) -> Path:
        run_dir = self.runs_root / session_id
        if self._is_new_run_dir(run_dir):
            return run_dir
        return self.output_root / session_id

    def _legacy_dir(self, session_id: str) -> Path:
        return self.output_root / session_id

    @staticmethod
    def _infer_status(output_files: dict[str, str]) -> str:
        if "paper_md" in output_files:
            return "completed"
        if "outline_json" in output_files:
            return "partial"
        return "unknown"

    @staticmethod
    def _is_new_run_dir(path: Path) -> bool:
        return path.is_dir() and any(
            candidate.exists()
            for candidate in (
                path / "request.json",
                path / "metadata.json",
                path / "output",
                path / "logs",
                path / "context",
            )
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            if not path.exists():
                return {}
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        items: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(data, dict):
                        items.append(data)
            if limit is not None:
                return items[-limit:]
            return items
        except OSError:
            return []
