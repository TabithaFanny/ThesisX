"""Tests for ProjectService (SQLite CRUD)."""

import pytest
import tempfile
import os
from pathlib import Path
from app.core.project.service import ProjectService
from app.core.project.models import Project, ResearchQuestion


@pytest.fixture
def svc(tmp_path, monkeypatch):
    """Service pointing at a temp DB."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("app.core.project.service._DB_PATH", db_path)
    # Patch Path.home() for this test
    return ProjectService()


class TestProjectService:
    def test_create_project(self, svc):
        p = svc.create_project(name="Test Project", discipline="CS")
        assert p.name == "Test Project"
        assert p.discipline == "CS"
        assert p.status == "active"
        assert p.id

    def test_get_project(self, svc):
        created = svc.create_project(name="Get Me")
        retrieved = svc.get_project(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Get Me"

    def test_get_project_not_found(self, svc):
        assert svc.get_project("not-exist") is None

    def test_update_project(self, svc):
        p = svc.create_project(name="Old Name")
        svc.update_project(p.id, {"name": "New Name"})
        updated = svc.get_project(p.id)
        assert updated.name == "New Name"

    def test_delete_project(self, svc):
        p = svc.create_project(name="To Delete")
        svc.delete_project(p.id)
        # Soft delete - project still exists but archived
        deleted = svc.get_project(p.id)
        assert deleted is not None
        assert deleted.status == "archived"
        # Should not appear in active list
        projects = svc.list_projects()
        assert all(pr.id != p.id for pr in projects)

    def test_list_projects(self, svc):
        p1 = svc.create_project(name="P1")
        p2 = svc.create_project(name="P2")
        projects = svc.list_projects()
        names = [pr.name for pr in projects]
        assert "P1" in names
        assert "P2" in names

    def test_list_projects_excludes_archived(self, svc):
        p = svc.create_project(name="Active")
        svc.delete_project(p.id)  # soft-delete
        projects = svc.list_projects()
        assert all(pr.id != p.id for pr in projects)


class TestResearchQuestionService:
    def test_create_research_question(self, svc):
        proj = svc.create_project(name="RQ Test")
        rq = svc.create_research_question(
            project_id=proj.id,
            question="How does X work?",
            keywords=["ai", "ml"],
            discipline="CS",
        )
        assert rq.project_id == proj.id
        assert rq.question == "How does X work?"
        assert rq.keywords == ["ai", "ml"]

    def test_get_research_question(self, svc):
        proj = svc.create_project(name="Get RQ")
        rq = svc.create_research_question(project_id=proj.id, question="Q1?")
        retrieved = svc.get_research_question(proj.id)
        assert retrieved is not None
        assert retrieved.id == rq.id
        assert retrieved.question == "Q1?"

    def test_get_research_question_not_found(self, svc):
        assert svc.get_research_question("not-exist") is None


class TestResearchDirectionService:
    def test_create_research_direction(self, svc):
        proj = svc.create_project(name="Dir Test")
        rd = svc.create_research_direction(
            project_id=proj.id,
            direction="方向A",
            rationale="因为...",
        )
        assert rd.direction == "方向A"
        assert rd.status == "exploring"

    def test_list_research_directions(self, svc):
        proj = svc.create_project(name="List Dir")
        svc.create_research_direction(project_id=proj.id, direction="A")
        svc.create_research_direction(project_id=proj.id, direction="B")
        directions = svc.list_research_directions(proj.id)
        assert len(directions) == 2


class TestResearchGoalService:
    def test_create_research_goal(self, svc):
        proj = svc.create_project(name="Goal Test")
        rg = svc.create_research_goal(
            project_id=proj.id,
            goal="目标A",
            milestone="Milestone1",
            deadline="2026-12-31",
        )
        assert rg.goal == "目标A"
        assert rg.status == "pending"

    def test_list_research_goals(self, svc):
        proj = svc.create_project(name="List Goal")
        svc.create_research_goal(project_id=proj.id, goal="G1")
        svc.create_research_goal(project_id=proj.id, goal="G2")
        goals = svc.list_research_goals(proj.id)
        assert len(goals) == 2


class TestKnowledgeLinkService:
    def test_link_knowledge_object(self, svc):
        proj = svc.create_project(name="Link Test")
        link = svc.link_knowledge_object(
            project_id=proj.id,
            knowledge_object_id="ko-123",
            role="core",
            priority=1,
        )
        assert link.knowledge_object_id == "ko-123"
        assert link.role == "core"

    def test_unlink_knowledge_object(self, svc):
        proj = svc.create_project(name="Unlink Test")
        svc.link_knowledge_object(project_id=proj.id, knowledge_object_id="ko-456")
        svc.unlink_knowledge_object(project_id=proj.id, knowledge_object_id="ko-456")
        links = svc.list_project_knowledge(proj.id)
        assert "ko-456" not in links

    def test_list_project_knowledge(self, svc):
        proj = svc.create_project(name="List KO")
        svc.link_knowledge_object(project_id=proj.id, knowledge_object_id="ko-a")
        svc.link_knowledge_object(project_id=proj.id, knowledge_object_id="ko-b")
        links = svc.list_project_knowledge(proj.id)
        assert "ko-a" in links
        assert "ko-b" in links


class TestRunLinkService:
    def test_link_run(self, svc):
        proj = svc.create_project(name="Run Link")
        link = svc.link_run(project_id=proj.id, run_id="run-001")
        assert link.run_id == "run-001"

    def test_list_project_runs(self, svc):
        proj = svc.create_project(name="List Runs")
        svc.link_run(project_id=proj.id, run_id="run-x")
        svc.link_run(project_id=proj.id, run_id="run-y")
        runs = svc.list_project_runs(proj.id)
        assert "run-x" in runs
        assert "run-y" in runs
