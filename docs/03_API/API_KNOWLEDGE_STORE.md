# API — Knowledge Store

> 定义 `KnowledgeStore` 类的完整接口、参数、返回值、数据类型。
> 对应 Vision 3.1 实现。

---

## 1. 概述

**模块路径：** `app/core/knowledge/store.py`
**数据对象：** `KnowledgeObject`（基类）+ `LiteratureItem` / `NoteItem` / `TheoryItem` / `EvidenceItem`（扩展）

**存储：** SQLite（`~/.wenbiao/thesisx.db`）
**检索：** FTS5 全文检索 + SQLite 条件过滤

---

## 2. 异常定义

```python
class KnowledgeStoreError(Exception): ...
class ObjectNotFoundError(KnowledgeStoreError): ...
class DuplicateObjectError(KnowledgeStoreError): ...
class ImportError(KnowledgeStoreError): ...
```

---

## 3. 数据类型

### 3.1 KnowledgeObject（基类）

```python
@dataclass
class KnowledgeObject:
    id: str                      # UUID
    type: Literal['literature', 'note', 'theory', 'evidence']
    title: str
    summary: str | None = None
    content: str | None = None
    source_type: str | None = None   # 'zotero' | 'obsidian' | 'local' | 'manual'
    source_uri: str | None = None   # 原始文件路径或 URL
    metadata_json: str | None = None # 扩展字段 JSON
    tags: list[str] = field(default_factory=list)
    project_ids: list[str] = field(default_factory=list)
    created_at: str                # ISO8601
    updated_at: str                # ISO8601
    version: int = 1
```

### 3.2 LiteratureItem

```python
@dataclass
class LiteratureItem:
    id: str                      # = KnowledgeObject.id
    authors: str | None = None   # "张三, 李四"
    year: str | None = None      # "2022"
    venue: str | None = None     # "Journal of ..."
    doi: str | None = None
    isbn: str | None = None
    citation_key: str | None = None  # "chen2022_digitalGovernance"
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    file_path: str | None = None  # 本地 PDF 路径
    zotero_key: str | None = None
    reading_status: Literal['unread', 'reading', 'read'] | None = None
```

### 3.3 NoteItem

```python
@dataclass
class NoteItem:
    id: str                      # = KnowledgeObject.id
    source_path: str | None = None
    vault_name: str | None = None
    note_type: Literal['fleeting', 'literature', 'permanent', 'project'] | None = None
```

### 3.4 TheoryItem

```python
@dataclass
class TheoryItem:
    id: str                      # = KnowledgeObject.id
    discipline: str               # 学科，必填
    school: str | None = None
    core_concepts: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    applicable_questions: list[str] = field(default_factory=list)
    explanatory_mechanism: str | None = None
    boundary_conditions: str | None = None
    misuse_risks: str | None = None
    writing_templates: list[str] = field(default_factory=list)
```

### 3.5 EvidenceItem

```python
@dataclass
class EvidenceItem:
    id: str                      # = KnowledgeObject.id
    claim_id: str | None = None
    subclaim_id: str | None = None
    quote: str | None = None
    evidence_type: Literal['quote', 'case', 'data', 'method', 'other'] | None = None
    source_object_id: str | None = None
    source_location: str | None = None
    page: str | None = None
    paragraph: str | None = None
    reliability: Literal['high', 'medium', 'low'] | None = None
    relevance_score: float | None = None
    support_strength: Literal['strong', 'moderate', 'weak'] | None = None
    counter_evidence: str | None = None
    gap_flag: bool = False
    gap_reason: str | None = None
    citation_key: str | None = None
    citation_status: Literal['pending', 'formatted', 'verified'] | None = None
```

### 3.6 SearchResult

```python
@dataclass
class SearchResult:
    object: KnowledgeObject
    score: float          # FTS5 BM25 评分
    highlights: dict      # {"title": ["matched <b>keyword</b>"], "content": [...]}
    matched_fields: list[str]  # ['title', 'content']
```

### 3.7 ProjectLink

```python
@dataclass
class ProjectLink:
    project_id: str
    object_id: str
    role: Literal['background', 'core', 'method', 'theory', 'evidence', 'contrast'] | None
    priority: int
    project_note: str | None = None
```

### 3.8 ImportResult

```python
@dataclass
class ImportResult:
    total: int             # 总文件数
    imported: int          # 成功数
    failed: int           # 失败数
    objects: list[KnowledgeObject]  # 成功导入的对象
    errors: list[str]     # 错误信息列表
```

### 3.9 Filters

```python
@dataclass
class KnowledgeFilters:
    type: Literal['literature', 'note', 'theory', 'evidence'] | None = None
    tags: list[str] | None = None         # 匹配任一标签
    project_id: str | None = None         # 绑定到指定项目
    source_type: str | None = None
    created_after: str | None = None     # ISO8601
    created_before: str | None = None
    limit: int = 50
    offset: int = 0
```

---

## 4. KnowledgeStore 类

```python
class KnowledgeStore:
    """
    知识库主接口。管理 KnowledgeObject 及其扩展类型的 CRUD + 检索 + 项目绑定。
    """

    def __init__(self, db_path: str | None = None):
        """
        Args:
            db_path: SQLite 数据库路径。默认 ~/.wenbiao/thesisx.db
        """
        ...

    # ─────────────────────────────────────────────────────────
    # CRUD（通用）
    # ─────────────────────────────────────────────────────────

    def create_object(
        self,
        obj: KnowledgeObject,
        literature: LiteratureItem | None = None,
        note: NoteItem | None = None,
        theory: TheoryItem | None = None,
        evidence: EvidenceItem | None = None,
    ) -> str:
        """
        创建知识对象及其扩展类型。

        Args:
            obj: 基类对象（必须含 id/type/title）
            literature/note/theory/evidence: 对应类型的扩展数据（可选）

        Returns:
            新对象的 id

        Raises:
            DuplicateObjectError: id 已存在
            ValueError: 必填字段缺失
        """
        ...

    def update_object(self, id: str, patch: dict) -> None:
        """
        部分更新 KnowledgeObject 字段。

        Args:
            id: 对象 ID
            patch: 要更新的字段字典，如 {"title": "新标题", "tags": ["tag1"]}

        Raises:
            ObjectNotFoundError: id 不存在
        """
        ...

    def update_object_full(
        self,
        id: str,
        obj: KnowledgeObject,
        literature: LiteratureItem | None = None,
        note: NoteItem | None = None,
        theory: TheoryItem | None = None,
        evidence: EvidenceItem | None = None,
    ) -> None:
        """
        全量更新（替换）知识对象及扩展。
        """
        ...

    def delete_object(self, id: str, hard: bool = False) -> None:
        """
        删除知识对象。

        Args:
            id: 对象 ID
            hard: True=硬删除，False=软删除（标记 deleted_at）

        Raises:
            ObjectNotFoundError: id 不存在
        """
        ...

    def get_object(self, id: str) -> KnowledgeObject:
        """
        获取单个 KnowledgeObject（含扩展类型数据）。

        Returns:
            KnowledgeObject（扩展数据在属性中）

        Raises:
            ObjectNotFoundError: id 不存在
        """
        ...

    def get_object_extended(
        self, id: str
    ) -> tuple[KnowledgeObject, LiteratureItem | NoteItem | TheoryItem | EvidenceItem | None]:
        """
        获取基类对象及其扩展类型。

        Returns:
            (基类对象, 扩展类型对象或 None)
        """
        ...

    # ─────────────────────────────────────────────────────────
    # 检索
    # ─────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        filters: KnowledgeFilters | None = None,
        include_extended: bool = False,
    ) -> list[SearchResult] | list[KnowledgeObject]:
        """
        全文检索。FTS5 BM25 + 可选元数据过滤。

        Args:
            query: 搜索关键词（支持空格分隔多词，OR 语义）
            filters: 可选过滤条件
            include_extended: True=返回 SearchResult（含评分+高亮），False=只返回对象

        Returns:
            匹配的 SearchResult 或 KnowledgeObject 列表，按评分降序
        """
        ...

    def list_all(
        self,
        filters: KnowledgeFilters | None = None,
        order_by: str = "updated_at",
        order: str = "DESC",
    ) -> list[KnowledgeObject]:
        """
        非检索的列表查询（不过 FTS5，按条件过滤）。

        Args:
            filters: 过滤条件
            order_by: 排序字段（updated_at / created_at / title）
            order: ASC / DESC

        Returns:
            符合条件的对象列表
        """
        ...

    def list_by_type(self, type: str, limit: int = 50, offset: int = 0) -> list[KnowledgeObject]:
        """按类型快速查询"""
        ...

    def list_by_project(
        self,
        project_id: str,
        type: str | None = None,
    ) -> list[KnowledgeObject]:
        """获取绑定到指定项目的所有知识对象"""
        ...

    # ─────────────────────────────────────────────────────────
    # 扩展类型快速访问
    # ─────────────────────────────────────────────────────────

    def get_literature(self, id: str) -> LiteratureItem | None: ...
    def get_note(self, id: str) -> NoteItem | None: ...
    def get_theory(self, id: str) -> TheoryItem | None: ...
    def get_evidence(self, id: str) -> EvidenceItem | None: ...

    def list_literature(
        self, project_id: str | None = None, reading_status: str | None = None
    ) -> list[LiteratureItem]: ...
    def list_theories(self, discipline: str | None = None) -> list[TheoryItem]: ...

    # ─────────────────────────────────────────────────────────
    # 标签
    # ─────────────────────────────────────────────────────────

    def add_tag(self, object_id: str, tag: str) -> None: ...
    def remove_tag(self, object_id: str, tag: str) -> None: ...
    def get_tags(self, object_id: str) -> list[str]: ...
    def list_all_tags(self) -> list[str]: ...

    # ─────────────────────────────────────────────────────────
    # 项目绑定
    # ─────────────────────────────────────────────────────────

    def link_to_project(
        self,
        object_id: str,
        project_id: str,
        role: str | None = None,
        priority: int = 0,
    ) -> None:
        """
        将知识对象绑定到项目。

        Raises:
            ObjectNotFoundError: object_id 不存在
        """
        ...

    def unlink_from_project(self, object_id: str, project_id: str) -> None: ...
    def update_link_role(
        self, object_id: str, project_id: str, role: str, priority: int = 0
    ) -> None: ...
    def get_project_links(self, object_id: str) -> list[ProjectLink]: ...

    # ─────────────────────────────────────────────────────────
    # 统计
    # ─────────────────────────────────────────────────────────

    def count_all(self, type: str | None = None) -> int: ...
    def get_type_distribution(self) -> dict[str, int]: ...
```

---

## 5. MarkdownImporter 类

```python
class MarkdownImporter:
    """
    导入 Markdown 文件为 KnowledgeObject。
    支持 frontmatter 解析 + 自动推断。
    """

    def __init__(self, store: KnowledgeStore): ...

    def import_file(
        self,
        path: Path,
        project_id: str | None = None,
        default_type: str = "note",
    ) -> KnowledgeObject:
        """
        导入单个 Markdown 文件。

        Args:
            path: .md 文件路径
            project_id: 可选，导入后立即绑定到项目
            default_type: 无 frontmatter 时的默认 type

        Returns:
            创建的 KnowledgeObject

        Raises:
            ImportError: 文件无法解析
        """
        ...

    def import_directory(
        self,
        dir_path: Path,
        project_id: str | None = None,
        recursive: bool = True,
        default_type: str = "note",
    ) -> ImportResult:
        """
        批量导入目录下的所有 .md 文件。
        """
        ...

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        解析 frontmatter。

        Returns:
            (frontmatter_dict, body_text)
        """
        ...

    def _infer_from_content(self, body: str, frontmatter: dict) -> dict:
        """
        无 frontmatter 或字段不全时，从内容推断字段。

        Returns:
            推断出的字段字典
        """
        ...
```

---

## 6. SQLite Schema（相关部分）

```sql
-- 基础表
CREATE TABLE knowledge_objects (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('literature','note','theory','evidence')),
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source_type TEXT,
    source_uri TEXT,
    metadata_json TEXT,
    tags_json TEXT,          -- JSON 数组
    project_ids_json TEXT,   -- JSON 数组
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    deleted_at TEXT          -- 软删除
);

-- FTS5 虚拟表
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    title, summary, content,
    content='knowledge_objects',
    content_rowid='rowid'
);

-- 扩展表（1:1 via id）
CREATE TABLE literature_items (
    id TEXT PRIMARY KEY REFERENCES knowledge_objects(id),
    authors TEXT, year TEXT, venue TEXT, doi TEXT, isbn TEXT,
    citation_key TEXT UNIQUE, abstract TEXT, keywords_json TEXT,
    file_path TEXT, zotero_key TEXT, reading_status TEXT
);

CREATE TABLE note_items (
    id TEXT PRIMARY KEY REFERENCES knowledge_objects(id),
    source_path TEXT, vault_name TEXT, note_type TEXT,
    linked_literature_json TEXT, linked_theory_json TEXT, linked_evidence_json TEXT
);

CREATE TABLE theory_items (
    id TEXT PRIMARY KEY REFERENCES knowledge_objects(id),
    discipline TEXT NOT NULL, school TEXT,
    core_concepts_json TEXT, assumptions_json TEXT,
    applicable_questions_json TEXT, explanatory_mechanism TEXT,
    boundary_conditions TEXT, misuse_risks TEXT,
    classic_literature_json TEXT, related_theory_json TEXT,
    writing_templates_json TEXT
);

CREATE TABLE evidence_items (
    id TEXT PRIMARY KEY REFERENCES knowledge_objects(id),
    claim_id TEXT, subclaim_id TEXT, quote TEXT, evidence_type TEXT,
    source_object_id TEXT, source_location TEXT, page TEXT, paragraph TEXT,
    reliability TEXT, relevance_score REAL, support_strength TEXT,
    counter_evidence TEXT, gap_flag INTEGER DEFAULT 0, gap_reason TEXT,
    linked_section_id TEXT, linked_paragraph_id TEXT,
    citation_key TEXT, citation_status TEXT
);

-- 项目绑定
CREATE TABLE project_knowledge_links (
    project_id TEXT NOT NULL,
    object_id TEXT NOT NULL,
    role TEXT, priority INTEGER DEFAULT 0, project_note TEXT,
    PRIMARY KEY (project_id, object_id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (object_id) REFERENCES knowledge_objects(id)
);

-- 索引
CREATE INDEX idx_ko_type ON knowledge_objects(type);
CREATE INDEX idx_ko_updated ON knowledge_objects(updated_at DESC);
CREATE INDEX idx_lit_citation ON literature_items(citation_key);
CREATE INDEX idx_pkl_project ON project_knowledge_links(project_id);
```

---

## 7. 分阶段实现

### Phase 1（3.1 MVP）

**实现：**
- `create_object` / `update_object` / `delete_object` / `get_object`
- `search`（FTS5）
- `list_all` / `list_by_type` / `list_by_project`
- `link_to_project` / `unlink_from_project` / `get_project_links`
- `MarkdownImporter.import_file` / `import_directory`
- `add_tag` / `remove_tag` / `get_tags`

**不实现：** 扩展类型快速访问（`get_literature` 等）、统计方法

### Phase 2（3.2+）

- `get_object_extended` / `get_literature` 等
- `LiteratureItem` 完整字段（authors/year/venue/citation_key）
- `TheoryItem` 完整字段
- `EvidenceItem` 完整字段

### Phase 3（后续）

- `import_bibtex`（BibTeXImporter）
- 向量 Embedding 索引

---

*本文档是 KnowledgeStore 接口实现的技术基准。*
*实现时以 TECHNICAL_ARCHITECTURE.md 和 DATA_MODEL.md 为准。*