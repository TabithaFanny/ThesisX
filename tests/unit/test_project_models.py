"""Tests for Research Workspace project models."""

import pytest
from app.core.project.models import (
    Project, ResearchQuestion, ResearchDirection, ResearchGoal,
    ProjectKnowledgeLink, ProjectRunLink,
)


class TestProject:
    def test_create(self):
        p = Project.create(name="Test", research_question="RQ", discipline="CS")
        assert p.name == "Test"
        assert p.research_question == "RQ"
        assert p.discipline == "CS"
        assert p.status == "active"
        assert p.id

    def test_to_dict_round_trip(self):
        p = Project.create(name="Round", discipline="Math")
        d = p.to_dict()
        p2 = Project.from_dict(d)
        assert p2.name == p.name
        assert p2.id == p.id


class TestResearchQuestion:
    def test_create(self):
        rq = ResearchQuestion.create(project_id="pid", question="Q?", keywords=["ai"], discipline="CS")
        assert rq.project_id == "pid"
        assert rq.question == "Q?"
        assert rq.keywords == ["ai"]
        assert rq.discipline == "CS"

    def test_keywords_default_empty(self):
        rq = ResearchQuestion.create(project_id="pid", question="Q?")
        assert rq.keywords == []

    def test_to_dict_round_trip(self):
        rq = ResearchQuestion.create(project_id="pid", question="Q?", keywords=["x", "y"])
        d = rq.to_dict()
        rq2 = ResearchQuestion.from_dict(d)
        assert rq2.question == rq.question
        assert rq2.keywords == ["x", "y"]


class TestResearchDirection:
    def test_create(self):
        rd = ResearchDirection.create(project_id="pid", direction="方向A", rationale="因为...")
        assert rd.direction == "方向A"
        assert rd.status == "exploring"

    def test_to_dict_round_trip(self):
        rd = ResearchDirection.create(project_id="pid", direction="方向B")
        d = rd.to_dict()
        rd2 = ResearchDirection.from_dict(d)
        assert rd2.direction == rd.direction


class TestResearchGoal:
    def test_create(self):
        rg = ResearchGoal.create(project_id="pid", goal="目标A", milestone="Milestone1", deadline="2026-12-31")
        assert rg.goal == "目标A"
        assert rg.milestone == "Milestone1"
        assert rg.status == "pending"

    def test_to_dict_round_trip(self):
        rg = ResearchGoal.create(project_id="pid", goal="目标B")
        d = rg.to_dict()
        rg2 = ResearchGoal.from_dict(d)
        assert rg2.goal == rg.goal


class TestProjectKnowledgeLink:
    def test_create(self):
        link = ProjectKnowledgeLink.create(project_id="pid", knowledge_object_id="kid", role="core", priority=1)
        assert link.role == "core"
        assert link.priority == 1

    def test_default_role(self):
        link = ProjectKnowledgeLink.create(project_id="pid", knowledge_object_id="kid")
        assert link.role == "background"

    def test_to_dict_round_trip(self):
        link = ProjectKnowledgeLink.create(project_id="pid", knowledge_object_id="kid", role="evidence")
        d = link.to_dict()
        link2 = ProjectKnowledgeLink.from_dict(d)
        assert link2.role == "evidence"


class TestProjectRunLink:
    def test_create(self):
        link = ProjectRunLink.create(project_id="pid", run_id="rid")
        assert link.project_id == "pid"
        assert link.run_id == "rid"

    def test_to_dict_round_trip(self):
        link = ProjectRunLink.create(project_id="pid", run_id="rid")
        d = link.to_dict()
        link2 = ProjectRunLink.from_dict(d)
        assert link2.run_id == link.run_id