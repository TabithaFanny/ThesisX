<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# ThesisX Product Blueprint

## 1. Product Definition

ThesisX is a local-first, knowledge-driven, traceable, provider-configurable academic writing workstation.

It is not a one-shot paper generator. It is a full research workflow environment where the user can:

1. Create a research project.
2. Define a research question.
3. Build a project knowledge base.
4. Import literature, notes, theories, and evidence.
5. Match theoretical frameworks to the research problem.
6. Build evidence packs for claims.
7. Use RAG to retrieve grounded context.
8. Generate drafts through Mock or Real Agent Runtime.
9. Insert results into Main Editor.
10. Edit, rewrite, rollback, and export.
11. Review run history, diagnostics, provider status, and provenance.

## 2. Final Product Positioning

ThesisX should become a desktop academic AI workbench with four core promises:

| Promise | Meaning |
|---|---|
| Knowledge-grounded | AI writing must be connected to literature, notes, theories, and evidence. |
| Local-first | Project assets, run records, diagnostics, and knowledge objects are stored locally by default. |
| Traceable | Every AI operation produces a session record, events, messages, outputs, and diagnostics. |
| Provider-flexible | The user may use Mock, Local CLI, Remote API, or external Agent Team providers. |

## 3. Final Product Main Loop

```text
Research Question
→ Project Workspace
→ Knowledge Base
→ Literature Management
→ Theory Matcher
→ Evidence Pack
→ RAG Context Bundle
→ Agent Runtime
→ Main Editor
→ Export
→ Run History / Diagnostics
```

## 4. User Personas

### 4.1 Student Writer

Needs:
- Turn vague research topics into paper structures.
- Understand which theory fits the topic.
- Manage required readings.
- Generate outline and first draft.
- Avoid AI hallucinated citations.

### 4.2 Researcher

Needs:
- Maintain a long-term literature and notes library.
- Reuse knowledge across multiple projects.
- Track evidence, claims, and writing decisions.
- Use AI without losing provenance.

### 4.3 Supervisor / Reviewer

Needs:
- Inspect logic, evidence, theoretical framing, and citation quality.
- Review drafts with structured comments.
- Produce revision guidance.

### 4.4 Advanced AI User

Needs:
- Switch providers.
- Use local CLI and remote API.
- Configure model/base URL/key source.
- Inspect diagnostics and event streams.
- Add local skills.

## 5. Core Product Modules

| Module | Final Status | Description |
|---|---|---|
| Workspace Home | Real dashboard | Project overview, health, recent runs, knowledge status. |
| Main Editor | Real editor | WYSIWYG/Markdown editing, AI insert, snapshots, export. |
| AI Draft Assistant | Real runtime UI | Mock and Real task launch, progress, diagnostics. |
| Knowledge Base | Real | Unified store for literature, notes, theories, evidence. |
| Literature Management | Real | Bibliographic metadata, citation keys, project binding. |
| Theory Matcher | Real | Research question → theory candidates → writing framework. |
| Evidence Pack | Real | Claim-evidence linking and gap analysis. |
| RAG Search | Real | Hybrid retrieval and context bundle preview. |
| Run History | Real read-only | Session list, paper.md, events, messages, diagnostics. |
| Runtime Diagnostics | Real | Provider, contract, session, and file health. |
| Provider Settings | Real | Local CLI, Remote API, Agent Team configuration. |
| Skill Library | Local skill package | Read local skills and inject them into context. |
| Connectors | Progressive | Zotero and Obsidian read-only import first. |
| Export Center | Real | DOCX, Markdown, BibTeX, diagnostics, archive. |

## 6. What Counts as Final Usable Beta

ThesisX reaches Final Usable Beta only when:

1. Desktop app launches reliably.
2. Main Editor can edit and save paper content.
3. Mock generation reliably creates full run session.
4. Real generation runs when provider configuration is valid.
5. Real failure is explicit, never disguised as success.
6. Knowledge Base can create and query four knowledge object types.
7. Literature items can be imported and bound to projects.
8. Theory Matcher can recommend theoretical frameworks with reasons and risks.
9. Evidence Pack can bind evidence to claims and detect basic gaps.
10. RAG can produce structured Context Bundle.
11. Agent Runtime can consume Context Bundle.
12. AI output can be inserted into Main Editor.
13. Run History can show sessions, outputs, diagnostics.
14. Provider Settings can detect local CLI, remote API, and Agent Team health.
15. Export can produce Markdown and DOCX at minimum.
16. Preview pages remain clearly marked and do not mislead.
17. All tests pass.
18. User Guide and Privacy Guide exist.

## 7. Product Boundary

Do not call the product final if only Runtime works. Runtime is infrastructure. The product is final only when the knowledge workflow is connected:

```text
Knowledge → Retrieval → Writing → Editing → Export → Traceability
```

## 8. Non-Goals for First Final Beta

These are not required for the first final beta:

1. Multi-user collaboration server.
2. Full marketplace skill registry.
3. Full Git version control.
4. Full Zotero two-way sync.
5. Full Obsidian write-back.
6. Cloud account system.
7. Hosted SaaS backend.
8. Multi-tenant permission system.

They may remain preview or future roadmap items.

## 9. Product Quality Bar

The agent must not optimize only for passing tests. It must satisfy:

- Functional usability.
- Data persistence.
- Clear error handling.
- Local privacy.
- Recoverability.
- Traceable AI actions.
- Minimal hallucination by grounding outputs.
- Clear distinction between Mock, Dry-run, and Real.
