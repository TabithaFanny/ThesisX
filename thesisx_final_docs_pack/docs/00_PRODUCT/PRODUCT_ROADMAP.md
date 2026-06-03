<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# ThesisX Product Roadmap

## 1. Roadmap Principle

The roadmap must move from infrastructure to actual academic workflow. Current state has Runtime foundation, but the product is not complete until Knowledge Base, Theory, Evidence, RAG, Editor Loop, Export, and History are connected.

## 2. Current Confirmed State

| Area | State |
|---|---|
| Frontend visual/SVG stage | Closed. Do not continue visual polishing unless blocking. |
| Main Editor | Real, must not break. |
| AgentTeamDialog | UI complete, Mock works, Real path exists. |
| Runtime | Half-connected, improving. |
| SessionStore | Implemented. |
| RunHistoryReader | Implemented. |
| RunDiagnostics | Implemented. |
| Provider detector | Implemented through provider config work. |
| Knowledge Base | Not complete. |
| Literature Management | Not complete. |
| Theory Matcher | Not complete. |
| Evidence Pack | Not complete. |
| RAG | Not complete. |
| Editor AI insert loop | Not complete. |
| Export finalization | Not complete. |

## 3. Vision Roadmap

### Vision 3.1 — Knowledge Base Core

Goal:
- Establish SQLite-backed project knowledge store.

Deliverables:
- Project model.
- KnowledgeObject model.
- LiteratureItem, NoteItem, TheoryItem, EvidenceItem.
- CRUD service.
- Search by type/tag/project.
- Unit tests.

Exit Criteria:
- User can create objects and bind them to projects.
- Store persists in `~/.wenbiao/thesisx.db`.
- Tests pass.

### Vision 3.2 — Literature Management

Goal:
- Turn literature from preview into usable structured data.

Deliverables:
- BibTeX/RIS/CSL JSON import.
- Citation key generator.
- Project-literature binding.
- Reading status.
- Literature notes.
- Metadata normalization.

Exit Criteria:
- User can import references and bind them to a project.
- Citation keys are stable and collision-safe.

### Vision 3.3 — Theory Matcher

Goal:
- Connect research question to theoretical frameworks.

Deliverables:
- Seed theory library with 30+ theories.
- Research question parser.
- BM25/FTS matching.
- Optional LLM explanation.
- Fit score and misuse risk.

Exit Criteria:
- User can input a research question and receive ranked theory recommendations.

### Vision 3.4 — Evidence Pack

Goal:
- Build claim-evidence structure.

Deliverables:
- Claim model.
- Evidence model.
- Claim-evidence links.
- Gap analysis rules.
- Evidence report.

Exit Criteria:
- User can connect evidence to claims and see missing evidence warnings.

### Vision 3.5 — RAG

Goal:
- Provide retrieval-grounded writing context.

Deliverables:
- Chunking.
- FTS5/BM25.
- Optional embedding provider.
- Context Bundle builder.
- RAG result preview.

Exit Criteria:
- Agent Runtime can receive structured Context Bundle.

### Vision 3.6 — Editor Loop

Goal:
- Close the loop between AI output and Main Editor.

Deliverables:
- Insert at cursor.
- Replace selection.
- Add as new section.
- AI diff preview.
- Snapshot and rollback.

Exit Criteria:
- AI output can be safely inserted and reverted.

### Vision 3.7 — Connectors

Goal:
- Read-only Zotero and Obsidian import.

Deliverables:
- Zotero API connector.
- Obsidian vault scanner.
- Import jobs.
- Conflict preview.
- No default write-back.

Exit Criteria:
- User can import external assets into Knowledge Base.

### Vision 3.8 — Skill Library Runtime Integration

Goal:
- Support local skill packages.

Deliverables:
- Local skill loader.
- YAML schema.
- Secret scanner.
- Project binding.
- Runtime context injection.

Exit Criteria:
- Selected skills affect runtime context.

### Vision 3.9 — Export and Delivery

Goal:
- Produce usable academic outputs.

Deliverables:
- Markdown export.
- DOCX export.
- BibTeX export.
- Evidence Pack report.
- Diagnostics report.
- Session archive.

Exit Criteria:
- User can export paper and supporting materials.

### Vision 4.0 — Final Usable Beta

Goal:
- Complete the whole workflow.

Exit Criteria:
- Research question → Knowledge → Theory → Evidence → RAG → AI → Editor → Export → History works.
- Full tests pass.
- User guides exist.
- Privacy guide exists.

## 4. Fast vs Slow Push

### Can Auto-Execute

- Documentation generation.
- SQLite schema and unit tests.
- Read-only importers.
- Local-only search.
- Mock-safe RAG.
- Diagnostics export.
- Non-destructive migration.

### Must Pause for User Confirmation

- Real API calls.
- Writing to Zotero or Obsidian.
- Deleting local files.
- Modifying Main Editor internals deeply.
- Replacing current Runtime contract.
- Adding heavy dependencies.
- Changing storage root.

## 5. Execution Rule

Each Vision must follow:

```text
review current state
→ plan
→ implement smallest coherent slice
→ run targeted tests
→ run full tests
→ write completion report
→ decide next Vision
```

## 6. Release Gates

### Gate A — Infrastructure Ready

- Runtime works in Mock.
- SessionStore works.
- Provider diagnostics works.

### Gate B — Knowledge Ready

- Knowledge Base.
- Literature.
- Theory.
- Evidence.

### Gate C — Writing Ready

- RAG.
- Agent context injection.
- Editor insertion.

### Gate D — Delivery Ready

- Export.
- History UI.
- User guide.
- Privacy guide.

### Gate E — Final Beta

- Full workflow verified.
- All tests pass.
- No misleading preview states.
