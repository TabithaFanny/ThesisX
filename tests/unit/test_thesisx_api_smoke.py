"""Smoke tests for the ThesisX FastAPI wrapper."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.knowledge.models import KnowledgeItem
from app.core.literature.models import Reference


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.project.service._DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr("app.core.knowledge.store._DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr("app.core.literature.service.LiteratureService.LIT_DIR", tmp_path / "literature")
    monkeypatch.setattr("thesisx_api.routes.pipeline.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(
        "thesisx_api.routes.rag.Path.home",
        lambda: tmp_path,
    )

    main = importlib.import_module("thesisx_api.main")
    return TestClient(main.app)


def test_api_imports_and_health(api_client):
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_crud_closed_loop(api_client):
    created = api_client.post(
        "/api/projects",
        json={"name": "Smoke Project", "research_question": "How?", "discipline": "CS"},
    )
    assert created.status_code == 201
    project = created.json()

    listed = api_client.get("/api/projects")
    assert listed.status_code == 200
    assert any(p["id"] == project["id"] for p in listed.json())

    fetched = api_client.get(f"/api/projects/{project['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Smoke Project"

    patched = api_client.patch(f"/api/projects/{project['id']}", json={"name": "Updated"})
    assert patched.status_code == 200
    assert patched.json()["name"] == "Updated"

    deleted = api_client.delete(f"/api/projects/{project['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True


def test_knowledge_search_route_not_shadowed(api_client):
    created = api_client.post(
        "/api/knowledge",
        json={
            "item_type": "note",
            "title": "Searchable Knowledge",
            "content": "needle alpha beta",
        },
    )
    assert created.status_code == 201

    response = api_client.get("/api/knowledge/search", params={"q": "needle"})

    assert response.status_code == 200
    assert any(item["title"] == "Searchable Knowledge" for item in response.json())


def test_literature_search_route_not_shadowed(api_client, tmp_path):
    from app.core.literature.service import LiteratureService

    svc = LiteratureService(base_dir=tmp_path / "literature")
    ref = Reference.new(title="Searchable Literature", authors=["Smith"], year="2024", abstract="needle paper")
    svc.update_reference(ref)

    response = api_client.get("/api/literature/search", params={"q": "needle"})

    assert response.status_code == 200
    assert any(item["title"] == "Searchable Literature" for item in response.json())


def test_rag_build_and_search_persist_between_requests(api_client):
    created = api_client.post(
        "/api/knowledge",
        json={
            "item_type": "note",
            "title": "RAG Smoke",
            "content": "persistent needlechunk material",
            "project_id": "proj-rag",
        },
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    build = api_client.post("/api/rag/index/build", params={"project_id": "proj-rag"})
    assert build.status_code == 200
    assert build.json()["count"] > 0

    status = api_client.get("/api/rag/index/status", params={"project_id": "proj-rag"})
    assert status.status_code == 200
    assert status.json()["size"] == build.json()["count"]

    search = api_client.post(
        "/api/rag/search",
        json={"query": "needlechunk", "project_id": "proj-rag", "object_id": item_id},
    )
    assert search.status_code == 200
    assert search.json()
    assert search.json()[0]["source_id"] == item_id


def test_pipeline_stream_returns_sse_text(api_client):
    created = api_client.post("/api/pipeline/sessions", json={"topic": "stream smoke"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    with api_client.stream("GET", f"/api/pipeline/sessions/{session_id}/stream") as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: stage" in body
    assert "event: chunk" in body
    assert "event: complete" in body


def test_pipeline_session_paper_endpoint_returns_markdown(api_client):
    created = api_client.post("/api/pipeline/sessions", json={"topic": "paper smoke"})
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    # Reuse the route-level patched RUNS_DIR by writing directly under the created session directory.
    # The TestClient fixture points the pipeline route to tmp_path / "runs".
    from thesisx_api.routes import pipeline as pipeline_routes

    target = pipeline_routes.RUNS_DIR / session_id / "output"
    target.mkdir(parents=True, exist_ok=True)
    (target / "paper.md").write_text("# Smoke Paper\n\nGenerated content.", encoding="utf-8")

    response = api_client.get(f"/api/pipeline/sessions/{session_id}/paper")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert "Smoke Paper" in payload["markdown"]


def test_pipeline_real_mode_requires_provider_config(api_client):
    response = api_client.post(
        "/api/pipeline/sessions",
        json={"topic": "real mode smoke", "run_mode": "real"},
    )

    assert response.status_code == 422
    payload = response.json()["detail"]
    assert payload["code"] == "PROVIDER_CONFIG_MISSING"
    assert payload["missing"] == ["api_key", "base_url", "model"]


def test_settings_obsidian_scan_persists_items(api_client, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# Note\nUseful content", encoding="utf-8")

    response = api_client.post(
        "/api/settings/obsidian/scan",
        params={"vault_path": str(vault), "max_files": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    listed = api_client.get("/api/knowledge")
    assert listed.status_code == 200
    assert any(item["title"] == payload[0]["title"] for item in listed.json())


def test_settings_zotero_import_persists_items(api_client, tmp_path):
    bib = tmp_path / "library.bib"
    bib.write_text(
        """
@article{smith2025,
  title={Structured Literature Maps},
  author={Smith, Alice and Lee, Bob},
  year={2025},
  journal={CHI}
}
""".strip(),
        encoding="utf-8",
    )

    response = api_client.post(
        "/api/settings/zotero/import",
        params={"file_path": str(bib), "format": "bibtex"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    listed = api_client.get("/api/knowledge")
    assert listed.status_code == 200
    assert any(item["title"] == "Structured Literature Maps" for item in listed.json())


def test_literature_structure_creates_knowledge_items(api_client, tmp_path):
    from app.core.literature.service import LiteratureService

    svc = LiteratureService(base_dir=tmp_path / "literature")
    ref = Reference.new(
        title="Structured Review Paper",
        authors=["Alice Smith"],
        year="2025",
        abstract=(
            "This paper studies structured literature workflows. "
            "It proposes a reusable method for research synthesis. "
            "Results show faster traceability."
        ),
        zotero_key="ZKEY1234",
    )
    svc.update_reference(ref)

    response = api_client.post(
        f"/api/literature/{ref.id}/structure",
        json={"project_id": "proj-structure"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["reference_id"] == ref.id
    assert len(payload["items"]) >= 4
    listed = api_client.get("/api/knowledge", params={"project_id": "proj-structure"})
    assert listed.status_code == 200
    assert any("Structured Review Paper" in item["title"] for item in listed.json())


def test_agent_context_returns_layered_bundle(api_client):
    created = api_client.post(
        "/api/projects",
        json={"name": "Context Project", "research_question": "How to assemble context?", "discipline": "HCI"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    rq = api_client.post(
        f"/api/projects/{project_id}/rq",
        json={"project_id": project_id, "question": "How should agent context be layered?", "keywords": ["context"]},
    )
    assert rq.status_code == 201

    api_client.post(
        "/api/knowledge",
        json={
            "item_type": "note",
            "title": "Context Note",
            "content": "Important project memory",
            "project_id": project_id,
            "source_file": "",
            "tags": [],
            "external_source": "manual",
        },
    )

    response = api_client.post(
        "/api/agent/context",
        json={
            "task_type": "writing",
            "project_id": project_id,
            "query": "draft a revision section",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "writing"
    assert payload["project_id"] == project_id
    assert "Project Context" in payload["assembled_context"]
    assert "Knowledge Items:" in payload["working_context"]
    assert "Output Contract" in payload["assembled_context"]


def test_agent_rewrite_uses_unified_context(api_client):
    created = api_client.post(
        "/api/projects",
        json={"name": "Rewrite Project", "research_question": "How to rewrite with context?", "discipline": "HCI"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    api_client.post(
        "/api/knowledge",
        json={
            "item_type": "note",
            "title": "Rewrite Context Note",
            "content": "Stored project knowledge",
            "project_id": project_id,
            "source_file": "",
            "tags": [],
            "external_source": "manual",
        },
    )

    response = api_client.post(
        "/api/agent/rewrite",
        json={
            "task_type": "quality",
            "selected_text": "This is very important in order to improve quality.",
            "mode": "polish",
            "project_id": project_id,
            "query": "generate revision guidance",
            "extra_context": "Focus on actionable revisions.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "quality"
    assert payload["mode"] == "polish"
    assert payload["rewritten"] != payload["original"]
    assert "Project Context" in payload["assembled_context"]
    assert "Focus on actionable revisions." in payload["assembled_context"]
    assert payload["sources"]


def test_agent_artifact_returns_structured_quality_plan(api_client):
    created = api_client.post(
        "/api/projects",
        json={"name": "Artifact Project", "research_question": "How to plan revisions?", "discipline": "HCI"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    response = api_client.post(
        "/api/agent/artifact",
        json={
            "task_type": "quality",
            "project_id": project_id,
            "query": "generate revision plan",
            "extra_context": "Focus on executable steps.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "quality"
    assert payload["artifact_type"] == "revision_plan"
    assert payload["summary"]
    assert payload["steps"]
    assert payload["actions"]
    assert "Output Contract" in payload["assembled_context"]


def test_agent_feedback_flows_into_context(api_client):
    feedback = api_client.post(
        "/api/agent/feedback",
        json={"task_type": "quality", "accepted": False, "signal": "步骤太泛，想要更具体"},
    )
    assert feedback.status_code == 200

    response = api_client.post(
        "/api/agent/context",
        json={"task_type": "quality", "query": "improve revision planning"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Recent feedback memory" in payload["memory_context"]
    assert "步骤太泛" in payload["memory_context"]


def test_agent_feedback_endpoint_accepts_signal(api_client):
    response = api_client.post(
        "/api/agent/feedback",
        json={"task_type": "writing", "accepted": True, "signal": "结构清晰，适合直接替换"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
