<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# API — Knowledge Store

## 1. Scope

This document defines internal Python APIs for ThesisX Knowledge Base.

These are not HTTP APIs. They are local service interfaces for the PyQt desktop application.

## 2. Core Classes

Recommended module:

```text
app/core/knowledge/
  models.py
  database.py
  store.py
  search.py
  importers.py
```

## 3. Data Models

### 3.1 KnowledgeObject

```python
@dataclass
class KnowledgeObject:
    id: str
    type: str
    title: str
    summary: str | None
    content: str | None
    source_type: str | None
    source_uri: str | None
    created_at: str
    updated_at: str
    metadata: dict[str, Any]
```

### 3.2 LiteratureItem

```python
@dataclass
class LiteratureItem:
    id: str
    object_id: str
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    doi: str | None
    isbn: str | None
    citation_key: str
    abstract: str | None
    keywords: list[str]
    file_path: str | None
    zotero_key: str | None
    reading_status: str
```

### 3.3 NoteItem

```python
@dataclass
class NoteItem:
    id: str
    object_id: str
    title: str
    content: str
    source_path: str | None
    vault_name: str | None
    note_type: str
    frontmatter: dict[str, Any]
    backlinks: list[str]
    tags: list[str]
```

### 3.4 TheoryItem

```python
@dataclass
class TheoryItem:
    id: str
    object_id: str
    name: str
    discipline: str
    core_concepts: list[str]
    assumptions: str
    applicable_questions: list[str]
    explanatory_mechanism: str
    boundary_conditions: str
    misuse_risks: str
    classic_sources: list[str]
    writing_templates: list[str]
```

### 3.5 EvidenceItem

```python
@dataclass
class EvidenceItem:
    id: str
    object_id: str
    project_id: str | None
    claim_id: str | None
    content: str
    quote: str | None
    evidence_type: str
    source_object_id: str | None
    source_title: str | None
    source_location: str | None
    page: str | None
    reliability: int
    relevance_score: float | None
    support_strength: str
    counter_evidence: bool
    gap_flag: bool
    gap_reason: str | None
    citation_key: str | None
    citation_status: str
```

## 4. Store Interface

### 4.1 Initialize

```python
store = KnowledgeStore(db_path=Path("~/.wenbiao/thesisx.db").expanduser())
store.initialize()
```

Behavior:
- Creates DB if missing.
- Applies migrations.
- Creates FTS tables.
- Does not require network.

### 4.2 Create Object

```python
object_id = store.create_object(
    type="note",
    title="数字治理笔记",
    summary="关于社区数字治理的阅读摘要",
    content="...",
    source_type="manual",
    source_uri=None,
    metadata={}
)
```

Returns:
- object_id

Errors:
- INVALID_OBJECT_TYPE
- EMPTY_TITLE
- DB_WRITE_FAILED

### 4.3 Get Object

```python
obj = store.get_object(object_id)
```

Returns:
- KnowledgeObject | None

### 4.4 Update Object

```python
store.update_object(object_id, {
    "summary": "new summary",
    "content": "new content"
})
```

Rules:
- Only allowed fields can be patched.
- updated_at changes.

### 4.5 Delete Object

```python
store.delete_object(object_id, soft=True)
```

Default:
- soft delete if implemented.
- Hard delete only with explicit confirmation.

### 4.6 Search

```python
results = store.search(
    query="数字治理 老年人",
    filters={
        "types": ["literature", "note"],
        "project_id": "project_001",
        "tags": ["数字治理"]
    },
    limit=20
)
```

Returns:

```python
@dataclass
class SearchResult:
    object_id: str
    type: str
    title: str
    snippet: str
    score: float
    source_type: str | None
```

### 4.7 Bind to Project

```python
store.bind_to_project(project_id, object_id, role="core")
```

Roles:
- core
- supporting
- theory
- evidence
- background
- excluded

### 4.8 Relations

```python
store.create_relation(source_id, target_id, relation_type="supports")
store.get_relations(object_id)
```

Relation types:
- supports
- contradicts
- cites
- defines
- uses_theory
- extracted_from
- generated_by_run

## 5. Specialized APIs

### 5.1 Literature

```python
store.create_literature_item(data)
store.get_literature_item(literature_id)
store.find_by_citation_key(citation_key)
store.list_project_literature(project_id)
```

### 5.2 Notes

```python
store.create_note_item(data)
store.import_markdown_note(path)
store.list_project_notes(project_id)
```

### 5.3 Theories

```python
store.create_theory_item(data)
store.list_theories(discipline=None)
store.get_theory(theory_id)
```

### 5.4 Evidence

```python
store.create_evidence_item(data)
store.link_evidence_to_claim(evidence_id, claim_id)
store.list_claim_evidence(claim_id)
store.list_project_evidence(project_id)
```

## 6. RAG API

### 6.1 Get Candidates

```python
candidates = store.get_rag_candidates(
    project_id="project_001",
    query="老年人数字参与困境",
    types=["literature", "note", "theory", "evidence"],
    limit=30
)
```

### 6.2 Get Chunks

```python
chunks = store.get_object_chunks(object_id)
```

### 6.3 Mark Indexed

```python
store.mark_indexed(object_id, index_type="fts")
```

## 7. Import APIs

### 7.1 Markdown

```python
ImportResult = store.import_markdown(
    path=Path("/path/to/note.md"),
    project_id="project_001",
    parse_frontmatter=True
)
```

### 7.2 BibTeX

```python
ImportResult = store.import_bibtex(
    path=Path("/path/to/references.bib"),
    project_id="project_001"
)
```

### 7.3 RIS

```python
ImportResult = store.import_ris(
    path=Path("/path/to/references.ris"),
    project_id="project_001"
)
```

## 8. Error Model

```python
@dataclass
class KnowledgeError:
    code: str
    message: str
    details: dict[str, Any]
```

Codes:
- DB_INIT_FAILED
- DB_WRITE_FAILED
- DB_READ_FAILED
- INVALID_OBJECT_TYPE
- IMPORT_PARSE_FAILED
- DUPLICATE_CITATION_KEY
- OBJECT_NOT_FOUND
- PROJECT_NOT_FOUND
- RELATION_INVALID

## 9. Testing Requirements

Tests:
- initialize empty DB
- migration idempotent
- create each object type
- search FTS
- bind project
- relation create
- import markdown
- import bibtex sample
- corrupted metadata JSON handled
- delete object does not orphan relation silently

## 10. Acceptance

Knowledge Store API is complete when a developer can build UI and RAG on top of it without directly writing SQL from UI.
