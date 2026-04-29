"""AgentTeamRunner — V1 adapter: ArchitectNode + Agent Team SequentialRunner.

Translates Agent Team events into unified PaperEvent objects.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent_team_bridge import (
    append_event_jsonl,
    ensure_agent_team_path,
    import_agent_team_api,
    read_paper_markdown,
    resolve_session_dir,
    sync_api_keys,
    write_json,
)
from .events import (
    PaperEvent,
    make_artifact_event,
    make_completion_event,
    make_cost_event,
    make_error_event,
    make_state_event,
    make_token_event,
)
from .models import PaperRequest
from .nodes.architect_node import ArchitectNode, build_enhanced_topic
from .quality_checks import build_quality_report
from .runner import PaperPipelineRunner

logger = logging.getLogger(__name__)


class AgentTeamRunner:
    """V1 pipeline runner: ArchitectNode (self-built) + Agent Team SequentialRunner.

    Implements PaperPipelineRunner protocol.
    """

    def __init__(self) -> None:
        self._cancelled = False
        self._task: asyncio.Task[None] | None = None
        self._architect = ArchitectNode()

    async def run(self, request: PaperRequest) -> AsyncIterator[PaperEvent]:
        """Execute the full pipeline, yielding PaperEvent objects."""
        self._cancelled = False
        session_id = request.session_id or uuid.uuid4().hex[:12]
        session_dir: Path | None = None
        event_log_path: Path | None = None
        cumulative_cost = 0.0
        _api: dict[str, Any] = {}

        try:
            # Resolve session directory
            base_dir = request.base_dir or Path.home() / ".wenbiao"
            session_dir = resolve_session_dir(base_dir, session_id)
            event_log_path = session_dir / "events.jsonl"

            # Save request
            write_json(session_dir / "request.json", {
                "topic": request.topic,
                "journal": request.journal,
                "run_mode": request.run_mode,
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
            })

            # Initialized
            yield make_state_event("initialized", message=f"Session {session_id}")

            # -----------------------------------------------------------
            # Stage 1: ArchitectNode
            # -----------------------------------------------------------
            yield make_state_event("architect_running", agent="architect")
            try:
                outline = await self._architect.run(request)
            except Exception as e:
                yield make_error_event(
                    f"大纲规划失败: {e}",
                    agent="architect",
                    stage="architect_running",
                    code="ARCHITECT_FAILED",
                )
                return

            # Save outline
            outline_path = session_dir / "outline.json"
            write_json(outline_path, asdict(outline))
            yield make_artifact_event("architect", str(outline_path), "architect_done")
            yield make_state_event("architect_done", agent="architect")

            if self._cancelled:
                yield make_state_event("cancelled")
                return

            # -----------------------------------------------------------
            # Stage 2-6: Agent Team SequentialRunner
            # -----------------------------------------------------------
            enhanced_topic = build_enhanced_topic(request, outline)

            # Import Agent Team API
            agent_team_root = ensure_agent_team_path(request.agent_team_path)
            _api = import_agent_team_api(agent_team_root)
            PipelineConfig = _api["PipelineConfig"]
            SequentialRunner = _api["SequentialRunner"]

            # Build config
            pipeline_config = PipelineConfig(
                base_dir=session_dir,
                topic=enhanced_topic,
                journal=request.journal,
                use_mock=(request.run_mode == "mock"),
                budget_cap_cny=request.budget_cap_cny,
                api_key=request.api_key,
                base_url=request.base_url,
                model=request.model,
            )

            runner = SequentialRunner(pipeline_config)

            # Consume Agent Team event stream
            async for raw_event in runner.run():
                if self._cancelled:
                    yield make_state_event("cancelled")
                    return

                paper_event = _translate_event(raw_event, _api)

                # Track cumulative cost
                if paper_event.type == "cost":
                    cost_val = paper_event.payload.get("cost_cny", 0.0)
                    cumulative_cost += cost_val

                    # Budget check
                    if cumulative_cost >= request.budget_cap_cny > 0:
                        yield make_error_event(
                            f"预算已超限（已花费 ¥{cumulative_cost:.2f}，"
                            f"上限 ¥{request.budget_cap_cny:.2f}）。"
                            f"已产生的费用无法撤回。",
                            code="BUDGET_EXCEEDED",
                        )
                        return

                # Append to event log
                if event_log_path:
                    append_event_jsonl(event_log_path, paper_event.to_dict())

                yield paper_event

            if self._cancelled:
                yield make_state_event("cancelled")
                return

            # -----------------------------------------------------------
            # Read paper.md
            # -----------------------------------------------------------
            try:
                paper_md = read_paper_markdown(session_dir)
            except FileNotFoundError:
                yield make_error_event(
                    "paper.md 未生成，Agent Team 流程可能未完成。",
                    code="PAPER_NOT_FOUND",
                )
                return

            # -----------------------------------------------------------
            # De-AI humanization pass
            # -----------------------------------------------------------
            from .nodes.deai_humanizer import DeAIHumanizer

            yield make_state_event("polisher_running", agent="deai")
            deai = DeAIHumanizer()
            try:
                deai_result = await deai.run(paper_md, request)
                if not deai_result.passed:
                    paper_md = deai_result.humanized_text
                    # Save humanized version
                    (session_dir / "paper.md").write_text(paper_md, encoding="utf-8")
                    yield make_artifact_event(
                        "deai",
                        str(session_dir / "paper.md"),
                        "polish_done",
                    )
                    yield PaperEvent(
                        type="message",
                        agent="deai",
                        message=f"去 AI 痕迹完成：检测到 {deai_result.pattern_count} 处模式",
                        payload={"pattern_count": deai_result.pattern_count},
                    )
                else:
                    yield PaperEvent(
                        type="message",
                        agent="deai",
                        message="文本已通过去 AI 检测，无需修改",
                    )
            except Exception as e:
                logger.warning("De-AI 处理失败（非致命）: %s", e)
                yield PaperEvent(
                    type="message",
                    agent="deai",
                    message=f"去 AI 处理跳过: {e}",
                )
            yield make_state_event("polish_done", agent="deai")

            # Quality check
            quality = build_quality_report(paper_md)

            # Save metadata
            write_json(session_dir / "metadata.json", {
                "session_id": session_id,
                "topic": request.topic,
                "journal": request.journal,
                "run_mode": request.run_mode,
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "total_cost_cny": cumulative_cost,
                "word_count": quality.word_count,
                "status": "completed",
            })

            yield make_completion_event(
                markdown=paper_md,
                word_count=quality.word_count,
                total_cost_cny=cumulative_cost,
                session_id=session_id,
            )

        except asyncio.CancelledError:
            yield make_state_event("cancelled")
        except Exception as e:
            logger.exception("AgentTeamRunner 异常")
            yield make_error_event(str(e), code="RUNNER_FAILED")

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True
        if self._task and not self._task.done():
            self._task.cancel()


# ---------------------------------------------------------------------------
# Event translator: Agent Team event → PaperEvent
# ---------------------------------------------------------------------------


def _translate_event(raw: Any, api: dict[str, Any]) -> PaperEvent:
    """Translate an Agent Team PipelineEvent into a unified PaperEvent.

    Handles all 7 Agent Team event types. Unknown events become "message" type.
    Field access is defensive — missing attrs don't crash.
    """
    TokenStreamEvent = api.get("TokenStreamEvent")
    StateUpdateEvent = api.get("StateUpdateEvent")
    CostUpdateEvent = api.get("CostUpdateEvent")
    AgentMessageEvent = api.get("AgentMessageEvent")
    ErrorEvent = api.get("ErrorEvent")
    CompletionEvent = api.get("CompletionEvent")
    HumanInterruptEvent = api.get("HumanInterruptEvent")

    # TokenStreamEvent
    if TokenStreamEvent and isinstance(raw, TokenStreamEvent):
        content = getattr(raw, "content", "")
        is_final = getattr(raw, "is_final", False)
        agent = getattr(raw, "agent", "")
        return make_token_event(content, agent=agent, is_final=is_final)

    # StateUpdateEvent
    if StateUpdateEvent and isinstance(raw, StateUpdateEvent):
        to_stage = getattr(raw, "to_stage", "")
        agent = getattr(raw, "agent", "")
        from_stage = getattr(raw, "from_stage", "")
        return make_state_event(
            to_stage,
            agent=agent,
            message=f"{from_stage} → {to_stage}",
        )

    # CostUpdateEvent
    if CostUpdateEvent and isinstance(raw, CostUpdateEvent):
        agent = getattr(raw, "agent", "")
        cost_cny = getattr(raw, "cost_cny", 0.0)
        cumulative_cny = getattr(raw, "cumulative_cny", 0.0)
        budget_cap = getattr(raw, "budget_cap_cny", 0.0)
        return make_cost_event(agent, cost_cny, cumulative_cny, budget_cap)

    # AgentMessageEvent
    if AgentMessageEvent and isinstance(raw, AgentMessageEvent):
        agent = getattr(raw, "agent", "")
        stage = getattr(raw, "stage", "")
        raw_content = getattr(raw, "raw_content", "")
        return PaperEvent(
            type="message",
            agent=agent,
            stage=stage,
            message=raw_content[:500] if raw_content else "",
            payload={
                "token_count": getattr(raw, "token_count", 0),
                "is_handoff": getattr(raw, "is_handoff", False),
            },
        )

    # ErrorEvent
    if ErrorEvent and isinstance(raw, ErrorEvent):
        agent = getattr(raw, "agent", "")
        stage = getattr(raw, "stage", "")
        message = getattr(raw, "message", "未知错误")
        return make_error_event(message, agent=agent, stage=stage)

    # CompletionEvent
    if CompletionEvent and isinstance(raw, CompletionEvent):
        return PaperEvent(
            type="completion",
            payload={
                "session_id": getattr(raw, "session_id", ""),
                "word_count": getattr(raw, "word_count", 0),
                "total_cost_cny": getattr(raw, "total_cost_cny", 0.0),
                "output_path": getattr(raw, "output_path", ""),
            },
        )

    # HumanInterruptEvent
    if HumanInterruptEvent and isinstance(raw, HumanInterruptEvent):
        return PaperEvent(
            type="message",
            agent="system",
            message=f"人工打断: {getattr(raw, 'command', '')}",
        )

    # Unknown event type — safe fallback
    return PaperEvent(
        type="message",
        agent="system",
        message=str(raw)[:200],
    )
