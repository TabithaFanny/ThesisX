<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# ThesisX Technical Architecture

## 1. Architecture Principle

ThesisX must be built as a local-first layered desktop application.

```text
UI Layer
→ Application Service Layer
→ Domain Service Layer
→ Storage Layer
→ Runtime / Provider Layer
→ External Connectors
```

No UI page should directly manipulate provider APIs, files, or external agents.

## 2. Current Stack

| Layer | Current / Recommended Tech |
|---|---|
| Desktop UI | PyQt6 |
| Main Editor | QTextEdit / QTextDocument / existing editor widgets |
| Runtime | AgentTeamRunner / PaperEvent / SessionStore |
| Storage | SQLite + local files |
| Search | SQLite FTS5 / BM25 |
| Embedding | Pluggable provider, optional |
| Documents | Markdown, DOCX via python-docx |
| Tests | pytest |
| Config | JSON under `~/.wenbiao/` |
| Local data | `~/.wenbiao/runs/`, `~/.wenbiao/thesisx.db` |

## 3. Target Directory Structure

```text
app/
  core/
    config.py
    knowledge/
      models.py
      database.py
      store.py
      search.py
      importers.py
    literature/
      service.py
      citation_key.py
      import_bibtex.py
      import_ris.py
    theory/
      seed_library.py
      matcher.py
      parser.py
      ranker.py
    evidence/
      models.py
      service.py
      gap_analysis.py
    rag/
      chunker.py
      indexer.py
      retriever.py
      context_bundle.py
      embedding_provider.py
    pipeline/
      events.py
      models.py
      agent_team_runner.py
      session_store.py
      run_history.py
      run_diagnostics.py
    providers/
      models.py
      detector.py
      service.py
      health.py
    skills/
      loader.py
      validator.py
      context.py
    connectors/
      zotero.py
      obsidian.py
      local_files.py
    export/
      markdown_exporter.py
      docx_exporter.py
      citation_exporter.py
      evidence_report.py
  ui/
    pages/
      knowledge_base.py
      literature.py
      theory_matcher.py
      evidence_pack.py
      rag_search.py
      run_history.py
      provider_settings.py
      export_center.py
```

## 4. Layer Responsibilities

### 4.1 UI Layer

Responsible for:
- Display.
- User input.
- Calling application services.
- Showing progress and errors.

Not responsible for:
- Direct SQL.
- Direct API call.
- Direct external CLI execution.
- Direct file migration.

### 4.2 Application Service Layer

Responsible for:
- Orchestrating user workflows.
- Combining Knowledge + RAG + Runtime.
- Returning UI-ready DTOs.

### 4.3 Domain Layer

Responsible for:
- Knowledge objects.
- Literature.
- Theory.
- Evidence.
- RAG.
- Runtime.

### 4.4 Storage Layer

Responsible for:
- SQLite persistence.
- File storage.
- JSONL logs.
- Atomic writes.
- Migrations.

### 4.5 Runtime Layer

Responsible for:
- PaperRequest.
- Agent execution.
- PaperEvent stream.
- SessionStore.
- Run diagnostics.

### 4.6 Provider Layer

Responsible for:
- Local CLI discovery.
- Remote API profile.
- Agent Team contract detection.
- Health status.

## 5. Data Storage

### 5.1 SQLite

Main database:

```text
~/.wenbiao/thesisx.db
```

Stores:
- projects
- knowledge objects
- literature
- notes
- theories
- evidence
- relations
- tags
- chunks
- skills
- provider profiles

### 5.2 Run Files

```text
~/.wenbiao/runs/<session_id>/
```

Stores:
- request.json
- metadata.json
- context
- logs
- outputs
- artifacts

### 5.3 Config Files

```text
~/.wenbiao/config.json
~/.wenbiao/providers.json
~/.wenbiao/skills/
```

## 6. Runtime Flow

```text
UI creates PaperRequest
→ Provider health check
→ Knowledge context build
→ RAG context bundle
→ Skill context injection
→ AgentTeamRunner
→ PaperEvent stream
→ SessionStore writes files
→ RunHistoryReader indexes
→ RunDiagnostics reports
→ Editor insertion
```

## 7. RAG Flow

```text
KnowledgeObject
→ Chunker
→ FTS index
→ Optional embedding index
→ Retriever
→ Reranker
→ ContextBundle
→ Runtime prompt injection
```

## 8. Provider Flow

```text
ProviderService
→ LocalCLIDetector
→ RemoteAPIProfileDetector
→ AgentTeamContractDetector
→ ProviderHealthReport
→ UI / Runtime
```

## 9. Connector Flow

### Zotero

```text
Zotero API
→ ZoteroConnector
→ LiteratureItem
→ KnowledgeStore
```

### Obsidian

```text
Vault scan
→ Markdown parser
→ NoteItem
→ KnowledgeStore
```

## 10. Error Handling

All core service errors should become typed results.

Recommended error types:

```text
CONFIG_MISSING
PROVIDER_UNAVAILABLE
AGENT_CONTRACT_UNSUPPORTED
RAG_INDEX_MISSING
KNOWLEDGE_OBJECT_NOT_FOUND
IMPORT_PARSE_FAILED
EXPORT_FAILED
PERMISSION_DENIED
```

## 11. Testing Strategy

### Unit

- models
- stores
- services
- parsers
- retrievers
- diagnostics

### Integration

- create project → add knowledge → search
- literature import → citation key
- theory match → evidence pack
- RAG bundle → mock runtime
- runtime → editor insert
- export docx

### No-Network Tests

All tests must pass without API keys.

### Real API Tests

Must be opt-in only.

## 12. Security

- API key source should be env reference or OS keychain if implemented.
- Do not store raw keys in project files.
- Do not send local files unless user selects them.
- Connectors default to read-only.
- Skills are scanned for secrets.
