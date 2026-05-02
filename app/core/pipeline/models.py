"""Core data models for the paper generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Literal types
# ---------------------------------------------------------------------------

RunMode = Literal["mock", "real"]
RunnerKind = Literal["sequential", "autogen"]
GenerationType = Literal["paper_draft"]
ImportMode = Literal["new", "replace", "append"]


# ---------------------------------------------------------------------------
# PaperRequest
# ---------------------------------------------------------------------------


@dataclass
class PaperRequest:
    """User inputs for a single paper generation run."""

    topic: str
    generation_type: GenerationType = "paper_draft"
    journal: str = "中文核心"
    run_mode: RunMode = "mock"
    runner_kind: RunnerKind = "sequential"
    auto_polish: bool = False
    budget_cap_cny: float = 10.0
    agent_team_path: str = ""
    base_dir: Path | None = None
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    session_id: str | None = None
    # Phase D wiring: optional paths to pre-built context files
    knowledge_context_path: str = ""
    theory_context_path: str = ""


# ---------------------------------------------------------------------------
# ArchitectOutput
# ---------------------------------------------------------------------------


@dataclass
class ArchitectOutput:
    """Structured output from the ArchitectNode."""

    paper_title: str = ""
    central_argument: str = ""
    argument_chain: list[str] = field(default_factory=list)
    outline: list[dict[str, Any]] = field(default_factory=list)
    missing_materials: list[str] = field(default_factory=list)
    writer_instructions: str = ""


# ---------------------------------------------------------------------------
# QualityCheckResult
# ---------------------------------------------------------------------------


@dataclass
class QualityCheckResult:
    """Static quality check results on the generated paper."""

    word_count: int = 0
    has_abstract: bool = False
    has_keywords: bool = False
    has_introduction: bool = False
    has_conclusion: bool = False
    has_references: bool = False
    citation_warning_count: int = 0
    data_missing_count: int = 0
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# PaperResult
# ---------------------------------------------------------------------------


@dataclass
class PaperResult:
    """Final result returned to the UI after pipeline completion."""

    markdown: str = ""
    word_count: int = 0
    total_cost_cny: float = 0.0
    session_id: str = ""
    session_dir: Path | None = None
    review_json: dict[str, Any] = field(default_factory=dict)
    quality: QualityCheckResult | None = None
    run_mode: RunMode = "mock"
