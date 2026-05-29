"""Typed artifact builder for ThesisX agent tasks."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.agent.context_assembler import AgentContextAssembler
from app.core.editor.rewrite import RewriteService
from app.core.project.service import ProjectService
from app.core.quality.service import QualityService


@dataclass
class AgentArtifactStep:
    id: str
    title: str
    rationale: str
    target_surface: str
    suggested_mode: str = ""
    priority: str = "medium"


@dataclass
class AgentArtifactAction:
    id: str
    label: str
    target_surface: str
    intent: str = ""
    suggested_mode: str = ""
    priority: str = "medium"


@dataclass
class AgentArtifactSection:
    id: str
    title: str
    content: str
    kind: str = "text"


@dataclass
class AgentArtifact:
    task_type: str
    artifact_type: str
    summary: str
    markdown: str = ""
    sections: list[AgentArtifactSection] = field(default_factory=list)
    steps: list[AgentArtifactStep] = field(default_factory=list)
    actions: list[AgentArtifactAction] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    assembled_context: str = ""
    output_contract: str = ""
    sources: list[str] = field(default_factory=list)


class AgentArtifactBuilder:
    """Build structured artifacts instead of returning only free-form text."""

    def build(
        self,
        *,
        task_type: str,
        project_id: str = "",
        session_id: str = "",
        selected_text: str = "",
        mode: str = "polish",
        query: str = "",
        extra_context: str = "",
    ) -> AgentArtifact:
        bundle = AgentContextAssembler().assemble(
            task_type=task_type,
            project_id=project_id,
            session_id=session_id,
            query=query,
        )
        full_context = bundle.assembled_context
        if extra_context.strip():
            full_context = f"{full_context}\n\n# Page-Specific Context\n{extra_context.strip()}"

        if task_type == "quality":
            artifact = self._build_quality_artifact(project_id=project_id, query=query)
        elif task_type == "writing":
            artifact = self._build_writing_artifact(
                selected_text=selected_text,
                mode=mode,
                project_id=project_id,
            )
        elif task_type == "theory":
            artifact = self._build_theory_artifact(
                selected_text=selected_text,
                project_id=project_id,
                query=query,
                extra_context=extra_context,
            )
        elif task_type == "evidence":
            artifact = self._build_evidence_artifact(
                selected_text=selected_text,
                project_id=project_id,
                query=query,
            )
        elif task_type == "knowledge":
            artifact = self._build_knowledge_artifact(
                selected_text=selected_text,
                mode=mode,
                project_id=project_id,
                query=query,
            )
        else:
            rewritten = RewriteService().rewrite(selected_text, mode, full_context)
            artifact = AgentArtifact(
                task_type=task_type,
                artifact_type="rewrite",
                summary="Structured rewrite artifact",
                markdown=rewritten.rewritten,
                sections=[
                    AgentArtifactSection(
                        id="rewrite-body",
                        title="Generated Content",
                        content=rewritten.rewritten,
                        kind="markdown",
                    )
                ],
                steps=[],
                actions=[],
            )

        artifact.assembled_context = full_context
        artifact.output_contract = bundle.output_contract
        artifact.sources = bundle.sources
        return artifact

    def _build_quality_artifact(self, *, project_id: str, query: str) -> AgentArtifact:
        dashboard = QualityService(project_id).get_dashboard()
        project = ProjectService().get_project(project_id) if project_id else None
        summary = (
            f"{project.name if project else '当前项目'} 当前总分 {dashboard.overall_score}，"
            f"写作进度 {dashboard.writing_progress}%，Claim 覆盖 {dashboard.claim_coverage}%，"
            f"证据完整性 {dashboard.evidence_integrity}%。"
        )
        steps: list[AgentArtifactStep] = []

        if dashboard.writing_progress < 60:
            steps.append(
                AgentArtifactStep(
                    id="writing-progress",
                    title="先补主稿内容",
                    rationale="写作进度偏低，会拖累后续证据和质量闭环。",
                    target_surface="writing",
                    suggested_mode="expand",
                    priority="high",
                )
            )
        if dashboard.claim_coverage < 80:
            steps.append(
                AgentArtifactStep(
                    id="claim-coverage",
                    title="补 Claim 对应证据",
                    rationale="Claim 覆盖率不足，关键论断还没有被证据充分支撑。",
                    target_surface="evidence",
                    suggested_mode="add_evidence",
                    priority="high",
                )
            )
        if dashboard.evidence_integrity < 70:
            steps.append(
                AgentArtifactStep(
                    id="evidence-integrity",
                    title="提高证据可用性",
                    rationale="证据完整性不足，现有材料还不适合直接进入写作。",
                    target_surface="knowledge",
                    suggested_mode="polish",
                    priority="medium",
                )
            )
        if dashboard.citation_completeness < 80 or dashboard.total_citations == 0:
            steps.append(
                AgentArtifactStep(
                    id="citations",
                    title="补引文与来源信息",
                    rationale="引文不完整会削弱最终可提交性与溯源可信度。",
                    target_surface="literature",
                    suggested_mode="",
                    priority="medium",
                )
            )
        if not steps:
            steps.append(
                AgentArtifactStep(
                    id="maintain",
                    title="继续精修与整合",
                    rationale="当前关键质量指标已达到可继续写作的水平。",
                    target_surface="writing",
                    suggested_mode="polish",
                    priority="low",
                )
            )

        markdown_lines = ["# 修订计划", "", summary, ""]
        for index, step in enumerate(steps, start=1):
            markdown_lines.append(f"{index}. {step.title}")
            markdown_lines.append(f"   - 原因: {step.rationale}")
            markdown_lines.append(f"   - 建议页面: {step.target_surface}")
            if step.suggested_mode:
                markdown_lines.append(f"   - 建议模式: {step.suggested_mode}")
        if dashboard.suggestions:
            markdown_lines.extend(["", "## 现有质量信号"])
            markdown_lines.extend(f"- {item}" for item in dashboard.suggestions)

        return AgentArtifact(
            task_type="quality",
            artifact_type="revision_plan",
            summary=summary,
            markdown="\n".join(markdown_lines).strip(),
            sections=[
                AgentArtifactSection(
                    id="quality-summary",
                    title="Revision Summary",
                    content=summary,
                ),
                AgentArtifactSection(
                    id="quality-signals",
                    title="Quality Signals",
                    content="\n".join(dashboard.suggestions) if dashboard.suggestions else "No explicit quality suggestions.",
                ),
            ],
            steps=steps,
            actions=[
                AgentArtifactAction(
                    id=step.id,
                    label=step.title,
                    target_surface=step.target_surface,
                    intent=step.rationale,
                    suggested_mode=step.suggested_mode,
                    priority=step.priority,
                )
                for step in steps
            ],
            metadata={"project_id": project_id, "query": query},
        )

    def _build_writing_artifact(self, *, selected_text: str, mode: str, project_id: str) -> AgentArtifact:
        rewritten = RewriteService().rewrite(selected_text, mode, f"project_id={project_id}")
        steps = [
            AgentArtifactStep(
                id="review-draft",
                title="检查 AI 草稿是否贴合当前章节目的",
                rationale="写作任务需要确认扩写或补强没有偏离当前段落目标。",
                target_surface="writing",
                suggested_mode=mode,
                priority="high",
            ),
            AgentArtifactStep(
                id="bind-support",
                title="为新增论点绑定证据或理论",
                rationale="新增内容应尽快补上可追溯支持，避免后续质量面板再次回落。",
                target_surface="evidence",
                suggested_mode="add_evidence" if mode != "add_theory" else "add_theory",
                priority="medium",
            ),
        ]
        return AgentArtifact(
            task_type="writing",
            artifact_type="draft",
            summary="AI 已生成可直接替换或继续编辑的写作草稿。",
            markdown=rewritten.rewritten,
            sections=[
                AgentArtifactSection(
                    id="writing-summary",
                    title="Draft Intent",
                    content=f"Mode: {mode}",
                ),
                AgentArtifactSection(
                    id="writing-body",
                    title="Generated Draft",
                    content=rewritten.rewritten,
                    kind="markdown",
                ),
            ],
            steps=steps,
            actions=[
                AgentArtifactAction(
                    id="replace-draft",
                    label="替换当前草稿",
                    target_surface="writing",
                    intent="Use the generated draft as the new working version.",
                    suggested_mode=mode,
                    priority="high",
                ),
                AgentArtifactAction(
                    id="bind-support",
                    label="补证据或理论",
                    target_surface="evidence" if mode != "add_theory" else "theory",
                    intent="Ground the generated draft with traceable support.",
                    suggested_mode="add_evidence" if mode != "add_theory" else "add_theory",
                    priority="medium",
                ),
            ],
            metadata={"project_id": project_id, "mode": mode},
        )

    def _build_theory_artifact(
        self,
        *,
        selected_text: str,
        project_id: str,
        query: str,
        extra_context: str,
    ) -> AgentArtifact:
        rewritten = RewriteService().rewrite(selected_text, "add_theory", extra_context)
        steps = [
            AgentArtifactStep(
                id="theory-fit",
                title="确认理论与研究问题的贴合度",
                rationale="理论稿首先要解释为什么这个理论适用于当前研究问题。",
                target_surface="theory",
                suggested_mode="add_theory",
                priority="high",
            ),
            AgentArtifactStep(
                id="theory-into-writing",
                title="把理论段落接入主稿",
                rationale="理论分析只有进入写作稿，才能影响后续质量与证据闭环。",
                target_surface="writing",
                suggested_mode="add_theory",
                priority="medium",
            ),
        ]
        return AgentArtifact(
            task_type="theory",
            artifact_type="theory_note",
            summary="AI 已生成理论分析稿，适合继续加工为 theory note 或接入主稿。",
            markdown=rewritten.rewritten,
            sections=[
                AgentArtifactSection(
                    id="theory-query",
                    title="Theory Focus",
                    content=query or selected_text,
                ),
                AgentArtifactSection(
                    id="theory-body",
                    title="Theory Draft",
                    content=rewritten.rewritten,
                    kind="markdown",
                ),
            ],
            steps=steps,
            actions=[
                AgentArtifactAction(
                    id="store-theory",
                    label="沉淀为 theory note",
                    target_surface="knowledge",
                    intent="Preserve the draft as a reusable theory asset.",
                    suggested_mode="add_theory",
                    priority="high",
                ),
                AgentArtifactAction(
                    id="apply-theory",
                    label="接入主稿",
                    target_surface="writing",
                    intent="Move the theory explanation into the working draft.",
                    suggested_mode="add_theory",
                    priority="medium",
                ),
            ],
            metadata={"project_id": project_id, "query": query},
        )

    def _build_evidence_artifact(self, *, selected_text: str, project_id: str, query: str) -> AgentArtifact:
        rewritten = RewriteService().rewrite(selected_text, "add_evidence", f"project_id={project_id}")
        steps = [
            AgentArtifactStep(
                id="evidence-source",
                title="定位具体证据来源",
                rationale="草稿指出的是支持方向，下一步应绑定到实际 evidence 或 literature 条目。",
                target_surface="evidence",
                suggested_mode="add_evidence",
                priority="high",
            ),
            AgentArtifactStep(
                id="evidence-bind",
                title="把证据摘录绑定到 Claim",
                rationale="只有绑定完成，质量面板里的 Claim 覆盖率才会真正提升。",
                target_surface="evidence",
                suggested_mode="",
                priority="high",
            ),
        ]
        return AgentArtifact(
            task_type="evidence",
            artifact_type="evidence_note",
            summary="AI 已生成证据补强稿，适合作为 Claim 支撑工作的起点。",
            markdown=rewritten.rewritten,
            sections=[
                AgentArtifactSection(
                    id="evidence-claim",
                    title="Target Claim",
                    content=query or selected_text,
                ),
                AgentArtifactSection(
                    id="evidence-body",
                    title="Evidence Draft",
                    content=rewritten.rewritten,
                    kind="markdown",
                ),
            ],
            steps=steps,
            actions=[
                AgentArtifactAction(
                    id="bind-evidence",
                    label="绑定到 Claim",
                    target_surface="evidence",
                    intent="Link the generated support into the selected claim workflow.",
                    suggested_mode="add_evidence",
                    priority="high",
                ),
                AgentArtifactAction(
                    id="promote-knowledge",
                    label="沉淀为 evidence note",
                    target_surface="knowledge",
                    intent="Store the draft as a reusable evidence-oriented knowledge item.",
                    suggested_mode="add_evidence",
                    priority="medium",
                ),
            ],
            metadata={"project_id": project_id, "query": query},
        )

    def _build_knowledge_artifact(
        self,
        *,
        selected_text: str,
        mode: str,
        project_id: str,
        query: str,
    ) -> AgentArtifact:
        rewritten = RewriteService().rewrite(selected_text, mode, f"project_id={project_id}")
        target_surface = "knowledge"
        artifact_type = "knowledge_note"
        if mode == "add_theory":
            artifact_type = "theory_note"
            target_surface = "theory"
        elif mode == "add_evidence":
            artifact_type = "evidence_note"
            target_surface = "evidence"

        steps = [
            AgentArtifactStep(
                id="store-artifact",
                title="把结果存成知识条目",
                rationale="生成结果应尽快沉淀为可检索对象，而不是只停留在页面草稿里。",
                target_surface="knowledge",
                suggested_mode=mode,
                priority="high",
            ),
            AgentArtifactStep(
                id="promote-artifact",
                title="必要时提升到目标工作面",
                rationale="如果内容已经偏 theory 或 evidence，应尽早进入对应工作流继续加工。",
                target_surface=target_surface,
                suggested_mode=mode,
                priority="medium",
            ),
        ]
        return AgentArtifact(
            task_type="knowledge",
            artifact_type=artifact_type,
            summary="AI 已生成可入库的知识草稿。",
            markdown=rewritten.rewritten,
            sections=[
                AgentArtifactSection(
                    id="knowledge-source",
                    title="Source Focus",
                    content=query or selected_text[:300],
                ),
                AgentArtifactSection(
                    id="knowledge-body",
                    title="Knowledge Draft",
                    content=rewritten.rewritten,
                    kind="markdown",
                ),
            ],
            steps=steps,
            actions=[
                AgentArtifactAction(
                    id="store-knowledge",
                    label="载入并保存",
                    target_surface="knowledge",
                    intent="Load the generated draft into the knowledge form and save it.",
                    suggested_mode=mode,
                    priority="high",
                ),
                AgentArtifactAction(
                    id="promote-surface",
                    label="进入目标工作面",
                    target_surface=target_surface,
                    intent="Continue the artifact in its natural next workflow.",
                    suggested_mode=mode,
                    priority="medium",
                ),
            ],
            metadata={"project_id": project_id, "mode": mode, "query": query},
        )
