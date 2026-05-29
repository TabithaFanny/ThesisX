"""Quality Dashboard models — Vision 3.10.

WritingProgress: per-section word count + edit status.
ClaimCoverage: which claims from ResearchQuestion are supported by evidence.
EvidenceIntegrity: are linked evidence objects verified.
CitationCompleteness: are citations present and complete.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WritingProgress:
    """Per-section progress within a paper."""
    section_type: str  # abstract|intro|method|result|discussion|conclusion|references
    word_count: int = 0
    target_words: int = 0
    edit_status: str = "pending"  # pending|in_progress|done
    last_edited_at: str = ""

    @staticmethod
    def new(section_type: str, target_words: int = 0) -> "WritingProgress":
        return WritingProgress(
            section_type=section_type,
            target_words=target_words,
            last_edited_at=_now(),
        )

    def to_dict(self) -> dict:
        return {
            "section_type": self.section_type,
            "word_count": self.word_count,
            "target_words": self.target_words,
            "edit_status": self.edit_status,
            "last_edited_at": self.last_edited_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WritingProgress":
        return cls(
            section_type=str(d.get("section_type", "")),
            word_count=int(d.get("word_count", 0)),
            target_words=int(d.get("target_words", 0)),
            edit_status=str(d.get("edit_status", "pending")),
            last_edited_at=str(d.get("last_edited_at", _now())),
        )


@dataclass
class ClaimCoverage:
    """Whether a research claim is covered by evidence."""
    claim_id: str
    claim_text: str
    project_id: str
    covered: bool = False
    evidence_ko_ids: list[str] = field(default_factory=list)  # ProjectKnowledgeLink ids
    coverage_score: float = 0.0  # 0.0–1.0
    notes: str = ""

    @staticmethod
    def new(claim_id: str, claim_text: str, project_id: str) -> "ClaimCoverage":
        return ClaimCoverage(
            claim_id=claim_id,
            claim_text=claim_text,
            project_id=project_id,
        )

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "project_id": self.project_id,
            "covered": self.covered,
            "evidence_ko_ids": self.evidence_ko_ids,
            "coverage_score": self.coverage_score,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ClaimCoverage":
        return cls(
            claim_id=str(d.get("claim_id", "")),
            claim_text=str(d.get("claim_text", "")),
            project_id=str(d.get("project_id", "")),
            covered=bool(d.get("covered", False)),
            evidence_ko_ids=list(d.get("evidence_ko_ids", [])),
            coverage_score=float(d.get("coverage_score", 0.0)),
            notes=str(d.get("notes", "")),
        )


@dataclass
class EvidenceIntegrity:
    """Whether linked evidence objects are verified and usable."""
    project_knowledge_link_id: str
    source_id: str
    knowledge_title: str
    verified_status: str = "unverified"  # unverified|suggested|verified|rejected
    usable_for_writing: bool = True
    issue: str = ""  # empty = no issue

    @staticmethod
    def new(source_id: str, knowledge_title: str = "", verified_status: str = "unverified") -> "EvidenceIntegrity":
        return EvidenceIntegrity(
            project_knowledge_link_id=str(uuid.uuid4())[:12],
            source_id=source_id,
            knowledge_title=knowledge_title,
            verified_status=verified_status,
        )

    def to_dict(self) -> dict:
        return {
            "project_knowledge_link_id": self.project_knowledge_link_id,
            "source_id": self.source_id,
            "knowledge_title": self.knowledge_title,
            "verified_status": self.verified_status,
            "usable_for_writing": self.usable_for_writing,
            "issue": self.issue,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceIntegrity":
        return cls(
            project_knowledge_link_id=str(d.get("project_knowledge_link_id", "")),
            source_id=str(d.get("source_id", "")),
            knowledge_title=str(d.get("knowledge_title", "")),
            verified_status=str(d.get("verified_status", "unverified")),
            usable_for_writing=bool(d.get("usable_for_writing", True)),
            issue=str(d.get("issue", "")),
        )


@dataclass
class CitationCompleteness:
    """Citation completeness check result."""
    citation_key: str  # e.g. "(李明, 2023)"
    context: str  # surrounding text
    is_present: bool = True
    is_formatted: bool = True
    is_complete: bool = True  # all required fields present
    missing_fields: list[str] = field(default_factory=list)

    @staticmethod
    def new(citation_key: str, is_complete: bool = True) -> "CitationCompleteness":
        return CitationCompleteness(
            citation_key=citation_key,
            context="",
            is_complete=is_complete,
        )

    def to_dict(self) -> dict:
        return {
            "citation_key": self.citation_key,
            "context": self.context,
            "is_present": self.is_present,
            "is_formatted": self.is_formatted,
            "is_complete": self.is_complete,
            "missing_fields": self.missing_fields,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CitationCompleteness":
        return cls(
            citation_key=str(d.get("citation_key", "")),
            context=str(d.get("context", "")),
            is_present=bool(d.get("is_present", True)),
            is_formatted=bool(d.get("is_formatted", True)),
            is_complete=bool(d.get("is_complete", True)),
            missing_fields=list(d.get("missing_fields", [])),
        )
