"""RewriteService — local text rewriting with mock transformations (Vision 3.6).

Supports modes: polish, expand, add_theory, add_evidence.
Mock mode applies rule-based transformations; real mode would call AgentTeamRunner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import EditPatch


@dataclass
class RewriteResult:
    """Result of a rewrite operation."""
    original: str
    rewritten: str
    mode: str
    patch: EditPatch | None = None


class RewriteService:
    """Apply text rewrites in different modes.

    In mock mode, transformations are rule-based:
    - polish: minor word refinements, fix common issues
    - expand: elaborate with filler sentences
    - add_theory: inject a theory reference block
    - add_evidence: inject an evidence note
    """

    REWRITE_MODES = frozenset(["polish", "expand", "add_theory", "add_evidence"])

    def __init__(self, agent_runner=None):
        self._runner = agent_runner

    @property
    def run_mode(self) -> str:
        return "mock" if self._runner is None else "real"

    def rewrite(self, selected_text: str, mode: str,
                context: str = "") -> RewriteResult:
        """Rewrite selected text in the given mode."""
        if mode not in self.REWRITE_MODES:
            raise ValueError(f"Unknown rewrite mode: {mode}")

        new_text = _MOCK_TRANSFORMS.get(mode, lambda t, c: t)(selected_text, context)

        patch = EditPatch.new(
            section_id="editor.selection",
            operation="replace",
            old_text=selected_text,
            new_text=new_text,
        )

        return RewriteResult(
            original=selected_text,
            rewritten=new_text,
            mode=mode,
            patch=patch,
        )


# ── mock transforms ─────────────────────────────────────────────────────────

def _mock_polish(text: str, _context: str = "") -> str:
    """Minor polish: replace weak phrases with stronger ones."""
    replacements = {
        "is a very": "is a",
        "very important": "critical",
        "in order to": "to",
        "due to the fact that": "because",
        "it is important to note that": "notably,",
        "a lot of": "many",
        "things": "aspects",
        "stuff": "materials",
        "big": "substantial",
        "small": "modest",
    }
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def _mock_expand(text: str, _context: str = "") -> str:
    """Expand: add an elaboration sentence."""
    sentences = re.split(r"(?<=[。.！!？?])\s*", text)
    if not sentences:
        return text

    expansions = {
        "zh": "。这一发现为后续研究提供了重要的参考依据。",
        "en": ". This finding provides important reference for future research.",
    }
    # Detect language
    if re.search(r"[\u4e00-\u9fff]", text):
        suffix = expansions["zh"]
    else:
        suffix = expansions["en"]

    last = sentences[-1].rstrip()
    sentences[-1] = last + suffix
    return "".join(sentences)


def _mock_add_theory(text: str, _context: str = "") -> str:
    """Add theory: append a theory reference note."""
    theory_block = (
        "\n\n> **理论视角 Reference**\n"
        "> 此处可结合制度理论（Institutional Theory）分析组织行为受制度环境的影响，"
        "包括合法性机制与同构压力。具体理论应用需结合研究问题进一步细化。\n"
    )
    return text.rstrip() + theory_block


def _mock_add_evidence(text: str, _context: str = "") -> str:
    """Add evidence: append an evidence note."""
    evidence_block = (
        "\n\n> **证据支撑 Evidence**\n"
        "> 此处需补充实证证据支持上述论点。"
        "可通过数据引用、案例描述或文献引证等方式充实论证。\n"
    )
    return text.rstrip() + evidence_block


_MOCK_TRANSFORMS = {
    "polish": _mock_polish,
    "expand": _mock_expand,
    "add_theory": _mock_add_theory,
    "add_evidence": _mock_add_evidence,
}
