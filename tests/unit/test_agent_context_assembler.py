from __future__ import annotations

from pathlib import Path

from app.core.agent.context_assembler import AgentContextAssembler
from app.core.agent.feedback_memory import AgentFeedbackMemory
from app.core.knowledge.models import KnowledgeItem
from app.core.knowledge.store import KnowledgeStore
from app.core.project.service import ProjectService
from app.core.pipeline.session_store import SessionStore
from app.core.pipeline.models import PaperRequest


def test_output_contract_is_included_for_known_task():
    bundle = AgentContextAssembler().assemble(task_type="quality", query="improve draft")

    assert bundle.task_type == "quality"
    assert "revision plan" in bundle.output_contract.lower()
    assert "# Output Contract" in bundle.assembled_context


def test_context_prefers_relevant_knowledge(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.core.project.service._DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr("app.core.knowledge.store._DB_PATH", tmp_path / "test.db")

    project_id = ProjectService().create_project("Ctx", "How to use evidence?", "HCI").id
    store = KnowledgeStore()
    store.add(
        KnowledgeItem.create(
            item_type="evidence",
            title="Evidence Binding Guide",
            content="claim evidence support binding strategy",
            project_id=project_id,
        )
    )
    store.add(
        KnowledgeItem.create(
            item_type="theory",
            title="Institutional Theory",
            content="organization legitimacy isomorphism",
            project_id=project_id,
        )
    )

    bundle = AgentContextAssembler().assemble(
        task_type="evidence",
        project_id=project_id,
        query="evidence support binding",
    )

    assert "Evidence Binding Guide" in bundle.working_context


def test_feedback_memory_is_project_aware(monkeypatch, tmp_path: Path):
    feedback_file = tmp_path / "agent_feedback.json"
    monkeypatch.setattr(AgentFeedbackMemory, "FILE", feedback_file)

    memory = AgentFeedbackMemory()
    memory.append(task_type="quality", project_id="p1", accepted=False, signal="计划太泛")
    memory.append(task_type="quality", project_id="p2", accepted=True, signal="计划足够具体")

    summary = memory.summarize("quality", project_id="p1")

    assert "计划太泛" in summary
    assert "计划足够具体" not in summary
