"""QualityService — aggregate quality metrics for thesis writing (Vision 3.10).

Computes: writing progress, claim coverage, evidence integrity, citation
completeness, and an overall 0–100 weighted score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import WritingProgress, ClaimCoverage, EvidenceIntegrity, CitationCompleteness


@dataclass
class QualityDashboard:
    """Aggregated quality metrics for a project."""

    writing_progress: float = 0.0  # 0–100
    claim_coverage: float = 0.0  # 0–100
    evidence_integrity: float = 0.0  # 0–100
    citation_completeness: float = 0.0  # 0–100
    overall_score: float = 0.0  # 0–100 weighted
    suggestions: list[str] = field(default_factory=list)
    # Breakdowns
    total_sections: int = 0
    sections_completed: int = 0
    total_claims: int = 0
    claims_covered: int = 0
    total_evidence_items: int = 0
    evidence_verified: int = 0
    total_citations: int = 0
    citations_complete: int = 0

    @property
    def grade(self) -> str:
        s = self.overall_score
        if s >= 90:
            return "优秀"
        elif s >= 75:
            return "良好"
        elif s >= 60:
            return "合格"
        elif s >= 40:
            return "需改进"
        else:
            return "数据不足"


class QualityService:
    """Compute quality metrics from project data.

    All methods gracefully handle missing data, returning zero/incomplete
    metrics rather than raising exceptions.
    """

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id
        self._progress_items: list[WritingProgress] = []
        self._coverages: list[ClaimCoverage] = []
        self._integrity_items: list[EvidenceIntegrity] = []
        self._citation_items: list[CitationCompleteness] = []

    # ── setters (called by UI or other services to feed data) ─────────────

    def set_progress(self, items: list[WritingProgress]) -> None:
        self._progress_items = items

    def set_coverages(self, items: list[ClaimCoverage]) -> None:
        self._coverages = items

    def set_integrity(self, items: list[EvidenceIntegrity]) -> None:
        self._integrity_items = items

    def set_citations(self, items: list[CitationCompleteness]) -> None:
        self._citation_items = items

    # ── metric calculations ───────────────────────────────────────────────

    def calc_writing_progress(self) -> tuple[float, int, int]:
        """Returns (percentage 0–100, sections_completed, total_sections)."""
        total = len(self._progress_items)
        if total == 0:
            return 0.0, 0, 0
        done = sum(1 for p in self._progress_items if p.edit_status == "done")
        pct = round(done / total * 100, 1)
        return pct, done, total

    def calc_claim_coverage(self) -> tuple[float, int, int]:
        """Returns (percentage 0–100, claims_covered, total_claims)."""
        total = len(self._coverages)
        if total == 0:
            return 0.0, 0, 0
        covered = sum(1 for c in self._coverages if c.covered)
        pct = round(covered / total * 100, 1)
        return pct, covered, total

    def calc_evidence_integrity(self) -> tuple[float, int, int]:
        """Returns (percentage 0–100, evidence_verified, total_evidence)."""
        total = len(self._integrity_items)
        if total == 0:
            return 0.0, 0, 0
        verified = sum(1 for e in self._integrity_items if e.verified_status == "verified")
        pct = round(verified / total * 100, 1)
        return pct, verified, total

    def calc_citation_completeness(self) -> tuple[float, int, int]:
        """Returns (percentage 0–100, citations_complete, total_citations)."""
        total = len(self._citation_items)
        if total == 0:
            return 0.0, 0, 0
        complete = sum(1 for c in self._citation_items if c.is_complete)
        pct = round(complete / total * 100, 1)
        return pct, complete, total

    def get_dashboard(self) -> QualityDashboard:
        """Aggregate all quality metrics into a dashboard."""
        wp, wdone, wtotal = self.calc_writing_progress()
        cc, ccover, ctotal = self.calc_claim_coverage()
        ei, ever, etotal = self.calc_evidence_integrity()
        ct, ccomp, cttotal = self.calc_citation_completeness()

        suggestions: list[str] = []
        if wtotal == 0:
            suggestions.append("尚无写作进度数据，请开始撰写论文。")
        elif wp < 50:
            suggestions.append("写作进度不足 50%，建议加速写作。")

        if ctotal == 0:
            suggestions.append("尚无 Claim 数据，建议在研究工作空间定义研究问题。")
        elif cc < 80:
            suggestions.append(f"Claim 覆盖率仅 {cc}%，建议为未覆盖的 Claim 绑定证据。")

        if etotal == 0:
            suggestions.append("尚无证据完整性数据，建议在证据包页面管理证据。")
        elif ei < 60:
            suggestions.append(f"证据验证率仅 {ei}%，建议标记更多证据为已验证。")

        if cttotal == 0:
            suggestions.append("尚无引文数据，建议在文献管理页面添加参考文献。")

        # Weighted overall score
        # writing 25% + claim coverage 35% + evidence integrity 25% + citation 15%
        # If a category has 0 data, redistribute its weight proportionally
        weights = {"writing": 0.25, "claim": 0.35, "evidence": 0.25, "citation": 0.15}
        scores = {"writing": wp, "claim": cc, "evidence": ei, "citation": ct}
        counts = {"writing": wtotal, "claim": ctotal, "evidence": etotal, "citation": cttotal}

        # Redistribute weights for empty categories
        available = {k: w for k, w in weights.items() if counts[k] > 0}
        if available:
            total_weight = sum(available.values())
            normalized = {k: w / total_weight for k, w in available.items()}
            overall = sum(scores[k] * normalized[k] for k in available)
        else:
            overall = 0.0

        return QualityDashboard(
            writing_progress=wp,
            claim_coverage=cc,
            evidence_integrity=ei,
            citation_completeness=ct,
            overall_score=round(overall, 1),
            suggestions=suggestions,
            total_sections=wtotal,
            sections_completed=wdone,
            total_claims=ctotal,
            claims_covered=ccover,
            total_evidence_items=etotal,
            evidence_verified=ever,
            total_citations=cttotal,
            citations_complete=ccomp,
        )
