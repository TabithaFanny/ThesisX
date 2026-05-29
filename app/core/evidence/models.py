"""Evidence Pack data models — Vision 3.4.

EvidenceItem: a piece of evidence bound to a Claim.
Claim-Evidence chain: ResearchQuestion → Claim → EvidenceItem → ProjectKnowledgeLink

Integrates with:
- app.core.knowledge.models.Claim  (already exists)
- app.core.project.models.ProjectKnowledgeLink  (already exists)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Evidence item statuses
EVIDENCE_STATUS_OPTIONS = ["unverified", "suggested", "verified", "rejected"]
CLAIM_STATUS_OPTIONS = ["pending", "in_progress", "covered", "partial", "gap"]


@dataclass
class EvidenceItem:
    """A single evidence piece bound to a Claim.

    Represents a concrete supporting or contradicting piece of evidence
    from a KnowledgeObject / KnowledgeSource.
    """
    id: str
    claim_id: str
    evidence_object_id: str  # KnowledgeSource.id or KnowledgeChunk.id
    evidence_text: str
    role: str = "evidence"  # evidence | contrast | method | background
    priority: int = 0  # 0=low, 1=medium, 2=high
    coverage_status: str = "unverified"  # unverified|suggested|verified|rejected
    page_ref: str = ""  # page number or location within source
    project_note: str = ""  # researcher's annotation
    used_in_sections: list[str] = field(default_factory=list)
    created_at: str = ""

    @staticmethod
    def new(
        claim_id: str,
        evidence_object_id: str,
        evidence_text: str,
        role: str = "evidence",
        priority: int = 0,
        page_ref: str = "",
    ) -> "EvidenceItem":
        return EvidenceItem(
            id=str(uuid.uuid4())[:12],
            claim_id=claim_id,
            evidence_object_id=evidence_object_id,
            evidence_text=evidence_text,
            role=role,
            priority=priority,
            page_ref=page_ref,
            created_at=_now(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "evidence_object_id": self.evidence_object_id,
            "evidence_text": self.evidence_text,
            "role": self.role,
            "priority": self.priority,
            "coverage_status": self.coverage_status,
            "page_ref": self.page_ref,
            "project_note": self.project_note,
            "used_in_sections": self.used_in_sections,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceItem":
        return cls(
            id=str(data.get("id", "")),
            claim_id=str(data.get("claim_id", "")),
            evidence_object_id=str(data.get("evidence_object_id", "")),
            evidence_text=str(data.get("evidence_text", "")),
            role=str(data.get("role", "evidence")),
            priority=int(data.get("priority", 0)),
            coverage_status=str(data.get("coverage_status", "unverified")),
            page_ref=str(data.get("page_ref", "")),
            project_note=str(data.get("project_note", "")),
            used_in_sections=list(data.get("used_in_sections", [])),
            created_at=str(data.get("created_at", _now())),
        )


@dataclass
class ClaimEvidenceStatus:
    """Coverage status for a single Claim.

    Produced by EvidencePackService.analyze_coverage().
    """
    claim_id: str
    claim_text: str
    claim_type: str = "fact"
    coverage: str = "gap"  # gap|partial|covered
    evidence_ids: list[str] = field(default_factory=list)  # EvidenceItem ids
    coverage_score: float = 0.0  # 0.0–1.0
    gap_reasons: list[str] = field(default_factory=list)
    notes: str = ""

    @staticmethod
    def new(claim_id: str, claim_text: str, claim_type: str = "fact") -> "ClaimEvidenceStatus":
        return ClaimEvidenceStatus(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "coverage": self.coverage,
            "evidence_ids": self.evidence_ids,
            "coverage_score": self.coverage_score,
            "gap_reasons": self.gap_reasons,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClaimEvidenceStatus":
        return cls(
            claim_id=str(data.get("claim_id", "")),
            claim_text=str(data.get("claim_text", "")),
            claim_type=str(data.get("claim_type", "fact")),
            coverage=str(data.get("coverage", "gap")),
            evidence_ids=list(data.get("evidence_ids", [])),
            coverage_score=float(data.get("coverage_score", 0.0)),
            gap_reasons=list(data.get("gap_reasons", [])),
            notes=str(data.get("notes", "")),
        )
