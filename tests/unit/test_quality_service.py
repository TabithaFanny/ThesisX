"""Tests for QualityService (Vision 3.10)."""

from __future__ import annotations

import pytest

from app.core.quality.service import QualityService, QualityDashboard
from app.core.quality.models import (
    WritingProgress,
    ClaimCoverage,
    EvidenceIntegrity,
    CitationCompleteness,
)


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def empty_svc() -> QualityService:
    return QualityService()


@pytest.fixture
def svc_with_data() -> QualityService:
    svc = QualityService(project_id="proj1")

    svc.set_progress([
        WritingProgress.new("abstract", target_words=300),
        WritingProgress.new("intro", target_words=1000),
        WritingProgress.new("method", target_words=800),
        WritingProgress.new("discussion", target_words=1000),
    ])
    # Mark 2 sections as done
    svc._progress_items[0].edit_status = "done"
    svc._progress_items[1].edit_status = "done"

    svc.set_coverages([
        ClaimCoverage.new("c1", "Claim A", "proj1"),
        ClaimCoverage.new("c2", "Claim B", "proj1"),
        ClaimCoverage.new("c3", "Claim C", "proj1"),
    ])
    svc._coverages[0].covered = True
    svc._coverages[1].covered = True

    svc.set_integrity([
        EvidenceIntegrity("e1", "src1", "Title A", verified_status="verified"),
        EvidenceIntegrity("e2", "src2", "Title B", verified_status="unverified"),
        EvidenceIntegrity("e3", "src3", "Title C", verified_status="verified"),
    ])

    svc.set_citations([
        CitationCompleteness("key1", "context1", is_complete=True),
        CitationCompleteness("key2", "context2", is_complete=False, missing_fields=["year"]),
    ])

    return svc


# ── writing progress ───────────────────────────────────────────────────────

class TestWritingProgress:
    def test_empty_returns_zero(self, empty_svc):
        pct, done, total = empty_svc.calc_writing_progress()
        assert pct == 0.0
        assert done == 0
        assert total == 0

    def test_with_data(self, svc_with_data):
        pct, done, total = svc_with_data.calc_writing_progress()
        assert total == 4
        assert done == 2
        assert pct == 50.0


# ── claim coverage ──────────────────────────────────────────────────────────

class TestClaimCoverage:
    def test_empty_returns_zero(self, empty_svc):
        pct, covered, total = empty_svc.calc_claim_coverage()
        assert pct == 0.0
        assert covered == 0

    def test_with_data(self, svc_with_data):
        pct, covered, total = svc_with_data.calc_claim_coverage()
        assert total == 3
        assert covered == 2
        assert pct == pytest.approx(66.7, abs=0.1)


# ── evidence integrity ──────────────────────────────────────────────────────

class TestEvidenceIntegrity:
    def test_empty_returns_zero(self, empty_svc):
        pct, verified, total = empty_svc.calc_evidence_integrity()
        assert pct == 0.0

    def test_with_data(self, svc_with_data):
        pct, verified, total = svc_with_data.calc_evidence_integrity()
        assert total == 3
        assert verified == 2
        assert pct == pytest.approx(66.7, abs=0.1)


# ── citation completeness ───────────────────────────────────────────────────

class TestCitationCompleteness:
    def test_empty_returns_zero(self, empty_svc):
        pct, complete, total = empty_svc.calc_citation_completeness()
        assert pct == 0.0

    def test_with_data(self, svc_with_data):
        pct, complete, total = svc_with_data.calc_citation_completeness()
        assert total == 2
        assert complete == 1
        assert pct == 50.0


# ── dashboard ───────────────────────────────────────────────────────────────

class TestDashboard:
    def test_empty_dashboard(self, empty_svc):
        d = empty_svc.get_dashboard()
        assert isinstance(d, QualityDashboard)
        assert d.overall_score == 0.0
        assert d.grade == "数据不足"
        assert len(d.suggestions) == 4  # All four categories empty

    def test_dashboard_with_data(self, svc_with_data):
        d = svc_with_data.get_dashboard()
        assert 0 <= d.overall_score <= 100
        assert d.writing_progress == 50.0
        assert d.claim_coverage == pytest.approx(66.7, abs=0.1)
        assert d.evidence_integrity == pytest.approx(66.7, abs=0.1)
        assert d.citation_completeness == 50.0

    def test_overall_score_is_weighted_average(self, svc_with_data):
        d = svc_with_data.get_dashboard()
        # writing:50(c25%), claim:66.7(c35%), evidence:66.7(c25%), citation:50(c15%)
        expected = 50 * 0.25 + 66.7 * 0.35 + 66.7 * 0.25 + 50 * 0.15
        assert d.overall_score == pytest.approx(expected, abs=0.2)

    def test_all_done_gives_100(self):
        svc = QualityService()
        svc.set_progress([WritingProgress.new("intro")])
        svc._progress_items[0].edit_status = "done"
        svc.set_coverages([ClaimCoverage.new("c1", "Test", "p")])
        svc._coverages[0].covered = True
        svc.set_integrity([EvidenceIntegrity("e1", "s1", "T", verified_status="verified")])
        svc.set_citations([CitationCompleteness("k1", "ctx", is_complete=True)])
        d = svc.get_dashboard()
        assert d.overall_score == 100.0
        assert d.grade == "优秀"

    def test_grade_levels(self):
        svc = QualityService(project_id="test")
        svc.set_progress([WritingProgress.new("intro")])
        svc._progress_items[0].edit_status = "done"

        svc.set_coverages([ClaimCoverage.new("c1", "Test", "p")])
        svc._coverages[0].covered = True if svc._coverages[0].covered else True

        svc.set_citations([CitationCompleteness("k1", "ctx", is_complete=True)])

        # Set evidence - verified gives 100
        svc.set_integrity([EvidenceIntegrity("e1", "s1", "T", verified_status="verified")])
        assert svc.get_dashboard().grade == "优秀"

        # Not verified: writing(100), claim(100), citation(100), evidence(0)
        svc.set_integrity([EvidenceIntegrity("e1", "s1", "T", verified_status="unverified")])
        d = svc.get_dashboard()
        # 100*0.25 + 100*0.35 + 0*0.25 + 100*0.15 = 75
        assert d.overall_score == 75.0

    def test_setters_accept_lists(self, empty_svc):
        items = [WritingProgress.new("abstract")]
        empty_svc.set_progress(items)
        pct, done, total = empty_svc.calc_writing_progress()
        assert total == 1
