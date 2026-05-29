"""Tests for EvidencePack models and service."""

import pytest
from app.core.evidence.models import EvidenceItem, ClaimEvidenceStatus
from app.core.knowledge.models import Claim


class TestEvidenceItem:
    def test_new(self):
        ei = EvidenceItem.new(
            claim_id="c-1",
            evidence_object_id="ko-123",
            evidence_text="研究表明AI可以提高学习效果",
            role="evidence",
            priority=1,
            page_ref="p.42",
        )
        assert ei.claim_id == "c-1"
        assert ei.evidence_object_id == "ko-123"
        assert ei.priority == 1
        assert ei.role == "evidence"

    def test_to_dict_round_trip(self):
        ei = EvidenceItem.new(
            claim_id="c-2",
            evidence_object_id="ko-456",
            evidence_text="实验数据显示显著差异",
            role="contrast",
            priority=2,
        )
        ei.project_note = "需要进一步验证"
        d = ei.to_dict()
        ei2 = EvidenceItem.from_dict(d)
        assert ei2.claim_id == ei.claim_id
        assert ei2.project_note == "需要进一步验证"

    def test_default_role_is_evidence(self):
        ei = EvidenceItem.new("c-1", "ko-1", "test evidence")
        assert ei.role == "evidence"

    def test_used_in_sections_default_empty(self):
        ei = EvidenceItem.new("c-1", "ko-1", "test")
        assert ei.used_in_sections == []


class TestClaimEvidenceStatus:
    def test_new(self):
        s = ClaimEvidenceStatus.new("claim-1", "AI improves learning", "finding")
        assert s.claim_id == "claim-1"
        assert s.coverage == "gap"
        assert s.coverage_score == 0.0

    def test_to_dict_round_trip(self):
        s = ClaimEvidenceStatus.new("c-2", "Social media is harmful", "fact")
        s.coverage = "partial"
        s.coverage_score = 0.4
        s.evidence_ids = ["ei-1", "ei-2"]
        s.gap_reasons.append("No verified items")
        d = s.to_dict()
        s2 = ClaimEvidenceStatus.from_dict(d)
        assert s2.coverage == "partial"
        assert s2.coverage_score == 0.4
        assert len(s2.evidence_ids) == 2


class TestClaimModel:
    """Tests for the Claim model in knowledge.models."""

    def test_claim_new(self):
        c = Claim.new("src-1", "chunk-1", "机器学习在教育中有广泛应用", "finding")
        assert c.source_id == "src-1"
        assert c.chunk_id == "chunk-1"
        assert c.claim_type == "finding"

    def test_claim_to_dict_round_trip(self):
        c = Claim.new("src-2", "chunk-2", "数字治理提升效率", "fact")
        c.discipline = "公共管理"
        d = c.to_dict()
        c2 = Claim.from_dict(d)
        assert c2.claim_text == c.claim_text
        assert c2.discipline == "公共管理"

    def test_claim_types(self):
        for ct in ["fact", "finding", "method", "limitation", "assumption"]:
            c = Claim.new("s", "ch", "test", claim_type=ct)
            assert c.claim_type == ct
