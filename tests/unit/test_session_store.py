from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.pipeline.agent_team_runner import AgentTeamRunner
from app.core.pipeline.events import make_state_event
from app.core.pipeline.models import PaperRequest
from app.core.pipeline.session_store import SessionStore


class TestSessionStore:
    def test_creates_directory_structure(self, tmp_path: Path):
        request = PaperRequest(topic="目录结构测试", base_dir=tmp_path)
        store = SessionStore.create_session("sess123", request)

        assert store.paths.run_dir.exists()
        assert store.paths.context_dir.exists()
        assert store.paths.logs_dir.exists()
        assert store.paths.output_dir.exists()
        assert store.paths.artifacts_dir.exists()
        assert store.paths.imported_files_dir.exists()
        assert store.paths.generated_dir.exists()
        assert store.paths.legacy_dir.exists()

    def test_writes_request_and_metadata(self, tmp_path: Path):
        request = PaperRequest(topic="写入测试", journal="CSSCI", base_dir=tmp_path)
        store = SessionStore.create_session("sess123", request)

        store.write_request(request)
        store.write_metadata({"session_id": "sess123", "status": "completed"})

        request_data = json.loads(store.paths.request_json.read_text(encoding="utf-8"))
        metadata_data = json.loads(store.paths.metadata_json.read_text(encoding="utf-8"))

        assert request_data["topic"] == "写入测试"
        assert request_data["journal"] == "CSSCI"
        assert metadata_data["session_id"] == "sess123"
        assert (store.paths.legacy_dir / "request.json").exists()
        assert (store.paths.legacy_dir / "metadata.json").exists()

    def test_build_metadata_contains_stable_fields(self, tmp_path: Path):
        request = PaperRequest(topic="元数据测试", journal="AMI", run_mode="mock", base_dir=tmp_path)
        store = SessionStore.create_session("sess123", request)
        store.write_output_file("outline.json", {"outline": []})
        store.append_event(make_state_event("initialized"))
        store.append_message({"message": "hello"})

        metadata = store.build_metadata(
            request=request,
            status="completed",
            created_at="2026-05-01T10:00:00",
            updated_at="2026-05-01T10:05:00",
        )

        assert metadata["session_id"] == "sess123"
        assert metadata["run_dir"].endswith("/runs/sess123")
        assert metadata["legacy_output_dir"].endswith("/output/sess123")
        assert metadata["status"] == "completed"
        assert metadata["run_mode"] == "mock"
        assert metadata["topic"] == "元数据测试"
        assert metadata["journal"] == "AMI"
        assert metadata["event_count"] == 1
        assert metadata["message_count"] == 1
        assert metadata["has_errors"] is False
        assert "outline_json" in metadata["output_files"]

    def test_writes_context_markdown(self, tmp_path: Path, monkeypatch):
        # Prevent loading real skills so we test the placeholder path
        monkeypatch.setattr("app.core.skills.loader.SkillLoader.load_local_skills", lambda self: [])
        request = PaperRequest(
            topic="上下文测试",
            run_mode="mock",
            budget_cap_cny=8.0,
            base_dir=tmp_path,
        )
        store = SessionStore.create_session("sess123", request)

        store.write_context_files(request)

        assert "上下文测试" in store.paths.paper_request_md.read_text(encoding="utf-8")
        assert "当前阶段不接真实 API" in store.paths.user_constraints_md.read_text(encoding="utf-8")
        assert "未启用任何本地技能" in store.paths.selected_skills_md.read_text(encoding="utf-8")

    def test_events_jsonl_is_append_only(self, tmp_path: Path):
        request = PaperRequest(topic="事件测试", base_dir=tmp_path)
        store = SessionStore.create_session("sess123", request)

        store.append_event(make_state_event("initialized"))
        store.append_event(make_state_event("architect_done", agent="architect"))

        lines = store.paths.events_jsonl.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["stage"] == "initialized"
        assert json.loads(lines[1])["stage"] == "architect_done"


class TestMockModeRunStore:
    def test_mock_mode_writes_new_run_layout(self, tmp_path: Path):
        async def _run() -> list:
            runner = AgentTeamRunner()
            request = PaperRequest(
                topic="Mock 落盘测试",
                run_mode="mock",
                base_dir=tmp_path,
            )
            return [event async for event in runner.run(request)]

        events = asyncio.run(_run())
        completion = [event for event in events if event.type == "completion"]
        assert completion

        runs_dir = tmp_path / "runs"
        session_dirs = [path for path in runs_dir.iterdir() if path.is_dir()]
        assert len(session_dirs) == 1
        session_dir = session_dirs[0]

        assert (session_dir / "logs" / "events.jsonl").exists()
        assert (session_dir / "logs" / "messages.jsonl").exists()
        assert (session_dir / "output" / "outline.json").exists()
        assert (session_dir / "output" / "paper.md").exists()
        assert (session_dir / "output" / "quality_report.json").exists()
        assert (session_dir / "metadata.json").exists()
        assert (session_dir / "context" / "paper_request.md").exists()

        event_lines = (session_dir / "logs" / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
        event_types = [json.loads(line)["type"] for line in event_lines]
        assert "state" in event_types
        assert "artifact" in event_types
        assert "completion" in event_types

        message_lines = (session_dir / "logs" / "messages.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert message_lines

        metadata = json.loads((session_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["session_id"] == session_dir.name
        assert metadata["run_dir"].endswith(f"/runs/{session_dir.name}")
        assert metadata["legacy_output_dir"].endswith(f"/output/{session_dir.name}")
        assert metadata["status"] == "completed"
        assert metadata["topic"] == "Mock 落盘测试"
        assert metadata["run_mode"] == "mock"
        assert metadata["event_count"] >= 1
        assert metadata["message_count"] >= 1
        assert "paper_md" in metadata["output_files"]

        legacy_output_dir = tmp_path / "output" / session_dir.name
        assert (legacy_output_dir / "request.json").exists()
        assert (legacy_output_dir / "outline.json").exists()
        assert (legacy_output_dir / "paper.md").exists()
        assert (legacy_output_dir / "metadata.json").exists()
