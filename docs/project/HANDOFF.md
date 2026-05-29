# Handoff — ThesisX Web Migration

## Context

- **Project**: Local-first, knowledge-driven paper-writing AI workbench for graduate students
- **Current goal**: Migrate from PyQt6 desktop to Web application (Next.js + FastAPI)
- **Critical pivot (2026-05-04)**: User explicitly rejected PyQt6 as frontend. Web-only from now on.

## What Was Done (Recent Useful State)

1. `thesisx-web/` is now the main delivery surface, with pages for workspace, projects, project detail, knowledge, literature, rag, pipeline, writing, history, quality, settings, theory, evidence, and export
2. Web AI entry points are no longer isolated to pipeline:
   - theory: generate theory draft
   - literature: generate AI digest + structure literature into knowledge items
   - knowledge: polish/expand/convert into theory/evidence drafts
   - evidence: generate evidence draft
   - quality: generate revision / evidence / theory plans
   - writing: import session paper, rewrite, merge section structure, export
3. Agent architecture is now substantially unified:
   - shared context assembler
   - centralized output contracts
   - unified context / rewrite / artifact / feedback routes
   - lightweight feedback memory
   - lightweight relevance-based context ranking
   - reusable artifact rendering on major web AI pages
4. Settings import flow is now real:
   - Obsidian scan persists into knowledge store
   - Zotero BibTeX/RIS import persists into knowledge store
5. Export flow is now real:
   - citations can be downloaded
   - DOCX export triggers download
   - session archive triggers download
6. API smoke coverage expanded:
   - settings import persistence
   - session paper fetch
   - literature structure endpoint
   - agent context endpoint
   - agent rewrite endpoint
   - agent artifact endpoint
   - agent feedback endpoint
7. Regression baseline hardened:
   - `scripts/test_all.sh` now runs clean build + production route smoke
   - full Python suite: `691 passed`
   - web lint clean
   - web production build clean
   - route smoke includes `/writing`

## Current State

### Completed
- `app/core/` — stable service backbone
- `thesisx_api/` — FastAPI wrapper is real and HTTP-verified
- `thesisx-web/` — main delivery surface, buildable and routable
- `scripts/test_all.sh` — unified regression entry point
- `writing` workspace — minimal web authoring closure is now shipped
- major agent surfaces now share one context / output / feedback architecture

### Partial
- AiService QThread coupling still exists in core architecture
- Several web pages are workflow-complete at MVP level, but some remain shallower than a full graph/stateful agent runtime

### Not Done
- No dedicated frontend route/integration test suite yet
- No user auth layer
- Literature graph / canvas export is not yet implemented
- Pipeline/detail UX still needs more closure
- Writing workspace is still Markdown-first rather than rich-text/editor parity
- Agent runtime is not yet a resumable graph/state-machine engine

### Blocked
- Nothing is hard-blocked; remaining issues are closure and quality work

## Risks / Blockers

| Risk | Severity | Mitigation |
|------|----------|------------|
| AiService has QThread dependency | HIGH | Need adapter to make it async-FastAPI compatible |
| Frontend route/runtime regressions are still smoke-tested rather than deeply integration-tested | MEDIUM | Add richer browser/integration coverage when cost justified |
| `.next` can produce false chunk errors if dev/build overlap | MEDIUM | Avoid concurrent Next processes; clean `.next` before cold verification |
| User wants "single-command start" | MEDIUM | docker-compose or Makefile at the end |

## Technical Debt (Important)

- **P1**: AiService QThread coupling → blocks FastAPI streaming
- **P1**: No dedicated frontend tests yet
- **P1**: `.next` artifact fragility during overlapping local runs
- **P2**: Pipeline/detail UX still shallow
- **P2**: Writing workspace needs richer editing semantics
- **P2**: Literature graph/canvas export still missing
- **P2**: Agent runtime still uses lightweight request/response orchestration rather than graph execution
- **Superseded**: All PyQt6 dark mode fixes are moot for web

## Constraints

- **Tech**: Next.js 14 + React + Tailwind (frontend), FastAPI + Python (backend)
- **Architecture**: Prefer keeping product semantics in `app/core/`; UI layers should stay thin
- **Do Not Change**: SQLite local-first storage (`~/.wenbiao/`), evidence traceability requirement, multi-provider AI
- **Delivery**: Single-user web app, no auth for MVP, local-first not cloud-first
- **PyQt6**: All `app/ui/` code is reference only. Do not expend effort fixing PyQt6 bugs.

## Next Step

- **Task**: Decide whether to stop at the current agent-capable MVP or continue into post-delivery agent/runtime enhancements
- **Scope**: If continuing, prioritize richer ranking, artifact-memory feedback, or graph-style agent orchestration
- **Acceptance**: Current shared context / contract / feedback architecture is stable; remaining work is enhancement-grade
- **Blocked by**: Nothing

## Read First

- `.memory/PROJECT_BRIEF.md` — What ThesisX is and delivery form
- `.memory/TECH_DECISIONS.md` — 6 confirmed decisions
- `.memory/CURRENT_STATE.md` — What's real vs fake
- `.memory/ROADMAP.md` — Web migration phases
- `.memory/TECH_DEBT.md` — P0-P3 debt inventory

## Do Not Do

- Do NOT fix PyQt6 bugs or dark mode (moot)
- Do NOT build auth/multi-user (MVP is single-user)
- Do NOT rewrite app/core/ services
- Do NOT add cloud storage
- Do NOT build online paper database
