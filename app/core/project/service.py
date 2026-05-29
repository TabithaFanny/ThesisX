"""Project service — SQLite CRUD for Research Workspace."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .models import (
    Project, ResearchQuestion, ResearchDirection, ResearchGoal,
    ProjectKnowledgeLink, ProjectRunLink,
)


_DB_PATH = Path.home() / ".wenbiao" / "thesisx.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all project tables if they don't exist."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            research_question TEXT,
            discipline TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_questions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            question TEXT NOT NULL,
            keywords TEXT DEFAULT '[]',
            discipline TEXT,
            clarity_score REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_directions (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            rationale TEXT,
            status TEXT DEFAULT 'exploring',
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS research_goals (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            goal TEXT NOT NULL,
            milestone TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_knowledge_links (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            knowledge_object_id TEXT NOT NULL,
            role TEXT DEFAULT 'background',
            priority INTEGER DEFAULT 0,
            project_note TEXT,
            used_in_sections TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            UNIQUE(project_id, knowledge_object_id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_run_links (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(project_id, run_id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    conn.commit()
    conn.close()


class ProjectService:
    """Main CRUD service for Research Workspace."""

    def __init__(self):
        init_db()

    # ── Project ──────────────────────────────────────────────────

    def create_project(self, name: str, research_question: Optional[str] = None, discipline: Optional[str] = None) -> Project:
        project = Project.create(name=name, research_question=research_question, discipline=discipline)
        conn = _get_conn()
        conn.execute(
            "INSERT INTO projects (id,name,research_question,discipline,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (project.id, project.name, project.research_question, project.discipline, project.status, project.created_at, project.updated_at),
        )
        conn.commit()
        conn.close()
        return project

    def get_project(self, id: str) -> Optional[Project]:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (id,)).fetchone()
        conn.close()
        if row:
            return Project.from_dict(dict(row))
        return None

    def update_project(self, id: str, patch: dict) -> None:
        if not patch:
            return
        set_clauses = [f"{k}=?" for k in patch.keys()]
        vals = list(patch.values()) + [id]
        conn = _get_conn()
        conn.execute(f"UPDATE projects SET {','.join(set_clauses)} WHERE id=?", vals)
        conn.commit()
        conn.close()

    def delete_project(self, id: str) -> None:
        conn = _get_conn()
        conn.execute("UPDATE projects SET status='archived' WHERE id=?", (id,))
        conn.commit()
        conn.close()

    def list_projects(self) -> list[Project]:
        conn = _get_conn()
        rows = conn.execute("SELECT * FROM projects WHERE status='active' ORDER BY updated_at DESC").fetchall()
        conn.close()
        return [Project.from_dict(dict(r)) for r in rows]

    # ── ResearchQuestion ─────────────────────────────────────────

    def create_research_question(self, project_id: str, question: str, keywords: Optional[list[str]] = None, discipline: Optional[str] = None) -> ResearchQuestion:
        rq = ResearchQuestion.create(project_id=project_id, question=question, keywords=keywords, discipline=discipline)
        conn = _get_conn()
        conn.execute(
            "INSERT INTO research_questions (id,project_id,question,keywords,discipline,clarity_score,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (rq.id, rq.project_id, rq.question, json.dumps(rq.keywords), rq.discipline, rq.clarity_score, rq.created_at, rq.updated_at),
        )
        conn.commit()
        conn.close()
        return rq

    def get_research_question(self, project_id: str) -> Optional[ResearchQuestion]:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM research_questions WHERE project_id=? ORDER BY created_at DESC LIMIT 1", (project_id,)).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["keywords"] = json.loads(d.get("keywords", "[]"))
            return ResearchQuestion.from_dict(d)
        return None

    def update_research_question(self, id: str, patch: dict) -> None:
        if "keywords" in patch and isinstance(patch["keywords"], list):
            patch["keywords"] = json.dumps(patch["keywords"])
        if not patch:
            return
        set_clauses = [f"{k}=?" for k in patch.keys()]
        vals = list(patch.values()) + [id]
        conn = _get_conn()
        conn.execute(f"UPDATE research_questions SET {','.join(set_clauses)} WHERE id=?", vals)
        conn.commit()
        conn.close()

    # ── ResearchDirection ────────────────────────────────────────

    def create_research_direction(self, project_id: str, direction: str, rationale: Optional[str] = None) -> ResearchDirection:
        rd = ResearchDirection.create(project_id=project_id, direction=direction, rationale=rationale)
        conn = _get_conn()
        conn.execute(
            "INSERT INTO research_directions (id,project_id,direction,rationale,status,created_at) VALUES (?,?,?,?,?,?)",
            (rd.id, rd.project_id, rd.direction, rd.rationale, rd.status, rd.created_at),
        )
        conn.commit()
        conn.close()
        return rd

    def list_research_directions(self, project_id: str) -> list[ResearchDirection]:
        conn = _get_conn()
        rows = conn.execute("SELECT * FROM research_directions WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        conn.close()
        return [ResearchDirection.from_dict(dict(r)) for r in rows]

    # ── ResearchGoal ─────────────────────────────────────────────

    def create_research_goal(self, project_id: str, goal: str, milestone: Optional[str] = None, deadline: Optional[str] = None) -> ResearchGoal:
        rg = ResearchGoal.create(project_id=project_id, goal=goal, milestone=milestone, deadline=deadline)
        conn = _get_conn()
        conn.execute(
            "INSERT INTO research_goals (id,project_id,goal,milestone,deadline,status,created_at) VALUES (?,?,?,?,?,?,?)",
            (rg.id, rg.project_id, rg.goal, rg.milestone, rg.deadline, rg.status, rg.created_at),
        )
        conn.commit()
        conn.close()
        return rg

    def list_research_goals(self, project_id: str) -> list[ResearchGoal]:
        conn = _get_conn()
        rows = conn.execute("SELECT * FROM research_goals WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        conn.close()
        return [ResearchGoal.from_dict(dict(r)) for r in rows]

    # ── ProjectKnowledgeLink ────────────────────────────────────

    def link_knowledge_object(self, project_id: str, knowledge_object_id: str, role: str = "background", priority: int = 0) -> ProjectKnowledgeLink:
        link = ProjectKnowledgeLink.create(project_id=project_id, knowledge_object_id=knowledge_object_id, role=role, priority=priority)
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO project_knowledge_links (id,project_id,knowledge_object_id,role,priority,project_note,used_in_sections,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (link.id, link.project_id, link.knowledge_object_id, link.role, link.priority, link.project_note, json.dumps(link.used_in_sections), link.created_at),
        )
        conn.commit()
        conn.close()
        return link

    def unlink_knowledge_object(self, project_id: str, knowledge_object_id: str) -> None:
        conn = _get_conn()
        conn.execute("DELETE FROM project_knowledge_links WHERE project_id=? AND knowledge_object_id=?", (project_id, knowledge_object_id))
        conn.commit()
        conn.close()

    def list_project_knowledge(self, project_id: str) -> list[str]:
        conn = _get_conn()
        rows = conn.execute("SELECT knowledge_object_id FROM project_knowledge_links WHERE project_id=?", (project_id,)).fetchall()
        conn.close()
        return [r["knowledge_object_id"] for r in rows]

    # ── ProjectRunLink ───────────────────────────────────────────

    def link_run(self, project_id: str, run_id: str) -> ProjectRunLink:
        link = ProjectRunLink.create(project_id=project_id, run_id=run_id)
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO project_run_links (id,project_id,run_id,created_at) VALUES (?,?,?,?)",
            (link.id, link.project_id, link.run_id, link.created_at),
        )
        conn.commit()
        conn.close()
        return link

    def list_project_runs(self, project_id: str) -> list[str]:
        conn = _get_conn()
        rows = conn.execute("SELECT run_id FROM project_run_links WHERE project_id=?", (project_id,)).fetchall()
        conn.close()
        return [r["run_id"] for r in rows]