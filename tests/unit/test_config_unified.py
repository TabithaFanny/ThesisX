"""Tests for unified Agent Team configuration (Vision 2.4)."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.config import Config


class TestAgentTeamConfig:
    def test_defaults_when_empty(self, monkeypatch):
        """When nothing is configured, defaults should be sensible."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        # Override _data to simulate clean config
        config = Config()
        config._data = {
            "agent_team_path": "",
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
            "agent_team_default_journal": "中文核心",
            "agent_team_default_mode": "mock",
            "agent_team_default_budget_cny": 10.0,
        }
        cfg = config.get_agent_team_config()

        assert cfg["agent_team_path"] == ""
        assert cfg["api_key"] == ""
        assert cfg["base_url"] == "https://api.openai.com/v1"
        assert cfg["model"] == "gpt-4o-mini"
        assert cfg["default_journal"] == "中文核心"
        assert cfg["default_mode"] == "mock"
        assert cfg["default_budget_cny"] == 10.0

    def test_env_overrides_all(self, monkeypatch):
        """Environment variables should take highest priority."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key-1234")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.api.com/v1")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": "",
            "custom_ai_api_url": "https://config.url.com",
            "custom_ai_model": "config-model",
            "custom_ai_api_key": "config-key",
        }
        cfg = config.get_agent_team_config()

        assert cfg["api_key"] == "sk-env-key-1234"
        assert cfg["base_url"] == "https://custom.api.com/v1"
        assert cfg["model"] == "gpt-4o"

    def test_ai_api_key_fallback(self, monkeypatch):
        """When OPENAI_API_KEY is not set, AI_API_KEY should be used."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("AI_API_KEY", "sk-ai-key-5678")

        config = Config()
        config._data = {
            "agent_team_path": "",
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
        }
        cfg = config.get_agent_team_config()

        assert cfg["api_key"] == "sk-ai-key-5678"

    def test_openai_key_priority_over_ai_key(self, monkeypatch):
        """OPENAI_API_KEY should take priority over AI_API_KEY."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-priority")
        monkeypatch.setenv("AI_API_KEY", "sk-ai-fallback")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {"custom_ai_api_key": ""}
        cfg = config.get_agent_team_config()

        assert cfg["api_key"] == "sk-openai-priority"


class TestAgentTeamConfigHealth:
    def test_health_with_no_config(self, monkeypatch):
        """Health check should detect missing config."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": "未选择",
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
        }
        health = config.get_agent_team_config_health()

        assert health["ok"] is False
        assert any("路径未设置" in issue for issue in health["issues"])
        assert health["config_snapshot"]["api_key_configured"] is False

    def test_health_with_api_key_but_no_path(self, monkeypatch):
        """API key alone is not enough — path must be set too."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": "未选择",
            "custom_ai_api_key": "",
            "custom_ai_api_url": "",
        }
        health = config.get_agent_team_config_health()

        assert health["ok"] is False
        assert any("路径未设置" in issue for issue in health["issues"])
        assert health["config_snapshot"]["api_key_configured"] is True

    def test_health_with_valid_tui_runner_path(self, tmp_path: Path, monkeypatch):
        """Valid tui_runner contract should pass health check."""
        pkg = tmp_path / "academic_agent_team" / "tui"
        pkg.mkdir(parents=True)
        (pkg / "runner.py").write_text("", encoding="utf-8")
        (pkg / "events.py").write_text("", encoding="utf-8")

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": str(tmp_path),
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
        }
        health = config.get_agent_team_config_health()
        assert health["ok"] is True
        assert len(health["issues"]) == 0

    def test_health_with_pipeline_v2_path(self, tmp_path: Path, monkeypatch):
        """pipeline_v2 contract should be detected but warn about dry-run only."""
        pkg = tmp_path / "academic_agent_team"
        pkg.mkdir(parents=True)
        (pkg / "pipeline_v2.py").write_text("", encoding="utf-8")

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": str(tmp_path),
            "custom_ai_api_key": "",
        }
        health = config.get_agent_team_config_health()
        assert health["ok"] is True
        assert any("dry-run" in w for w in health["warnings"])

    def test_health_with_invalid_path(self, monkeypatch):
        """Non-existent path should be caught."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        config = Config()
        config._data = {
            "agent_team_path": "/nonexistent/path/12345",
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
        }
        health = config.get_agent_team_config_health()
        assert health["ok"] is False
        assert any("不存在" in issue for issue in health["issues"])

    def test_health_default_base_url_warns(self, monkeypatch):
        """Default base_url without explicit configuration should warn."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        config = Config()
        config._data = {
            "agent_team_path": "未选择",
            "custom_ai_api_url": "",
            "custom_ai_model": "",
            "custom_ai_api_key": "",
        }
        health = config.get_agent_team_config_health()
        assert any("默认值" in w for w in health["warnings"])
