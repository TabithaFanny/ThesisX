"""Read-only diagnostics for local ThesisX runtime runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .run_history import RunDetail, RunHealth, RunHistoryReader


@dataclass(frozen=True)
class RunDiagnosticsReport:
    session_id: str
    status: str
    health_status: str
    run_dir: str
    legacy_output_dir: str
    topic: str
    journal: str
    run_mode: str
    missing_files: list[str] = field(default_factory=list)
    output_files: dict[str, str] = field(default_factory=dict)
    event_count: int = 0
    message_count: int = 0
    has_paper: bool = False
    has_errors: bool = False
    diagnosis_notes: list[str] = field(default_factory=list)
    recommended_next_actions: list[str] = field(default_factory=list)


class RunDiagnostics:
    """Generate read-only health reports from RunHistoryReader."""

    def __init__(self, reader: RunHistoryReader | None = None, *, base_dir: Path | None = None) -> None:
        self.reader = reader or RunHistoryReader(base_dir=base_dir)

    def diagnose_run(self, session_id: str) -> RunDiagnosticsReport:
        detail = self.reader.get_run(session_id)
        return self._build_report(detail)

    def diagnose_latest(self, limit: int = 5) -> list[RunDiagnosticsReport]:
        summaries = self.reader.list_runs(limit=limit)
        return [self.diagnose_run(summary.session_id) for summary in summaries]

    def report_to_dict(self, report: RunDiagnosticsReport) -> dict[str, object]:
        return {
            "session_id": report.session_id,
            "status": report.status,
            "health_status": report.health_status,
            "run_dir": report.run_dir,
            "legacy_output_dir": report.legacy_output_dir,
            "topic": report.topic,
            "journal": report.journal,
            "run_mode": report.run_mode,
            "missing_files": list(report.missing_files),
            "output_files": dict(report.output_files),
            "event_count": report.event_count,
            "message_count": report.message_count,
            "has_paper": report.has_paper,
            "has_errors": report.has_errors,
            "diagnosis_notes": list(report.diagnosis_notes),
            "recommended_next_actions": list(report.recommended_next_actions),
        }

    def render_report_markdown(self, report: RunDiagnosticsReport) -> str:
        lines = [
            "# ThesisX Run Diagnostics Report",
            "",
            f"- Session ID: `{report.session_id}`",
            f"- Status: `{report.status}`",
            f"- Health: `{report.health_status}`",
            f"- Topic: {report.topic or '未知'}",
            f"- Journal: {report.journal or '未知'}",
            f"- Run Mode: `{report.run_mode or '未知'}`",
            f"- Run Dir: `{report.run_dir or 'N/A'}`",
            f"- Legacy Output Dir: `{report.legacy_output_dir or 'N/A'}`",
            f"- Has Paper: `{report.has_paper}`",
            f"- Has Errors: `{report.has_errors}`",
            f"- Event Count: `{report.event_count}`",
            f"- Message Count: `{report.message_count}`",
            "",
            "## Missing Files",
            "",
        ]
        if report.missing_files:
            lines.extend([f"- `{item}`" for item in report.missing_files])
        else:
            lines.append("- None")
        lines.extend(["", "## Output Files", ""])
        if report.output_files:
            lines.extend([f"- `{key}`: `{value}`" for key, value in sorted(report.output_files.items())])
        else:
            lines.append("- None")
        lines.extend(["", "## Diagnosis Notes", ""])
        if report.diagnosis_notes:
            lines.extend([f"- {item}" for item in report.diagnosis_notes])
        else:
            lines.append("- None")
        lines.extend(["", "## Recommended Next Actions", ""])
        if report.recommended_next_actions:
            lines.extend([f"- {item}" for item in report.recommended_next_actions])
        else:
            lines.append("- None")
        lines.append("")
        return "\n".join(lines)

    def render_report_json(self, report: RunDiagnosticsReport) -> str:
        return json.dumps(self.report_to_dict(report), ensure_ascii=False, indent=2)

    def render_latest_markdown(self, limit: int = 5) -> str:
        reports = self.diagnose_latest(limit=limit)
        lines = [
            "# ThesisX Latest Run Diagnostics",
            "",
            f"- Included Runs: `{len(reports)}`",
            "",
        ]
        if not reports:
            lines.append("No runs found.")
            lines.append("")
            return "\n".join(lines)
        for report in reports:
            lines.extend([
                f"## {report.session_id}",
                "",
                f"- Status: `{report.status}`",
                f"- Health: `{report.health_status}`",
                f"- Topic: {report.topic or '未知'}",
                f"- Run Mode: `{report.run_mode or '未知'}`",
                f"- Has Paper: `{report.has_paper}`",
                f"- Has Errors: `{report.has_errors}`",
                f"- Event Count: `{report.event_count}`",
                f"- Message Count: `{report.message_count}`",
            ])
            if report.missing_files:
                lines.append(f"- Missing: {', '.join(report.missing_files)}")
            if report.diagnosis_notes:
                lines.append(f"- Note: {report.diagnosis_notes[0]}")
            lines.append("")
        return "\n".join(lines)

    def render_latest_json(self, limit: int = 5) -> str:
        reports = self.diagnose_latest(limit=limit)
        payload = {
            "count": len(reports),
            "reports": [self.report_to_dict(report) for report in reports],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def export_report(self, session_id: str, destination: Path, *, format: str = "markdown") -> Path:
        report = self.diagnose_run(session_id)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if format == "markdown":
            destination.write_text(self.render_report_markdown(report), encoding="utf-8")
        elif format == "json":
            destination.write_text(self.render_report_json(report), encoding="utf-8")
        else:
            raise ValueError("format must be 'markdown' or 'json'")
        return destination

    def export_latest(self, destination: Path, *, limit: int = 5, format: str = "markdown") -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if format == "markdown":
            destination.write_text(self.render_latest_markdown(limit=limit), encoding="utf-8")
        elif format == "json":
            destination.write_text(self.render_latest_json(limit=limit), encoding="utf-8")
        else:
            raise ValueError("format must be 'markdown' or 'json'")
        return destination

    def _build_report(self, detail: RunDetail) -> RunDiagnosticsReport:
        summary = detail.summary
        health = detail.health
        notes = list(health.notes)
        actions: list[str] = []

        if "request.json" in health.missing_files:
            notes.append("缺少 request.json，无法稳定还原原始运行请求。")
            actions.append("检查该 session 是否写入中断，优先恢复 request.json。")
        if "metadata.json" in health.missing_files:
            actions.append("未来运行建议保留 metadata.json，以便历史扫描稳定读取。")
        if "paper.md" in health.missing_files:
            notes.append("未发现最终论文输出。该 run 可能只完成到 outline 或中途失败。")
            actions.append("检查 output/outline.json 和 errors.log，确认是否停在中间阶段。")
        if "logs/events.jsonl" in health.missing_files:
            actions.append("检查该 run 是否来自旧 output 目录，或确认事件日志写入是否启用。")
        if "logs/messages.jsonl" in health.missing_files:
            actions.append("当前缺少消息摘要日志，无法还原关键阶段说明。")
        if summary.has_errors:
            notes.append("errors.log 存在且非空，说明该 run 有错误记录。")
            actions.append("优先查看 errors.log 和 events.jsonl 中的 error event。")
        if summary.legacy_output_dir and not summary.run_dir:
            notes.append("该 run 仅存在于旧 output 兼容目录。")
            actions.append("后续新运行会优先写入 runs/；旧历史保持只读兼容。")
        if not health.missing_files and not summary.has_errors:
            notes.append("run 结构完整，可用于后续本地历史与诊断读取。")
            actions.append("当前无需修复，可继续作为基线样例。")

        return RunDiagnosticsReport(
            session_id=summary.session_id,
            status=summary.status,
            health_status=health.status,
            run_dir=summary.run_dir,
            legacy_output_dir=summary.legacy_output_dir,
            topic=summary.topic,
            journal=summary.journal,
            run_mode=summary.run_mode,
            missing_files=list(health.missing_files),
            output_files=dict(detail.output_files),
            event_count=detail.event_count,
            message_count=detail.message_count,
            has_paper=summary.has_paper,
            has_errors=summary.has_errors,
            diagnosis_notes=notes,
            recommended_next_actions=actions,
        )
