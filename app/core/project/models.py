"""Project data models for ThesisX Research Workspace."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Project:
    """论文项目容器。"""
    id: str
    name: str
    research_question: Optional[str] = None
    discipline: Optional[str] = None
    status: str = "active"  # active | archived | completed
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()
        if not self.updated_at:
            self.updated_at = now_iso()

    @classmethod
    def create(cls, name: str, research_question: Optional[str] = None, discipline: Optional[str] = None) -> "Project":
        return cls(
            id=new_id(),
            name=name,
            research_question=research_question,
            discipline=discipline,
            status="active",
            created_at=now_iso(),
            updated_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "research_question": self.research_question,
            "discipline": self.discipline,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        return cls(
            id=d["id"],
            name=d["name"],
            research_question=d.get("research_question"),
            discipline=d.get("discipline"),
            status=d.get("status", "active"),
            created_at=d.get("created_at", now_iso()),
            updated_at=d.get("updated_at", now_iso()),
        )


@dataclass
class ResearchQuestion:
    """研究问题。"""
    id: str
    project_id: str
    question: str
    keywords: list[str] = field(default_factory=list)
    discipline: Optional[str] = None
    clarity_score: Optional[float] = None  # 4.1+ feature
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()
        if not self.updated_at:
            self.updated_at = now_iso()

    @classmethod
    def create(cls, project_id: str, question: str, keywords: Optional[list[str]] = None, discipline: Optional[str] = None) -> "ResearchQuestion":
        return cls(
            id=new_id(),
            project_id=project_id,
            question=question,
            keywords=keywords or [],
            discipline=discipline,
            clarity_score=None,
            created_at=now_iso(),
            updated_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question": self.question,
            "keywords": self.keywords,
            "discipline": self.discipline,
            "clarity_score": self.clarity_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ResearchQuestion":
        return cls(
            id=d["id"],
            project_id=d["project_id"],
            question=d["question"],
            keywords=d.get("keywords", []),
            discipline=d.get("discipline"),
            clarity_score=d.get("clarity_score"),
            created_at=d.get("created_at", now_iso()),
            updated_at=d.get("updated_at", now_iso()),
        )


@dataclass
class ResearchDirection:
    """研究方向。"""
    id: str
    project_id: str
    direction: str
    rationale: Optional[str] = None
    status: str = "exploring"  # exploring | selected | rejected
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()

    @classmethod
    def create(cls, project_id: str, direction: str, rationale: Optional[str] = None) -> "ResearchDirection":
        return cls(
            id=new_id(),
            project_id=project_id,
            direction=direction,
            rationale=rationale,
            status="exploring",
            created_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "direction": self.direction,
            "rationale": self.rationale,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ResearchDirection":
        return cls(
            id=d["id"],
            project_id=d["project_id"],
            direction=d["direction"],
            rationale=d.get("rationale"),
            status=d.get("status", "exploring"),
            created_at=d.get("created_at", now_iso()),
        )


@dataclass
class ResearchGoal:
    """研究目标。"""
    id: str
    project_id: str
    goal: str
    milestone: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "pending"  # pending | in_progress | completed
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()

    @classmethod
    def create(cls, project_id: str, goal: str, milestone: Optional[str] = None, deadline: Optional[str] = None) -> "ResearchGoal":
        return cls(
            id=new_id(),
            project_id=project_id,
            goal=goal,
            milestone=milestone,
            deadline=deadline,
            status="pending",
            created_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "goal": self.goal,
            "milestone": self.milestone,
            "deadline": self.deadline,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ResearchGoal":
        return cls(
            id=d["id"],
            project_id=d["project_id"],
            goal=d["goal"],
            milestone=d.get("milestone"),
            deadline=d.get("deadline"),
            status=d.get("status", "pending"),
            created_at=d.get("created_at", now_iso()),
        )


@dataclass
class ProjectKnowledgeLink:
    """项目-知识对象绑定。"""
    id: str
    project_id: str
    knowledge_object_id: str
    role: str = "background"  # background | core | method | theory | evidence | contrast | section_claim
    priority: int = 0
    project_note: Optional[str] = None
    used_in_sections: list[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()

    @classmethod
    def create(cls, project_id: str, knowledge_object_id: str, role: str = "background", priority: int = 0) -> "ProjectKnowledgeLink":
        return cls(
            id=new_id(),
            project_id=project_id,
            knowledge_object_id=knowledge_object_id,
            role=role,
            priority=priority,
            project_note=None,
            used_in_sections=[],
            created_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "knowledge_object_id": self.knowledge_object_id,
            "role": self.role,
            "priority": self.priority,
            "project_note": self.project_note,
            "used_in_sections": self.used_in_sections,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectKnowledgeLink":
        return cls(
            id=d["id"],
            project_id=d["project_id"],
            knowledge_object_id=d["knowledge_object_id"],
            role=d.get("role", "background"),
            priority=d.get("priority", 0),
            project_note=d.get("project_note"),
            used_in_sections=d.get("used_in_sections", []),
            created_at=d.get("created_at", now_iso()),
        )


@dataclass
class ProjectRunLink:
    """项目-Run绑定。"""
    id: str
    project_id: str
    run_id: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()

    @classmethod
    def create(cls, project_id: str, run_id: str) -> "ProjectRunLink":
        return cls(
            id=new_id(),
            project_id=project_id,
            run_id=run_id,
            created_at=now_iso(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectRunLink":
        return cls(
            id=d["id"],
            project_id=d["project_id"],
            run_id=d["run_id"],
            created_at=d.get("created_at", now_iso()),
        )