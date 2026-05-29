"""Central output contracts for ThesisX agent tasks."""

from __future__ import annotations


OUTPUT_CONTRACTS: dict[str, str] = {
    "writing": (
        "Return directly usable Markdown only. "
        "Prefer headings, concise paragraphs, explicit academic transitions, "
        "and concrete revision language. Do not include meta commentary."
    ),
    "quality": (
        "Return an actionable revision plan. "
        "Include priorities, weak signal mapping, and immediately executable next steps."
    ),
    "theory": (
        "Return theory-oriented output with four parts: "
        "candidate lens, fit rationale, limitations, and how it should be applied."
    ),
    "evidence": (
        "Return evidence-oriented output with three parts: "
        "missing support, recommended evidence type, and how it should be linked."
    ),
    "knowledge": (
        "Return a reusable knowledge artifact suitable for direct storage. "
        "Keep it compact, factual, and structured enough to become note/theory/evidence content."
    ),
}


def get_output_contract(task_type: str) -> str:
    return OUTPUT_CONTRACTS.get(
        task_type,
        "Return concise, structured output usable directly inside ThesisX.",
    )
