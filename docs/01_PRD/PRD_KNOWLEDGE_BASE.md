# PRD — Knowledge Base

> 定义 ThesisX Knowledge Base 模块的产品需求。对应 Vision 3.1。

---

## 1. 基本信息

| 字段 | 内容 |
|------|------|
| 模块名称 | Knowledge Base（知识库） |
| PRD 编号 | PRD-KB-001 |
| 版本 | 1.0 |
| 状态 | 3.1 实现 |
| 负责人 | Agent（按 Vision 3.1 执行） |
| 最后更新 | 2026-05-03 |

---

## 2. 背景与问题

ThesisX 的核心差异化在于"知识驱动"：AI 写作必须基于用户真实文献、笔记、理论、证据，而不是自由发挥。

当前（v2.x）没有 Knowledge Base 模块。用户的文献、笔记散落在 Zotero、Obsidian、文件夹里，AI 写作无法利用这些材料，导致：
- AI 容易胡编文献和来源
- 用户无法追溯 AI 生成内容的依据
- 写作和知识管理割裂

**Knowledge Base 要解决的核心问题：** 建立 ThesisX 的研究资产中枢，统一管理文献、笔记、理论、证据、概念、方法、数据材料，并支持项目绑定、标签、关系、检索、RAG 调用。

---

## 3. 目标

### 3.1 最终目标（4.0）

用户能：
- 从 Obsidian / Zotero / 本地文件夹导入文献/笔记/理论/证据
- 在统一界面查看/搜索/管理所有知识资产
- 给知识对象打标签、分类、项目绑定
- 查看知识对象之间的关系（引用/支撑/反驳）
- RAG 检索知识库，检索结果注入 AI 写作
- 任何 AI 生成的内容都能追溯到来源

### 3.2 MVP 目标（3.1 最小闭环）

3.1 实现最小可用集：
- 创建/查看/删除 KnowledgeObject（不区分类型都可以）
- 导入 Markdown 文件（带/不带 frontmatter）
- 按类型筛选（Literature / Note / Theory / Evidence）
- 全文检索（FTS5）
- 项目绑定（一个对象可绑定多个项目）

---

## 4. 非目标

- ~~3.1 不做 PDF 内容解析~~（只解析元数据）
- ~~3.1 不做 Zotero 导入~~（留给 3.7）
- ~~3.1 不做 Obsidian 连接器~~（留给 3.7）
- ~~3.1 不做 RAG 检索~~（留给 3.5）
- ~~3.1 不做复杂关系图~~（留给后续版本）

---

## 5. 用户角色

| 角色 | 描述 |
|------|------|
| 研究生 | 有明确研究问题，需要积累和管理文献/笔记 |
| 独立研究者 | 需要长期积累研究资产，支持多项目复用 |
| 论文写作者 | 需要在写作时快速检索和引用知识库 |

---

## 6. 核心功能

### 6.1 知识对象管理

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 创建知识对象 | 手动创建 Literature/Note/Theory/Evidence，手动填字段 | P0 |
| 查看知识对象 | 点击对象查看详情（标题/摘要/来源/标签/项目绑定） | P0 |
| 编辑知识对象 | 修改标题/摘要/标签/项目绑定 | P0 |
| 删除知识对象 | 删除对象（软删除或硬删除） | P0 |
| 列表展示 | 按类型筛选，分页，支持排序 | P0 |

### 6.2 导入功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 导入 Markdown | 解析 frontmatter 或自动推断，创建 KnowledgeObject | P0 |
| 导入 BibTeX | 解析 .bib 文件，创建 LiteratureItem | P1 |
| 批量导入 | 扫描文件夹，批量导入 .md 文件 | P2 |

### 6.3 检索功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 全文检索 | FTS5 搜索标题/摘要/内容 | P0 |
| 类型筛选 | 只看 Literature / Note / Theory / Evidence | P0 |
| 标签筛选 | 按标签筛选 | P0 |
| 项目筛选 | 只看某个项目绑定的对象 | P0 |
| 组合筛选 | 类型+标签+项目组合 | P1 |

### 6.4 关系管理

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 对象关系 | 创建对象间关系（引用/支撑/反驳/相关） | P1 |
| 关系可视化 | 显示对象的关系图 | P2 |
| 来源追溯 | 查看对象被哪些其他对象引用 | P1 |

### 6.5 项目绑定

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 绑定到项目 | 将对象绑定到项目，指定角色（background/core/method/theory/evidence） | P0 |
| 项目视图 | 按项目查看所有绑定的知识对象 | P0 |
| 批量绑定 | 选中多个对象批量绑定到项目 | P1 |

---

## 7. 数据对象定义

### 7.1 KnowledgeObject（基类）

```python
@dataclass
class KnowledgeObject:
    id: str                    # UUID
    type: str                  # 'literature' | 'note' | 'theory' | 'evidence'
    title: str
    summary: str | None
    content: str | None       # Markdown 原文
    source_type: str | None   # 'zotero' | 'obsidian' | 'local' | 'manual'
    source_uri: str | None    # 原始文件路径
    metadata_json: str | None # 扩展字段
    tags: list[str]           # 标签列表
    project_ids: list[str]    # 绑定的项目 ID 列表
    sync_status: str          # 'synced' | 'pending' | 'conflict' | 'readonly'
    external_source: str | None # 'zotero' | 'obsidian' | 'manual'
    external_id: str | None
    external_uri: str | None
    external_updated_at: str | None
    external_hash: str | None
    verified_status: str      # 'unverified' | 'partially_verified' | 'verified'
    usable_for_writing: bool  # 是否可用于写作
    usable_for_rag: bool     # 是否可用于 RAG
    ai_generated: bool       # 是否 AI 生成
    human_verified: bool     # 是否人工验证
    relevance_score: float | None  # 相关性分数
    confidence_score: float | None  # 置信度分数
    created_at: str           # ISO8601
    updated_at: str           # ISO8601
    version: int              # 版本号
```

### 7.2 LiteratureItem（扩展）

```python
@dataclass
class LiteratureItem:
    id: str                    # = KnowledgeObject.id
    authors: str | None        # "张三, 李四"
    year: str | None           # "2022"
    venue: str | None         # "Journal of ..."
    doi: str | None
    isbn: str | None
    citation_key: str | None  # "chen2022_digitalGovernance"
    abstract: str | None
    keywords: list[str]        # ["社区治理", "数字治理"]
    file_path: str | None      # 本地 PDF 路径
    zotero_key: str | None
    reading_status: str | None # 'unread' | 'reading' | 'read'
```

### 7.3 NoteItem（扩展）

```python
@dataclass
class NoteItem:
    id: str
    source_path: str | None    # Obsidian vault 内路径
    vault_name: str | None
    note_type: str | None     # 'fleeting' | 'literature' | 'permanent' | 'project'
```

### 7.4 TheoryItem（扩展）

```python
@dataclass
class TheoryItem:
    id: str
    discipline: str           # 学科
    school: str | None        # 理论流派
    core_concepts: list[str]
    assumptions: list[str]
    applicable_questions: list[str]
    explanatory_mechanism: str | None
    boundary_conditions: str | None
    misuse_risks: str | None
    writing_templates: list[str]
```

### 7.5 EvidenceItem（扩展）

```python
@dataclass
class EvidenceItem:
    id: str
    claim_id: str | None      # 关联的 claim（后接 Evidence Pack）
    quote: str | None          # 直接引文
    evidence_type: str | None # 'quote' | 'case' | 'data' | 'method'
    source_object_id: str | None
    source_location: str | None # "p.42"
    page: str | None
    reliability: str | None  # 'high' | 'medium' | 'low'
    gap_flag: bool = False
```

### 7.6 Claim（论点）

Evidence Pack 的顶层结构，支持嵌套。

```python
@dataclass
class Claim:
    id: str                    # UUID
    project_id: str            # 所属项目
    parent_claim_id: str | None  # 父论点（支持嵌套）
    text: str                  # 论点文本
    claim_type: str           # 'core' | 'sub' | 'counter' | 'section'
    priority: int              # 优先级
    created_at: str            # ISO8601
```

---

## 8. 技术实现

### 8.1 存储

- **SQLite** 作为主库（`~/.wenbiao/thesisx.db`）
- **FTS5** 虚拟表用于全文检索
- **JSON** 用于 metadata_json 等扩展字段
- **文件系统** 用于存储导入的源文件（`~/.wenbiao/knowledge/imports/`）

### 8.2 核心模块

```
app/core/knowledge/
├── __init__.py
├── models.py           # KnowledgeObject + 四类扩展 dataclass
├── store.py            # KnowledgeStore（SQLite CRUD + FTS5）
├── importers/
│   ├── __init__.py
│   ├── base.py        # Importer 基类
│   └── markdown.py    # MarkdownImporter
├── search.py          # FTS5 搜索
└── links.py           # 项目绑定、对象关系
```

### 8.3 核心 API

```python
class KnowledgeStore:
    def create_object(item: KnowledgeObject) -> str: ...
    def update_object(id: str, patch: dict) -> None: ...
    def delete_object(id: str) -> None: ...
    def get_object(id: str) -> KnowledgeObject: ...
    def search(query: str, filters: dict) -> list[SearchResult]: ...
    def link_to_project(object_id: str, project_id: str, role: str) -> None: ...
    def unlink_from_project(object_id: str, project_id: str) -> None: ...
    def list_by_project(project_id: str, type: str | None) -> list[KnowledgeObject]: ...
    def list_all(type: str | None, tag: str | None, limit: int, offset: int) -> list[KnowledgeObject]: ...

class MarkdownImporter:
    def import_file(path: Path, project_id: str | None) -> KnowledgeObject: ...
    def import_directory(dir: Path, project_id: str | None) -> ImportResult: ...
```

---

## 9. 分阶段实现路径

### Phase 1（3.1 MVP — 最小闭环）

**目标：** Knowledge Base 可运行，能导入 Markdown，能查看/搜索/删除

**实现：**
- [ ] `knowledge_objects` + 四类扩展表（SQLite）
- [ ] FTS5 虚拟表 + 同步触发器
- [ ] `KnowledgeStore.create_object / get_object / update_object / delete_object`
- [ ] `KnowledgeStore.search`（FTS5 全文检索）
- [ ] `MarkdownImporter`（frontmatter 解析 + 自动推断）
- [ ] `KnowledgeBasePage`（列表 + 详情 + 导入按钮）
- [ ] 项目绑定（`project_knowledge_links`）

**不实现：** Zotero、Obsidian、RAG、关系图

### Phase 2（3.2+ 完善）

**目标：** 完善 Literature、Note、Theory、Evidence 专用字段

**实现：**
- [ ] Literature 专用字段（authors/year/venue/doi/citation_key）
- [ ] Theory 专用字段（discipline/core_concepts/boundary_conditions）
- [ ] Evidence 专用字段（quote/reliability/gap_flag）
- [ ] BibTeX 导入
- [ ] 标签管理
- [ ] 对象关系（引用/支撑/反驳）

### Phase 3（后续版本）

- [ ] Zotero 连接器（3.7）
- [ ] Obsidian 连接器（3.7）
- [ ] RAG 检索（3.5）
- [ ] 关系可视化
- [ ] 向量 Embedding 索引

---

## 10. 禁止事项

- **禁止** 导入时修改用户原始文件
- **禁止** 在 Knowledge Base 中自动删除 Zotero/Obsidian 原始数据
- **禁止** 把 preview 功能标为已接通
- **禁止** 使用 JSON 作为主数据源（只用 SQLite）
- **禁止** 在 3.1 实现 RAG（留到 3.5）

---

## 11. 验收标准

### 3.1 MVP 验收

| # | 标准 | 验证方式 |
|---|------|---------|
| KB-01 | 用户可手动创建 KnowledgeObject | 创建 → 列表显示 → 详情正确 |
| KB-02 | Markdown 文件可导入，frontmatter 正确解析 | 导入测试文件 → 字段正确提取 |
| KB-03 | 无 frontmatter 的 Markdown 导入后字段合理推断 | 导入无 frontmatter 文件 → 有合理默认值 |
| KB-04 | FTS5 全文检索可命中标题/摘要/内容 | 插入对象 → 搜索关键词 → 结果正确 |
| KB-05 | 按类型筛选正确 | 创建 4 种类型对象 → 分别筛选 → 结果正确 |
| KB-06 | 对象可绑定到项目 | 绑定 → 查看项目视图 → 正确显示 |
| KB-07 | KnowledgeBasePage 显示真实数据（不是 mock） | 导入对象 → 页面显示 → 不是 coming soon |
| KB-08 | 删除对象正确 | 删除 → 列表不再显示 → 数据库无记录 |
| KB-09 | 测试覆盖率 ≥ 80% | `pytest tests/unit/test_knowledge_store.py` |

---

## 12. 与其他模块的关系

| 模块 | 关系 |
|------|------|
| Literature Management（3.2） | 扩展 literature_items 专用字段 |
| Theory Matcher（3.3） | TheoryItem 是 Theory Matcher 的数据基础 |
| Evidence Pack（3.4） | EvidenceItem 是 Evidence Pack 的数据基础 |
| RAG（3.5） | Knowledge Base 是 RAG 的数据来源 |
| Zotero/Obsidian（3.7） | 连接器导入数据到 Knowledge Base |
| Main Editor（3.6） | Editor 中可引用 Knowledge Base 对象 |

---

*本文档是 Knowledge Base 模块的产品需求基准。*
*技术实现以 TECHNICAL_ARCHITECTURE.md 和 DATA_MODEL.md 为准。*
*产品决策以 PRODUCT_DECISIONS.md 为准。*