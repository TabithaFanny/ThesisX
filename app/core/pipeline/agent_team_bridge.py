"""Agent Team bridge — path validation, dependency checks, import helpers."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path & dependency helpers
# ---------------------------------------------------------------------------


def ensure_agent_team_path(path: str) -> Path:
    """Validate that the Agent Team path exists and contains the expected package.

    Raises:
        FileNotFoundError: if path is empty or doesn't exist.
        NotADirectoryError: if path doesn't contain the expected package.
    """
    if not path or not path.strip():
        raise FileNotFoundError("Agent Team 路径为空，请先选择路径。")
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Agent Team 路径不存在: {p}")
    pkg_dir = p / "academic_agent_team"
    if not pkg_dir.is_dir():
        raise NotADirectoryError(
            f"路径中未找到 academic_agent_team 包: {p}\n"
            "请确认选择的是 Agent Team 项目根目录。"
        )
    return p


def check_dependencies() -> list[str]:
    """Check that required runtime dependencies are importable.

    Returns a list of missing package names (empty if all OK).
    """
    missing: list[str] = []
    for pkg in ("httpx", "pydantic"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


# ---------------------------------------------------------------------------
# sys.path management for Agent Team import
# ---------------------------------------------------------------------------

_original_sys_path: list[str] = list(sys.path)
_agent_team_added = False


def _add_agent_team_to_sys_path(agent_team_root: Path) -> None:
    """Add agent team root to sys.path[0] if not already present, idempotently."""
    global _agent_team_added
    root_str = str(agent_team_root)
    if root_str in sys.path:
        return
    sys.path.insert(0, root_str)
    _agent_team_added = True
    logger.debug("Added to sys.path: %s", root_str)


def import_agent_team_api(agent_team_root: Path) -> dict[str, Any]:
    """Import Agent Team API classes, adding the path if needed.

    Returns:
        dict with keys: PipelineConfig, SequentialRunner,
        TokenStreamEvent, StateUpdateEvent, CostUpdateEvent,
        AgentMessageEvent, ErrorEvent, CompletionEvent, HumanInterruptEvent

    Raises:
        ImportError: if the Agent Team package cannot be imported.
    """
    _add_agent_team_to_sys_path(agent_team_root)
    try:
        from academic_agent_team.tui.events import (  # type: ignore[import-untyped]
            AgentMessageEvent,
            CompletionEvent,
            CostUpdateEvent,
            ErrorEvent,
            HumanInterruptEvent,
            StateUpdateEvent,
            TokenStreamEvent,
        )
        from academic_agent_team.tui.runner import (  # type: ignore[import-untyped]
            PipelineConfig,
            SequentialRunner,
        )
    except ImportError as e:
        raise ImportError(
            f"无法导入 Agent Team 模块，请检查路径和依赖: {e}"
        ) from e
    return {
        "PipelineConfig": PipelineConfig,
        "SequentialRunner": SequentialRunner,
        "TokenStreamEvent": TokenStreamEvent,
        "StateUpdateEvent": StateUpdateEvent,
        "CostUpdateEvent": CostUpdateEvent,
        "AgentMessageEvent": AgentMessageEvent,
        "ErrorEvent": ErrorEvent,
        "CompletionEvent": CompletionEvent,
        "HumanInterruptEvent": HumanInterruptEvent,
    }


# ---------------------------------------------------------------------------
# API Key helpers
# ---------------------------------------------------------------------------


def sync_api_keys(config: Any) -> dict[str, str]:
    """Read API keys from environment (never logged).

    Returns:
        dict with api_key, base_url, model (values may be empty strings).
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("AI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    model = os.environ.get("OPENAI_MODEL", "")
    return {"api_key": api_key, "base_url": base_url, "model": model}


# ---------------------------------------------------------------------------
# Session / output helpers
# ---------------------------------------------------------------------------


def resolve_session_dir(base_dir: Path, session_id: str) -> Path:
    """Create and return the session output directory."""
    d = base_dir / "output" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path: Path, data: Any) -> None:
    """Write JSON data to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_event_jsonl(path: Path, event_dict: dict[str, Any]) -> None:
    """Append a single JSON-serializable dict as a line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")


def read_paper_markdown(session_dir: Path) -> str:
    """Read paper.md from the session output directory.

    Raises:
        FileNotFoundError: if paper.md doesn't exist.
    """
    paper_path = session_dir / "paper.md"
    if not paper_path.exists():
        raise FileNotFoundError(f"paper.md 未生成: {paper_path}")
    return paper_path.read_text(encoding="utf-8")
