"""Unified agent context assembler for ThesisX workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from app.core.knowledge.store import KnowledgeStore
from app.core.context_compressor import ContextCompressor
from app.core.agent.feedback_memory import AgentFeedbackMemory
from app.core.agent.output_contracts import get_output_contract
from app.core.pipeline.run_history import RunHistoryReader
from app.core.project.service import ProjectService
from app.core.quality.service import QualityService
from app.core.skills.enabled_store import EnabledSkillsStore


@dataclass
class AgentContextBundle:
    task_type: str
    project_id: str = ""
    session_id: str = ""
    project_summary: str = ""
    working_context: str = ""
    memory_context: str = ""
    output_contract: str = ""
    assembled_context: str = ""
    sources: list[str] = field(default_factory=list)


class AgentContextAssembler:
    """Build layered context so pages stop hand-rolling tiny prompt strings."""

    def assemble(
        self,
        *,
        task_type: str,
        project_id: str = "",
        session_id: str = "",
        query: str = "",
    ) -> AgentContextBundle:
        project_summary, project_sources = self._build_project_summary(project_id, query)
        working_context, working_sources = self._build_working_context(project_id, session_id, query, task_type)
        memory_context, memory_sources = self._build_memory_context(task_type, project_id)
        output_contract = self._build_output_contract(task_type)

        project_summary = self._trim(project_summary, 1200, from_end=False)
        working_context = self._trim(working_context, 2200, from_end=True)
        memory_context = self._trim(memory_context, 800, from_end=True)

        sections = [
            f"# Task Type\n{task_type}",
            f"# Project Context\n{project_summary or 'No project context available.'}",
            f"# Working Context\n{working_context or 'No working context available.'}",
            f"# Memory Context\n{memory_context or 'No memory context available.'}",
            f"# Output Contract\n{output_contract}",
        ]
        if query.strip():
            sections.append(f"# User Query\n{query.strip()}")

        return AgentContextBundle(
            task_type=task_type,
            project_id=project_id,
            session_id=session_id,
            project_summary=project_summary,
            working_context=working_context,
            memory_context=memory_context,
            output_contract=output_contract,
            assembled_context="\n\n".join(sections).strip(),
            sources=project_sources + working_sources + memory_sources,
        )

    def _build_project_summary(self, project_id: str, query: str) -> tuple[str, list[str]]:
        if not project_id:
            return "", []
        svc = ProjectService()
        project = svc.get_project(project_id)
        if not project:
            return "", []
        rq = svc.get_research_question(project_id)
        directions = svc.list_research_directions(project_id)
        goals = svc.list_research_goals(project_id)
        lines = [
            f"Project: {project.name}",
            f"Discipline: {project.discipline or 'unspecified'}",
            f"Research Question: {rq.question if rq else (project.research_question or 'not set')}",
        ]
        ranked_directions = self._rank_records(
            [(item.direction, item) for item in directions],
            query=query,
        )[:3]
        ranked_goals = self._rank_records(
            [(item.goal, item) for item in goals],
            query=query,
        )[:3]
        if ranked_directions:
            lines.append("Directions:")
            lines.extend(f"- {item.direction}" for item in ranked_directions)
        if ranked_goals:
            lines.append("Goals:")
            lines.extend(f"- {item.goal}" for item in ranked_goals)
        return "\n".join(lines), ["project", "research_question", "research_directions", "research_goals"]

    def _build_working_context(
        self,
        project_id: str,
        session_id: str,
        query: str,
        task_type: str,
    ) -> tuple[str, list[str]]:
        lines: list[str] = []
        sources: list[str] = []

        if project_id:
            store = KnowledgeStore()
            knowledge_items = store.list(project_id=project_id, limit=20)
            knowledge_items = self._rank_knowledge_items(knowledge_items, query=query, task_type=task_type)[:5]
            if knowledge_items:
                lines.append("Knowledge Items:")
                for item in knowledge_items:
                    excerpt = (item.content or "").strip().replace("\n", " ")[:180]
                    lines.append(f"- [{item.item_type}] {item.title}: {excerpt}")
                sources.append("knowledge_store")

            dashboard = QualityService(project_id).get_dashboard()
            lines.extend([
                "Quality Signals:",
                f"- overall_score={dashboard.overall_score}",
                f"- writing_progress={dashboard.writing_progress}",
                f"- claim_coverage={dashboard.claim_coverage}",
                f"- evidence_integrity={dashboard.evidence_integrity}",
            ])
            if dashboard.suggestions:
                lines.append("- suggestions:")
                lines.extend(f"  - {item}" for item in dashboard.suggestions[:5])
            sources.append("quality_dashboard")

        if session_id:
            reader = RunHistoryReader()
            try:
                detail = reader.get_run(session_id)
                lines.extend([
                    "Session Snapshot:",
                    f"- session_id={session_id}",
                    f"- status={detail.summary.status}",
                    f"- topic={detail.summary.topic}",
                    f"- event_count={detail.event_count}",
                    f"- message_count={detail.message_count}",
                ])
                if detail.output_files.get("paper_md"):
                    paper_text = Path(detail.output_files["paper_md"]).read_text(encoding="utf-8")
                    lines.append("Session Paper Excerpt:")
                    lines.append(self._select_relevant_paragraphs(paper_text, query=query, limit=3, max_chars=700))
                sources.append("run_history")
            except Exception:
                pass

        rag_path = Path.home() / ".wenbiao" / "runs" / "_context" / "rag_context.md"
        if rag_path.exists():
            try:
                rag_text = rag_path.read_text(encoding="utf-8").strip()
                if rag_text:
                    lines.append("RAG Context Excerpt:")
                    lines.append(rag_text[:800])
                    sources.append("rag_context")
            except OSError:
                pass

        if query.strip():
            lines.append(f"Immediate user intent: {query.strip()}")

        return "\n".join(lines).strip(), sources

    def _build_memory_context(self, task_type: str, project_id: str) -> tuple[str, list[str]]:
        enabled_skills = sorted(EnabledSkillsStore().load())
        lines = []
        if enabled_skills:
            lines.append("Enabled skills:")
            lines.extend(f"- {skill}" for skill in enabled_skills[:12])
        else:
            lines.append("Enabled skills: none")
        feedback = AgentFeedbackMemory().summarize(task_type, project_id=project_id)
        if feedback:
            lines.append(feedback)
        lines.append("Preference: preserve local-first, traceable, project-linked outputs.")
        return "\n".join(lines), ["skills_enabled", "agent_feedback"]

    def _build_output_contract(self, task_type: str) -> str:
        return get_output_contract(task_type)

    @staticmethod
    def _trim(text: str, max_chars: int, from_end: bool) -> str:
        if not text:
            return ""
        return ContextCompressor.compress(text, max_chars=max_chars, from_end=from_end)

    @staticmethod
    def _extract_terms(text: str) -> set[str]:
        if not text:
            return set()
        normalized = text.lower()
        terms = set(re.findall(r"[a-zA-Z]{2,}", normalized))
        chinese = re.findall(r"[\u4e00-\u9fff]+", text)
        for chunk in chinese:
            if len(chunk) <= 2:
                terms.add(chunk)
                continue
            for i in range(len(chunk) - 1):
                terms.add(chunk[i : i + 2])
        return {term for term in terms if term.strip()}

    @classmethod
    def _score_text(cls, text: str, query: str) -> int:
        if not text:
            return 0
        if not query.strip():
            return 0
        text_terms = cls._extract_terms(text)
        query_terms = cls._extract_terms(query)
        return len(text_terms & query_terms)

    @classmethod
    def _rank_records(cls, pairs: list[tuple[str, object]], query: str) -> list[object]:
        if not query.strip():
            return [item for _, item in pairs]
        ranked = sorted(
            pairs,
            key=lambda pair: cls._score_text(pair[0], query),
            reverse=True,
        )
        return [item for text, item in ranked if cls._score_text(text, query) > 0] or [item for _, item in pairs]

    @classmethod
    def _rank_knowledge_items(cls, items, *, query: str, task_type: str):
        type_bonus = {
            "evidence": {"evidence": 4, "literature": 2},
            "theory": {"theory": 4, "note": 1},
            "knowledge": {"note": 2, "theory": 1, "evidence": 1},
            "writing": {"note": 2, "evidence": 2, "theory": 2},
            "quality": {"evidence": 2, "theory": 2, "note": 1},
        }
        ranked = sorted(
            items,
            key=lambda item: (
                cls._score_text(f"{item.title}\n{item.content}", query) * 3
                + type_bonus.get(task_type, {}).get(item.item_type, 0)
            ),
            reverse=True,
        )
        return ranked

    @classmethod
    def _select_relevant_paragraphs(cls, text: str, *, query: str, limit: int, max_chars: int) -> str:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        if not paragraphs:
            return text[:max_chars]
        if not query.strip():
            joined = "\n\n".join(paragraphs[:limit])
            return joined[:max_chars]
        ranked = sorted(paragraphs, key=lambda part: cls._score_text(part, query), reverse=True)
        selected = [part for part in ranked if cls._score_text(part, query) > 0][:limit]
        if not selected:
            selected = paragraphs[:limit]
        joined = "\n\n".join(selected)
        return joined[:max_chars]
