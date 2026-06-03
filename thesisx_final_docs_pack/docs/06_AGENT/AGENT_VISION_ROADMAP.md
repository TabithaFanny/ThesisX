<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# Agent Vision Roadmap

## 1. Purpose

This document tells a coding agent how to move ThesisX from current state to final usable product.

The agent must not confuse:
- Runtime success with product success.
- Mock success with Real success.
- Preview UI with real functionality.
- Documentation with implementation.

## 2. Current Known State

- Frontend visual/SVG phase is closed.
- Main Editor is real and must not be broken.
- AgentTeamDialog exists and Mock works.
- Real Agent Team has partial path and provider work.
- SessionStore / RunHistoryReader / RunDiagnostics exist.
- Provider detection exists.
- Knowledge Base is not complete.
- Literature, Theory, Evidence, RAG are not complete.
- Editor AI insertion loop is not complete.
- Export is not final.
- Final product is not reached.

## 3. Roadmap

### Vision 3.1 — Knowledge Base Core

Implement:
- SQLite DB.
- KnowledgeObject.
- LiteratureItem.
- NoteItem.
- TheoryItem.
- EvidenceItem.
- Project binding.
- FTS search.
- Tests.

Do not:
- RAG embeddings.
- Zotero full sync.
- UI overhaul.

### Vision 3.2 — Literature Management

Implement:
- LiteratureService.
- BibTeX import.
- RIS import.
- Citation key.
- Project binding.
- Literature UI minimal.

Do not:
- Full Zotero write-back.
- Citation style perfection.

### Vision 3.3 — Theory Matcher

Implement:
- Seed theory library.
- Research question parser.
- Theory match.
- Fit score.
- Misuse risk.
- Save theory to project.

Do not:
- Depend fully on LLM.
- Hide mismatch risk.

### Vision 3.4 — Evidence Pack

Implement:
- Claims.
- Evidence.
- Claim-evidence links.
- Gap analysis.
- Evidence report.

Do not:
- Pretend AI gap analysis is definitive.

### Vision 3.5 — RAG

Implement:
- Chunking.
- FTS/BM25 retrieval.
- Optional embedding interface.
- ContextBundle.
- Runtime injection.

Do not:
- Require paid embedding API for baseline.
- Inject raw unstructured text only.

### Vision 3.6 — Editor Loop

Implement:
- Insert generated content.
- Replace selection.
- Add section.
- Snapshot.
- Rollback.
- Diff preview.

Do not:
- Break Main Editor.
- Overwrite user text without snapshot.

### Vision 3.7 — Connectors

Implement:
- Zotero read-only import.
- Obsidian read-only scan.
- ImportJob.
- Conflict preview.

Do not:
- Default write-back.
- Delete external files.

### Vision 3.8 — Skill Local Package

Implement:
- Local SkillLoader.
- YAML schema.
- Secret scan.
- Project binding.
- Runtime context injection.

Do not:
- Marketplace.
- Remote registry.
- Store API keys in skills.

### Vision 3.9 — Export

Implement:
- Markdown export.
- DOCX export.
- BibTeX export.
- Evidence report.
- Diagnostics report.
- Session archive.

Do not:
- Overpromise all journal formats.

### Vision 4.0 — Final Beta

Implement:
- User Guide.
- Privacy Guide.
- Release Report.
- End-to-end verification.

## 4. Execution Per Vision

Every Vision must follow:

```text
1. Review current code.
2. Confirm no forbidden scope.
3. Write short implementation plan.
4. Implement smallest coherent slice.
5. Run targeted tests.
6. Run full tests.
7. Write completion report.
8. Decide whether to continue.
```

## 5. Fast-Track Visions

Can usually auto-run:
- Documentation.
- SQLite schema.
- Unit tests.
- Local-only CRUD.
- Read-only import.
- Mock-safe RAG.
- Diagnostics.

## 6. Must Pause

Pause before:
- Real API calls.
- Zotero write-back.
- Obsidian write-back.
- Deleting local data.
- Changing Main Editor architecture.
- Adding heavy dependencies.
- Modifying external Agent Team repo.
- Changing storage root.

## 7. Final Product Completion Definition

Final product is not complete until:

```text
Project
→ Knowledge Base
→ Literature
→ Theory
→ Evidence
→ RAG
→ Runtime
→ Main Editor
→ Export
→ Run History
```

works as one user-facing workflow.

## 8. Completion Report Template

Every Vision report must include:

```text
1. Modified files
2. New files
3. What was implemented
4. What was not implemented
5. Tests run
6. Test result
7. Data migration impact
8. UI impact
9. API impact
10. Remaining risks
11. Next recommended Vision
```
