# ThesisX V5.0 TODO

> Last updated: 2026-05-06

## Current Stage

- Vision alignment: `V3.x core capabilities` feeding `V5.0 Web Migration`
- Working phase: `V5.0 Phase 1.5 / 2`
- Delivery target: local-first web workbench with real API closure, not PyQt polish

## Done

- `thesisx_api/` import/start critical blockers fixed
- Native FastAPI `StreamingResponse` replaced `sse-starlette`
- `AiServiceAdapter` mock/real semantics corrected
- knowledge/literature static search route ordering fixed
- RAG chunk index made SQLite-persistent with filters
- API smoke tests added and passing
- `thesisx-web/` scaffolded and built
- Pages shipped:
  - workspace home
  - projects
  - project detail
  - knowledge
  - literature
  - rag
  - pipeline
  - history
  - quality
  - settings

## In Progress

- Stabilize Next.js dev runtime and navigation behavior
- Close `projects -> detail` interaction reliability
- Turn current web pages from shell screens into workflow-complete workspaces

## P0

- [ ] Ensure `projects` list can always open detail pages without dev-runtime crashes
- [ ] Make `pipeline` session flow feel complete: create session, stream events, inspect history
- [ ] Add a simple root web/status landing behavior that never looks broken

## P1

- [ ] Connect project context into knowledge / rag / quality pages
- [ ] Add project-linked run history instead of global session-only browsing
- [ ] Expand quality dashboard from read-only stats into actionable workflow
- [ ] Add theory / evidence / export pages in web

## P2

- [ ] Build import flows for Obsidian / Zotero in settings
- [ ] Add editor-facing writing workspace
- [ ] Add light frontend test coverage for key routes

## Working Rules

- Keep changes minimal and closure-oriented
- Prefer fixing in `thesisx_api/` and `thesisx-web/` unless business semantics live in `app/core/`
- Do not silently fake real AI success
- Do not stop at partial UI shells when a workflow can be closed in the same turn
