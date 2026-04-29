"""Tests for ArchitectNode — mock mode, output parsing, enhanced topic builder."""

import json

import pytest

from app.core.pipeline.models import PaperRequest
from app.core.pipeline.nodes.architect_node import (
    ArchitectNode,
    ArchitectOutput,
    _mock_outline,
    build_enhanced_topic,
)


class TestMockOutline:
    def test_returns_architect_output(self):
        result = _mock_outline("数字治理", "中文核心")
        assert isinstance(result, ArchitectOutput)
        assert "数字治理" in result.paper_title
        assert len(result.outline) >= 5
        assert result.central_argument != ""
        assert len(result.argument_chain) >= 3

    def test_outline_has_required_sections(self):
        result = _mock_outline("test", "CSSCI")
        titles = [item.get("title", "") for item in result.outline]
        assert any("摘要" in t for t in titles)
        assert any("引言" in t for t in titles)
        assert any("结论" in t for t in titles)
        assert any("参考文献" in t for t in titles)

    def test_missing_materials_nonempty(self):
        result = _mock_outline("test", "test")
        assert len(result.missing_materials) > 0

    def test_writer_instructions_nonempty(self):
        result = _mock_outline("test", "test")
        assert len(result.writer_instructions) > 0


class TestArchitectNodeRun:
    @pytest.mark.asyncio
    async def test_mock_mode(self):
        node = ArchitectNode()
        req = PaperRequest(topic="AI in education", run_mode="mock")
        result = await node.run(req)
        assert isinstance(result, ArchitectOutput)
        assert "AI in education" in result.paper_title or "AI in education" in result.central_argument

    @pytest.mark.asyncio
    async def test_real_mode_no_key_fallback(self):
        node = ArchitectNode()
        req = PaperRequest(topic="test", run_mode="real", api_key="")
        result = await node.run(req)
        # Should fallback to mock
        assert isinstance(result, ArchitectOutput)
        assert len(result.outline) > 0


class TestParseOutput:
    def test_valid_json(self):
        data = {
            "paper_title": "Test",
            "central_argument": "arg",
            "argument_chain": ["a"],
            "outline": [{"section_number": 1, "title": "S1"}],
            "missing_materials": [],
            "writer_instructions": "do it",
        }
        result = ArchitectNode._parse_output(json.dumps(data), "test", "test")
        assert result.paper_title == "Test"
        assert result.central_argument == "arg"

    def test_json_with_markdown_codeblock(self):
        data = {"paper_title": "Test", "central_argument": "arg"}
        md = f"```json\n{json.dumps(data)}\n```"
        result = ArchitectNode._parse_output(md, "test", "test")
        assert result.paper_title == "Test"

    def test_invalid_json_fallback(self):
        result = ArchitectNode._parse_output("not json at all", "fallback topic", "test")
        assert isinstance(result, ArchitectOutput)
        assert "fallback topic" in result.paper_title

    def test_json_embedded_in_text(self):
        data = {"paper_title": "Embedded", "central_argument": "found it"}
        text = f"Here is the output:\n{json.dumps(data)}\nEnd."
        result = ArchitectNode._parse_output(text, "test", "test")
        assert result.paper_title == "Embedded"


class TestBuildEnhancedTopic:
    def test_contains_config(self):
        req = PaperRequest(topic="test topic", journal="CSSCI", run_mode="mock")
        outline = ArchitectOutput(
            paper_title="Title",
            central_argument="Arg",
            argument_chain=["a", "b"],
            outline=[
                {"section_number": 1, "title": "Intro", "section_goal": "introduce", "target_word_count": 1000}
            ],
            writer_instructions="instructions here",
        )
        result = build_enhanced_topic(req, outline)
        assert "CSSCI" in result
        assert "mock" in result
        assert "Title" in result
        assert "Arg" in result
        assert "test topic" in result
        assert "instructions here" in result

    def test_contains_3_round_strategy(self):
        req = PaperRequest(topic="test", journal="test", run_mode="mock")
        outline = ArchitectOutput(paper_title="T", central_argument="A")
        result = build_enhanced_topic(req, outline)
        assert "逻辑轮" in result
        assert "理论轮" in result
        assert "语言轮" in result

    def test_contains_5_dimension_scoring(self):
        req = PaperRequest(topic="test", journal="test", run_mode="mock")
        outline = ArchitectOutput(paper_title="T", central_argument="A")
        result = build_enhanced_topic(req, outline)
        assert "Directness" in result
        assert "Rhythm" in result
        assert "Trust" in result
        assert "Authenticity" in result
        assert "Density" in result

    def test_contains_deai_blacklist(self):
        req = PaperRequest(topic="test", journal="test", run_mode="mock")
        outline = ArchitectOutput(paper_title="T", central_argument="A")
        result = build_enhanced_topic(req, outline)
        assert "leverage" in result.lower()
        assert "至关重要" in result
