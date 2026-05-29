"""Evidence Pack Service — Vision 3.4.

Claim-Evidence chain:
  ResearchQuestion → Claims (extracted from KB) → EvidenceItems (bound to KnowledgeObjects) → Gap Analysis

Integrates with:
- app.core.project.service.ProjectService
- app.core.knowledge.service.KnowledgeService  (already has extract_claims)
- app.core.project.models.ProjectKnowledgeLink
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.knowledge.models import Claim
from app.core.knowledge.service import KnowledgeService
from app.core.project.service import ProjectService
from app.core.evidence.models import ClaimEvidenceStatus, EvidenceItem


class EvidencePackService:
    """Build and manage Claim-Evidence chains for a project."""

    CLAIMS_DIR = Path.home() / ".wenbiao" / "evidence"

    def __init__(self, project_id: str, kb_dir: str | Path | None = None):
        self.project_id = project_id
        self._project_svc = ProjectService()
        self._kb_svc = KnowledgeService(base_dir=kb_dir) if kb_dir else KnowledgeService()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.CLAIMS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Claims from ResearchQuestion ──────────────────────────────────────

    def create_claim_from_question(
        self,
        research_question_id: str,
        claim_text: str,
        claim_type: str = "fact",
    ) -> Claim:
        """Create a Claim attached to a ResearchQuestion (project).

        The claim is stored via ProjectKnowledgeLink with role='section_claim'.
        """
        rq = self._project_svc.get_research_question(self.project_id)
        if not rq:
            raise ValueError(f"No research question found for project {self.project_id}")

        # Find or create the KB source for this claim
        # (claims are stored per source, but for project-level claims we use project_id as source)
        claim = Claim.new(
            source_id=f"project:{self.project_id}",
            chunk_id=research_question_id,
            claim_text=claim_text,
            claim_type=claim_type,
        )

        self._save_claim(claim)
        return claim

    def list_claims(self) -> list[Claim]:
        """List all Claims for this project."""
        path = self._claims_file()
        if not path.exists():
            return []
        claims: list[Claim] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                claims.append(Claim.from_dict(json.loads(line)))
            except Exception:
                continue
        return claims

    def delete_claim(self, claim_id: str) -> bool:
        """Delete a claim and its bound evidence items."""
        path = self._claims_file()
        if not path.exists():
            return False
        lines = []
        found = False
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("id") == claim_id:
                found = True
                continue
            lines.append(line)
        if not found:
            return False
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # Also delete all evidence items for this claim
        ev_path = self._evidence_file(claim_id)
        if ev_path.exists():
            ev_path.unlink()
        return True

    # ── Evidence Items ─────────────────────────────────────────────────────

    def bind_evidence(
        self,
        claim_id: str,
        evidence_object_id: str,
        evidence_text: str,
        role: str = "evidence",
        priority: int = 0,
        page_ref: str = "",
    ) -> EvidenceItem:
        """Bind an evidence item to a Claim."""
        item = EvidenceItem.new(
            claim_id=claim_id,
            evidence_object_id=evidence_object_id,
            evidence_text=evidence_text,
            role=role,
            priority=priority,
            page_ref=page_ref,
        )
        self._save_evidence(item)
        return item

    def list_evidence(self, claim_id: str) -> list[EvidenceItem]:
        """List all EvidenceItems for a Claim."""
        path = self._evidence_file(claim_id)
        if not path.exists():
            return []
        items: list[EvidenceItem] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(EvidenceItem.from_dict(json.loads(line)))
            except Exception:
                continue
        return items

    def unbind_evidence(self, evidence_id: str, claim_id: str) -> bool:
        """Remove an EvidenceItem from a Claim."""
        path = self._evidence_file(claim_id)
        if not path.exists():
            return False
        lines = []
        found = False
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("id") == evidence_id:
                found = True
                continue
            lines.append(line)
        if not found:
            return False
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True

    # ── Gap Analysis ──────────────────────────────────────────────────────

    def analyze_coverage(self) -> list[ClaimEvidenceStatus]:
        """Analyze coverage for all Claims in a project.

        Returns one ClaimEvidenceStatus per Claim:
        - gap: no evidence items bound
        - partial: some evidence but coverage_score < 0.6
        - covered: coverage_score >= 0.6
        """
        results: list[ClaimEvidenceStatus] = []
        for claim in self.list_claims():
            items = self.list_evidence(claim.id)
            status = ClaimEvidenceStatus.new(
                claim_id=claim.id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
            )
            if not items:
                status.coverage = "gap"
                status.coverage_score = 0.0
                status.gap_reasons.append("No evidence items bound")
            else:
                verified = [i for i in items if i.coverage_status == "verified"]
                status.evidence_ids = [i.id for i in items]
                status.coverage_score = len(verified) / len(items) if items else 0.0
                if status.coverage_score >= 0.6:
                    status.coverage = "covered"
                else:
                    status.coverage = "partial"
                    if not verified:
                        status.gap_reasons.append("No verified evidence items")

            results.append(status)
        return results

    # ── File helpers ───────────────────────────────────────────────────────

    def _claims_file(self) -> Path:
        return self.CLAIMS_DIR / f"{self.project_id}_claims.jsonl"

    def _evidence_file(self, claim_id: str) -> Path:
        return self.CLAIMS_DIR / f"{claim_id}_evidence.jsonl"

    def _save_claim(self, claim: Claim) -> None:
        path = self._claims_file()
        lines = [json.dumps(claim.to_dict(), ensure_ascii=False)]
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines() + lines
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _save_evidence(self, item: EvidenceItem) -> None:
        path = self._evidence_file(item.claim_id)
        lines = [json.dumps(item.to_dict(), ensure_ascii=False)]
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines() + lines
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── Export ─────────────────────────────────────────────────────────────

    def export_evidence_report(self, output_path: str | Path) -> int:
        """Export all Claim-Evidence chains as a Markdown report.

        Returns the number of claims written.
        """
        out = Path(output_path)
        lines = ["# Evidence Pack Report\n"]
        total_claims = 0
        for claim in self.list_claims():
            items = self.list_evidence(claim.id)
            total_claims += 1
            lines.append(f"\n## Claim: {claim.claim_text}")
            lines.append(f"\n**ID:** `{claim.id}`")
            lines.append(f"\n**Type:** {claim.claim_type}")
            lines.append(f"\n**Evidence Items:** {len(items)}")
            if not items:
                lines.append("\n*⚠ No evidence bound — GAP*")
            else:
                for item in items:
                    badge = "✅" if item.coverage_status == "verified" else "❓"
                    lines.append(f"\n- {badge} `{item.role}` {item.evidence_text[:80]}...")
        out.write_text("\n".join(lines), encoding="utf-8")
        return total_claims
