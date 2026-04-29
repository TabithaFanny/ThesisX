"""Tests for Batch 2/3 nodes: Translator, LogicAuditor, CitationVerifier + new prompts."""

import pytest

from app.core.pipeline.models import PaperRequest
from app.core.pipeline.nodes.translator_node import TranslatorNode, TranslationResult
from app.core.pipeline.nodes.logic_auditor_node import LogicAuditorNode, LogicAuditResult
from app.core.pipeline.nodes.citation_verifier_node import (
    CitationVerifierNode,
    CitationVerificationResult,
    CitationIssue,
)


# ===========================================================================
# TranslatorNode
# ===========================================================================

class TestTranslatorNode:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_original(self):
        node = TranslatorNode()
        req = PaperRequest(topic="test", run_mode="mock")
        result = await node.run("这是一段中文测试", req)
        assert isinstance(result, TranslationResult)
        assert result.translated_text == "这是一段中文测试"
        assert "[Mock]" in result.modification_log

    @pytest.mark.asyncio
    async def test_real_mode_no_key_skips(self):
        node = TranslatorNode()
        req = PaperRequest(topic="test", run_mode="real", api_key="")
        result = await node.run("test text", req, direction="e2c")
        assert "跳过" in result.modification_log

    def test_parse_result_two_parts(self):
        content = "Part 1 [LaTeX]\nThis is the translated text.\n\nPart 2 [Translation]\n这是翻译后的文本。"
        result = TranslatorNode._parse_result(content, "c2e")
        assert "This is the translated text" in result.translated_text
        assert "这是翻译后的文本" in result.back_translation

    def test_parse_result_single_part(self):
        content = "Just the translated text."
        result = TranslatorNode._parse_result(content, "c2e")
        assert result.translated_text == "Just the translated text."


# ===========================================================================
# LogicAuditorNode
# ===========================================================================

class TestLogicAuditorNode:
    @pytest.mark.asyncio
    async def test_mock_mode_always_passes(self):
        node = LogicAuditorNode()
        req = PaperRequest(topic="test", run_mode="mock")
        result = await node.run("论文文本", req)
        assert isinstance(result, LogicAuditResult)
        assert result.passed is True
        assert result.issues == []

    @pytest.mark.asyncio
    async def test_real_mode_no_key_skips(self):
        node = LogicAuditorNode()
        req = PaperRequest(topic="test", run_mode="real", api_key="")
        result = await node.run("test", req)
        assert result.passed is True

    def test_parse_pass(self):
        result = LogicAuditorNode._parse_result("[检测通过，无实质性问题]")
        assert result.passed is True
        assert result.issues == []

    def test_parse_issues(self):
        content = "- 第3段声称准确率提升，但实验表中数据不支持\n- 核心概念'注意力机制'在第5节变为'关注模块'"
        result = LogicAuditorNode._parse_result(content)
        assert result.passed is False
        assert len(result.issues) == 2


# ===========================================================================
# CitationVerifierNode
# ===========================================================================

class TestCitationVerifierNode:
    @pytest.mark.asyncio
    async def test_mock_mode(self):
        node = CitationVerifierNode()
        req = PaperRequest(topic="test", run_mode="mock")
        result = await node.run("Some text \\cite{vaswani2017} and \\cite{devlin2019}", req)
        assert isinstance(result, CitationVerificationResult)
        assert result.total_citations == 2
        assert "[Mock]" in result.summary

    @pytest.mark.asyncio
    async def test_real_mode_no_key_skips(self):
        node = CitationVerifierNode()
        req = PaperRequest(topic="test", run_mode="real", api_key="")
        result = await node.run("test", req)
        assert result.total_citations == 0
        assert "跳过" in result.summary

    def test_parse_json_result(self):
        import json
        data = {
            "total_citations": 3,
            "verified_count": 2,
            "suspicious_count": 1,
            "unverifiable_count": 0,
            "results": [
                {"citation_key": "vaswani2017", "status": "verified", "issues": [], "suggestion": ""},
                {"citation_key": "fake2024", "status": "suspicious", "issues": ["论文不存在"], "suggestion": "删除或替换"},
            ],
            "summary": "验证完成",
        }
        result = CitationVerifierNode._parse_result(json.dumps(data))
        assert result.total_citations == 3
        assert result.verified_count == 2
        assert result.suspicious_count == 1
        assert len(result.results) == 2
        assert result.results[0].status == "verified"
        assert result.results[1].status == "suspicious"

    def test_parse_invalid_json_fallback(self):
        result = CitationVerifierNode._parse_result("not json at all")
        assert result.total_citations == 0
        assert "解析失败" in result.summary or "未找到 JSON" in result.summary


# ===========================================================================
# New Prompt Builders
# ===========================================================================

class TestNewPromptBuilders:
    def test_translator_auto_detect_zh(self):
        from app.core.pipeline.prompts import build_translator_prompt
        sys, user = build_translator_prompt("这是一段中文学术文本用于测试")
        assert "中文" in user
        assert "Part 1" in sys

    def test_translator_auto_detect_en(self):
        from app.core.pipeline.prompts import build_translator_prompt
        sys, user = build_translator_prompt("This is an English academic text for testing", direction="e2c")
        assert "英文" in user
        assert "cite" in sys

    def test_logic_auditor_prompt(self):
        from app.core.pipeline.prompts import build_logic_auditor_prompt
        sys, user = build_logic_auditor_prompt("论文文本")
        assert "红线审查" in sys
        assert "论文文本" in user

    def test_citation_verifier_prompt(self):
        from app.core.pipeline.prompts import build_citation_verifier_prompt
        sys, user = build_citation_verifier_prompt("正文", "参考文献列表")
        assert "引用" in sys
        assert "参考文献列表" in user

    def test_experiment_analysis_prompt(self):
        from app.core.pipeline.prompts import build_experiment_analysis_prompt
        sys, user = build_experiment_analysis_prompt("实验数据")
        assert "paragraph" in sys.lower() or "Paragraph" in sys
        assert "实验数据" in user

    def test_chart_recommendation_prompt(self):
        from app.core.pipeline.prompts import build_chart_recommendation_prompt
        sys, user = build_chart_recommendation_prompt("数据描述")
        assert "19" in sys
        assert "数据描述" in user

    def test_illustrator_cn_prompt(self):
        from app.core.pipeline.prompts import build_illustrator_prompt
        sys, user = build_illustrator_prompt("方法描述", language="cn")
        assert "扁平化" in sys
        assert "方法描述" in user

    def test_illustrator_en_prompt(self):
        from app.core.pipeline.prompts import build_illustrator_prompt
        sys, user = build_illustrator_prompt("method description", language="en")
        assert "flat vector" in sys.lower()

    def test_caption_figure_prompt(self):
        from app.core.pipeline.prompts import build_caption_prompt
        sys, user = build_caption_prompt("图的描述", caption_type="figure")
        assert "Title Case" in sys
        assert "figure" in user

    def test_caption_table_prompt(self):
        from app.core.pipeline.prompts import build_caption_prompt
        sys, user = build_caption_prompt("表的描述", caption_type="table")
        assert "Comparison with" in sys

    def test_optimizer_compress_prompt(self):
        from app.core.pipeline.prompts import build_optimizer_prompt
        sys, user = build_optimizer_prompt("LaTeX text", mode="compress")
        assert "缩减" in user
        assert "5-15" in sys

    def test_optimizer_expand_prompt(self):
        from app.core.pipeline.prompts import build_optimizer_prompt
        sys, user = build_optimizer_prompt("LaTeX text", mode="expand")
        assert "扩展" in user

    def test_rebuttal_prompt(self):
        from app.core.pipeline.prompts import build_rebuttal_prompt
        sys, user = build_rebuttal_prompt(
            "The paper lacks comparison with method X.",
            paper_title="Test Paper",
            venue="NeurIPS",
        )
        assert "Rebuttal" in sys
        assert "NeurIPS" in user
        assert "Test Paper" in user
        assert "method X" in user

    def test_camera_ready_slides_prompt(self):
        from app.core.pipeline.prompts import build_camera_ready_prompt
        sys, user = build_camera_ready_prompt(
            paper_title="Test Paper",
            preparation_type="slides",
            duration="15分钟",
        )
        assert "幻灯片" in user
        assert "15分钟" in user
        assert "Test Paper" in user

    def test_camera_ready_poster_prompt(self):
        from app.core.pipeline.prompts import build_camera_ready_prompt
        sys, user = build_camera_ready_prompt(
            paper_title="Test Paper",
            preparation_type="poster",
        )
        assert "海报" in user

    def test_camera_ready_promotion_prompt(self):
        from app.core.pipeline.prompts import build_camera_ready_prompt
        sys, user = build_camera_ready_prompt(
            paper_title="Test Paper",
            preparation_type="promotion",
        )
        assert "Twitter" in user or "推广" in user

    def test_latex_template_prompt(self):
        from app.core.pipeline.prompts import build_latex_template_prompt
        sys, user = build_latex_template_prompt(
            file_structure="main.tex\nsample-sigconf.tex\nacmart.cls",
            conference_info="KDD 2026",
        )
        assert "LaTeX" in sys or "模板" in sys
        assert "KDD 2026" in user
        assert "main.tex" in user


# ===========================================================================
# ARIS Batch 5 Prompt Builders
# ===========================================================================

class TestARISNoveltyPrompts:
    def test_claim_extraction(self):
        from app.core.pipeline.prompts import build_claim_extraction_prompt
        prompt = build_claim_extraction_prompt("We propose a novel attention mechanism for graph neural networks")
        assert "核心技术主张" in prompt
        assert "attention mechanism" in prompt
        assert "JSON" in prompt

    def test_novelty_search(self):
        from app.core.pipeline.prompts import build_novelty_search_prompt
        prompt = build_novelty_search_prompt('{"method": "GNN attention"}', claim_id=1)
        assert "检索" in prompt
        assert "arXiv" in prompt or "arxiv" in prompt
        assert "1" in prompt

    def test_novelty_verification(self):
        from app.core.pipeline.prompts import build_novelty_verification_prompt
        prompt = build_novelty_verification_prompt(
            method_description="Novel GNN method",
            claims_json='[{"claim_id": 1}]',
            search_results="Paper A (2025)...",
        )
        assert "新颖性" in prompt
        assert "PROCEED" in prompt
        assert "Novel GNN method" in prompt

    def test_novelty_report(self):
        from app.core.pipeline.prompts import build_novelty_report
        report = build_novelty_report(
            method_description="Test method",
            score=7,
            recommendation="PROCEED",
            key_differentiator="novel architecture",
            risk="Similar work by A et al.",
            suggested_positioning="Focus on the unique aspect",
        )
        assert "查新报告" in report
        assert "7/10" in report
        assert "PROCEED" in report


class TestARISClaimAuditPrompts:
    def test_system_prompt(self):
        from app.core.pipeline.prompts import build_claim_audit_system_prompt
        prompt = build_claim_audit_system_prompt()
        assert "审计员" in prompt
        assert "exact_match" in prompt
        assert "数字膨胀" in prompt
        assert "种子挑选" in prompt

    def test_user_prompt(self):
        from app.core.pipeline.prompts import build_claim_audit_user_prompt
        prompt = build_claim_audit_user_prompt(
            paper_files_summary="main.tex",
            result_files_summary="results.json",
            paper_excerpt="We achieved 85.3%",
            results_excerpt='{"accuracy": 84.7}',
        )
        assert "main.tex" in prompt
        assert "85.3%" in prompt
        assert "84.7" in prompt

    def test_report(self):
        from app.core.pipeline.prompts import build_claim_audit_report
        report = build_claim_audit_report(
            date="2026-04-28",
            paper_title="Test Paper",
            verdict="WARN",
            total_claims=10,
            exact_match=7,
            rounding_ok=2,
            ambiguous=0,
            mismatch=1,
        )
        assert "WARN" in report
        assert "10" in report
        assert "Test Paper" in report


class TestARISAutoReviewPrompts:
    def test_round_prompt(self):
        from app.core.pipeline.prompts import build_auto_review_round_prompt
        prompt = build_auto_review_round_prompt(
            round_num=1, max_rounds=4,
            research_context="We train a GNN model...",
        )
        assert "1/4" in prompt
        assert "GNN" in prompt
        assert "1-10" in prompt

    def test_memory_prompt(self):
        from app.core.pipeline.prompts import build_auto_review_memory_prompt
        prompt = build_auto_review_memory_prompt(
            round_num=2, max_rounds=4,
            reviewer_memory="Round 1: Concerned about baselines",
            research_context="Updated results...",
        )
        assert "记忆" in prompt
        assert "Round 1" in prompt
        assert "2/4" in prompt

    def test_nightmare_prompt(self):
        from app.core.pipeline.prompts import build_auto_review_nightmare_prompt
        prompt = build_auto_review_nightmare_prompt(
            round_num=1, max_rounds=4,
            reviewer_memory="No prior memory",
        )
        assert "对抗性" in prompt
        assert "仓库" in prompt or "repo" in prompt.lower()

    def test_rebuttal_prompt(self):
        from app.core.pipeline.prompts import build_review_rebuttal_prompt
        prompt = build_review_rebuttal_prompt("The reviewer claims X is not novel")
        assert "反驳" in prompt
        assert "SUSTAINED" in prompt

    def test_nightmare_rebuttal(self):
        from app.core.pipeline.prompts import build_review_rebuttal_prompt
        prompt = build_review_rebuttal_prompt("Rebuttal text", nightmare=True)
        assert "对抗性" in prompt
        assert "验证" in prompt

    def test_round_update(self):
        from app.core.pipeline.prompts import build_round_update_prompt
        prompt = build_round_update_prompt(
            round_num=3,
            actions_taken="Added baseline comparison",
            updated_results="Table 1: ...",
        )
        assert "3" in prompt
        assert "baseline" in prompt

    def test_difficulty_levels(self):
        from app.core.pipeline.prompts import REVIEW_DIFFICULTY_LEVELS
        assert "medium" in REVIEW_DIFFICULTY_LEVELS
        assert "hard" in REVIEW_DIFFICULTY_LEVELS
        assert "nightmare" in REVIEW_DIFFICULTY_LEVELS
        assert REVIEW_DIFFICULTY_LEVELS["nightmare"]["has_repo_access"] is True
        assert REVIEW_DIFFICULTY_LEVELS["medium"]["has_memory"] is False


class TestARISLiteratureSearchPrompts:
    def test_system_prompt(self):
        from app.core.pipeline.prompts import build_literature_search_system_prompt
        prompt = build_literature_search_system_prompt()
        assert "七" in prompt or "7" in prompt or "Zotero" in prompt
        assert "去重" in prompt

    def test_analysis_prompt(self):
        from app.core.pipeline.prompts import build_literature_analysis_prompt
        prompt = build_literature_analysis_prompt(
            topic="graph neural networks",
            title="Attention-based GNN",
            authors="Zhang et al.",
            year="2025",
            abstract="We propose...",
        )
        assert "graph neural networks" in prompt
        assert "Zhang" in prompt
        assert "HIGHLY_RELATED" in prompt

    def test_synthesis_prompt(self):
        from app.core.pipeline.prompts import build_literature_synthesis_prompt
        prompt = build_literature_synthesis_prompt(
            topic="GNN research",
            papers_summary="1. Paper A: ...\n2. Paper B: ...",
        )
        assert "综述" in prompt
        assert "分组" in prompt
        assert "GNN research" in prompt

    def test_scoring_prompt(self):
        from app.core.pipeline.prompts import build_paper_scoring_prompt
        prompt = build_paper_scoring_prompt(
            title="Test Paper",
            authors="Author A",
            year="2025",
            venue="NeurIPS",
            citations="50",
            abstract="We present...",
        )
        assert "评分" in prompt
        assert "NeurIPS" in prompt
        assert "metadata_score" in prompt


class TestARISCitationAuditPrompts:
    def test_citation_audit_prompt_pair(self):
        from app.core.pipeline.prompts import build_citation_audit_prompt
        sys, user = build_citation_audit_prompt("正文 \\cite{a}", "参考文献\n[1] A et al.")
        assert "三层" in sys
        assert "存在性" in sys
        assert "元数据" in sys
        assert "上下文" in sys
        assert "A et al." in user

    def test_citation_audit_auto_extract_refs(self):
        from app.core.pipeline.prompts import build_citation_audit_prompt
        sys, user = build_citation_audit_prompt("正文 参考文献\n[1] Paper A")
        assert "Paper A" in user
