"""Tests for agent_team_bridge — path validation, dependencies, helpers."""

import json
import os
from pathlib import Path

import pytest

from app.core.pipeline.agent_team_bridge import (
    append_event_jsonl,
    check_dependencies,
    ensure_agent_team_path,
    read_paper_markdown,
    resolve_session_dir,
    write_json,
)


class TestEnsureAgentTeamPath:
    def test_empty_path_raises(self):
        with pytest.raises(FileNotFoundError, match="为空"):
            ensure_agent_team_path("")

    def test_whitespace_path_raises(self):
        with pytest.raises(FileNotFoundError, match="为空"):
            ensure_agent_team_path("   ")

    def test_nonexistent_path_raises(self):
        with pytest.raises(FileNotFoundError, match="不存在"):
            ensure_agent_team_path("/nonexistent/path/that/does/not/exist")

    def test_path_without_package_raises(self, tmp_path):
        with pytest.raises(NotADirectoryError, match="academic_agent_team"):
            ensure_agent_team_path(str(tmp_path))

    def test_valid_path(self, tmp_path):
        # Create the expected package directory
        (tmp_path / "academic_agent_team").mkdir()
        result = ensure_agent_team_path(str(tmp_path))
        assert result == tmp_path.resolve()


class TestCheckDependencies:
    def test_returns_list(self):
        result = check_dependencies()
        assert isinstance(result, list)


class TestWriteJson:
    def test_writes_json(self, tmp_path):
        path = tmp_path / "test.json"
        write_json(path, {"key": "value", "中文": "测试"})
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["key"] == "value"
        assert data["中文"] == "测试"

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "test.json"
        write_json(path, {"ok": True})
        assert path.exists()


class TestAppendEventJsonl:
    def test_appends_lines(self, tmp_path):
        path = tmp_path / "events.jsonl"
        append_event_jsonl(path, {"type": "state", "stage": "init"})
        append_event_jsonl(path, {"type": "token", "content": "hello"})
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["type"] == "state"
        assert json.loads(lines[1])["type"] == "token"


class TestResolveSessionDir:
    def test_creates_directory(self, tmp_path):
        result = resolve_session_dir(tmp_path, "abc123")
        assert result.exists()
        assert result.name == "abc123"
        assert result.parent.name == "output"


class TestReadPaperMarkdown:
    def test_reads_file(self, tmp_path):
        paper = tmp_path / "paper.md"
        paper.write_text("# Hello\n\nWorld", encoding="utf-8")
        result = read_paper_markdown(tmp_path)
        assert result == "# Hello\n\nWorld"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="paper.md"):
            read_paper_markdown(tmp_path)
