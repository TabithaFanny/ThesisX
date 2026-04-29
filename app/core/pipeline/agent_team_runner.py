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
            # Stage 2-6: Agent Team SequentialRunner (or Mock fallback)
            # -----------------------------------------------------------
            enhanced_topic = build_enhanced_topic(request, outline)

            if request.run_mode == "mock":
                # Mock mode: generate synthetic events without Agent Team
                async for paper_event in self._run_mock_stages(
                    enhanced_topic, request, session_dir, event_log_path,
                ):
                    if self._cancelled:
                        yield make_state_event("cancelled")
                        return
                    yield paper_event
            else:
                # Real mode: import and run Agent Team
                agent_team_root = ensure_agent_team_path(request.agent_team_path)
                _api = import_agent_team_api(agent_team_root)
                PipelineConfig = _api["PipelineConfig"]
                SequentialRunner = _api["SequentialRunner"]

                pipeline_config = PipelineConfig(
                    base_dir=session_dir,
                    topic=enhanced_topic,
                    journal=request.journal,
                    use_mock=False,
                    budget_cap_cny=request.budget_cap_cny,
                    api_key=request.api_key,
                    base_url=request.base_url,
                    model=request.model,
                )

                runner = SequentialRunner(pipeline_config)

                async for raw_event in runner.run():
                    if self._cancelled:
                        yield make_state_event("cancelled")
                        return

                    paper_event = _translate_event(raw_event, _api)

                    if paper_event.type == "cost":
                        cost_val = paper_event.payload.get("cost_cny", 0.0)
                        cumulative_cost += cost_val

                        if cumulative_cost >= request.budget_cap_cny > 0:
                            yield make_error_event(
                                f"预算已超限（已花费 ¥{cumulative_cost:.2f}，"
                                f"上限 ¥{request.budget_cap_cny:.2f}）。"
                                f"已产生的费用无法撤回。",
                                code="BUDGET_EXCEEDED",
                            )
                            return

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

    async def _run_mock_stages(
        self,
        enhanced_topic: str,
        request: PaperRequest,
        session_dir: Path | None,
        event_log_path: Path | None,
    ) -> AsyncIterator[PaperEvent]:
        """Mock fallback: generate synthetic events for stages 2-6."""
        mock_stages = [
            ("advisor", "advisor_running", "topic_done"),
            ("researcher", "researcher_running", "literature_done"),
            ("writer", "writer_running", "writing_done"),
            ("reviewer", "reviewer_running", "review_done"),
            ("polisher", "polisher_running", "polish_done"),
        ]
        for agent, running_stage, done_stage in mock_stages:
            yield make_state_event(running_stage, agent=agent)
            yield PaperEvent(
                type="message",
                agent=agent,
                stage=running_stage,
                message=f"[Mock] {agent} 阶段模拟完成",
            )
            yield make_state_event(done_stage, agent=agent)

        # Generate mock paper.md
        mock_paper = _generate_mock_paper(request.topic, enhanced_topic)
        if session_dir:
            paper_path = session_dir / "paper.md"
            paper_path.write_text(mock_paper, encoding="utf-8")


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


def _generate_mock_paper(topic: str, enhanced_topic: str) -> str:
    """Generate a realistic mock paper for demo purposes."""
    return f"""# {topic}研究

## 摘要

本研究旨在探讨{topic}的核心问题与优化路径。通过文献梳理与案例分析，本文构建了系统性的分析框架，并提出了针对性的政策建议。研究发现，{topic}在实践层面仍面临诸多挑战，需要多方协同推进。

## 关键词

{topic}；数字化转型；治理现代化；路径优化

## 一、引言

在当前社会背景下，{topic}已成为学术界和实务界共同关注的重要议题。现有研究从多个维度展开讨论，但在系统性和实证深度方面仍有提升空间。本文试图在已有研究基础上，进一步深化对该领域的认识。

## 二、文献综述

国内外学者围绕{topic}展开了丰富的研究。从理论层面看，主要形成了三种分析范式：制度分析视角、技术赋能视角和多元治理视角。本研究在综合上述视角的基础上，构建了更具整合性的分析框架。

## 三、研究设计

本研究采用混合研究方法，结合定量数据分析与定性案例研究。数据来源包括：政策文本、统计数据和深度访谈资料。研究选取了三个典型案例进行比较分析。

## 四、研究发现

研究发现：（1）制度环境对{topic}具有显著影响；（2）技术应用水平与治理效能呈正相关；（3）多元主体协同机制仍需完善。具体而言，数字化工具的引入使相关工作效率提升了约23.5%[数据待补充]。

## 五、讨论

上述发现表明，{topic}的优化路径需要兼顾制度建设与技术创新。与已有研究相比，本文的贡献在于提出了更具操作性的政策建议。

## 六、结论

本研究系统分析了{topic}的现状、问题与优化路径。未来研究可进一步扩大样本范围，并关注长期效果评估。

## 参考文献

[1] 张三. {topic}研究综述[J]. 中国社会科学, 2024(1): 45-62. [引用待核查]
[2] 李四, 王五. 数字化转型与治理现代化[M]. 北京: 社会科学文献出版社, 2023. [引用待核查]
[3] Smith, J. et al. Digital Governance and Public Service[J]. Public Administration Review, 2024, 84(2): 123-145. [引用待核查]
[4] 赵六. 基层治理创新的实践逻辑[J]. 管理世界, 2023(8): 78-91. [引用待核查]
"""
