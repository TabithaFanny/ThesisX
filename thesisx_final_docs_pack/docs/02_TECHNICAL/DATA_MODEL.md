<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# ThesisX Data Model

## 1. Storage Decision

Final product should use SQLite as the main structured store.

Reason:
- Queryable.
- Supports FTS5.
- Supports joins.
- Better than scattered JSON.
- Still local-first.
- Easy to backup.

JSON remains appropriate for:
- run session files
- diagnostics reports
- config
- provider profiles
- imported raw metadata cache

## 2. Main Database

Path:

```text
~/.wenbiao/thesisx.db
```

## 3. Core Entities

### 3.1 Project

Fields:
- id
- name
- research_question
- description
- discipline
- status
- created_at
- updated_at
- metadata_json

### 3.2 KnowledgeObject

Unified base object.

Fields:
- id
- type
- title
- summary
- content
- source_type
- source_uri
- created_at
- updated_at
- metadata_json

Types:
- literature
- note
- theory
- evidence
- dataset
- claim

### 3.3 LiteratureItem

Fields:
- id
- object_id
- title
- authors
- year
- venue
- doi
- isbn
- citation_key
- abstract
- keywords
- file_path
- zotero_key
- reading_status
- project_notes
- created_at
- updated_at

### 3.4 NoteItem

Fields:
- id
- object_id
- title
- content
- source_path
- vault_name
- note_type
- frontmatter_json
- backlinks_json
- tags_json
- created_at
- updated_at

### 3.5 TheoryItem

Fields:
- id
- object_id
- name
- discipline
- school
- core_concepts
- assumptions
- applicable_questions
- explanatory_mechanism
- boundary_conditions
- misuse_risks
- classic_sources
- writing_templates
- created_at
- updated_at

### 3.6 EvidenceItem

Fields:
- id
- object_id
- project_id
- claim_id
- content
- quote
- evidence_type
- source_object_id
- source_title
- source_location
- page
- reliability
- relevance_score
- support_strength
- counter_evidence
- gap_flag
- gap_reason
- citation_key
- citation_status
- created_at
- updated_at

### 3.7 Claim

Fields:
- id
- project_id
- text
- claim_type
- section
- status
- created_at
- updated_at

### 3.8 Chunk

Fields:
- id
- object_id
- project_id
- chunk_text
- chunk_type
- source_location
- token_count
- embedding_provider
- embedding_id
- created_at
- updated_at

## 4. SQL Schema Draft

```sql
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  research_question TEXT,
  description TEXT,
  discipline TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_objects (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT,
  content TEXT,
  source_type TEXT,
  source_uri TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS project_knowledge_links (
  project_id TEXT NOT NULL,
  object_id TEXT NOT NULL,
  role TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (project_id, object_id)
);

CREATE TABLE IF NOT EXISTS literature_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  title TEXT NOT NULL,
  authors_json TEXT,
  year INTEGER,
  venue TEXT,
  doi TEXT,
  isbn TEXT,
  citation_key TEXT UNIQUE,
  abstract TEXT,
  keywords_json TEXT,
  file_path TEXT,
  zotero_key TEXT,
  reading_status TEXT,
  project_notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS note_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  source_path TEXT,
  vault_name TEXT,
  note_type TEXT,
  frontmatter_json TEXT,
  backlinks_json TEXT,
  tags_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS theory_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  name TEXT NOT NULL,
  discipline TEXT,
  school TEXT,
  core_concepts_json TEXT,
  assumptions TEXT,
  applicable_questions_json TEXT,
  explanatory_mechanism TEXT,
  boundary_conditions TEXT,
  misuse_risks TEXT,
  classic_sources_json TEXT,
  writing_templates_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  text TEXT NOT NULL,
  claim_type TEXT,
  section TEXT,
  status TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_items (
  id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  project_id TEXT,
  claim_id TEXT,
  content TEXT NOT NULL,
  quote TEXT,
  evidence_type TEXT,
  source_object_id TEXT,
  source_title TEXT,
  source_location TEXT,
  page TEXT,
  reliability INTEGER,
  relevance_score REAL,
  support_strength TEXT,
  counter_evidence INTEGER DEFAULT 0,
  gap_flag INTEGER DEFAULT 0,
  gap_reason TEXT,
  citation_key TEXT,
  citation_status TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  color TEXT
);

CREATE TABLE IF NOT EXISTS object_tags (
  object_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  PRIMARY KEY (object_id, tag_id)
);

CREATE TABLE IF NOT EXISTS object_relations (
  id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL,
  target_object_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  metadata_json TEXT,
  created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
USING fts5(object_id, title, summary, content);
```

## 5. Object Relation Types

Recommended:
- cites
- supports
- contradicts
- extends
- defines
- uses_theory
- is_note_of
- extracted_from
- belongs_to_project
- generated_by_run

## 6. JSON Field Rules

When using JSON fields:
- Always store valid JSON.
- Use `[]` for lists.
- Use `{}` for objects.
- Never store Python repr.
- Add migration if shape changes.

## 7. Migration Strategy

Create:

```text
app/core/knowledge/migrations/
```

Migration table:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
```

Migration rules:
- Migrations are idempotent.
- Never destroy user data.
- Always backup before destructive change.
- No migration should require network.

## 8. Indexing

Minimum:
- FTS5 for title, summary, content.
- Index on project_id.
- Index on type.
- Index on citation_key.
- Index on source_object_id.

## 9. Acceptance Tests

Required tests:
- create project
- create four object types
- bind object to project
- search text
- tag object
- create relation
- corrupted JSON does not crash
- missing DB auto-initializes
- migration idempotent
