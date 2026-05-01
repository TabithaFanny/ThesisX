"""Compatibility adapter for multiple external Agent Team contracts.

This layer keeps ThesisX stable while external academic_agent_team repos drift
between old TUI runner contracts and newer pipeline function contracts.
"""

from __future__ import annotations

import shutil
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .agent_team_bridge import ensure_agent_team_path, import_agent_team_api
from .events import PaperEvent, make_cost_event, make_error_event, make_state_event, make_token_event
from .models import PaperRequest

ContractType = Literal["tui_runner", "pipeline_v2", "pipeline_function", "unsupported"]


@dataclass(frozen=True)
class ContractCheckResult:
    """Result of probing an external Agent Team root."""

    contract_type: ContractType
    supported: bool
    reason: str = ""
    agent_team_root: Path | None = None
    error_code: str = ""


class AgentTeamCompatAdapter:
    """Detect and normalize supported external Agent Team contracts."""

    def __init__(self) -> None:
        self._cancelled = False
        self._external_runner: Any = None

    def cancel(self) -> None:
        """Request cancellation from the underlying external runner when possible."""
        self._cancelled = True
        runner = self._external_runner
        if runner and hasattr(runner, "cancel"):
            runner.cancel()

    @staticmethod
    def detect_contract(agent_team_root: Path) -> ContractCheckResult:
        """Detect which external contract shape is present under the root."""
        pkg_root = agent_team_root / "academic_agent_team"
        tui_runner = pkg_root / "tui" / "runner.py"
        tui_events = pkg_root / "tui" / "events.py"
        pipeline_v2 = pkg_root / "pipeline_v2.py"
        pipeline_real = pkg_root / "pipeline_real.py"
        pipeline_py = pkg_root / "pipeline.py"

        if tui_runner.is_file() and tui_events.is_file():
            return ContractCheckResult(
                contract_type="tui_runner",
                supported=True,
                agent_team_root=agent_team_root,
            )
        if pipeline_v2.is_file():
            return ContractCheckResult(
                contract_type="pipeline_v2",
                supported=True,
                reason="检测到 pipeline_v2 函数式契约，需要 CompatAdapter 后续补完事件流适配。",
                agent_team_root=agent_team_root,
            )
        if pipeline_real.is_file() or pipeline_py.is_file():
            return ContractCheckResult(
                contract_type="pipeline_function",
                supported=True,
                reason="检测到 pipeline.py / pipeline_real.py 函数式契约，需要 CompatAdapter 后续补完事件流适配。",
                agent_team_root=agent_team_root,
            )
        return ContractCheckResult(
            contract_type="unsupported",
            supported=False,
            reason="未检测到 academic_agent_team 的 tui_runner、pipeline_v2 或 pipeline_function 契约文件。",
            agent_team_root=agent_team_root,
            error_code="IMPORT_FAILED",
        )

    @classmethod
    def validate_agent_team_contract(cls, agent_team_root: str | Path | None) -> ContractCheckResult:
        """Validate the root path and identify the supported contract shape."""
        if agent_team_root is None:
            return ContractCheckResult(
                contract_type="unsupported",
                supported=False,
                reason="Agent Team 路径为空，请先选择路径。",
                error_code="AGENT_PATH_EMPTY",
            )

        raw_path = str(agent_team_root).strip()
        if not raw_path or raw_path == "未选择":
            return ContractCheckResult(
                contract_type="unsupported",
                supported=False,
                reason="Agent Team 路径为空，请先选择路径。",
                error_code="AGENT_PATH_EMPTY",
            )

        try:
            validated_root = ensure_agent_team_path(raw_path)
        except FileNotFoundError as exc:
            return ContractCheckResult(
                contract_type="unsupported",
                supported=False,
                reason=str(exc),
                error_code="AGENT_PATH_INVALID",
            )
        except NotADirectoryError as exc:
            return ContractCheckResult(
                contract_type="unsupported",
                supported=False,
                reason=str(exc),
                error_code="AGENT_PATH_INVALID",
            )

        return cls.detect_contract(validated_root)

    async def run_external_agent_team(
        self,
        request: PaperRequest,
        *,
        base_dir: Path,
    ) -> AsyncIterator[PaperEvent]:
        """Run the external Agent Team when the detected contract is supported.

        Contract routing:
        - tui_runner → real import + SequentialRunner (requires valid Agent Team path)
        - pipeline_v2 → dry-run event flow (no real import, no API calls)
        - pipeline_function → dry-run event flow (no real import, no API calls)
        - unsupported → error event
        """
        check = self.validate_agent_team_contract(request.agent_team_path)
        if not check.supported:
            yield self._make_contract_error_event(check)
            return

        if check.contract_type == "tui_runner":
            async for event in self._run_tui_runner(request, check.agent_team_root, base_dir):
                yield event
            return

        if check.contract_type == "pipeline_v2":
            async for event in self._run_pipeline_v2_dry(request, check.agent_team_root):
                yield event
            return

        if check.contract_type == "pipeline_function":
            async for event in self._run_pipeline_function_dry(request, check.agent_team_root):
                yield event
            return

        yield self._make_contract_error_event(
            ContractCheckResult(
                contract_type=check.contract_type,
                supported=False,
                reason=f"不支持的契约类型: {check.contract_type}",
                agent_team_root=check.agent_team_root,
                error_code="IMPORT_FAILED",
            )
        )

    async def _run_tui_runner(
        self,
        request: PaperRequest,
        agent_team_root: Path | None,
        base_dir: Path,
    ) -> AsyncIterator[PaperEvent]:
        """Execute old TUI runner contract and translate events."""
        if agent_team_root is None:
            yield self._make_contract_error_event(
                ContractCheckResult(
                    contract_type="unsupported",
                    supported=False,
                    reason="未提供有效的 Agent Team 根目录。",
                    error_code="AGENT_PATH_INVALID",
                )
            )
            return

        try:
            api = import_agent_team_api(agent_team_root)
        except ImportError as exc:
            yield self._make_contract_error_event(
                ContractCheckResult(
                    contract_type="unsupported",
                    supported=False,
                    reason=str(exc),
                    agent_team_root=agent_team_root,
                    error_code="IMPORT_FAILED",
                )
            )
            return

        PipelineConfig = api["PipelineConfig"]
        SequentialRunner = api["SequentialRunner"]
        pipeline_config = PipelineConfig(
            base_dir=base_dir,
            topic=request.topic,
            journal=request.journal,
            use_mock=False,
            budget_cap_cny=request.budget_cap_cny,
            api_key=request.api_key,
            base_url=request.base_url,
            model=request.model,
        )
        self._external_runner = SequentialRunner(pipeline_config)

        async for raw_event in self._external_runner.run():
            if self._cancelled:
                yield make_state_event("cancelled")
                return
            yield self.translate_tui_event(raw_event, api=api)

    # -----------------------------------------------------------------------
    # Dry-run adapters for pipeline_v2 / pipeline_function contracts
    # -----------------------------------------------------------------------

    async def _run_pipeline_v2_dry(
        self,
        request: PaperRequest,
        agent_team_root: Path | None,
    ) -> AsyncIterator[PaperEvent]:
        """Dry-run adapter for pipeline_v2 contract.

        Does NOT import or execute the real pipeline_v2 module.
        Emits a standard 6-phase event flow with mock paper content,
        mimicking what a pipeline_v2 run would produce.
        """
        yield PaperEvent(
            type="message",
            agent="system",
            stage="initialized",
            message=f"[dry-run] pipeline_v2 适配模式（不发真实 API）。"
                  f" 检测到外部 Agent Team 路径: {agent_team_root}",
            payload={
                "contract": "pipeline_v2",
                "mode": "dry-run",
                "agent_team_root": str(agent_team_root) if agent_team_root else "",
            },
        )

        # Phase 1: Advisor — topic discussion
        yield make_state_event("advisor_running", agent="advisor",
                               message="[dry-run] Phase 1 — Advisor 选题分析中...")
        yield PaperEvent(
            type="message", agent="advisor", stage="advisor_running",
            message=f"[dry-run] Advisor 分析课题: {request.topic[:80]}",
        )
        yield make_state_event("topic_done", agent="advisor")

        if self._cancelled:
            yield make_state_event("cancelled")
            return

        # Phase 2: Researcher — literature review
        yield make_state_event("researcher_running", agent="researcher",
                               message="[dry-run] Phase 2 — Researcher 文献调研中...")
        yield PaperEvent(
            type="message", agent="researcher", stage="researcher_running",
            message="[dry-run] Researcher 搜索相关文献（dry-run，不发起真实检索）",
        )
        yield make_state_event("literature_done", agent="researcher")

        if self._cancelled:
            yield make_state_event("cancelled")
            return

        # Phase 3: Writer — draft writing
        yield make_state_event("writer_running", agent="writer",
                               message="[dry-run] Phase 3 — Writer 撰写初稿中...")
        yield make_token_event(
            content="[dry-run] Writer token stream...", agent="writer",
        )
        yield PaperEvent(
            type="message", agent="writer", stage="writer_running",
            message="[dry-run] Writer 完成初稿撰写",
        )
        yield make_state_event("writing_done", agent="writer")

        if self._cancelled:
            yield make_state_event("cancelled")
            return

        # Phase 4: Reviewer — review feedback
        yield make_state_event("reviewer_running", agent="reviewer",
                               message="[dry-run] Phase 4 — Reviewer 审稿中...")
        yield PaperEvent(
            type="message", agent="reviewer", stage="reviewer_running",
            message="[dry-run] Reviewer 完成审稿：直接性 7/10, 节奏感 7/10, "
                    "信任度 8/10, 真实感 6/10, 密度 7/10 → 总分 35/50",
            payload={
                "scores": {
                    "directness": 7, "rhythm": 7, "trust": 8,
                    "authenticity": 6, "density": 7,
                },
                "total": 35,
            },
        )
        yield make_state_event("review_done", agent="reviewer")

        if self._cancelled:
            yield make_state_event("cancelled")
            return

        # Phase 5: Polisher — polish
        yield make_state_event("polisher_running", agent="polisher",
                               message="[dry-run] Phase 5 — Polisher 润色中...")
        yield PaperEvent(
            type="message", agent="polisher", stage="polisher_running",
            message="[dry-run] Polisher 完成去 AI 痕迹和语言润色",
            payload={"pattern_count": 3},
        )
        yield make_state_event("polish_done", agent="polisher")

        # Phase 6: Export — LaTeX / paper.md
        yield make_state_event("export_done", agent="export",
                               message="[dry-run] Phase 6 — Export 导出 paper.md")

        # Cost summary (dry-run = zero cost)
        yield make_cost_event("system", 0.0, 0.0, request.budget_cap_cny)

        # Completion
        yield PaperEvent(
            type="completion",
            payload={
                "session_id": request.session_id or "",
                "word_count": 3000,
                "total_cost_cny": 0.0,
                "output_path": "",
                "contract": "pipeline_v2",
                "mode": "dry-run",
            },
        )

    async def _run_pipeline_function_dry(
        self,
        request: PaperRequest,
        agent_team_root: Path | None,
    ) -> AsyncIterator[PaperEvent]:
        """Dry-run adapter for pipeline_function contract (pipeline.py / pipeline_real.py).

        Same semantics as _run_pipeline_v2_dry — emits standard 6-phase event flow
        without importing or executing the real module.
        """
        yield PaperEvent(
            type="message",
            agent="system",
            stage="initialized",
            message=f"[dry-run] pipeline_function 适配模式（不发真实 API）。"
                    f" 检测到外部 Agent Team 路径: {agent_team_root}",
            payload={
                "contract": "pipeline_function",
                "mode": "dry-run",
                "agent_team_root": str(agent_team_root) if agent_team_root else "",
            },
        )

        stages = [
            ("advisor", "advisor_running", "topic_done",
             "[dry-run] Advisor 完成选题分析"),
            ("researcher", "researcher_running", "literature_done",
             "[dry-run] Researcher 完成文献调研"),
            ("writer", "writer_running", "writing_done",
             "[dry-run] Writer 完成初稿撰写"),
            ("reviewer", "reviewer_running", "review_done",
             "[dry-run] Reviewer 完成审稿反馈"),
            ("polisher", "polisher_running", "polish_done",
             "[dry-run] Polisher 完成润色定稿"),
        ]

        for agent, running, done, msg in stages:
            if self._cancelled:
                yield make_state_event("cancelled")
                return
            yield make_state_event(running, agent=agent)
            yield PaperEvent(
                type="message", agent=agent, stage=running, message=msg,
            )
            yield make_state_event(done, agent=agent)

        yield make_state_event("export_done", agent="export")

        yield make_cost_event("system", 0.0, 0.0, request.budget_cap_cny)
        yield PaperEvent(
            type="completion",
            payload={
                "session_id": request.session_id or "",
                "word_count": 3000,
                "total_cost_cny": 0.0,
                "output_path": "",
                "contract": "pipeline_function",
                "mode": "dry-run",
            },
        )

    @staticmethod
    def translate_tui_event(raw_event: Any, *, api: dict[str, Any] | None = None) -> PaperEvent:
        """Translate external TUI contract events into ThesisX PaperEvent."""
        api = api or {}

        def _matches(expected_name: str) -> bool:
            expected_cls = api.get(expected_name)
            if expected_cls is not None and isinstance(raw_event, expected_cls):
                return True
            return raw_event.__class__.__name__ == expected_name

        if _matches("TokenStreamEvent"):
            return make_token_event(
                getattr(raw_event, "content", ""),
                agent=getattr(raw_event, "agent", ""),
                is_final=getattr(raw_event, "is_final", False),
            )

        if _matches("StateUpdateEvent"):
            to_stage = getattr(raw_event, "to_stage", "")
            from_stage = getattr(raw_event, "from_stage", "")
            to_stage_value = getattr(to_stage, "value", to_stage)
            from_stage_value = getattr(from_stage, "value", from_stage)
            return make_state_event(
                str(to_stage_value),
                agent=getattr(raw_event, "agent", ""),
                message=f"{from_stage_value} → {to_stage_value}",
            )

        if _matches("CostUpdateEvent"):
            return make_cost_event(
                getattr(raw_event, "agent", ""),
                getattr(raw_event, "cost_cny", 0.0),
                getattr(raw_event, "cumulative_cny", 0.0),
                getattr(raw_event, "budget_cap_cny", 0.0),
            )

        if _matches("AgentMessageEvent"):
            stage = getattr(raw_event, "stage", "")
            stage_value = getattr(stage, "value", stage)
            return PaperEvent(
                type="message",
                agent=getattr(raw_event, "agent", ""),
                stage=str(stage_value),
                message=(getattr(raw_event, "raw_content", "") or "")[:500],
                payload={
                    "token_count": getattr(raw_event, "token_count", 0),
                    "is_handoff": getattr(raw_event, "is_handoff", False),
                    "handoff_target": getattr(raw_event, "handoff_target", ""),
                },
            )

        if _matches("ErrorEvent"):
            stage = getattr(raw_event, "stage", "")
            stage_value = getattr(stage, "value", stage)
            return make_error_event(
                getattr(raw_event, "message", "未知错误"),
                agent=getattr(raw_event, "agent", ""),
                stage=str(stage_value),
                code="RUNNER_FAILED",
            )

        if _matches("CompletionEvent"):
            return PaperEvent(
                type="completion",
                payload={
                    "session_id": getattr(raw_event, "session_id", ""),
                    "word_count": getattr(raw_event, "word_count", 0),
                    "total_cost_cny": getattr(raw_event, "total_cost_cny", 0.0),
                    "output_path": getattr(raw_event, "output_path", ""),
                },
            )

        if _matches("HumanInterruptEvent"):
            return PaperEvent(
                type="message",
                agent="system",
                message=f"人工打断: {getattr(raw_event, 'command', '')}",
            )

        return PaperEvent(
            type="message",
            agent="system",
            message=str(raw_event)[:200],
        )

    @staticmethod
    def _make_contract_error_event(check: ContractCheckResult) -> PaperEvent:
        return PaperEvent(
            type="error",
            message=check.reason,
            payload={
                "code": check.error_code or "IMPORT_FAILED",
                "contract_type": check.contract_type,
                "agent_team_root": str(check.agent_team_root) if check.agent_team_root else "",
            },
        )


def copy_external_paper_if_needed(external_output_path: str, session_dir: Path) -> bool:
    """Copy external paper.md back into ThesisX session_dir when available."""
    if not external_output_path:
        return False
    paper_path = Path(external_output_path) / "paper.md"
    if not paper_path.exists():
        return False
    targets = [session_dir / "output" / "paper.md", session_dir / "paper.md"]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paper_path, target)
    return True
