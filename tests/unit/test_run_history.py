from __future__ import annotations

import json
from pathlib import Path

from app.core.pipeline.run_history import RunHealth, RunHistoryReader


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class TestRunHistoryReader:
    def test_list_runs(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess001"
        _write_json(run_dir / "request.json", {"topic": "题目A", "journal": "CSSCI", "run_mode": "mock"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess001", "status": "completed", "created_at": "2026-05-01T10:00:00"})
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "state", "stage": "initialized"}])
        _write_jsonl(run_dir / "logs" / "messages.jsonl", [{"message": "ok"}])

        reader = RunHistoryReader(base_dir=tmp_path)
        runs = reader.list_runs()

        assert len(runs) == 1
        assert runs[0].session_id == "sess001"
        assert runs[0].has_paper is True
        assert runs[0].has_events is True
        assert runs[0].has_messages is True

    def test_get_run_complete(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess002"
        _write_json(run_dir / "request.json", {"topic": "题目B", "journal": "北大核心", "run_mode": "mock"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess002", "status": "completed", "topic": "题目B"})
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "state"}, {"type": "completion"}])
        _write_jsonl(run_dir / "logs" / "messages.jsonl", [{"message": "m1"}])
        _write_json(run_dir / "output" / "outline.json", {"outline": []})
        (run_dir / "output" / "paper.md").parent.mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")
        _write_json(run_dir / "output" / "quality_report.json", {"word_count": 123})

        reader = RunHistoryReader(base_dir=tmp_path)
        detail = reader.get_run("sess002")

        assert detail.summary.session_id == "sess002"
        assert detail.request["topic"] == "题目B"
        assert detail.metadata["status"] == "completed"
        assert detail.event_count == 2
        assert detail.message_count == 1
        assert "paper_md" in detail.output_files
        assert detail.health.status == "ok"

    def test_missing_metadata_does_not_crash(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess003"
        _write_json(run_dir / "request.json", {"topic": "题目C"})
        (run_dir / "output").mkdir(parents=True, exist_ok=True)

        reader = RunHistoryReader(base_dir=tmp_path)
        detail = reader.get_run("sess003")

        assert detail.metadata == {}
        assert detail.summary.topic == "题目C"
        assert detail.health.status in {"warning", "broken"}

    def test_missing_events_warns(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess004"
        _write_json(run_dir / "request.json", {"topic": "题目D"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess004", "status": "completed"})
        (run_dir / "output").mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")

        reader = RunHistoryReader(base_dir=tmp_path)
        health = reader.detect_run_health("sess004")

        assert isinstance(health, RunHealth)
        assert health.status == "warning"
        assert "logs/events.jsonl" in health.missing_files

    def test_missing_paper_has_paper_false(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess005"
        _write_json(run_dir / "request.json", {"topic": "题目E"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess005"})
        _write_jsonl(run_dir / "logs" / "events.jsonl", [{"type": "state"}])

        reader = RunHistoryReader(base_dir=tmp_path)
        summary = reader.get_run("sess005").summary

        assert summary.has_paper is False

    def test_detect_output_files(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess006"
        _write_json(run_dir / "request.json", {"topic": "题目F"})
        _write_json(run_dir / "metadata.json", {"session_id": "sess006"})
        _write_json(run_dir / "output" / "outline.json", {"outline": []})
        (run_dir / "output" / "paper.md").parent.mkdir(parents=True, exist_ok=True)
        (run_dir / "output" / "paper.md").write_text("# paper", encoding="utf-8")

        reader = RunHistoryReader(base_dir=tmp_path)
        files = reader.read_output_files("sess006")

        assert "outline_json" in files
        assert "paper_md" in files

    def test_compat_old_output_directory(self, tmp_path: Path):
        legacy_dir = tmp_path / "output" / "legacy001"
        _write_json(legacy_dir / "request.json", {"topic": "旧目录题目", "journal": "旧刊物", "run_mode": "mock"})
        _write_json(legacy_dir / "metadata.json", {"session_id": "legacy001", "status": "completed"})
        (legacy_dir / "paper.md").write_text("# old paper", encoding="utf-8")
        _write_json(legacy_dir / "outline.json", {"outline": []})

        reader = RunHistoryReader(base_dir=tmp_path)
        detail = reader.get_run("legacy001")

        assert detail.summary.session_id == "legacy001"
        assert detail.summary.legacy_output_dir.endswith("legacy001")
        assert detail.summary.run_dir == ""
        assert detail.summary.has_paper is True
        assert detail.health.status == "warning"

    def test_read_only_does_not_modify_files(self, tmp_path: Path):
        run_dir = tmp_path / "runs" / "sess007"
        _write_json(run_dir / "request.json", {"topic": "只读测试"})
        before = (run_dir / "request.json").read_text(encoding="utf-8")

        reader = RunHistoryReader(base_dir=tmp_path)
        _ = reader.get_run("sess007")

        after = (run_dir / "request.json").read_text(encoding="utf-8")
        assert before == after
