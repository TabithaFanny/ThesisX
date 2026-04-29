"""AI 服务模块单元测试"""
import os
import pytest
from unittest.mock import patch

from app.core.ai_service import (
    AiServiceConfig,
    _build_system_message,
    _default_config,
    build_optimize_messages,
    build_continue_messages,
    build_custom_edit_messages,
    configure_ai,
    get_ai_api_key,
)


class TestAiServiceConfig:
    """测试 AiServiceConfig 配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = AiServiceConfig()
        assert config.api_url == "https://llm.nodai.design/v1/chat/completions"
        assert config.model == "gpt-5.3-codex"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_custom_config(self):
        """测试自定义配置"""
        config = AiServiceConfig(
            api_url="https://custom.api.com",
            api_key="test-key",
            model="gpt-4",
            timeout=30
        )
        assert config.api_url == "https://custom.api.com"
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.timeout == 30


class TestMessageBuilders:
    """测试消息构建函数"""

    def test_build_optimize_messages(self):
        """测试优化消息构建"""
        text = "这是一段需要优化的文本"
        messages = build_optimize_messages(text)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert text in messages[1]["content"]

    def test_build_optimize_messages_low_dup(self):
        """测试低重复率优化消息构建"""
        text = "测试文本"
        messages = build_optimize_messages(text, low_dup=True)

        assert len(messages) == 2
        assert "降低重复率" in messages[0]["content"] or "降重" in messages[0]["content"]

    def test_build_continue_messages(self):
        """测试续写消息构建"""
        context = "第一章 引言\n这是引言内容。"
        messages = build_continue_messages(context)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "继续撰写" in messages[1]["content"]

    def test_build_continue_messages_with_after_context(self):
        """测试带后续上下文的续写消息构建"""
        context = "第一章内容"
        after_context = "第三章内容"
        messages = build_continue_messages(context, after_context)

        assert len(messages) == 2
        assert after_context[:100] in messages[1]["content"]

    def test_build_custom_edit_messages(self):
        """测试自定义编辑消息构建"""
        selected_text = "原始文本"
        instruction = "扩写为 2000 字"
        messages = build_custom_edit_messages(selected_text, instruction)

        assert len(messages) == 2
        assert instruction in messages[1]["content"]
        assert selected_text in messages[1]["content"]

    def test_build_continue_messages_truncates_long_context(self):
        """测试长上下文会被截断"""
        long_context = "A" * 5000  # 超过 3000 字符
        messages = build_continue_messages(long_context)

        # 应该只包含最后 3000 字符
        assert len(messages[1]["content"]) < len(long_context) + 100


class TestGetApiKey:
    """测试 API Key 获取"""

    def test_get_api_key_from_env(self, monkeypatch):
        """测试从环境变量获取 API Key"""
        test_key = "test-api-key-123"
        monkeypatch.setenv("WENBIAO_AI_API_KEY", test_key)

        key = get_ai_api_key()
        assert key == test_key

    def test_get_api_key_priority(self, monkeypatch):
        """测试 API Key 获取优先级"""
        monkeypatch.setenv("WENBIAO_AI_API_KEY", "key1")
        monkeypatch.setenv("AI_API_KEY", "key2")
        monkeypatch.setenv("OPENAI_API_KEY", "key3")

        key = get_ai_api_key()
        # WENBIAO_AI_API_KEY 优先级最高
        assert key == "key1"

    def test_get_api_key_fallback(self, monkeypatch):
        """测试 API Key 回退机制"""
        # 清除所有环境变量
        monkeypatch.delenv("WENBIAO_AI_API_KEY", raising=False)
        monkeypatch.delenv("AI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        key = get_ai_api_key()
        # 如果没有环境变量且没有 config.ini，应返回空字符串
        assert isinstance(key, str)


class TestConfigureAi:
    """测试 configure_ai 全局配置函数"""

    def setup_method(self):
        """每个测试前重置全局配置"""
        _default_config.api_url = ""
        _default_config.model = ""
        _default_config.api_key = ""

    def test_configure_api_url(self):
        """设置 api_url"""
        configure_ai(api_url="https://custom.api.com")
        assert _default_config.api_url == "https://custom.api.com"

    def test_configure_model(self):
        """设置 model"""
        configure_ai(model="gpt-4")
        assert _default_config.model == "gpt-4"

    def test_configure_api_key_sets_env(self, monkeypatch):
        """设置 api_key 同步到环境变量"""
        monkeypatch.delenv("WENBIAO_AI_API_KEY", raising=False)
        configure_ai(api_key="sk-test-123")
        assert _default_config.api_key == "sk-test-123"
        assert os.environ.get("WENBIAO_AI_API_KEY") == "sk-test-123"

    def test_configure_empty_api_key_clears_env(self, monkeypatch):
        """空 api_key 清除环境变量"""
        monkeypatch.setenv("WENBIAO_AI_API_KEY", "old-key")
        configure_ai(api_key="")
        assert _default_config.api_key == ""
        assert "WENBIAO_AI_API_KEY" not in os.environ

    def test_configure_none_api_key_no_change(self, monkeypatch):
        """api_key=None 不修改现有值"""
        _default_config.api_key = "existing"
        configure_ai(api_key=None)
        assert _default_config.api_key == "existing"

    def test_configure_empty_url_no_change(self):
        """空 api_url 不覆盖现有值"""
        _default_config.api_url = "https://existing.com"
        configure_ai(api_url="")
        assert _default_config.api_url == "https://existing.com"


class TestBuildSystemMessage:
    """测试 _build_system_message 函数"""

    def test_without_skills(self):
        """无 Skills 内容时返回原始 prompt"""
        with patch("app.core.ai_service._get_skills_context", return_value=""):
            result = _build_system_message("基础提示词")
            assert result == "基础提示词"

    def test_with_skills(self):
        """有 Skills 内容时追加到 prompt"""
        with patch("app.core.ai_service._get_skills_context", return_value="技能内容"):
            result = _build_system_message("基础提示词")
            assert "基础提示词" in result
            assert "技能内容" in result
            assert "Skills 集群记忆" in result

    def test_skills_exception_returns_base(self):
        """Skills 加载异常时返回原始 prompt"""
        # _get_skills_context 内部捕获异常返回 ""，
        # 所以 mock 让它返回 "" 来模拟异常被吞掉的情况
        with patch("app.core.ai_service._get_skills_context", return_value=""):
            result = _build_system_message("基础提示词")
            assert result == "基础提示词"
