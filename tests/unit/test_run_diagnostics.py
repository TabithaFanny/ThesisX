from __future__ import annotations

import json
from pathlib import Path

from app.core.pipeline.run_diagnostics import RunDiagnostics


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class TestRunDiagnostics:
    def test_complete_run_is_ok(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess001"
        _write_json(run_dir / "request.json", {"topic": "题目A", "journal": "CSSCI", "run_mode": "mock"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess001", "status": "completed", "updated_at": "2026-05-01T11:00:00"})
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "state"}])
        _write_jsonl(run_dir / "logs" / "messages.jsonl", [{"message": "ok"}])
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")
        _write_json(run_dir / "output" / "outline.json", {"outline": []})
        _write_json(run_dir / "output" / "quality_report.json", {"word_count": 100})

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess001")
        assert report.health_status == "ok"
        assert report.has_paper is True
        assert report.has_errors is False

    def test_missing_request_is_broken(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess002"
        _write_json(run_dir / "metadata.json", {"session_id": "sess002"})

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess002")
        assert report.health_status == "broken"
        assert "request.json" in report.missing_files

    def test_missing_metadata_is_warning(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess003"
        _write_json(run_dir / "request.json", {"topic": "题目C"})

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess003")
        assert report.health_status == "warning"
        assert "metadata.json" in report.missing_files

    def test_missing_events_messages_is_warning(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess004"
        _write_json(run_dir / "request.json", {"topic": "题目D"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess004"})
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess004")
        assert report.health_status == "warning"
        assert "logs/events.jsonl" in report.missing_files
        assert "logs/messages.jsonl" in report.missing_files

    def test_errors_log_non_empty_is_warning(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess005"
        _write_json(run_dir / "request.json", {"topic": "题目E"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess005"})
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "error"}])
        _write_jsonl(run_dir / "logs" / "messages.jsonl", [{"message": "oops"}])
        (run_dir / "logs" / "errors.log").parent.mkdir(parents=True, exist_ok=True)
        (run_dir / "logs" / "errors.log").write_text("boom", encoding="utf-8")
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess005")
        assert report.health_status == "warning"
        assert report.has_errors is True

    def test_legacy_output_run_is_supported(self, tmp_path: Path):
        legacy_dir = tmp_path / "output" / "legacy001"
        _write_json(legacy_dir / "request.json", {"topic": "旧题目", "journal": "旧刊物"})
        _write_json(legacy_dir / "metadata.json", {"session_id": "legacy001", "created_at": "2026-05-01T09:00:00"})
        (legacy_dir / "paper.md").write_text("# legacy", encoding="utf-8")

        report = RunDiagnostics(base_dir=tmp_path).diagnose_run("legacy001")
        assert report.legacy_output_dir.endswith("legacy001")
        assert report.run_dir == ""
        assert report.health_status == "warning"

    def test_diagnose_latest_sorted_by_updated_or_created(self, tmp_path: Path):
        run1 = tmp_path / "runs" / "sess010"
        _write_json(run1 / "request.json", {"topic": "旧"})
        _write_json(run1 / "metadata.json", {"session_id": "sess010", "updated_at": "2026-05-01T08:00:00"})

        run2 = tmp_path / "runs" / "sess011"
        _write_json(run2 / "request.json", {"topic": "新"})
        _write_json(run2 / "metadata.json", {"session_id": "sess011", "updated_at": "2026-05-01T09:00:00"})

        reports = RunDiagnostics(base_dir=tmp_path).diagnose_latest(limit=2)
        assert [report.session_id for report in reports] == ["sess011", "sess010"]

    def test_diagnostics_does_not_write_files(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess012"
        _write_json(run_dir / "request.json", {"topic": "只读"})
        before = (run_dir / "request.json").read_text(encoding="utf-8")

        _ = RunDiagnostics(base_dir=tmp_path).diagnose_run("sess012")

        after = (run_dir / "request.json").read_text(encoding="utf-8")
        assert before == after

    def test_render_single_report_markdown_and_json(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess013"
        _write_json(run_dir / "request.json", {"topic": "导出题目", "journal": "CSSCI", "run_mode": "mock"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess013", "status": "completed"})
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "state"}])
        _write_jsonl(run_dir / "logs" / "messages.jsonl", [{"message": "ok"}])
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")

        diagnostics = RunDiagnostics(base_dir=tmp_path)
        report = diagnostics.diagnose_run("sess013")
        markdown = diagnostics.render_report_markdown(report)
        json_text = diagnostics.render_report_json(report)

        assert "ThesisX Run Diagnostics Report" in markdown
        assert "sess013" in markdown
        assert json.loads(json_text)["session_id"] == "sess013"

    def test_export_single_report_to_files(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess014"
        _write_json(run_dir / "request.json", {"topic": "导出单 run"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess014"})

        diagnostics = RunDiagnostics(base_dir=tmp_path)
        md_path = tmp_path / "reports" / "sess014.md"
        json_path = tmp_path / "reports" / "sess014.json"

        diagnostics.export_report("sess014", md_path, format="markdown")
        diagnostics.export_report("sess014", json_path, format="json")

        assert md_path.exists()
        assert json_path.exists()
        assert "sess014" in md_path.read_text(encoding="utf-8")
        assert json.loads(json_path.read_text(encoding="utf-8"))["session_id"] == "sess014"

    def test_render_and_export_latest_reports(self, tmp_path: Path):
        run1 = tmp_path / "runs" / "sess020"
        _write_json(run1 / "request.json", {"topic": "A"})
        _write_json(run1 / "metadata.json", {"session_id": "sess020", "updated_at": "2026-05-01T08:00:00"})

        run2 = tmp_path / "runs" / "sess021"
        _write_json(run2 / "request.json", {"topic": "B"})
        _write_json(run2 / "metadata.json", {"session_id": "sess021", "updated_at": "2026-05-01T09:00:00"})

        diagnostics = RunDiagnostics(base_dir=tmp_path)
        markdown = diagnostics.render_latest_markdown(limit=2)
        json_text = diagnostics.render_latest_json(limit=2)
        out_md = tmp_path / "reports" / "latest.md"
        out_json = tmp_path / "reports" / "latest.json"

        diagnostics.export_latest(out_md, limit=2, format="markdown")
        diagnostics.export_latest(out_json, limit=2, format="json")

        assert "ThesisX Latest Run Diagnostics" in markdown
        assert "sess021" in markdown
        latest_payload = json.loads(json_text)
        assert latest_payload["count"] == 2
        assert latest_payload["reports"][0]["session_id"] == "sess021"
        assert out_md.exists()
        assert out_json.exists()

    def test_export_does_not_modify_run_files(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess022"
        _write_json(run_dir / "request.json", {"topic": "保持只读"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess022"})
        before = (run_dir / "request.json").read_text(encoding="utf-8")

        diagnostics = RunDiagnostics(base_dir=tmp_path)
        diagnostics.export_report("sess022", tmp_path / "reports" / "sess022.md", format="markdown")

        after = (run_dir / "request.json").read_text(encoding="utf-8")
        assert before == after
