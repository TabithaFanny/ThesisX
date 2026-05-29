# Data Model — ThesisX 数据库设计文档

> 定义 ThesisX SQLite 数据库所有表的字段、类型、索引、约束、外键关系。
> 以最终产品视角设计，v3.1 实现最小子集，后续版本扩展。

---

## 1. 表总览及关系

```
projects
  └── project_knowledge_links ← 多对多（项目 ←→ 知识对象）

knowledge_objects（基类）
  ├── literature_items（1:1 扩展）
  ├── note_items（1:1 扩展）
  ├── theory_items（1:1 扩展）
  └── evidence_items（1:1 扩展）
        └── claim_evidence_links（多对多 via claims）

object_relations（对象间关系：引用/链接）
object_tags（多对多：对象 ←→ 标签）
citations（引用链）

skills
  └── skill_bindings（多对多：skill ←→ project/task_type）

runs（运行记录）
  └── 无外键（独立历史）

import_jobs（导入任务）
embedding_chunks（向量分块）
```

---

## 2. projects

论文项目。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| name | TEXT | NOT NULL | 项目名称 |
| research_question | TEXT | | 研究问题/方向 |
| discipline | TEXT | | 学科领域 |
| created_at | TEXT | NOT NULL | ISO8601 |
| updated_at | TEXT | NOT NULL | ISO8601 |

**索引：** `idx_projects_name`

---

## 3. knowledge_objects

统一知识对象基类。所有文献/笔记/理论/证据都有这条记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| type | TEXT | NOT NULL, CHECK(type IN ('literature','note','theory','evidence')) | 对象类型 |
| title | TEXT | NOT NULL | 标题 |
| summary | TEXT | | 摘要/简介 |
| content | TEXT | | 完整内容（Markdown） |
| source_type | TEXT | | 来源类型：zotero/obsidian/local/manual |
| source_uri | TEXT | | 来源路径或URL |
| metadata_json | TEXT | | 扩展元数据（JSON） |
| sync_status | TEXT | DEFAULT 'synced' | 同步状态：synced/pending/conflict/readonly |
| external_source | TEXT | | 外部来源：zotero/obsidian/manual |
| external_id | TEXT | | 外部系统 ID |
| external_uri | TEXT | | 外部系统 URI |
| external_updated_at | TEXT | | 外部系统更新时间 ISO8601 |
| external_hash | TEXT | | 外部内容哈希（冲突检测） |
| verified_status | TEXT | DEFAULT 'unverified' | 验证状态：unverified/partially_verified/verified |
| usable_for_writing | INTEGER | DEFAULT 1 | 是否可用于写作（0/1） |
| usable_for_rag | INTEGER | DEFAULT 1 | 是否可用于 RAG（0/1） |
| ai_generated | INTEGER | DEFAULT 0 | 是否 AI 生成（0/1） |
| human_verified | INTEGER | DEFAULT 0 | 是否人工验证（0/1） |
| relevance_score | REAL | | 相关性分数（0-1） |
| confidence_score | REAL | | 置信度分数（0-1） |
| created_at | TEXT | NOT NULL | ISO8601 |
| updated_at | TEXT | NOT NULL | ISO8601 |
| version | INTEGER | DEFAULT 1 | 版本号 |

**索引：**
- `idx_ko_type` ON (type)
- `idx_ko_title` ON (title)

**FTS5 虚拟表：** `knowledge_fts`（见第 17 节）

---

## 4. literature_items

文献专用字段。与 `knowledge_objects` 是 1:1 关系（通过 `id = knowledge_objects.id`）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY, REFERENCES knowledge_objects(id) | 同 KO.id |
| authors | TEXT | | 作者，逗号分隔 |
| year | TEXT | | 出版年份 |
| venue | TEXT | | 期刊/会议/出版社 |
| doi | TEXT | | DOI |
| isbn | TEXT | | ISBN |
| citation_key | TEXT | UNIQUE | authorYearShortTitle 格式 |
| abstract | TEXT | | 摘要 |
| keywords | TEXT | | 关键词，逗号分隔 |
| file_path | TEXT | | 本地 PDF 路径 |
| zotero_key | TEXT | | Zotero item key |
| reading_status | TEXT | CHECK(reading_status IN ('unread','reading','read')) | 阅读状态 |
| notes_count | INTEGER | DEFAULT 0 | 关联笔记数 |
| evidence_count | INTEGER | DEFAULT 0 | 关联证据数 |

**索引：** `idx_lit_citation_key` ON (citation_key)，`idx_lit_year` ON (year)

---

## 5. note_items

笔记专用字段。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY, REFERENCES knowledge_objects(id) | 同 KO.id |
| source_path | TEXT | | Obsidian vault 内路径 |
| vault_name | TEXT | | Vault 名称 |
| note_type | TEXT | CHECK(note_type IN ('fleeting','literature','permanent','project')) | 笔记类型（参考 Zettelkasten） |
| linked_literature_json | TEXT | | 关联文献 ID 列表（JSON 数组） |
| linked_theory_json | TEXT | | 关联理论 ID 列表（JSON 数组） |
| linked_evidence_json | TEXT | | 关联证据 ID 列表（JSON 数组） |

**索引：** `idx_note_vault` ON (vault_name)

---

## 6. theory_items

理论框架专用字段。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY, REFERENCES knowledge_objects(id) | 同 KO.id |
| discipline | TEXT | NOT NULL | 学科领域 |
| school | TEXT | | 理论流派 |
| core_concepts_json | TEXT | | 核心概念列表（JSON） |
| assumptions_json | TEXT | | 基本假设列表（JSON） |
| applicable_questions_json | TEXT | | 适用问题类型（JSON） |
| explanatory_mechanism | TEXT | | 解释机制说明 |
| boundary_conditions | TEXT | | 边界条件 |
| misuse_risks | TEXT | | 误用风险 |
| classic_literature_json | TEXT | | 经典文献 ID 列表（JSON） |
| related_theory_json | TEXT | | 相关理论 ID 列表（JSON） |
| writing_templates_json | TEXT | | 写作框架模板（JSON） |

**索引：** `idx_theory_discipline` ON (discipline)

---

## 7. evidence_items

证据包专用字段。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY, REFERENCES knowledge_objects(id) | 同 KO.id |
| claim_id | TEXT | | 所属 Claim ID（关联到 claims 表） |
| subclaim_id | TEXT | | 所属 Subclaim ID |
| quote | TEXT | | 直接引文 |
| evidence_type | TEXT | CHECK(evidence_type IN ('quote','case','data','method','other')) | 证据类型 |
| source_object_id | TEXT | REFERENCES knowledge_objects(id) | 来源知识对象 |
| source_location | TEXT | | 来源位置（如"p.42"、"第3章"） |
| page | TEXT | | 页码 |
| paragraph | TEXT | | 段落位置 |
| reliability | TEXT | CHECK(reliability IN ('high','medium','low')) | 可靠性 |
| relevance_score | REAL | | 与 Claim 相关度（0-1） |
| support_strength | TEXT | CHECK(support_strength IN ('strong','moderate','weak')) | 支撑强度 |
| counter_evidence | TEXT | | 反证说明 |
| gap_flag | INTEGER | DEFAULT 0 | 是否有缺口 |
| gap_reason | TEXT | | 缺口原因 |
| linked_section_id | TEXT | | 绑定到的论文章节 |
| linked_paragraph_id | TEXT | | 绑定到的段落 |
| citation_key | TEXT | | 关联 citation key |
| citation_status | TEXT | CHECK(citation_status IN ('pending','formatted','verified')) | 引用状态 |

**索引：** `idx_ev_claim` ON (claim_id)，`idx_ev_gap` ON (gap_flag)

---

## 8. claims

论文论点（Evidence Pack 的顶层结构）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| project_id | TEXT | NOT NULL, REFERENCES projects(id) | 所属项目 |
| parent_claim_id | TEXT | REFERENCES claims(id) | 父论点（支持嵌套） |
| text | TEXT | NOT NULL | 论点文本 |
| claim_type | TEXT | CHECK(claim_type IN ('core','sub','counter')) | 论点类型 |
| priority | INTEGER | DEFAULT 0 | 优先级 |
| created_at | TEXT | NOT NULL | ISO8601 |

**索引：** `idx_claim_project` ON (project_id)，`idx_claim_parent` ON (parent_claim_id)

---

## 9. project_knowledge_links

项目与知识对象的多对多绑定。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| project_id | TEXT | NOT NULL, REFERENCES projects(id) | 项目 ID |
| object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 知识对象 ID |
| role | TEXT | CHECK(role IN ('background','core','method','theory','evidence','contrast','section_claim')) | 在项目中的用途 |
| priority | INTEGER | DEFAULT 0 | 优先级（影响推荐排序） |
| project_note | TEXT | | 项目内备注 |
| used_in_sections | TEXT | | 使用在哪些章节（JSON 数组） |
| UNIQUE(project_id, object_id) | | | 唯一约束 |

**索引：** `idx_pkl_project` ON (project_id)，`idx_pkl_object` ON (object_id)

---

## 10. object_relations

知识对象之间的关系（双链/引用/支撑/反驳等）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| from_object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 源对象 |
| to_object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 目标对象 |
| relation_type | TEXT | NOT NULL | 类型：cites/supports/challenges/extends/related_to |
| context | TEXT | | 关系上下文说明 |
| UNIQUE(from_object_id, to_object_id, relation_type) | | | |

**索引：** `idx_or_from` ON (from_object_id)，`idx_or_to` ON (to_object_id)

---

## 11. tags

标签。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| name | TEXT | NOT NULL, UNIQUE | 标签名 |
| color | TEXT | | 颜色代码（可选） |

---

## 12. object_tags

对象与标签的多对多关系。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 对象 |
| tag_id | TEXT | NOT NULL, REFERENCES tags(id) | 标签 |
| UNIQUE(object_id, tag_id) | | | |

---

## 13. citations

引用记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| source_object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 引用方对象 |
| target_object_id | TEXT | NOT NULL, REFERENCES knowledge_objects(id) | 被引用方对象 |
| context | TEXT | | 引用上下文（前后的句子） |
| page | TEXT | | 页码 |
| paragraph | TEXT | | 段落位置 |

**索引：** `idx_cit_source` ON (source_object_id)，`idx_cit_target` ON (target_object_id)

---

## 14. skills

Skill 定义（读取 YAML 文件后同步进来）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | 与 YAML 文件名对齐 |
| name | TEXT | NOT NULL | 显示名称 |
| description | TEXT | | 描述 |
| category | TEXT | | 分类：writing/review/editing |
| file_path | TEXT | NOT NULL | YAML 文件路径 |
| version | TEXT | | 版本 |
| created_at | TEXT | NOT NULL | 首次扫描时间 |

---

## 15. skill_bindings

Skill 到项目/任务类型的绑定。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| skill_id | TEXT | NOT NULL, REFERENCES skills(id) | Skill ID |
| project_id | TEXT | NOT NULL, REFERENCES projects(id) | 项目（NULL=全局） |
| task_type | TEXT | NOT NULL | 任务类型：outline/draft/rewrite/polish/review |
| enabled | INTEGER | DEFAULT 1 | 是否启用 |
| priority | INTEGER | DEFAULT 0 | 优先级 |
| PRIMARY KEY(skill_id, project_id, task_type) | | | |

---

## 16. runs

运行记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| session_id | TEXT | PRIMARY KEY | UUID，对应文件夹名 |
| project_id | TEXT | REFERENCES projects(id) | 关联项目（可为空） |
| research_question | TEXT | | 研究问题 |
| run_mode | TEXT | CHECK(run_mode IN ('mock','real','dry_run')) | 运行模式 |
| status | TEXT | CHECK(status IN ('running','completed','failed','cancelled')) | 状态 |
| provider_type | TEXT | | Provider 类型 |
| model | TEXT | | 模型名称 |
| cost | REAL | | 费用（估算） |
| token_count | INTEGER | | token 数 |
| started_at | TEXT | NOT NULL | ISO8601 |
| ended_at | TEXT | | ISO8601 |
| error_message | TEXT | | 错误信息（失败时） |

**索引：** `idx_runs_project` ON (project_id)，`idx_runs_status` ON (status)

---

## 17. import_jobs

导入任务记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| project_id | TEXT | REFERENCES projects(id) | 目标项目 |
| import_type | TEXT | NOT NULL | 类型：markdown/bibtex/ris/zotero/obsidian |
| source_path | TEXT | | 源文件/目录 |
| status | TEXT | CHECK(status IN ('pending','running','completed','failed')) | 状态 |
| items_imported | INTEGER | DEFAULT 0 | 成功导入数 |
| items_failed | INTEGER | DEFAULT 0 | 失败数 |
| error_message | TEXT | | 错误信息 |
| started_at | TEXT | NOT NULL | ISO8601 |
| ended_at | TEXT | | ISO8601 |

---

## 18. FTS5 虚拟表

```sql
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    title,
    summary,
    content,
    content='knowledge_objects',
    content_rowid='rowid'
);

-- 触发器：保持 FTS 与主表同步
CREATE TRIGGER knowledge_ai AFTER INSERT ON knowledge_objects BEGIN
    INSERT INTO knowledge_fts(rowid, title, summary, content)
    VALUES (NEW.rowid, NEW.title, NEW.summary, NEW.content);
END;

CREATE TRIGGER knowledge_ad AFTER DELETE ON knowledge_objects BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, summary, content)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.summary, OLD.content);
END;

CREATE TRIGGER knowledge_au AFTER UPDATE ON knowledge_objects BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, summary, content)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.summary, OLD.content);
    INSERT INTO knowledge_fts(rowid, title, summary, content)
    VALUES (NEW.rowid, NEW.title, NEW.summary, NEW.content);
END;
```

---

## 19. 分阶段实现

| 阶段 | 表 |
|------|---|
| **v3.1 最小** | projects, knowledge_objects, literature_items, note_items, theory_items, evidence_items, project_knowledge_links, object_relations, tags, object_tags, knowledge_fts |
| **v3.2** | citations, claims, claim_evidence_links |
| **v3.3+** | skills, skill_bindings（已有部分） |
| **后续** | import_jobs, embeddings（向量索引） |

---

*本文档是数据库实现的技术基准。实际实现时使用 SQLAlchemy 或直接 sqlite3。*
*所有字段和约束以本文档为准。*