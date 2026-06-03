<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# ThesisX PRD Overview

## 1. Product Goal

ThesisX helps users complete academic writing through a full workflow:

```text
Define research problem
→ Build knowledge base
→ Manage literature
→ Match theory
→ Build evidence
→ Generate grounded draft
→ Edit
→ Export
→ Trace history
```

## 2. Core Jobs-To-Be-Done

### JTBD 1: Turn vague ideas into research structure

When a user has only a vague topic, ThesisX should help identify:
- Research object.
- Research question.
- Possible variables.
- Theoretical frameworks.
- Search keywords.
- Evidence needs.

### JTBD 2: Organize research assets

When a user has many PDFs, notes, and references, ThesisX should:
- Import and normalize them.
- Link them to projects.
- Search and filter them.
- Convert them into usable writing context.

### JTBD 3: Generate grounded writing

When a user asks AI to write, ThesisX should:
- Retrieve relevant knowledge.
- Add theories and evidence.
- Preserve citation constraints.
- Produce traceable output.
- Avoid invented sources.

### JTBD 4: Let user remain in control

User should:
- Edit manually.
- Preview AI changes.
- Roll back.
- See what was sent to AI.
- Know which provider was used.
- See cost and errors.

## 3. Functional Scope

| Feature | Required for Final Beta | Notes |
|---|---:|---|
| Main Editor | Yes | Existing real function. |
| Mock AI Draft | Yes | Must be stable. |
| Real AI Draft | Yes | Minimal verified path. |
| Knowledge Base | Yes | SQLite-backed. |
| Literature Management | Yes | Import and citation key. |
| Theory Matcher | Yes | Local first + optional LLM explanation. |
| Evidence Pack | Yes | Claim/evidence linking. |
| RAG | Yes | At least FTS5/BM25, optional embedding. |
| Run History | Yes | Read-only. |
| Runtime Diagnostics | Yes | Must expose errors. |
| Provider Settings | Yes | Local CLI + Remote API + Agent Team. |
| Skill Local Package | Yes | Minimal local skill. |
| Zotero | Should | Read-only import. |
| Obsidian | Should | Read-only import. |
| DOCX Export | Yes | At least default template. |
| Version History | Later | Can remain preview unless editor snapshots are implemented. |
| Collaboration | Later | Preview only. |

## 4. Product Modules

### 4.1 Project Workspace

Functions:
- Create project.
- Edit research question.
- View project health.
- See knowledge count, literature count, evidence gaps, latest runs.

### 4.2 Main Editor

Functions:
- Edit paper.
- Insert generated content.
- Rewrite selection.
- Snapshot before AI changes.
- Export.

### 4.3 AI Draft Assistant

Functions:
- Configure task.
- Select Mock/Real.
- Select Provider.
- Select context sources.
- Start run.
- Display progress.
- Show error and diagnostics.

### 4.4 Knowledge Base

Functions:
- CRUD knowledge objects.
- Search.
- Filter.
- Bind to project.
- View relations.

### 4.5 Literature Management

Functions:
- Import.
- Normalize metadata.
- Generate citation keys.
- Bind to project.
- Create notes/evidence.

### 4.6 Theory Matcher

Functions:
- Parse research question.
- Match theories.
- Explain fit.
- Warn misuse.
- Insert into project framework.

### 4.7 Evidence Pack

Functions:
- Create claims.
- Add evidence.
- Link evidence.
- Analyze gaps.
- Export evidence report.

### 4.8 RAG

Functions:
- Index chunks.
- Search.
- Preview results.
- Build Context Bundle.
- Inject into AI runtime.

### 4.9 Provider Settings

Functions:
- Discover local CLI.
- Manage remote API profiles.
- Detect Agent Team contracts.
- Health check.
- Show conflict.

### 4.10 Run History

Functions:
- List runs.
- Show outputs.
- Show events/messages.
- Show diagnostics.
- Export report.

## 5. Non-Functional Requirements

### 5.1 Stability

- No crash on missing files.
- Degraded mode if provider unavailable.
- Clear errors.

### 5.2 Privacy

- Local-first storage.
- Remote API sends only declared context.
- API keys not stored in project content.
- Connectors are read-only by default.

### 5.3 Traceability

Every AI run must record:
- Request.
- Context bundle.
- Events.
- Messages.
- Cost.
- Output.
- Diagnostics.

### 5.4 Testability

Every module needs:
- Unit tests.
- File corruption tests.
- Missing config tests.
- No-network tests.
- Mock run tests.

## 6. Acceptance Summary

The product is not complete when “AI can write once.” It is complete when the user can complete the whole academic workflow with local traceability.
