<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# Frontend Interface Mapping

## 1. Purpose

This document maps each frontend page to:

- user goal
- visible modules
- backend service
- data objects
- API calls
- real/preview status
- implementation priority

## 2. Global UI Rules

1. Do not continue SVG pixel polishing.
2. Keep existing design token system.
3. Preview functions must be labeled.
4. Disabled buttons must not imply real execution.
5. Real pages must show errors and empty states.
6. Main Editor must not be broken.
7. AgentTeamDialog must not be structurally rewritten unless required.

## 3. Page Mapping Table

| Page | Target File | Real Status | Backend Dependency |
|---|---|---|---|
| Workspace Home | app/ui/pages/workspace_home.py | Partial | ProjectService, RunHistory, ProviderHealth |
| Main Editor | existing editor files | Real | EditorService, ExportService |
| AI Draft Assistant | app/ui/agent_team_dialog.py | Partial real | AgentTeamRunner, ProviderService |
| Knowledge Base | app/ui/pages/knowledge_base.py | To implement | KnowledgeStore |
| Literature Management | app/ui/pages/literature.py | To implement | LiteratureService |
| Theory Matcher | app/ui/pages/theory_matcher.py | To implement | TheoryMatcher |
| Evidence Pack | app/ui/pages/evidence_pack.py | To implement | EvidencePackService |
| RAG Search | app/ui/pages/rag_search.py | To implement | RagService |
| Run History | app/ui/pages/run_history.py | To implement | RunHistoryReader |
| Runtime Diagnostics | app/ui/pages/runtime_diagnostics.py | To implement | RunDiagnostics |
| Provider Settings | app/ui/pages/provider_settings.py | Partial | ProviderService |
| Skill Library | app/ui/pages/skill_library.py | Preview | SkillLoader later |
| Export Center | app/ui/pages/export_center.py | To implement | ExportService |
| Zotero Connector | app/ui/pages/zotero_connector.py | To implement | ZoteroConnector |
| Obsidian Connector | app/ui/pages/obsidian_connector.py | To implement | ObsidianConnector |

## 4. Workspace Home

### Visible Components

- Project summary card.
- Research question card.
- Knowledge status cards.
- Recent runs list.
- Provider health panel.
- Next action suggestions.

### Interfaces

```python
ProjectService.get_current_project()
KnowledgeStore.get_project_summary(project_id)
RunHistoryReader.list_runs(limit=5)
ProviderService.generate_provider_health_report()
EvidencePackService.get_gap_summary(project_id)
```

### Empty States

- No project: show “创建项目”
- No knowledge: show “导入文献 / 笔记”
- No provider: show “配置 Provider”
- No run: show “运行一次 Mock 生成”

## 5. Main Editor

### Visible Components

- Outline panel.
- Editor body.
- Formatting toolbar.
- Preview widget.
- AI action panel.
- Evidence/theory side panel.

### Interfaces

```python
EditorService.get_document(project_id)
EditorService.save_document(project_id, content)
EditorService.insert_content(position, content)
EditorService.replace_selection(range, content)
EditorService.create_snapshot(reason)
EditorService.rollback(snapshot_id)
```

### AI Interfaces

```python
RagService.build_context_bundle(project_id, selected_text)
AgentTeamRunner.run(request)
EditorOperationService.apply_ai_patch()
```

## 6. AI Draft Assistant

### Visible Components

- Research question input.
- Provider selector.
- Context selector.
- Mock / Real switch.
- Budget field.
- Progress timeline.
- Event log.
- Completion panel.
- Diagnostics button.

### Interfaces

```python
ProviderService.validate_runtime_config()
AgentTeamRunner.run(request)
SessionStore.get_session(session_id)
RunDiagnostics.diagnose_run(session_id)
EditorService.insert_generated_paper(session_id)
```

## 7. Knowledge Base Page

### Visible Components

- Type filters.
- Search bar.
- Object table.
- Object detail panel.
- Relation panel.
- Project binding.

### Interfaces

```python
KnowledgeStore.search(query, filters)
KnowledgeStore.get_object(id)
KnowledgeStore.create_object(data)
KnowledgeStore.update_object(id, patch)
KnowledgeStore.bind_to_project(project_id, object_id)
KnowledgeStore.get_relations(object_id)
```

## 8. Literature Management

### Visible Components

- Collection sidebar.
- Literature table.
- Citation key column.
- Reading status.
- Abstract panel.
- Notes panel.
- Evidence extraction button.

### Interfaces

```python
LiteratureService.import_bibtex(path)
LiteratureService.import_ris(path)
LiteratureService.add_manual(data)
LiteratureService.generate_citation_key(item)
LiteratureService.bind_to_project(project_id, literature_id)
```

## 9. Theory Matcher

### Visible Components

- Research question input.
- Discipline filter.
- Theory recommendation cards.
- Fit score.
- Misuse risk.
- Writing framework preview.

### Interfaces

```python
TheoryMatcher.parse_research_question(text)
TheoryMatcher.match(project_id, question)
TheoryMatcher.explain(theory_id, question)
TheoryMatcher.save_to_project(project_id, theory_id)
```

## 10. Evidence Pack

### Visible Components

- Claims list.
- Evidence table.
- Source column.
- Support strength.
- Gap analysis panel.

### Interfaces

```python
EvidencePackService.create_claim(project_id, text)
EvidencePackService.add_evidence(data)
EvidencePackService.link_evidence(claim_id, evidence_id)
EvidencePackService.analyze_gaps(project_id)
```

## 11. RAG Search

### Visible Components

- Query input.
- Filters.
- Result list.
- Source badges.
- Relevance score.
- Add to context button.
- Context Bundle preview.

### Interfaces

```python
RagService.search(project_id, query, filters)
RagService.build_context_bundle(project_id, query, selected_ids)
```

## 12. Run History

### Visible Components

- Run list.
- Metadata.
- paper.md preview.
- events viewer.
- messages viewer.
- diagnostics.

### Interfaces

```python
RunHistoryReader.list_runs()
RunHistoryReader.get_run(session_id)
RunDiagnostics.diagnose_run(session_id)
```

## 13. Provider Settings

### Visible Components

- Local CLI list.
- Remote API profiles.
- Agent Team candidates.
- Health report.
- Config priority explanation.

### Interfaces

```python
ProviderService.discover_local_clis()
ProviderService.detect_remote_api_config()
ProviderService.detect_agent_team_paths()
ProviderService.save_provider_profile()
ProviderService.generate_provider_health_report()
```

## 14. Skill Library

### Visible Components

- Skill categories.
- Skill cards.
- Skill detail.
- Input/output schema.
- Risk warning.
- Project binding.

### Interfaces

```python
SkillLoader.scan_skills()
SkillLoader.validate_skill(path)
SkillService.bind_skill_to_project(project_id, skill_id)
SkillService.build_selected_skills_context(project_id)
```

## 15. Export Center

### Visible Components

- Format selection.
- Template selection.
- Citation style.
- Export preview.
- Export logs.

### Interfaces

```python
ExportService.export_docx(project_id, template_id)
ExportService.export_markdown(project_id)
ExportService.export_bibtex(project_id)
ExportService.export_evidence_report(project_id)
ExportService.export_run_archive(session_id)
```

## 16. Real vs Preview Rules

| Page | Must be Real for Beta? | If Not Real |
|---|---:|---|
| Workspace Home | Yes | Show missing setup states. |
| Main Editor | Yes | Cannot be preview. |
| AI Draft Assistant | Yes | Mock must work; Real must fail clearly. |
| Knowledge Base | Yes | Cannot remain preview. |
| Literature | Yes | Cannot remain preview. |
| Theory Matcher | Yes | Minimal real matcher needed. |
| Evidence Pack | Yes | Minimal real gap analysis needed. |
| RAG Search | Yes | At least FTS real search. |
| Run History | Yes | Read-only real. |
| Provider Settings | Yes | Real detection. |
| Skill Library | Partial | Local skills real; marketplace preview. |
| Collaboration | No | Preview acceptable. |
| Version History | Partial | Editor snapshots later; Git preview. |
