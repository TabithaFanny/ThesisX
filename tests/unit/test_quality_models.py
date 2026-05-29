"""Tests for Quality Dashboard models."""

import pytest
from app.core.quality.models import (
    WritingProgress, ClaimCoverage, EvidenceIntegrity, CitationCompleteness,
)


class TestWritingProgress:
    def test_new(self):
        wp = WritingProgress.new("abstract", target_words=300)
        assert wp.section_type == "abstract"
        assert wp.target_words == 300
        assert wp.edit_status == "pending"

    def test_to_dict_round_trip(self):
        wp = WritingProgress.new("method", target_words=800)
        wp.word_count = 450
        d = wp.to_dict()
        wp2 = WritingProgress.from_dict(d)
        assert wp2.section_type == wp.section_type
        assert wp2.word_count == wp.word_count


class TestClaimCoverage:
    def test_new(self):
        cc = ClaimCoverage.new("claim-1", "AI improves learning outcomes", "proj-1")
        assert cc.claim_id == "claim-1"
        assert not cc.covered

    def test_to_dict_round_trip(self):
        cc = ClaimCoverage.new("claim-2", "Social media causes addiction", "proj-2")
        cc.covered = True
        cc.coverage_score = 0.7
        d = cc.to_dict()
        cc2 = ClaimCoverage.from_dict(d)
        assert cc2.covered == cc.covered
        assert cc2.coverage_score == 0.7


class TestEvidenceIntegrity:
    def test_new(self):
        ei = EvidenceIntegrity(
            project_knowledge_link_id="link-1",
            source_id="src-1",
            knowledge_title="Study on AI in education",
        )
        assert ei.verified_status == "unverified"
        assert ei.usable_for_writing

    def test_to_dict_round_trip(self):
        ei = EvidenceIntegrity(
            project_knowledge_link_id="link-2",
            source_id="src-2",
            knowledge_title="Digital governance study",
            verified_status="verified",
            usable_for_writing=True,
        )
        d = ei.to_dict()
        ei2 = EvidenceIntegrity.from_dict(d)
        assert ei2.verified_status == "verified"
        assert ei2.usable_for_writing


class TestCitationCompleteness:
    def test_new(self):
        cc = CitationCompleteness(
            citation_key="(张三, 2023)",
            context="According to Zhang San...",
        )
        assert cc.is_present

    def test_to_dict_round_trip(self):
        cc = CitationCompleteness(
            citation_key="(李四, 2022)",
            context="As Li Si demonstrates...",
            is_complete=False,
            missing_fields=["doi"],
        )
        d = cc.to_dict()
        cc2 = CitationCompleteness.from_dict(d)
        assert cc2.missing_fields == ["doi"]
        assert not cc2.is_complete

    def test_missing_fields_empty(self):
        cc = CitationCompleteness(
            citation_key="(王五, 2021)",
            context="Wang Wu argues...",
        )
        assert cc.missing_fields == []
