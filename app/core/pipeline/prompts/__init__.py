"""Prompt library — curated prompts from academic writing skill repositories.

Sources:
- claude-scholar (Galaxy-Dawn/claude-scholar): research-ideation, ml-paper-writing, paper-self-review, writing-anti-ai, citation-verification
- academic-agents (ChenHaNing/academic-agents): 11 specialized agents with battle-tested Chinese prompts
- awesome-ai-research-writing (Leey21/awesome-ai-research-writing): 17 writing prompt templates
- Humanizer-zh (op7418/Humanizer-zh): 24 AI writing patterns
- review-response (claude-scholar): rebuttal writing strategies and templates
- post-acceptance (claude-scholar): conference presentation, poster, promotion
- latex-conference-template-organizer (claude-scholar): LaTeX template cleanup
- ARIS (affaan-m/Auto-claude-code-research-in-sleep): novelty-check, paper-claim-audit, auto-review-loop, research-lit, citation-audit
"""

from .architect_prompts import ARCHITECT_SYSTEM_PROMPT_V2, build_research_ideation_prompt
from .auto_review_prompts import (
    REVIEW_DIFFICULTY_LEVELS,
    build_auto_review_memory_prompt,
    build_auto_review_nightmare_prompt,
    build_auto_review_round_prompt,
    build_review_rebuttal_prompt,
    build_round_update_prompt,
)
from .camera_ready_prompts import build_camera_ready_prompt
from .caption_prompts import build_caption_prompt
from .citation_prompts import build_citation_audit_prompt, build_citation_verifier_prompt
from .claim_audit_prompts import (
    build_claim_audit_report,
    build_claim_audit_system_prompt,
    build_claim_audit_user_prompt,
)
from .deai_prompts import (
    DEAI_BLACKLIST_EN,
    DEAI_BLACKLIST_ZH,
    DEAI_PATTERNS_ZH,
    DEAI_SYSTEM_PROMPT_V2,
    build_deai_user_prompt,
)
from .experiment_prompts import (
    build_chart_recommendation_prompt,
    build_experiment_analysis_prompt,
)
from .illustrator_prompts import build_illustrator_prompt
from .latex_template_prompts import build_latex_template_prompt
from .literature_search_prompts import (
    build_literature_analysis_prompt,
    build_literature_search_system_prompt,
    build_literature_synthesis_prompt,
    build_paper_scoring_prompt,
)
from .logic_auditor_prompts import build_logic_auditor_prompt
from .novelty_prompts import (
    build_claim_extraction_prompt,
    build_novelty_report,
    build_novelty_search_prompt,
    build_novelty_verification_prompt,
)
from .optimizer_prompts import build_optimizer_prompt
from .rebuttal_prompts import build_rebuttal_prompt
from .reviewer_prompts import (
    REVIEWER_SYSTEM_PROMPT,
    SELF_REVIEW_CHECKLIST,
    build_reviewer_user_prompt,
)
from .translator_prompts import build_translator_prompt
from .writer_lang_prompts import WRITER_LANG_POLISH_PROMPT_ZH
from .writer_logic_prompts import WRITER_LOGIC_SYSTEM_PROMPT
from .writer_theory_prompts import WRITER_THEORY_RESTRUCTURE_PROMPT_ZH

__all__ = [
    # Architect
    "ARCHITECT_SYSTEM_PROMPT_V2",
    "build_research_ideation_prompt",
    # Writer (3-round)
    "WRITER_LOGIC_SYSTEM_PROMPT",
    "WRITER_THEORY_RESTRUCTURE_PROMPT_ZH",
    "WRITER_LANG_POLISH_PROMPT_ZH",
    # Reviewer
    "REVIEWER_SYSTEM_PROMPT",
    "build_reviewer_user_prompt",
    "SELF_REVIEW_CHECKLIST",
    # De-AI
    "DEAI_SYSTEM_PROMPT_V2",
    "build_deai_user_prompt",
    "DEAI_BLACKLIST_ZH",
    "DEAI_BLACKLIST_EN",
    "DEAI_PATTERNS_ZH",
    # Translator
    "build_translator_prompt",
    # Logic Auditor
    "build_logic_auditor_prompt",
    # Citation Verifier (basic + 3-layer audit)
    "build_citation_verifier_prompt",
    "build_citation_audit_prompt",
    # Experiment Analyst
    "build_experiment_analysis_prompt",
    "build_chart_recommendation_prompt",
    # Illustrator
    "build_illustrator_prompt",
    # Caption Writer
    "build_caption_prompt",
    # Text Optimizer
    "build_optimizer_prompt",
    # Rebuttal Writer
    "build_rebuttal_prompt",
    # Camera-ready Preparation
    "build_camera_ready_prompt",
    # LaTeX Template Organizer
    "build_latex_template_prompt",
    # Novelty Check (ARIS)
    "build_claim_extraction_prompt",
    "build_novelty_search_prompt",
    "build_novelty_verification_prompt",
    "build_novelty_report",
    # Paper Claim Audit (ARIS)
    "build_claim_audit_system_prompt",
    "build_claim_audit_user_prompt",
    "build_claim_audit_report",
    # Auto Review Loop (ARIS)
    "REVIEW_DIFFICULTY_LEVELS",
    "build_auto_review_round_prompt",
    "build_auto_review_memory_prompt",
    "build_auto_review_nightmare_prompt",
    "build_review_rebuttal_prompt",
    "build_round_update_prompt",
    # Literature Search (ARIS)
    "build_literature_search_system_prompt",
    "build_literature_analysis_prompt",
    "build_literature_synthesis_prompt",
    "build_paper_scoring_prompt",
]
