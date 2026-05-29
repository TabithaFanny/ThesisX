"""Local session/run storage for ThesisX pipeline runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .events import PaperEvent
from .models import PaperRequest


@dataclass(frozen=True)
class SessionPaths:
    """Canonical paths for one local ThesisX runtime session."""

    base_dir: Path
    session_id: str
    run_dir: Path
    legacy_dir: Path
    context_dir: Path
    logs_dir: Path
    output_dir: Path
    artifacts_dir: Path
    imported_files_dir: Path
    generated_dir: Path
    request_json: Path
    metadata_json: Path
    events_jsonl: Path
    messages_jsonl: Path
    errors_log: Path
    outline_json: Path
    paper_md: Path
    quality_report_json: Path
    paper_request_md: Path
    runtime_instructions_md: Path
    user_constraints_md: Path
    selected_skills_md: Path
    knowledge_context_md: Path
    theory_context_md: Path
    rag_context_md: Path


class SessionStore:
    """Manage append-only logs and structured local run artifacts."""

    def __init__(self, base_dir: Path, session_id: str) -> None:
        self.base_dir = Path(base_dir).expanduser()
        self.session_id = session_id
        self.paths = self._build_paths()

    @classmethod
    def create_session(cls, session_id: str, request: PaperRequest) -> "SessionStore":
        base_dir = request.base_dir or Path.home() / ".wenbiao"
        store = cls(base_dir=base_dir, session_id=session_id)
        store._ensure_layout()
        return store

    def write_request(self, request: PaperRequest) -> None:
        payload = self._jsonable_request(request)
        self._write_json(self.paths.request_json, payload)
        self._write_json(self.paths.legacy_dir / "request.json", payload)

    def write_context_files(self, request: PaperRequest) -> None:
        self._write_text(
            self.paths.paper_request_md,
            "\n".join([
                "# Paper Request",
                "",
                f"- Session ID: `{self.session_id}`",
                f"- Topic: {request.topic}",
                f"- Journal: {request.journal}",
                f"- Generation Type: {request.generation_type}",
            ]),
        )
        self._write_text(
            self.paths.runtime_instructions_md,
            "\n".join([
                "# Runtime Instructions",
                "",
                "- 当前运行目录采用 ThesisX 本地 run 契约。",
                "- 本轮目标是论文初稿生成与静态质量检查。",
                "- 本地历史需保留 request / context / logs / output / artifacts。",
                "- 当前阶段不得把 Mock 页面、Mock 链路伪装成真实外部 Agent Team 已接通。",
            ]),
        )
        self._write_text(
            self.paths.user_constraints_md,
            "\n".join([
                "# User Constraints",
                "",
                f"- Run Mode: `{request.run_mode}`",
                f"- Runner Kind: `{request.runner_kind}`",
                f"- Auto Polish: `{request.auto_polish}`",
                f"- Budget Cap (CNY): `{request.budget_cap_cny}`",
                f"- Agent Team Path: `{request.agent_team_path or '未提供'}`",
                f"- Model: `{request.model or '未指定'}`",
                "",
                "- 当前阶段不接真实 API，不接 CLI，不接 Skill Registry，不接 RAG / Zotero / Git。",
            ]),
        )
        # Selected skills — from enabled skill store (Vision 3.8)
        try:
            from app.core.skills.loader import SkillLoader
            from app.core.skills.enabled_store import EnabledSkillsStore
            loader = SkillLoader()
            all_skills = loader.load_local_skills()
            enabled_set = EnabledSkillsStore().load()
            enabled_skills = [s for s in all_skills if s.name in enabled_set]
            if enabled_skills:
                self._write_text(self.paths.selected_skills_md, loader.render_selected_skills_md(enabled_skills))
            else:
                # Write placeholder when no skills enabled
                self._write_text(
                    self.paths.selected_skills_md,
                    "\n".join([
                        "# Selected Skills",
                        "",
                        "（未启用任何本地技能。请在写作技能库页面启用。）",
                    ]),
                )
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to load skills for session context", exc_info=True)
            self._write_text(
                self.paths.selected_skills_md,
                "\n".join([
                    "# Selected Skills",
                    "",
                    "（技能库加载失败，请联系开发者。）",
                ]),
            )

        # knowledge_context.md — populated from pre-built context file or Phase B default
        if request.knowledge_context_path:
            kp = Path(request.knowledge_context_path)
            if kp.exists():
                self._write_text(self.paths.knowledge_context_md, kp.read_text(encoding="utf-8"))
            else:
                self._write_text(
                    self.paths.knowledge_context_md,
                    "# Knowledge Context\n\n- Knowledge context file not found.\n",
                )
        else:
            self._write_text(
                self.paths.knowledge_context_md,
                "# Knowledge Context\n\n"
                "- 当前未连接知识库。\n"
                "- 用户未选择本次生成使用的资料范围。\n"
                "- Phase B（知识库）接入后将填充本文件。\n",
            )

        # theory_context.md — populated from pre-built context file or Phase B default
        if request.theory_context_path:
            tp = Path(request.theory_context_path)
            if tp.exists():
                self._write_text(self.paths.theory_context_md, tp.read_text(encoding="utf-8"))
            else:
                self._write_text(
                    self.paths.theory_context_md,
                    "# Theory Context\n\n- Theory context file not found.\n",
                )
        else:
            self._write_text(
                self.paths.theory_context_md,
                "# Theory Context\n\n"
                "- 当前未连接理论匹配系统。\n"
                "- 用户未选择本次生成使用的理论框架。\n"
                "- Phase B（理论匹配）接入后将填充本文件。\n",
            )

        # rag_context.md — populated from pre-built RAG context or placeholder
        rag_path = Path.home() / ".wenbiao" / "runs" / "_context" / "rag_context.md"
        if rag_path.exists():
            try:
                self._write_text(
                    self.paths.rag_context_md,
                    rag_path.read_text(encoding="utf-8"),
                )
            except Exception:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Failed to read RAG context file", exc_info=True)
                self._write_text(
                    self.paths.rag_context_md,
                    "# RAG Context\n\n- RAG context file not readable.\n",
                )
        else:
            self._write_text(
                self.paths.rag_context_md,
                "# RAG Context\n\n"
                "- 当前未注入 RAG 上下文。\n"
                "- 请在 RAG 检索页面搜索并注入上下文。\n",
            )

    def append_event(self, event: PaperEvent | dict[str, Any]) -> None:
        payload = event.to_dict() if isinstance(event, PaperEvent) else dict(event)
        self._append_jsonl(self.paths.events_jsonl, payload)
        if payload.get("type") == "error":
            stamp = payload.get("timestamp", datetime.now().isoformat())
            message = payload.get("message", "")
            code = payload.get("payload", {}).get("code", "")
            self._append_text(self.paths.errors_log, f"{stamp} [{code}] {message}\n")

    def append_message(self, message: dict[str, Any]) -> None:
        entry = dict(message)
        entry.setdefault("timestamp", datetime.now().isoformat())
        self._append_jsonl(self.paths.messages_jsonl, entry)

    def write_output_file(self, name: str, content: str | dict[str, Any] | list[Any]) -> Path:
        target = self.paths.output_dir / name
        legacy_target = self.paths.legacy_dir / name
        if name.endswith(".json"):
            self._write_json(target, content)
            if name in {"outline.json", "quality_report.json"}:
                self._write_json(legacy_target, content)
        else:
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
            self._write_text(target, text)
            if name == "paper.md":
                self._write_text(legacy_target, text)
        return target

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        self._write_json(self.paths.metadata_json, metadata)
        self._write_json(self.paths.legacy_dir / "metadata.json", metadata)

    def ensure_artifacts_dirs(self) -> None:
        self.paths.imported_files_dir.mkdir(parents=True, exist_ok=True)
        self.paths.generated_dir.mkdir(parents=True, exist_ok=True)

    def output_files_map(self) -> dict[str, str]:
        files: dict[str, str] = {}
        if self.paths.outline_json.exists():
            files["outline_json"] = str(self.paths.outline_json)
        if self.paths.paper_md.exists():
            files["paper_md"] = str(self.paths.paper_md)
        if self.paths.quality_report_json.exists():
            files["quality_report_json"] = str(self.paths.quality_report_json)
        return files

    def event_count(self) -> int:
        return self._count_jsonl_lines(self.paths.events_jsonl)

    def message_count(self) -> int:
        return self._count_jsonl_lines(self.paths.messages_jsonl)

    def has_errors(self) -> bool:
        return self.paths.errors_log.exists() and self.paths.errors_log.stat().st_size > 0

    def build_metadata(
        self,
        *,
        request: PaperRequest,
        status: str,
        created_at: str,
        updated_at: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "session_id": self.session_id,
            "run_dir": str(self.paths.run_dir),
            "legacy_output_dir": str(self.paths.legacy_dir),
            "status": status,
            "created_at": created_at,
            "updated_at": updated_at,
            "run_mode": request.run_mode,
            "topic": request.topic,
            "journal": request.journal,
            "output_files": self.output_files_map(),
            "event_count": self.event_count(),
            "message_count": self.message_count(),
            "has_errors": self.has_errors(),
        }
        if extra:
            metadata.update(extra)
        return metadata

    def _build_paths(self) -> SessionPaths:
        run_dir = self.base_dir / "runs" / self.session_id
        legacy_dir = self.base_dir / "output" / self.session_id
        context_dir = run_dir / "context"
        logs_dir = run_dir / "logs"
        output_dir = run_dir / "output"
        artifacts_dir = run_dir / "artifacts"
        imported_files_dir = artifacts_dir / "imported_files"
        generated_dir = artifacts_dir / "generated"
        return SessionPaths(
            base_dir=self.base_dir,
            session_id=self.session_id,
            run_dir=run_dir,
            legacy_dir=legacy_dir,
            context_dir=context_dir,
            logs_dir=logs_dir,
            output_dir=output_dir,
            artifacts_dir=artifacts_dir,
            imported_files_dir=imported_files_dir,
            generated_dir=generated_dir,
            request_json=run_dir / "request.json",
            metadata_json=run_dir / "metadata.json",
            events_jsonl=logs_dir / "events.jsonl",
            messages_jsonl=logs_dir / "messages.jsonl",
            errors_log=logs_dir / "errors.log",
            outline_json=output_dir / "outline.json",
            paper_md=output_dir / "paper.md",
            quality_report_json=output_dir / "quality_report.json",
            paper_request_md=context_dir / "paper_request.md",
            runtime_instructions_md=context_dir / "runtime_instructions.md",
            user_constraints_md=context_dir / "user_constraints.md",
            selected_skills_md=context_dir / "selected_skills.md",
            knowledge_context_md=context_dir / "knowledge_context.md",
            theory_context_md=context_dir / "theory_context.md",
            rag_context_md=context_dir / "rag_context.md",
        )

    def _ensure_layout(self) -> None:
        for path in (
            self.paths.run_dir,
            self.paths.legacy_dir,
            self.paths.context_dir,
            self.paths.logs_dir,
            self.paths.output_dir,
            self.paths.artifacts_dir,
            self.paths.imported_files_dir,
            self.paths.generated_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _jsonable_request(request: PaperRequest) -> dict[str, Any]:
        payload = asdict(request)
        if payload.get("base_dir") is not None:
            payload["base_dir"] = str(payload["base_dir"])
        return payload

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _write_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, ensure_ascii=False) + "\n")

    @staticmethod
    def _append_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)

    @staticmethod
    def _count_jsonl_lines(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                return sum(1 for line in handle if line.strip())
        except OSError:
            return 0
