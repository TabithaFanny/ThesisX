# ThesisX 最终产品 PRD

> 版本：v2.0
> 日期：2026-06-01
> 状态：产品定义完成，审查通过，待进入开发
> 基于：前序 7 层审计报告 + 盲区补充审计 + PRD 穷尽式审查

---

## 0. Executive Summary

ThesisX 是一个**面向中文社科学生的本地优先研究陪跑工作台**。它帮助用户从模糊选题走到可追溯的论文初稿，核心价值是"AI 辅助研究推进，而非 AI 代写论文"。

**当前状态：** 论文工作台 MVP。后端 API 闭环可跑，前端可用但残缺，数据层不统一（Literature=JSON、Knowledge=SQLite、Evidence=JSONL），Agent 写作未真正调用 RAG。

**P1 目标：** 统一数据层 + 砍掉 PyQt6 + 实现可信知识驱动写作闭环（Source Trace + Grounded Writing + Feedback Rewrite）。

**P2 目标：** 真实研究流程增强（文献综述矩阵、理论推荐解释、Claim-Evidence 自动建议、方法推荐前端）。

**P3 目标：** 研究方法与交付增强（Zotero 实时同步、CSL 引用、定性编码、定量增强、Docker）。

---

## 1. 产品定位

### 1.1 最终定位

> **ThesisX 是一个面向中文社科学生和青年研究者的本地优先研究陪跑工作台。**
>
> 它不是论文生成器，不是文献管理器，不是数据分析平台。
> 它帮助用户从模糊选题、文献积累、知识库构建、理论框架、证据组织，到可追溯写作、反馈迭代和最终导出。

### 1.2 不适合的定位

| 错误定位 | 为什么不合适 |
|---------|------------|
| AI 论文生成器 | 用户点击按钮等结果，没有研究过程，没有可追溯性，没有学术诚信 |
| 全能文献管理器 | Zotero 已经做得很好，ThesisX 应该增强而非替代 |
| 专业计量分析工具 | Stata/R/SPSS 不可替代，ThesisX 只做简单辅助 |
| 多人协作平台 | 当前阶段单人研究陪跑是最大痛点，协作是 v5.0 的事 |
| 知识图谱大屏 | 好看但没用，典型的功能堆砌陷阱 |

### 1.3 最小可成立的产品价值主张

> "我输入一个模糊的研究想法，ThesisX 帮我拆题、找文献、建知识库、匹配理论、组织证据，然后 AI 基于我的知识库帮我写论文——每一段都能追溯到来源。"

---

## 2. 目标用户

| 用户类型 | 核心痛点 | ThesisX 帮什么 | 不帮什么 | 优先级 |
|---------|---------|---------------|---------|:--:|
| 社科本科生 | 写课程论文不知从何下手 | 拆题、找文献、推荐理论、辅助写作 | 不代写、不保证高分 | P1 |
| 大创/挑战杯学生 | 需要系统化研究流程 | 文献综述矩阵、Claim-Evidence、方法推荐 | 不做完整项目申报书 | P1 |
| 社科研究生 | 开题报告、文献综述、论文初稿 | RAG 知识库、理论匹配、可追溯写作 | 不做完整方法论统计分析 | P1 |
| 青年研究者 | 需要快速整理文献和组织论证 | 知识库构建、证据组织、写作辅助 | 不做投稿全流程 | P2 |
| ~~专业期刊作者~~ | 投稿全流程 | 不做 | — | P3 |
| ~~多人协作实验室~~ | 协作写作 | 不做 | — | P3 |
| ~~计量经济学用户~~ | 复杂统计建模 | 不做 | — | P3 |

---

## 3. 核心问题与价值主张

### 3.1 用户最痛的问题

1. **有模糊想法，但不知道如何变成可操作的研究问题。**
2. **有大量 PDF/笔记/文献，但不会组织成论文。**
3. **AI 生成的论文看起来很专业，但无法验证来源是否可靠。**
4. **写完初稿后不知道如何修改、如何组织论据。**

### 3.2 ThesisX 的解决方案

| 痛点 | 解决方案 |
|------|---------|
| 模糊想法 | AI 拆题 → 关键词提取 → 学科判断 → 研究方向推荐 |
| 材料散乱 | 导入 PDF/DOCX/笔记 → 统一知识库 → RAG 索引 |
| AI 不可信 | 每个 AI 段落标注来源 chunk → 可点击追溯 |
| 不会修改 | 选中段落 → AI 基于原 sources 局部改写 → 保存版本 |

---

## 4. 用户主路径

Text
用户输入模糊想法
  → AI 拆题、提关键词、判断学科、推荐方向
  → 用户确认研究问题
  → 搜索 Semantic Scholar / 本地文献
  → 用户选择导入文献
  → PDF/DOCX 解析为结构化 Markdown
  → 文献进入知识库和 RAG 索引
  → AI 推荐理论框架与文献综述矩阵
  → 用户确认 Claim 和论点
  → AI 从知识库检索证据
  → AI 生成带 [C1][C2] 引用的段落（每段可追溯）
  → 用户反馈某段
  → AI 基于原 sources 局部改写
  → 保存版本记录
  → 导出 DOCX / BibTeX / Sources 清单

| 阶段 | 用户操作 | AI 行为 | 系统数据 | 当前状态 | 缺口 | 验收标准 |
|------|---------|---------|---------|:--:|------|---------|
| 1. 输入想法 | 输入一句话研究方向 | 提取关键词、判断学科、推荐方向 | Project + ResearchQuestion | 🔴 | 关键词提取、学科判断、方向推荐全是手动 | 输入"AI对大学生学习的影响"→ 自动返回关键词+学科+3个方向 |
| 2. 确认问题 | 选择/修改研究方向 | 展示方向可行性和理论建议 | ResearchQuestion + Direction | 🔴 | 可行性评估不存在 | 用户确认后生成结构化研究问题卡片 |
| 3. 搜索文献 | 点击搜索 | 调 Semantic Scholar + 本地索引 | LiteratureItem（临时） | 🟡 | 前端无搜索入口，后端有 API | 搜索返回 10+ 结果，可预览摘要 |
| 4. 导入文献 | 勾选文献 → 导入 | 解析 PDF/DOCX 为 Markdown → 分 chunk → 写入知识库 | LiteratureItem + KnowledgeItem + RagChunk | 🟡 | 文献是 JSON 文件，不进入 RAG | 导入后可在知识库和 RAG 中检索到 |
| 5. 建知识库 | 查看导入结果 | 自动建索引 | KnowledgeItem + RagChunk | 🟢 | 知识库无分类筛选，无批量操作 | 知识库列表显示所有导入项（含标题、类型、日期），可按类型筛选，RAG 可检索到全部内容 |
| 6. 理论匹配 | 点击"匹配理论" | 关键词匹配 24 个理论 → 返回 top 5 | TheoryCandidate | 🟡 | 规则引擎，无语义匹配 | 返回匹配结果含解释和局限性 |
| 7. 确认论点 | 确认/修改 Claim | 从知识库建议 Claim | Claim + Evidence | 🟡 | Claim 手动创建，无自动建议 | 至少 3 个 Claim 被自动建议 |
| 8. 检索证据 | 查看检索结果 | RAG 检索相关 chunk → 返回带来源片段 | RagResult[] | 🟢 | 检索结果无高亮、无分页 | 检索结果含 source_id 和标题，关键词高亮，支持分页（每页 10 条） |
| 9. AI 写作 | 点击"生成初稿" | **基于 RAG 检索结果**生成段落，标注 [C1] | WritingBlock + SourceTrace | 🔴 | **Agent 不调 RAG，读静态文件** | 每个段落可追溯到至少 1 个 chunk |
| 10. 反馈改写 | 选中段落 → 点改写 | 基于原 sources 局部改写 | RewriteVersion | 🟡 | 桌面端有 diff，Web 端无 diff 组件 | 改写后双栏显示原始 vs 改写，红色删除/绿色新增，可一键回滚到原始版本 |
| 11. 导出 | 选择格式 → 导出 | 生成 DOCX + Sources 清单 | ExportRecord | 🟡 | 只验证 content-type，不验证文件内容和引用完整性 | 导出 DOCX 用 Word/LibreOffice 可打开，内容完整无乱码，Sources 清单列出所有引用文献的标题、作者、年份和 chunk ID |

---

## 5. 用户做什么，AI 做什么

| 用户负责 | AI 负责 |
|---------|---------|
| 输入研究想法 | 拆题、提取关键词、推荐方向 |
| 确认/拒绝 AI 建议 | 基于用户选择缩小范围 |
| 选择导入哪些文献 | 搜索、解析、分 chunk、建索引 |
| 阅读和判断文献质量 | 提取元数据、摘要、关键词 |
| 选择理论框架 | 匹配推荐、解释适用性 |
| 确认 Claim 和论证逻辑 | 从知识库建议 Claim、匹配 Evidence |
| 写论文（编辑、修改） | 基于知识库检索结果生成初稿 |
| 判断 AI 生成内容是否准确 | 标注来源、提供可追溯引用 |
| 反馈某段不好 | 基于原 sources 局部改写 |
| 选择导出格式 | 格式化文档、生成引用 |

**核心原则：AI 不替用户做研究判断。** 用户是研究者，AI 是研究助理。AI 可以建议，但最终决定权在用户。

---

## 6. 产品原则

1. **AI 不替用户做研究判断，只辅助研究推进。** 理论选择、Claim 确认、文献质量判断——这些必须用户决定。
2. **每个 AI 输出都必须可追溯。** 写作段落标注 source chunk，引用标注文献 ID。
3. **无来源，不伪装知识驱动。** Agent 写作必须基于 RAG 实时检索，不能用静态文件或裸 LLM 猜测。
4. **本地优先，保护用户论文和材料。** 所有数据存本地，API Key 只存环境变量。
5. **先做好单人研究陪跑，不急着做多人协作。**
6. **先做好社科论文流程，不急着做所有学科。**
7. **先做好 Web 端，不再双线维护 PyQt6。**
8. **先做好真实闭环，不堆空壳页面。**
9. **先让用户知道下一步做什么，再做复杂功能。**
10. **先做可验证能力，再做宏大叙事。**

---

## 7. 功能范围 MoSCoW

### Must Have（P1）— 没有就不成立

| 功能 | 为什么 | 当前状态 | 依赖 | 验收标准 |
|------|--------|:--:|------|---------|
| 项目创建 | 所有功能的基础 | ✅ | — | 可创建项目，输入研究问题 |
| 研究问题拆解 | 核心价值第一步 | 🔴 | 需 LLM | 输入模糊想法 → 返回关键词+学科+3个方向 |
| 文献搜索（Semantic Scholar） | 唯一在线文献源 | 🟡 后端有 | 前端入口 | 搜索返回 10+ 结果 |
| 文献导入 | 建知识库的前提 | 🟡 | — | 导入后进入知识库和 RAG |
| PDF/DOCX 解析 | 处理用户已有材料 | 🟡 | PyMuPDF | 解析为结构化 Markdown，分 chunk |
| Knowledge Store（SQLite） | 统一数据层 | 🟢 | — | 可创建、读取、更新、删除知识条目，每次操作返回正确结果；支持按 item_type 和 project_id 筛选 |
| RAG 检索（BM25+FAISS） | 知识驱动检索 | 🟢 | — | 输入查询 → 返回 top 10 结果，每条含 source_id/title/text/score，支持 project_id 和 item_type 过滤 |
| Grounded Writing（真 RAG） | 核心差异化 | 🔴 | **Agent 需改** | 生成初稿后，每段标注 [C{n}] 引用标记；点击标记跳转到来源 chunk；至少 50% 段落有 source trace |
| Source Trace | 可追溯性 | 🔴 | 需新增 WritingBlock/SourceTrace 表 + 前端面板 | 点击 [C{n}] → 弹出侧栏显示来源 chunk 的标题、全文片段、文献出处；所有 SourceTrace 记录可通过 API 查询 |
| Feedback Rewrite | 修改闭环 | 🟡 | Web 端需补 | 改写显示 diff，可回滚 |
| Version History | 修改追溯 | 🟡 | 需新增 RewriteVersion 表 + 前端页面 | 改写版本列表显示时间戳、操作类型（生成/改写/手动编辑）、内容摘要；点击任意版本可回滚 |
| DOCX 导出 | 最终交付 | 🟡 | 需验证内容 | 导出含完整引用和 Sources 页 |
| Sources 清单 | 可追溯交付 | 🔴 | 需新增前端页面 + 导出逻辑 | 导出 DOCX 时附 Sources 附录页，列出所有被引用的 chunk：序号、标题、文献出处、chunk 文本片段 |
| 新手引导 | 降低入门门槛 | 🔴 | 需新增引导组件 | 首次打开显示 5 步引导流程：创建项目 → 输入研究问题 → 搜索文献 → 导入文献 → 生成初稿；每步有明确的操作说明和进度指示 |
| Web 主界面 | 唯一 UI | 🟢 | — | 所有 P1 功能可在 Web 端操作，无 PyQt6 依赖；左侧导航包含首页/项目/文献/知识库/写作/导出/设置 |

### Should Have（P2）— 增强真实研究体验

| 功能 | 为什么 | 依赖 |
|------|--------|------|
| Zotero 实时同步 | 学术用户刚需 | Zotero API Key |
| CSL / GB/T 7714 引用 | 中文社科必备 | citeproc-js 或 pycsl |
| 文献综述矩阵 | 研究流程增强 | RAG + LLM |
| 理论推荐解释 | 帮助用户理解理论 | 理论库扩展 |
| Claim-Evidence 自动建议 | 减少手动操作 | RAG + LLM |
| 方法推荐（前端） | 后端已有 API | 前端入口 |
| 访谈提纲/问卷生成（前端） | 后端已有 API | 前端入口 |
| 质量审查升级 | 不只检查字段，检查逻辑 | LLM |

### Could Have（P3）— 后续扩展

| 功能 | 为什么是 P3 |
|------|-----------|
| OCR | 扫描件论文识别 |
| LaTeX 导出 | 理工科需求 |
| 定性编码 UI | 需要完整编码流程 |
| 定量稳健性检验 | 需要专业统计 |
| 投稿期刊匹配 | 次要场景 |
| 知识图谱 | 可视化而非功能 |
| Web Search 热点发现 | 次要场景 |
| Docker 生产部署 | 部署需求 |

### Won't Have Now — 明确不做

| 功能 | 理由 |
|------|------|
| 多用户协作 | 当前单人场景，协作是 v5.0 |
| 云同步 | 本地优先承诺 |
| 商业后台 | 无商业化计划 |
| 全自动代写 | 违背产品原则 |
| 投稿全流程 | 不做期刊投稿系统 |
| 复杂权限系统 | 单人使用不需要 |
| **PyQt6 新功能** | 冻结桌面端，不再开发 |
| Blueprint 可视化编辑器 | 空壳，用户不需要手写 DAG |
| Skill Library 空壳页面 | 功能未接通 |
| Collaboration 页面 | v5.0 才需要 |
| Submission 页面 | 空壳 |
| Data Charts 页面 | 空壳 |

---

## 8. 信息架构与页面

### 8.1 最终页面（Web 端）

| 页面 | 目标 | 主要组件 | 用户动作 | AI 动作 | 数据来源 | 优先级 |
|------|------|---------|---------|---------|---------|:--:|
| 首页/工作台 | 项目总览 + 引导 | 项目列表、进度卡、下一步建议 | 创建/打开项目 | 建议下一步 | Projects API | P1 |
| 新手引导 | 降低入门门槛 | Step-by-step 引导流程 | 跟随引导完成首次操作 | 引导提示 | — | P1 |
| 项目详情 | 项目管理中心 | 研究问题卡、进度、快捷入口 | 编辑问题、跳转各模块 | 拆题、推荐方向 | Project + RQ API | P1 |
| 文献发现 | 搜索和导入文献 | 搜索框、结果列表、导入按钮 | 搜索 → 勾选 → 导入 | Semantic Scholar 搜索 | Semantic Scholar API | P1 |
| 文献库 | 管理已导入文献 | 文献列表、筛选、详情面板 | 查看、筛选、删除 | 元数据提取 | Literature API | P1 |
| 文档解析 | 上传 PDF/DOCX | 上传区、解析进度、预览 | 拖拽/选择文件 → 上传 | 解析为 Markdown → 分 chunk | Import API | P1 |
| 知识库/RAG | 检索和管理知识 | 搜索框、结果列表、来源标注 | 搜索 → 查看来源 | RAG 检索 | RAG API | P1 |
| 理论与设计 | 理论匹配 + 方法推荐 | 研究问题输入、理论结果、方法推荐 | 输入问题 → 查看结果 | 匹配理论、推荐方法 | Theory + Research API | P2 |
| Claim-Evidence | 论点和证据管理 | Claim 列表、证据绑定、缺口分析 | 创建 Claim、绑定证据 | 建议 Claim、匹配 Evidence | Evidence API | P2 |
| 写作工作台 | AI 写作 + 编辑 | 编辑器、Source Trace 面板、改写面板 | 生成 → 编辑 → 改写 | 基于 RAG 生成、局部改写、标注来源 | Pipeline + RAG API | P1 |
| 版本历史 | 查看改写记录 | 版本列表、diff 视图 | 查看历史 → 回滚 | — | 本地存储 | P1 |
| 导出 | 导出论文 | 格式选择、预览、导出按钮 | 选格式 → 导出 | 格式化文档、生成引用 | Export API | P1 |
| 设置 | 配置 Provider/连接器 | API Key、Zotero、Semantic Scholar | 填写配置 | 检测连接状态 | Settings API | P1 |

### 8.2 页面合并/删除/后置

| 现有页面 | 处理 | 理由 |
|---------|:--:|------|
| Approval Inbox | 🔴 删除 | 单人场景无审批需求 |
| Blueprint 编辑器 | 🟡 隐藏为高级功能 | 用户不需要手写 DAG |
| Pipeline 控制台 | 🟡 合并到写作工作台 | 不要暴露技术细节给用户 |
| Collaboration | 🔴 后置到 v5.0 | 单人场景不需要 |
| Submission | 🔴 后置到 v5.0 | 空壳 |
| Data Charts | 🔴 后置到 v5.0 | 空壳 |
| Skill Library | 🔴 后置 | 功能未接通 |
| AI Chat | 🟡 合并到写作工作台 | 作为侧边栏功能 |
| PyQt6 全部页面 | 🔴 冻结 | 不再维护桌面端 |

---

## 9. 数据模型

### 9.1 核心数据对象

| 数据对象 | 作用 | 关键字段 | 与其他对象关系 | 当前状态 | 优先级 |
|---------|------|---------|---------------|:--:|:--:|
| Project | 论文项目容器 | id, name, research_question, discipline | 1:N ResearchQuestion | ✅ SQLite | P1 |
| ResearchQuestion | 研究问题 | id, project_id, question, keywords, discipline, clarity_score | N:1 Project | ✅ SQLite | P1 |
| LiteratureItem | 文献条目 | id, title, authors, year, doi, abstract, source_type | 1:N RagChunk | 🔴 JSON 文件 | P1 |
| SourceDocument | 导入的源文档 | id, title, file_path, file_type, parsed_markdown | 1:N DocumentChunk | 🔴 不存在 | P1 |
| DocumentChunk | 文档分块 | id, source_id, chunk_index, text, start_char, end_char | N:1 SourceDocument | 🟡 部分存在 | P1 |
| KnowledgeItem | 知识条目 | id, item_type, title, content, project_id, source_document_id | N:1 Project, N:1 SourceDocument | ✅ SQLite | P1 |
| RagChunk | RAG 检索块 | chunk_id, source_id, source_title, text, item_type, project_id | N:1 LiteratureItem/SourceDocument | ✅ SQLite | P1 |
| Claim | 论点 | id, project_id, claim_text, claim_type | N:1 Project | 🟡 JSONL 文件 | P1 |
| Evidence | 证据 | id, claim_id, evidence_text, source_chunk_id | N:1 Claim, N:1 RagChunk | 🟡 JSONL 文件 | P1 |
| WritingBlock | 写作段落 | id, project_id, section, content, created_at | N:1 Project | 🔴 不存在 | P1 |
| SourceTrace | 来源追踪 | id, writing_block_id, chunk_id, citation_text | N:1 WritingBlock, N:1 RagChunk | 🔴 不存在 | P1 |
| Citation | 引用记录 | id, source_trace_id, literature_item_id, context, page | N:1 SourceTrace, N:1 LiteratureItem | 🟡 部分存在 | P1 |
| RewriteVersion | 改写版本 | id, writing_block_id, original_content, rewritten_content, created_at | N:1 WritingBlock | 🔴 不存在 | P1 |
| RunSession | 运行记录 | session_id, project_id, status, provider, model, cost | N:1 Project | ✅ 文件系统 | P2 |
| ExportRecord | 导出记录 | id, project_id, format, file_path, citation_count | N:1 Project | 🔴 不存在 | P2 |

### 9.2 数据统一原则

1. **Literature 从 JSON 文件迁移到 SQLite `literature_items` 表。** 表结构已在 DATA_MODEL.md 中定义。
2. **Evidence 从 JSONL 文件迁移到 SQLite `claims` + `claim_evidence_links` 表。**
3. **所有对象用 UUID 作为主键，统一外键关联。**
4. **删除项目时必须级联删除关联数据。**
5. **写作结果（WritingBlock）必须通过 SourceTrace 关联到 RagChunk。**
6. **导出结果（ExportRecord）必须通过 Citation 关联到 LiteratureItem。**

### 9.3 P1 新增表 DDL

```sql
-- 写作段落
CREATE TABLE writing_blocks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    section TEXT NOT NULL DEFAULT 'body',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX idx_wb_project ON writing_blocks(project_id);

-- 来源追踪（多对多：WritingBlock ↔ RagChunk）
CREATE TABLE source_traces (
    id TEXT PRIMARY KEY,
    writing_block_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    citation_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (writing_block_id) REFERENCES writing_blocks(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES rag_chunks(chunk_id) ON DELETE CASCADE
);
CREATE INDEX idx_st_block ON source_traces(writing_block_id);
CREATE INDEX idx_st_chunk ON source_traces(chunk_id);

-- 改写版本
CREATE TABLE rewrite_versions (
    id TEXT PRIMARY KEY,
    writing_block_id TEXT NOT NULL,
    version_number INTEGER NOT NULL DEFAULT 1,
    original_content TEXT NOT NULL,
    rewritten_content TEXT NOT NULL,
    operation_type TEXT NOT NULL DEFAULT 'rewrite',
    created_at TEXT NOT NULL,
    FOREIGN KEY (writing_block_id) REFERENCES writing_blocks(id) ON DELETE CASCADE
);
CREATE INDEX idx_rv_block ON rewrite_versions(writing_block_id);

-- 导出记录
CREATE TABLE export_records (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'docx',
    file_path TEXT NOT NULL,
    citation_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX idx_er_project ON export_records(project_id);
```

---

## 10. AI 能力边界

| 能力 | 当前实现类型 | 最终应实现类型 | 需 LLM？ | 需 RAG？ | 需 MCP？ | 验收标准 |
|------|------------|--------------|:--:|:--:|:--:|---------|
| 研究问题拆解 | 🔴 CRUD | LLM | ✅ | — | — | 输入模糊想法→返回关键词+学科+方向 |
| 关键词提取 | 🔴 手动 | LLM | ✅ | — | — | 自动提取并写入 DB |
| 学科判断 | 🔴 手动 | LLM + 规则 | ✅ | — | — | 自动判断并写入 DB |
| 研究方向推荐 | 🔴 不存在 | LLM | ✅ | — | — | 返回 3 个方向含可行性 |
| 文献搜索 | 🟢 外部 API | 外部 API | — | — | ✅ | Semantic Scholar 返回结果 |
| 文献摘要 | 🔴 不存在 | LLM | ✅ | — | — | 自动生成中文摘要 |
| 理论推荐 | 🟡 规则引擎 | 规则 + LLM 解释 | ✅ | — | — | 匹配+解释，非纯关键词 |
| Claim 抽取 | 🔴 不存在 | LLM + RAG | ✅ | ✅ | — | 从知识库抽取 3+ Claim |
| Evidence 匹配 | 🔴 手动 | RAG + LLM | ✅ | ✅ | — | 自动匹配证据到 Claim |
| RAG 检索 | 🟢 BM25+FAISS | BM25+FAISS | — | — | — | 返回带来源片段 |
| Grounded Writing | 🔴 静态文件 | LLM + RAG 实时 | ✅ | ✅ | — | 每段标注 chunk 来源 |
| Feedback Rewrite | 🟡 桌面端 | LLM + RAG | ✅ | ✅ | — | 改写显示 diff，可回滚 |
| 版本历史 | 🟡 部分 | CRUD | — | — | — | 保存每次改写版本 |
| 质量审查 | 🟡 规则引擎 | 规则 + LLM | ✅ | — | — | 不只检查字段，检查逻辑 |
| 方法推荐 | 🟡 规则引擎 | 规则 + LLM 定制 | ✅ | — | — | 根据研究问题定制方法 |
| 定性分析 | 🟡 LLM 编码 | LLM + 人工审核 | ✅ | — | — | 编码结果可导出 |
| 定量分析 | 🟡 pandas | pandas + statsmodels | — | — | ✅ | 描述统计+OLS 结果可验证 |
| 引用导出 | 🟡 手写 5 格式 | CSL 引擎 | — | — | — | 支持 GB/T 7714 等 10+ 格式 |

---

## 11. MCP 与外部工具策略

### 11.1 MCP 定位

ThesisX 有两层 MCP：
1. **对外：** ThesisX 作为 MCP Server，让外部 AI（Claude Desktop、Codex）调用 ThesisX 的 14 个工具。
2. **对内：** CEO Agent 调用 MCP 工具（detect_mcp_tools、run_quant_analysis 等）。

### 11.2 MCP 工具保留策略

| MCP Tool | 用户场景 | 保留？ | P1？ | 数据写回 | 验收标准 |
|---------|---------|:--:|:--:|---------|---------|
| list_projects | 外部 AI 查询项目 | ✅ | P1 | — | 返回项目列表 |
| create_project | 外部 AI 创建项目 | ✅ | P1 | SQLite | 创建成功 |
| search_literature | 外部 AI 搜索文献 | ✅ | P1 | — | 返回搜索结果 |
| detect_mcp_tools | CEO Agent 检测工具 | ✅ | P1 | — | 返回可用工具列表 |
| run_quant_analysis | 用户做简单定量分析 | ✅ | P2 | 文件系统 | 返回分析结果 |
| run_qual_analysis | 用户做简单定性分析 | ✅ | P2 | 文件系统 | 返回编码结果 |
| recommend_methods | 用户选择研究方法 | ✅ | P2 | — | 返回方法推荐 |
| generate_survey | 用户生成问卷 | ✅ | P2 | — | 返回问卷草稿 |
| get_ethics_checklist | 用户查看伦理清单 | ✅ | P2 | — | 返回 10 项清单 |
| search_trending_topics | 搜索研究热点 | 🟡 | P3 | — | 返回热点趋势 |
| find_suitable_venues | 查找投稿期刊 | 🟡 | P3 | — | 返回期刊列表 |
| list_leaders | 调试用 | 🔴 | — | — | 删除 |
| check_existing_work | 外部 AI 检查工作 | 🟡 | P3 | — | 返回历史记录 |
| list_directory | 调试用 | 🔴 | — | — | 删除 |

---

## 12. 研究方法能力边界

### P1 可以做

- 方法推荐（正则匹配 + LLM 定制）
- 访谈提纲生成（LLM）
- 问卷草稿生成（LLM）
- 简单描述统计（pandas）
- 简单 OLS 回归（statsmodels）
- 简单主题分析（LLM 编码）

### P2 再做

- 研究设计定制化
- 文献综述矩阵
- Claim-Evidence Reasoning
- 定性编码本
- 引用一致性检查

### P3 再做

- 稳健性检验
- DID 平行趋势
- PSM、IV
- 编码一致性（Cohen's Kappa）
- 理论饱和判断
- Audit trail
- 投稿格式适配

**声明：ThesisX 不是专业计量分析软件或 NVivo 替代品。定量分析只做简单辅助，定性分析只做初步编码。复杂分析请使用 Stata/R/NVivo。**

---

## 13. P1 / P2 / P3 路线图

### P1：可信知识驱动写作闭环（3-4 周）

**目标：** 证明 AI 写作可以追溯到用户知识库中的 source/chunk。

**用户价值：** 用户从导入文献到导出带来源标注的论文，全链路可走通。

**功能清单：**
- 研究问题拆解（LLM）
- 文献搜索与导入（Semantic Scholar 前端入口）
- PDF/DOCX 解析 → 知识库 → RAG
- 统一数据层（Literature → SQLite，Evidence → SQLite）
- **Grounded Writing（Agent 真调 RAG）**
- **Source Trace（写作段落标注 chunk 来源）**
- Feedback Rewrite（Web 端）
- Version History
- DOCX 导出 + Sources 清单
- 新手引导
- 砍掉 PyQt6 代码（**注意：在 Web 端 P1 功能全部完成并验证通过后执行**）

**技术任务：**
- Literature JSON → SQLite 迁移脚本
- Evidence JSONL → SQLite 迁移脚本
- Agent context_assembler 改为调 RagService.search()
- 新增 WritingBlock + SourceTrace + Citation 数据模型
- 新增 Source Trace 前端面板
- 新增 RewriteVersion 数据模型
- 新增版本历史页面
- 删除 PyQt6 目录（**前提：Web 端 P1 全流程验证通过**）

**不做什么：**
- 不碰 Zotero 实时同步
- 不碰 CSL 引用引擎
- 不碰定性定量增强
- 不碰 Blueprint 编辑器

**验收标准：**
1. 输入"AI 对大学生学习的影响" → 自动返回关键词+学科+3 个方向
2. 搜索 Semantic Scholar → 导入文献 → 可在 RAG 中检索到
3. 上传 PDF → 解析为 Markdown → 分 chunk → 可检索
4. 点击"生成初稿" → AI 基于 RAG 检索结果生成 → 每段有 [C1] 标注
5. 点击 [C1] → 跳转到来源 chunk 详情
6. 选中段落 → 改写 → 显示 diff → 可回滚
7. 导出 DOCX → 含完整引用和 Sources 清单
8. 首次打开 → 新手引导流程
9. 全量测试通过（覆盖率 ≥ 30%）

---

### P2：真实研究流程增强（4-6 周）

**目标：** 覆盖更多研究环节，让 ThesisX 不只是"写作工具"。

**用户价值：** 从选题到文献综述到理论框架到证据组织，全流程辅助。

**功能清单：**
- 文献综述矩阵
- 理论推荐解释（LLM 增强）
- Claim-Evidence 自动建议
- 方法推荐（前端）
- 访谈提纲/问卷生成（前端）
- 质量审查升级（LLM 检查逻辑）
- 引用一致性交叉验证
- Zotero 实时同步（API）

**技术任务：**
- 文献综述矩阵生成逻辑
- 理论匹配 LLM 增强
- Claim 自动抽取 + Evidence 自动匹配
- 方法推荐前端页面
- 引用一致性检查器
- Zotero API 集成

**不做什么：**
- 不碰 CSL 引擎
- 不碰定性编码 UI
- 不碰定量增强

**验收标准：**
1. 选择项目 → 自动生成文献综述矩阵
2. 理论推荐含解释和适用性分析
3. 自动抽取 3+ Claim，匹配对应 Evidence
4. 方法推荐页面可操作
5. 引用一致性检查通过

---

### P3：研究方法与交付增强（6-8 周）

**目标：** 完善研究方法支持和交付格式。

**用户价值：** 定性定量分析辅助、CSL 引用、LaTeX 导出。

**功能清单：**
- CSL 引用引擎（GB/T 7714 等）
- 定性编码 UI
- 定量分析增强（稳健性检验等）
- LaTeX 导出
- Docker 生产部署
- CI/CD

**技术任务：**
- 集成 citeproc-js 或 pycsl
- 定性编码 UI 组件
- 定量分析扩展
- LaTeX 模板
- Dockerfile 优化
- GitHub Actions

**不做什么：**
- 不碰多用户协作
- 不碰云同步
- 不碰投稿全流程

---

## 14. 验收标准

| 验收项 | 验收方式 | 命令/操作 | 通过标准 |
|--------|---------|---------|---------|
| P1 source trace | 自动化脚本 | `python scripts/verify_source_trace.py` | 每条引用可追溯到 rag_chunks 表中的 chunk_id |
| P1 grounded writing | 自动化脚本 | 导入 3 篇测试文献 → 生成初稿 → 运行验证 | 至少 50% 段落有 source_traces 记录 |
| P1 feedback rewrite | 手工 | 选中段落 → 点"改写" → 查看 diff → 点"回滚" | diff 显示原始 vs 改写（红删绿增），回滚后内容恢复到改写前 |
| P1 version history | 手工 | 生成初稿 → 改写 3 次 → 打开版本历史 | 显示 4 个版本（初始 + 3 次改写），可选择任意版本回滚 |
| 文献导入→RAG | 自动化脚本 | `python scripts/verify_literature_to_rag.py` | 导入文献后，用文献标题在 RAG 中搜索，返回至少 1 条结果 |
| DOCX 导出 Sources | 手工 + 脚本 | 导出 DOCX → 用 python-docx 读取 → 检查末尾页 | 末尾页标题为 "Sources"，列出所有被引用 chunk 的序号和出处 |
| Web UI 主路径 | 手工 | 从首页开始 → 创建项目 → 搜索文献 → 导入 → 生成 → 导出 | 11 步主路径每步可操作，无 console error，无白屏 |
| API 测试 | 脚本 | `pytest tests/ -v --tb=short` | 全部通过，0 failed，0 error |
| 全量测试 | 脚本 | `pytest tests/ --cov=app --cov-report=term` | P1 ≥ 30%，P2 ≥ 50%，P3 ≥ 70% |
| 数据迁移验证 | 脚本 | `python scripts/verify_migration.py --dry-run` → 确认无误 → `--apply` | 迁移后 SQLite 中 literature_items 和 claims 表数据与原 JSON/JSONL 一致 |

---

## 15. 明确不做什么

| 不做什么 | 为什么 |
|---------|--------|
| 不开发 PyQt6 新功能 | 冻结桌面端，全力 Web |
| 不做多用户协作 | 当前单人场景 |
| 不做云同步 | 本地优先承诺 |
| 不做全自动代写 | 违背产品原则 |
| 不做投稿全流程 | 不做期刊投稿系统 |
| 不做 Blueprint 可视化编辑器 | 空壳，用户不需要 |
| 不做 Skill Library 空壳 | 功能未接通 |
| 不做 Collaboration/Submission/Data Charts | 空壳页面 |
| 不把 CRUD 叫 AI | 诚实标注 |
| 不把规则引擎叫 AI | 诚实标注 |
| 不把后端能力叫用户可用 | 前端未接就是不可用 |

---

## 16. 最大风险与缓解方案

| 风险 | 严重度 | 缓解方案 |
|------|:--:|---------|
| 数据迁移破坏现有数据 | 🔴 | 先备份 `~/.wenbiao/thesisx.db` 到 `~/.wenbiao/backups/`，迁移脚本加 `--dry-run` 模式 |
| 数据迁移后旧代码仍引用 JSON 路径 | 🔴 | 迁移后全局搜索 `lit_dir`/`CLAIMS_DIR`/`.json`/`.jsonl`，确保所有引用已更新 |
| Agent 改 RAG 后生成质量下降 | 🟡 | A/B 对比：静态 context vs 实时 RAG，用相同 prompt 生成 3 次取平均 |
| 砍掉 PyQt6 后桌面端用户流失 | 🟡 | 桌面端用户少（当前无外部用户），Web 端体验更好 |
| Semantic Scholar API 不可用 | 🟡 | 加本地文献搜索作为 fallback；不 fallback 到 mock |
| LLM 生成内容不可靠 | 🟡 | Source Trace 强制标注，用户可验证；无 source trace 的段落阻断导出 |
| 开发周期过长 | 🟡 | P1 只做最小闭环（Source Trace + Grounded Writing），P2/P3 按需调整 |
| 删除 PyQt6 后 Web 端功能未完成 | 🔴 | **先完成 Web 端 P1 功能，再删除 PyQt6**；删除前验证 Web 端可走通全流程 |

---

## 17. 下一步最小行动

### 行动 1：统一数据层

**目标：** 把 Literature JSON 文件和 Evidence JSONL 迁移到 SQLite。

**操作：**
1. 写迁移脚本：读取 JSON 文件 → 写入 SQLite `literature_items` 和 `claims` 表
2. 修改 LiteratureService 和 EvidenceService 的读写逻辑
3. 验证：导入一篇文献 → 在 SQLite 中可查到 → RAG 可检索到

**验收：** `sqlite3 ~/.wenbiao/thesisx.db "SELECT COUNT(*) FROM literature_items"` 返回 > 0

### 行动 2：让 Agent 真正用 RAG

**目标：** 修改 `context_assembler.py`，把读静态文件改为调 `RagService.search()`。

**操作：**
1. 在 `AgentContextAssembler.assemble()` 中注入 `RagService` 实例
2. 替换 `rag_path.read_text()` 为 `rag_service.search(query, top_k=10)`
3. 将检索结果格式化为 context 注入 Agent prompt
4. 验证：生成初稿 → 检查段落是否引用了导入的文献

**验收：** 导入 3 篇文献 → 生成初稿 → 至少 1 段标注了文献来源

### 行动 3：砍掉 PyQt6，确定 Web 端为唯一 UI

**目标：** 冻结桌面端代码，不再维护。

**操作：**
1. 删除 `app/ui/` 目录（或归档到 `legacy/` 分支）
2. 删除 `main.py`（桌面端入口）
3. 更新 README 移除 PyQt6 相关内容
4. 验证：`uvicorn thesisx_api.main:app` + `npm run dev` 可正常启动

**验收：** Web 端可完成 P1 主路径全部操作

---

## 18. P4：协作与研究社区（远期愿景）

> **前提：** P1-P3 的单人研究陪跑体验已经成熟，用户留存和口碑验证了产品价值。
> **时间：** P3 完成后 6-12 个月，视资源决定。

### 18.1 阶段目标

从"单人研究陪跑"升级为"有协作的研究工作台"，让导师、同门、合作者能围绕同一项目工作。

### 18.2 用户价值

- 导师可以在学生论文上直接批注，而不是导出 Word 再邮件来回
- 同门可以共享文献库和理论框架，减少重复劳动
- 合作者可以各自负责不同章节，最终合并

### 18.3 功能清单

#### 18.3.1 导师-学生协作

| 功能 | 用户场景 | 如何实现 | 验收标准 |
|------|---------|---------|---------|
| 项目分享 | 学生把论文项目分享给导师 | 生成分享链接 + 可选密码 | 导师打开链接 → 看到学生的论文 |
| 行内批注 | 导师在论文段落上直接批注 | 类似 Notion/Google Docs 的评论系统 | 批注出现在段落右侧，可回复 |
| 修改建议 | 导师建议修改某段 → AI 生成改写方案 | 批注 + AI Rewrite 结合 | 导师批注"这段逻辑不通" → AI 建议改写 |
| 审核状态机 | 草稿 → 导师审核 → 修改 → 再审 → 通过 | 状态流转 + 通知 | 学生在面板看到当前状态和下一步 |
| 版本对比 | 导师对比学生修改前后的版本 | 双栏 diff 视图 | 红色删除、绿色新增，清晰可读 |

#### 18.3.2 同门协作

| 功能 | 用户场景 | 如何实现 | 验收标准 |
|------|---------|---------|---------|
| 共享文献库 | 同门共用一套文献库 | 项目级权限：只读/可编辑/管理员 | 同门可在自己项目中引用共享文献 |
| 共享理论框架 | 同门共用理论匹配结果 | 理论和 Claim 可选择共享范围 | 同门看到"同门已用理论"列表 |
| 章节分工 | 合作者各自负责不同章节 | 章节锁定 + 合并 | A 写引言，B 写文献综述，合并后无冲突 |
| 研究备忘录 | 团队共享研究笔记和决策记录 | 项目级 memo 系统 | 每个人可写 memo，按时间线展示 |

#### 18.3.3 同行评议

| 功能 | 用户场景 | 如何实现 | 验收标准 |
|------|---------|---------|---------|
| 匿名评审 | 邀请同学匿名评审论文 | 生成评审链接，不显示作者 | 评审者看到论文，可打分+写评语 |
| 评审模板 | 结构化评审表 | 创新性、方法、论证、写作各维度打分 | 评审结果汇总为雷达图 |
| AI 预评审 | 提交前 AI 先模拟评审 | 基于 Reviewer 节点 + 评审模板 | 返回各维度评分和改进建议 |

### 18.4 技术任务

- 用户系统（注册/登录/权限）
- 项目分享与权限管理
- 实时协作编辑（CRDT 或 OT）
- 批注系统
- 通知系统
- 数据同步（可选云端）

### 18.5 不做什么

- 不做实时协同编辑（Google Docs 级别）——太复杂，先做异步批注
- 不做团队管理后台——先做点对点分享
- 不做组织架构和 SSO——先做简单注册登录
- 不做公有云存储——用户自选是否同步

### 18.6 验收标准

1. 学生分享项目 → 导师打开 → 可批注 → 学生收到通知
2. 同门共享文献库 → 各自项目中可引用共享文献
3. 邀请评审 → 评审者打开链接 → 填写评审表 → 作者收到结果
4. AI 预评审 → 返回各维度评分和改进建议

---

## 19. P5：研究智能与生态（终极愿景）

> **前提：** P4 的协作功能已经验证了多用户场景的价值。
> **时间：** P4 完成后 12-24 个月，视资源和用户规模决定。

### 19.1 阶段目标

ThesisX 不只是工具，而是一个**研究智能平台**——它理解你的研究领域、跟踪你的研究进展、主动推荐你可能需要的资源、帮助你建立学术影响力。

### 19.2 用户价值

- 不再需要每天刷 arXiv/知网，ThesisX 自动告诉你"有 3 篇新论文可能和你的研究相关"
- 写论文时，ThesisX 知道你的研究脉络，推荐的文献越来越精准
- 论文发表后，ThesisX 帮你跟踪引用、推荐可以引用的新研究

### 19.3 功能清单

#### 19.3.1 研究智能

| 功能 | 用户场景 | 如何实现 | 关键挑战 |
|------|---------|---------|---------|
| 个性化文献推荐 | 基于用户研究历史推荐新论文 | 用户兴趣向量 + Semantic Scholar/arXiv 新论文匹配 | 冷启动、推荐准确性 |
| 研究趋势分析 | 用户想了解某个领域的研究热点变化 | 分析 Semantic Scholar 引用网络 + 关键词趋势 | 数据量、分析深度 |
| 研究空白识别 | 用户想知道"这个领域还有什么没被研究" | 文献综述矩阵 + 引用网络分析 + LLM 推理 | 假阳性、LLM 幻觉 |
| 跨项目知识迁移 | 用户做了多个项目，AI 自动发现关联 | 项目间知识图谱 + 相似度计算 | 关联质量、隐私 |
| 研究脉络可视化 | 用户想看自己的研究轨迹 | 项目时间线 + 知识图谱可视化 | 可视化复杂度 |
| 自动文献监控 | 用户设置关注领域，自动推送新文献 | RSS/API 监控 + 相关性过滤 | 信息过载 |

#### 19.3.2 学术影响力

| 功能 | 用户场景 | 如何实现 | 关键挑战 |
|------|---------|---------|---------|
| 引用追踪 | 用户发表论文后，跟踪被引情况 | Google Scholar / Semantic Scholar 引用追踪 | API 限制 |
| 影响力分析 | 用户想看自己的论文影响力 | h-index、引用网络、合作者网络 | 数据完整性 |
| 合作者推荐 | 用户想找合作者 | 研究兴趣匹配 + 引用网络分析 | 隐私、准确性 |
| 投稿策略建议 | 基于论文内容推荐最适合的期刊 | 期刊匹配算法 + 接受率/周期数据 | 数据来源 |

#### 19.3.3 研究生态

| 功能 | 用户场景 | 如何实现 | 关键挑战 |
|------|---------|---------|---------|
| 公开研究主页 | 用户展示自己的研究历程 | 个人主页 + 项目展示 | 隐私控制 |
| 研究模板市场 | 用户分享和复用研究模板 | 模板上传/下载/评分 | 质量控制 |
| 技能市场 | 用户分享自定义 Skill/AI Prompt | Skill 分享 + 评价系统 | 安全审核 |
| 数据集共享 | 用户共享研究数据集 | 数据集上传 + 引用追踪 | 隐私、合规 |
| 开源研究工具集成 | 与 Zotero/Obsidian/Overleaf 深度集成 | API/插件开发 | 维护成本 |
| 学术会议/期刊日历 | 用户管理投稿时间线 | 日历 + 提醒 + 模板 | 数据维护 |

#### 19.3.4 高级 AI 能力

| 功能 | 用户场景 | 如何实现 | 关键挑战 |
|------|---------|---------|---------|
| 多轮研究对话 | 用户和 AI 进行多轮深度研究讨论 | 长上下文 + 记忆系统 + 工具调用 | 上下文管理、推理深度 |
| 研究假设自动生成 | AI 基于文献空白自动提出可验证假设 | 文献综述 + 空白识别 + LLM 推理 | 假设质量、可验证性 |
| 全文自动审稿 | AI 模拟期刊审稿人做完整评审 | 多维度评审 + 结构化输出 | 评审深度、可靠性 |
| 研究复现助手 | AI 帮助用户复现论文结果 | 代码理解 + 数据匹配 + 结果对比 | 技术难度极高 |
| 多语言论文翻译 | 中英论文互译，保持学术风格 | 学术翻译专用模型 + 术语库 | 术语一致性、风格保持 |
| 演讲/海报生成 | 基于论文自动生成会议演讲 PPT/海报 | 内容提取 + 视觉设计 | 设计质量 |

### 19.4 技术架构升级

```
P1-P3: 本地单机架构
  FastAPI + SQLite + FAISS + Next.js

P4: 协作架构
  + 用户系统 (PostgreSQL)
  + 实时协作 (WebSocket/CRDT)
  + 通知系统 (消息队列)
  + 可选云同步 (对象存储)

P5: 智能平台架构
  + 推荐引擎 (向量检索 + 协同过滤)
  + 知识图谱 (Neo4j/图数据库)
  + 研究智能 Pipeline (定时任务 + 事件驱动)
  + 多模态 AI (PDF/图片/表格理解)
  + 插件系统 (第三方集成)
  + API 开放平台 (开发者生态)
```

### 19.5 不做什么（即使 P5）

| 不做什么 | 理由 |
|---------|------|
| 不做论文代写 | 违背学术伦理 |
| 不做学术造假 | 红线 |
| 不做论文买卖 | 红线 |
| 不做学术评价排名 | 价值观问题 |
| 不做社交网络 | ThesisX 是工具，不是社交平台 |
| 不做通用 AI 助手 | 聚焦研究场景 |
| 不做企业知识管理 | 聚焦学术研究 |

### 19.6 产品终极形态

> **ThesisX 最终形态：一个研究者的第二大脑。**
>
> 它不只是帮你写论文，而是：
> - 记住你研究过的每一个方向
> - 理解你的研究兴趣和学术脉络
> - 在你需要时主动提供最相关的文献、理论、方法
> - 连接你和你的导师、同门、合作者
> - 帮助你从学生研究者成长为独立学者
>
> **它不是替代你的思考，而是放大你的研究能力。**

---

## 20. 产品路线图全景

| 阶段 | 时间 | 目标 | 核心交付 | 用户规模预期 |
|------|------|------|---------|------------|
| P1 | 3-4 周 | 可信知识驱动写作闭环 | Source Trace + Grounded Writing + Web | 你自己 + 内测 |
| P2 | 4-6 周 | 真实研究流程增强 | 文献综述矩阵 + 理论增强 + Evidence | 早期用户 10-50 |
| P3 | 6-8 周 | 研究方法与交付增强 | CSL + 定性编码 + 定量增强 + Docker | 公测 50-200 |
| P4 | 6-12 月 | 协作与研究社区 | 导师协作 + 同门共享 + 同行评议 | 增长期 200-2000 |
| P5 | 12-24 月 | 研究智能与生态 | 推荐引擎 + 知识图谱 + 影响力追踪 | 规模期 2000+ |

**注意：P4 和 P5 的启动条件是 P1-P3 验证了单人研究陪跑的产品价值。如果单人场景都没人用，协作和智能就是空中楼阁。**

---

## 21. P4/P5 功能优先级矩阵

| 功能 | 用户价值 | 技术难度 | 依赖 | 建议优先级 |
|------|:--:|:--:|------|:--:|
| 导师-学生协作 | 🔴 极高 | 🟡 中 | 用户系统 | P4 首批 |
| 行内批注 | 🔴 极高 | 🟡 中 | 项目分享 | P4 首批 |
| 个性化文献推荐 | 🔴 极高 | 🔴 高 | 用户画像 | P5 首批 |
| 研究趋势分析 | 🟡 中 | 🔴 高 | 数据积累 | P5 |
| 研究空白识别 | 🟡 中 | 🔴 极高 | LLM 推理 | P5 |
| 同门共享文献库 | 🟡 中 | 🟢 低 | 用户系统 | P4 |
| 共享理论框架 | 🟡 中 | 🟢 低 | 用户系统 | P4 |
| 章节分工 | 🟡 中 | 🟡 中 | 协作编辑 | P4 |
| 匿名评审 | 🟡 中 | 🟢 低 | 项目分享 | P4 |
| AI 预评审 | 🟡 中 | 🟡 中 | Reviewer 节点 | P4 |
| 引用追踪 | 🟡 中 | 🟡 中 | 外部 API | P5 |
| 合作者推荐 | 🟢 低 | 🔴 高 | 用户网络 | P5 |
| 公开研究主页 | 🟢 低 | 🟢 低 | 用户系统 | P5 |
| 研究模板市场 | 🟢 低 | 🟡 中 | 用户系统 | P5 |
| 多轮研究对话 | 🟡 中 | 🔴 极高 | 长上下文 | P5 |
| 全文自动审稿 | 🟡 中 | 🔴 极高 | LLM 推理 | P5 |
| 演讲/海报生成 | 🟢 低 | 🟡 中 | 多模态 AI | P5 |
| 插件系统 | 🟡 中 | 🔴 极高 | 平台架构 | P5 |

---

---

## 22. Invariants（不可破坏规则）

> 以下规则是 ThesisX 的宪法。任何功能、任何阶段、任何 Agent 都不可违反。

| # | Invariant | 违反后果 | 检测方式 |
|---|-----------|---------|---------|
| I1 | **AI 不替用户做研究判断。** 理论选择、Claim 确认、文献质量判断——必须用户决定 | 学术不端风险 | 所有 AI 输出必须标注"建议，请确认" |
| I2 | **每个 AI 写作段落必须可追溯到 source chunk。** 无来源的段落不允许出现 | 产品核心价值崩塌 | 验收脚本检查 SourceTrace 覆盖率 |
| I3 | **本地数据永不自动发送到远程。** 用户必须显式触发才能发送 | 隐私泄露，用户信任崩塌 | 所有网络请求必须经过用户确认 |
| I4 | **API Key 只存环境变量或系统 Keychain，不存配置文件。** | 安全漏洞 | 代码审查 + 安全扫描 |
| I5 | **不修改用户原始文件（Zotero/Obsidian/PDF）。** 默认只读 | 数据损坏 | 所有导入操作只读源文件 |
| I6 | **Mock 不能声称是真实功能。** | 用户误判产品能力 | 前端必须标注数据来源 |
| I7 | **不破坏已有功能。** 每次变更必须通过全量测试 | 回归 bug | CI pipeline |
| I8 | **数据层必须统一。** 所有模块走 SQLite，不允许新增 JSON/JSONL 存储 | 数据孤岛，无法追踪 | 代码审查 |
| I9 | **删除项目时必须级联删除所有关联数据。** | 数据残留 | 验收脚本 |
| I10 | **前端未接的功能不等于产品可用。** | 虚假进度 | 只有前端可操作的功能才算完成 |

---

## 23. 用户故事（User Stories）

> 每个 Must-Have 功能必须有对应的用户故事。故事格式：As a [用户], I want [功能], so that [价值].

### 23.1 P1 用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|:--:|
| US1 | 作为一个社科学生，我输入"AI 对大学生学习的影响"，系统自动帮我拆解为可操作的研究问题 | 返回关键词+学科+3个研究方向 | P1 |
| US2 | 作为一个社科学生，我可以搜索 Semantic Scholar 并导入文献到我的项目 | 搜索返回 10+ 结果，导入后可在知识库中看到 | P1 |
| US3 | 作为一个社科学生，我可以上传 PDF/DOCX 文件，系统自动解析为可检索的知识条目 | 上传后可在 RAG 中检索到文件内容 | P1 |
| US4 | 作为一个社科学生，我点击"生成初稿"，AI 基于我的知识库生成论文，每段标注来源 | 至少 50% 段落有 source trace | P1 |
| US5 | 作为一个社科学生，我可以点击任意引用标注，跳转到原始文献片段 | 点击 [C1] → 显示来源 chunk 详情 | P1 |
| US6 | 作为一个社科学生，我选中不满意的段落，AI 基于原来源重新改写 | 显示 diff，可接受或回滚 | P1 |
| US7 | 作为一个社科学生，我可以查看每次改写的版本历史，并回滚到任意版本 | 版本列表可查看，回滚后内容恢复 | P1 |
| US8 | 作为一个社科学生，我可以导出论文为 DOCX，包含完整的引用和 Sources 清单 | DOCX 可打开，含 Sources 页 | P1 |
| US9 | 作为新用户，我首次打开 ThesisX 时看到引导流程，知道如何开始 | 引导流程完成首次项目创建 | P1 |

### 23.2 P2 用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|:--:|
| US10 | 作为一个社科学生，系统自动为我的文献生成综述矩阵 | 矩阵含作者、年份、方法、发现、与本研究关系 | P2 |
| US11 | 作为一个社科学生，系统推荐理论时解释为什么适合我的研究 | 推荐含解释和局限性 | P2 |
| US12 | 作为一个社科学生，系统自动从知识库提取 Claim 并建议匹配的 Evidence | 自动提取 3+ Claim，匹配对应 Evidence | P2 |
| US13 | 作为一个社科学生，系统根据我的研究问题推荐合适的研究方法 | 推荐方法含理由和适用条件 | P2 |
| US14 | 作为一个社科学生，我可以一键检查论文引用是否一致 | 文内引用 vs 参考文献交叉验证 | P2 |

### 23.3 P3 用户故事

| ID | 用户故事 | 验收标准 | 优先级 |
|----|---------|---------|:--:|
| US15 | 作为一个社科学生，我可以用 GB/T 7714 格式导出引用 | 引用格式符合国标 | P3 |
| US16 | 作为一个社科学生，我可以对访谈材料进行初步编码 | 编码结果可导出 | P3 |
| US17 | 作为一个社科学生，我可以做简单的描述统计和回归分析 | 描述统计和 OLS 结果可验证 | P3 |

---

## 24. 分支路径与边界条件

> 主路径是"Happy Path"。以下是用户可能遇到的分支路径和边界条件。

### 24.1 用户没有 API Key

| 场景 | 用户行为 | 系统行为 | 当前状态 |
|------|---------|---------|:--:|
| 搜索文献 | 点击搜索 | Semantic Scholar 无需 API Key，但有限速 | 🟢 已处理 |
| AI 写作 | 点击生成 | **阻断**：提示"请先配置 AI Provider"，引导到设置页 | 🔴 需实现 |
| 拆题/推荐 | 输入研究问题 | **阻断**：提示"需要 AI Provider 才能使用此功能" | 🔴 需实现 |

### 24.2 搜索失败

| 场景 | 用户行为 | 系统行为 | 当前状态 |
|------|---------|---------|:--:|
| Semantic Scholar 限速 | 点击搜索 | 显示"搜索暂时不可用，请稍后重试"，**不 fallback 到 mock** | 🔴 当前有 mock fallback 掩盖失败 |
| 搜索无结果 | 点击搜索 | 显示"未找到相关文献，请尝试其他关键词" | 🟡 需实现 |

### 24.3 文件导入失败

| 场景 | 系统行为 | 当前状态 |
|------|---------|:--:|
| PDF 无元数据 | 用文件名作为标题，提取第一页文本作为摘要 | 🟢 已实现 |
| PDF 加密/损坏 | 显示"无法解析此文件，请检查文件是否完整" | 🔴 需实现 |
| DOCX 格式异常 | 显示"无法解析此文件，请尝试另存为标准 DOCX" | 🔴 需实现 |
| 文件超过 50MB | 阻断上传，提示"文件过大，请压缩后重试" | 🟢 已实现 |
| 不支持的文件格式 | 阻断上传，提示"仅支持 PDF/DOCX 格式" | 🟢 已实现 |

### 24.4 AI 生成失败

| 场景 | 系统行为 | 当前状态 |
|------|---------|:--:|
| API 超时 | 显示"生成超时，请检查网络或稍后重试"，保留已生成内容 | 🔴 需实现 |
| API 余额不足 | 显示"API 余额不足，请检查账户" | 🔴 需实现 |
| 生成内容过短 | 标记"生成内容可能不完整"，建议用户补充或重试 | 🔴 需实现 |
| 生成内容无 source trace | **阻断导出**，提示"此段落无来源标注，请检查后重试" | 🔴 需实现 |

### 24.5 用户操作边界

| 场景 | 系统行为 | 当前状态 |
|------|---------|:--:|
| 删除已有 source trace 的段落 | 提示"此段落有来源标注，删除后无法恢复" | 🔴 需实现 |
| 导出时 Sources 清单为空 | 提示"当前论文无来源标注，导出将不包含 Sources 页" | 🔴 需实现 |
| 项目删除 | 确认"删除后所有关联数据将被清除，不可恢复" | 🔴 需实现 |
| 切换项目时未保存 | 提示"当前有未保存的修改，是否保存？" | 🔴 需实现 |

---

## 25. 竞品分析

> 了解 ThesisX 在什么位置，与谁竞争，差异化在哪。

### 25.1 竞品矩阵

| 产品 | 类型 | 核心能力 | 用户群 | ThesisX 优势 | ThesisX 劣势 |
|------|------|---------|--------|-------------|-------------|
| **ChatGPT/Claude** | 通用 AI 助手 | 自由对话写作 | 所有人 | 知识库驱动、可追溯、研究流程 | 上手门槛、功能深度 |
| **Jenni AI** | AI 论文写作 | 自动补全、引用、改写 | 英文论文写作者 | 中文本地化、理论匹配、社科适配 | 英文写作体验、品牌认知 |
| **Paperpal** | 学术写作辅助 | 语法检查、学术改写 | 英文学术写作者 | 知识库、RAG、中文社科 | 语言检查、期刊投稿 |
| **Zotero** | 文献管理 | 文献收集、引用管理 | 所有研究者 | 知识库、AI 写作、研究流程 | 文献管理深度、插件生态 |
| **Notion AI** | 知识管理+AI | 笔记、数据库、AI 辅助 | 知识工作者 | 研究流程专业化、可追溯 | 灵活性、通用性 |
| **Elicit** | AI 研究助手 | 文献搜索、摘要、对比 | 研究者 | 中文支持、本地知识库、全流程 | 文献搜索深度、英文 |
| **Scite_** | 引文分析 | 引用上下文分析 | 研究者 | 写作辅助、全流程 | 引文分析深度 |
| **知网研学** | 中文文献管理 | 知网文献、笔记 | 中文学生 | 开放文献源、AI 写作、理论 | 知网文献量 |

### 25.2 ThesisX 的差异化定位

| 维度 | ThesisX | 竞品 |
|------|---------|------|
| 数据主权 | **本地优先**，数据在用户电脑 | 云端存储，数据在厂商服务器 |
| 可追溯性 | **每段 AI 写作标注来源 chunk** | 大部分不标注，或只标注文献 |
| 研究流程 | **全流程陪跑**：选题→文献→理论→证据→写作→导出 | 单一环节工具 |
| 目标用户 | **中文社科学生**，学科适配 | 通用或英文为主 |
| 理论框架 | **社会科学理论匹配**（30+ 理论） | 不提供 |
| 隐私 | **API Key 本地存储**，数据不离开用户 | 数据在云端 |

### 25.3 竞品会怎么攻击 ThesisX

1. "你的文献库才 30 个理论，我用 ChatGPT 可以匹配任何理论"
2. "你的编辑器不如 Word/Overleaf，我为什么要在这里写？"
3. "你依赖 Semantic Scholar，中文文献很少，我还是要用知网"
4. "你要求我自己配 API Key，Jenni AI 直接内置了"
5. "你的 UI 不如 Notion 好看，功能不如 Zotero 全"

**ThesisX 的回应：**
1. "30 个理论是针对社科论文精心筛选的，每个都有适用性解释和局限性——ChatGPT 不会告诉你理论不适用的情况"
2. "编辑器不是你的主要写作工具，是 AI 辅助的编辑场所——最终你还是导出到 Word 排版"
3. "Semantic Scholar 是起点，P2 会接入 Zotero 实时同步和本地文件导入"
4. "自己配 API Key 意味着数据隐私——你的论文不会经过我们的服务器"
5. "我们不是 Notion，不是 Zotero——我们是研究陪跑，专注的是研究流程而非单一功能"

---

## 26. 成功指标（KPIs）

> 这些指标用于判断 P1/P2/P3 是否成功，以及产品是否在正确的方向上。

### 26.1 产品健康指标

| 指标 | P1 目标 | P2 目标 | P3 目标 | 测量方式 |
|------|:--:|:--:|:--:|---------|
| 新用户首次完成全流程比例 | ≥ 50% | ≥ 70% | ≥ 80% | 统计完成"创建项目→导出论文"的用户占比 |
| Source Trace 覆盖率 | ≥ 50% | ≥ 70% | ≥ 85% | 统计 AI 生成段落中有 source trace 的比例 |
| 用户反馈改写使用率 | ≥ 30% | ≥ 50% | ≥ 60% | 统计使用改写功能的用户占比 |
| 文献导入成功率 | ≥ 90% | ≥ 95% | ≥ 98% | 统计导入操作成功/失败比例 |
| 搜索成功率 | ≥ 80% | ≥ 90% | ≥ 95% | 统计 Semantic Scholar 搜索返回结果的比例 |
| 导出成功率 | ≥ 95% | ≥ 98% | ≥ 99% | 统计导出操作成功/失败比例 |

### 26.2 技术健康指标

| 指标 | P1 目标 | P2 目标 | P3 目标 |
|------|:--:|:--:|:--:|
| 测试覆盖率 | ≥ 30% | ≥ 50% | ≥ 70% |
| API 响应时间（P95） | < 2s | < 1.5s | < 1s |
| RAG 检索延迟（P95） | < 500ms | < 300ms | < 200ms |
| AI 写作生成时间（P95） | < 60s | < 45s | < 30s |
| 前端首屏加载时间 | < 3s | < 2s | < 1.5s |

### 26.3 用户满意度指标

| 指标 | 测量方式 |
|------|---------|
| 论文完成率 | 开始项目 → 导出论文的用户比例 |
| 功能发现率 | 使用 ≥ 3 个不同功能的用户比例 |
| 回访率 | 7 天内再次使用的用户比例 |
| NPS | 通过"你会推荐给同学吗"调查 |

---

## 27. 系统架构设计（Gate 3 补充）

### 27.1 技术选型（唯一，不可模糊）

| 选型 | 决策 | 替代方案 | 为何不选 |
|------|------|---------|---------|
| 后端框架 | **FastAPI** | Flask, Django | FastAPI 原生 async、自动 OpenAPI、Pydantic 集成 |
| 前端框架 | **Next.js 15** | React SPA, Vue, Svelte | 已有代码、SSR 可选、App Router |
| 数据库 | **SQLite** | PostgreSQL, MySQL | 本地优先、零配置、单文件 |
| 向量检索 | **FAISS** | ChromaDB, Milvus, Qdrant | 轻量、本地、Python 原生 |
| 全文检索 | **FTS5** | Elasticsearch, Meilisearch | SQLite 内置、零运维 |
| 状态管理 | **localStorage + React state** | Redux, Zustand, Jotai | 当前规模不需要全局状态管理 |
| CSS | **CSS Modules** | Tailwind, styled-components | 已有 globals.css，保持简单 |
| 引用引擎 | **citeproc-js（P3）** | 手写, pycsl | 标准 CSL 引擎，支持 10,000+ 格式 |
| LLM Provider | **DeepSeek（默认）** | OpenAI, Qwen | 性价比高、中文好、API 兼容 OpenAI |
| 部署 | **本地 dev server** | Docker, Vercel | 本地优先，P3 加 Docker |
| 测试 | **pytest** | unittest, nose | 已有 641 测试，生态成熟 |

### 27.2 系统分层

```
┌────────────────────────────────────────────────┐
│                   UI Layer                      │
│  Next.js Pages → Components → API Client        │
├────────────────────────────────────────────────┤
│                  API Layer                      │
│  FastAPI Routers → Pydantic Schemas → Auth     │
├────────────────────────────────────────────────┤
│               Service Layer                     │
│  ProjectService  │ LiteratureService            │
│  KnowledgeService│ TheoryMatcher               │
│  EvidenceService │ RagService                  │
│  PipelineService │ ExportService               │
├────────────────────────────────────────────────┤
│                 Data Layer                      │
│  SQLite (all tables) │ FAISS (vectors)         │
│  File System (runs/│ imports/)                 │
├────────────────────────────────────────────────┤
│              External Services                  │
│  Semantic Scholar │ LLM API │ Zotero API       │
└────────────────────────────────────────────────┘
```

### 27.3 数据流（不可变）

```
用户输入 → API Router → Service → SQLite
                                  ↓
用户导入 PDF/DOCX → Importer → Parser → Chunker → SQLite + FAISS
                                                      ↓
用户搜索文献 → Semantic Scholar API → LiteratureItem → SQLite
                                                           ↓
用户匹配理论 → TheoryMatcher → TheoryCandidate → 返回 UI
                                                      ↓
用户查询 RAG → RagService → BM25 + FAISS → RagResult[] → 返回 UI
                                                            ↓
用户生成写作 → PipelineService → ContextAssembler → RagService.search()
                                                       ↓
                                                  LLM API
                                                       ↓
                                                  WritingBlock + SourceTrace → SQLite
                                                                                   ↓
用户改写 → PipelineService → 原 WritingBlock + SourceTrace → LLM → RewriteVersion → SQLite
                                                                                         ↓
用户导出 → ExportService → 读取 WritingBlock + SourceTrace + Citation → DOCX + Sources
```

**数据流禁令：**
- ❌ UI 层不允许直接访问 SQLite
- ❌ Service 层不允许直接调用 LLM API（必须通过 PipelineService）
- ❌ 不允许绕过 RagService 直接读 FAISS 索引
- ❌ 不允许在 API Router 中写业务逻辑

### 27.4 Single Source of Truth（SSOT）

| 数据类型 | SSOT | 缓存/索引 | 备注 |
|---------|------|---------|------|
| 项目信息 | SQLite `projects` | — | — |
| 研究问题 | SQLite `research_questions` | — | — |
| 文献条目 | SQLite `literature_items`（P1 迁移后） | — | 当前是 JSON 文件 |
| 知识条目 | SQLite `knowledge_items` | — | — |
| 论点 | SQLite `claims`（P1 迁移后） | — | 当前是 JSONL |
| 证据 | SQLite `evidence_items`（P1 迁移后） | — | 当前是 JSONL |
| RAG 分块 | SQLite `rag_chunks` | FAISS 向量索引 | FAISS 是 SQLite 的缓存 |
| 写作段落 | SQLite `writing_blocks`（新增） | — | — |
| 来源追踪 | SQLite `source_traces`（新增） | — | — |
| 引用记录 | SQLite `citations` | — | — |
| 改写版本 | SQLite `rewrite_versions`（新增） | — | — |
| 运行记录 | 文件系统 `~/.wenbiao/runs/` | SQLite `runs` 表 | 文件系统为主 |
| Provider 配置 | 环境变量 | `providers.json` | 环境变量优先 |

---

## 28. Agent 系统设计（Gate 4 补充）

### 28.1 开发 Agent 角色分工

| 角色 | 职责 | 对应开发阶段 |
|------|------|------------|
| **产品经理 Agent** | 需求分析、用户故事、验收标准 | 每个 Phase 开始前 |
| **架构师 Agent** | 技术选型、系统设计、数据模型 | Gate 3 阶段 |
| **项目经理 Agent** | 任务分解、里程碑、依赖管理 | 每个 Phase 规划 |
| **前端工程师 Agent** | Next.js 页面、组件、API client | 前端任务 |
| **后端工程师 Agent** | FastAPI 路由、Service、数据迁移 | 后端任务 |
| **审核者 Agent** | Code Review、质量把控、架构合规 | 每个任务完成后 |
| **调试者 Agent** | Bug 定位、修复验证 | 测试失败时 |

### 28.2 Memory 系统

| 层级 | 存储 | 内容 | 生命周期 |
|------|------|------|---------|
| Long-term | `docs/PRD.md`、`docs/ARCHITECTURE.md`、`docs/PRODUCT_DECISIONS.md` | 产品定义、架构决策、Invariants | 跨版本 |
| Mid-term | `~/.wenbiao/agent_feedback.json`、`~/.wenbiao/runs/` | 用户反馈、运行历史、已知问题 | 跨会话 |
| Short-term | Session 上下文 | 当前任务、用户偏好、最近操作 | 当前会话 |

### 28.3 错误控制机制

| 机制 | 实现方式 | 触发条件 |
|------|---------|---------|
| 已知问题列表 | `KNOWN_ISSUES.md` | 每次发现新 bug 时记录 |
| 回归测试 | `pytest tests/` | 每次 commit 前 |
| 架构合规检查 | Code Review checklist | 每个 PR |
| 数据一致性检查 | 验收脚本 | 每个 Phase 结束 |
| Source Trace 验证 | 自动化脚本 | 每次 AI 写作后 |
| 回滚机制 | Git revert + 数据备份 | 部署失败时 |

---

## 29. 稳定性保障（Gate 5 补充）

### 29.1 变更溯源

每次修改必须记录：
- **What：** 改了什么（commit message）
- **Why：** 为什么改（PR description）
- **Who：** 谁改的（git author）
- **Impact：** 影响哪些模块（PR checklist）

### 29.2 回归测试套件

```bash
# P1 回归测试（每次 commit 必须通过）
pytest tests/unit/test_knowledge_store.py
pytest tests/unit/test_rag_service.py
pytest tests/unit/test_project_service.py
pytest tests/unit/test_literature_service.py
pytest tests/unit/test_pipeline_events.py
pytest tests/unit/test_export.py

# P1 集成测试（每次 PR 必须通过）
pytest tests/integration/
```

### 29.3 快速回滚

- 保留上一个稳定版本的 Git tag（如 `v1.0-stable`）
- 数据迁移前自动备份 `~/.wenbiao/thesisx.db` → `~/.wenbiao/backups/thesisx_YYYYMMDD.db`
- 迁移脚本支持 `--dry-run` 和 `--rollback`

### 29.4 监控告警

| 指标 | 告警阈值 | 处理方式 |
|------|---------|---------|
| Semantic Scholar API 可用性 | 连续 3 次失败 | 通知用户，降级到本地搜索 |
| LLM API 可用性 | 连续 2 次失败 | 通知用户检查 API Key |
| 数据库文件大小 | > 1GB | 提醒用户清理或压缩 |
| RAG 索引大小 | > 100K chunks | 提醒用户可能影响性能 |
| 测试覆盖率下降 | < 目标值 | 阻断 PR |

---

## 30. 术语表（Glossary）

| 术语 | 定义 |
|------|------|
| **Source Trace** | 从 AI 写作段落到 RAG chunk 的追溯链路 |
| **Grounded Writing** | 基于 RAG 实时检索结果（而非静态文件或 LLM 记忆）的 AI 写作 |
| **RAG Chunk** | 知识库文档被分割后的最小检索单元 |
| **Claim** | 研究论文中的核心论点 |
| **Evidence** | 支撑 Claim 的证据，来自文献或数据 |
| **Source Document** | 用户导入的原始 PDF/DOCX 文件 |
| **Knowledge Item** | 知识库中的条目，类型可以是 literature/note/theory/evidence |
| **Context Bundle** | 注入 AI 写作的上下文信息包 |
| **Pipeline** | AI 写作的完整执行流程 |
| **Blueprint** | 定义 Pipeline 节点和边的 YAML 配置 |
| **MCP** | Model Context Protocol，AI 工具调用的标准协议 |
| **CSL** | Citation Style Language，引用格式定义语言 |
| **SSOT** | Single Source of Truth，单一数据源 |
| **Invariant** | 不可破坏的产品/技术规则 |

---

## 31. 需要人类确认的问题清单

> 以下问题需要你（产品负责人）确认后才能进入开发。按优先级排序。

### 🔴 必须确认（阻塞 P1 开发）

| # | 问题 | 选项 | 当前假设 |
|---|------|------|---------|
| Q1 | P1 结束后是否立即砍掉 PyQt6 代码？ | A) 是，删除 / B) 归档到 legacy 分支 | 假设 A |
| Q2 | AI 写作的默认 Provider 用哪个？ | A) DeepSeek / B) Qwen / C) 让用户自选 | 假设 A |
| Q3 | 是否接受 P1 不碰 Zotero 实时同步？ | A) 是 / B) 必须做 | 假设 A |

### 🟡 建议确认（影响 P1 范围）

| # | 问题 | 选项 | 当前假设 |
|---|------|------|---------|
| Q4 | 是否接受 P1 只做 Semantic Scholar 一个文献源？ | A) 是 / B) 加 CNKI | 假设 A |
| Q5 | 是否接受 P1 导出只有 DOCX + Markdown？ | A) 是 / B) 加 LaTeX | 假设 A |
| Q6 | Agent 改 RAG 后，是否保留静态文件 fallback？ | A) 是 / B) 不保留，直接报错 | 假设 A |

### 🟢 次要确认（影响 P2+）

| # | 问题 | 当前假设 |
|---|------|---------|
| Q7 | 文献迁移到 SQLite 后，是否删除旧的 JSON 文件？ | 假设 B（保留作为备份） |
| Q8 | 测试覆盖率 P1 目标 30%，是否接受？ | 假设 A（接受） |
| Q9 | Blueprint 编辑器是否完全隐藏？ | 假设 是 |
| Q10 | Approval Inbox 是否完全删除？ | 假设 是 |
| Q11 | Skill Library 是否后置到 P3？ | 假设 是 |

---

## 32. 开发团队协作规范

### 32.1 分支策略

```
main ← 稳定版本，只接受 PR
  ├── p1/unified-data-layer
  ├── p1/grounded-writing
  ├── p1/source-trace
  ├── p1/feedback-rewrite
  ├── p1/remove-pyqt6
  └── ...
```

### 32.2 Commit 规范

```
feat: 新功能
fix: 修复 bug
refactor: 重构
test: 测试
docs: 文档
chore: 构建/工具
data: 数据迁移
```

### 32.3 PR 检查清单

- [ ] 全量测试通过 (`pytest tests/ -v`)
- [ ] 新增功能有测试 (至少 1 个 test case)
- [ ] 不违反任何 Invariant（§22 的 10 条规则）
- [ ] 前端可操作（如是前端功能，在浏览器中验证）
- [ ] API 文档已更新（如是 API 变更）
- [ ] 数据迁移有 dry-run 验证（如是数据变更）
- [ ] TypeScript 类型检查通过 (`npx tsc --noEmit`)
- [ ] Python 类型检查通过 (`mypy app/`)

---

## 33. P1 实现级开发者故事（Implementation Stories）

> 以下是将 §13 P1 路线图拆解为**单个上下文窗口可完成**的开发者故事。
> 每个故事 ≤ 10 分钟 AI 工作量，按依赖顺序排列。

### 33.1 阶段 1：数据层统一（依赖：无）

| ID | 故事 | 输入 | 输出 | 验收 |
|----|------|------|------|------|
| IS-001 | 创建 `literature_items` SQLite 表 | DATA_MODEL.md 中的 schema | 表创建成功，含所有字段和索引 | `sqlite3 .schema literature_items` 有输出 |
| IS-002 | 创建 `claims` + `claim_evidence_links` SQLite 表 | DATA_MODEL.md 中的 schema | 表创建成功，含外键约束 | `sqlite3 .schema claims` 有输出 |
| IS-003 | 创建 `writing_blocks` + `source_traces` + `rewrite_versions` SQLite 表 | §9 数据模型 | 表创建成功 | 3 个 `.schema` 都有输出 |
| IS-004 | Literature JSON → SQLite 迁移脚本 | 读取 `~/.wenbiao/literature/*.json` | 写入 `literature_items` 表，保留原 JSON 文件 | `SELECT COUNT(*) FROM literature_items` = JSON 文件数 |
| IS-005 | Evidence JSONL → SQLite 迁移脚本 | 读取 `~/.wenbiao/evidence/*.jsonl` | 写入 `claims` + `claim_evidence_links` 表 | `SELECT COUNT(*) FROM claims` = JSONL 行数 |
| IS-006 | LiteratureService 改为读写 SQLite | 替换 `lit_dir.glob("*.json")` 为 SQL 查询 | 所有读写操作走 SQLite | 现有测试通过 + 新增测试 |
| IS-007 | EvidenceService 改为读写 SQLite | 替换 `CLAIMS_DIR/*.jsonl` 为 SQL 查询 | 所有读写操作走 SQLite | 现有测试通过 + 新增测试 |
| IS-008 | 项目删除级联清理 | `DELETE FROM projects WHERE id=?` | 级联删除 literature_items/claims/rag_chunks/writing_blocks 等 | 删除项目后所有关联表该 project_id 的行数为 0 |

### 33.2 阶段 2：Agent 真 RAG（依赖：IS-001~003 表创建）

| ID | 故事 | 输入 | 输出 | 验收 |
|----|------|------|------|------|
| IS-009 | AgentContextAssembler 注入 RagService | 修改 `assemble()` 方法签名 | 接受 `rag_service` 参数 | 类型检查通过 |
| IS-010 | 替换静态文件读取为 RagService.search() | 删除 `rag_path.read_text()` | 改为 `rag_service.search(query, top_k=10)` | 单元测试：mock RagService，验证 search 被调用 |
| IS-011 | Agent context 中标注 RAG 来源 | RagResult[] → 格式化 | 每条 fragment 标注 `[source: {title}]` | context 中包含来源标注 |
| IS-012 | PipelineService 传递 RagService 给 ContextAssembler | PipelineService.run() | ContextAssembler 拿到 RagService 实例 | 集成测试：Pipeline 调用 RagService |

### 33.3 阶段 3：Source Trace（依赖：IS-003 表创建 + IS-012）

| ID | 故事 | 输入 | 输出 | 验收 |
|----|------|------|------|------|
| IS-013 | WritingBlock 写入逻辑 | AI 生成的段落 | 写入 `writing_blocks` 表 | `SELECT COUNT(*) FROM writing_blocks` > 0 |
| IS-014 | SourceTrace 写入逻辑 | WritingBlock + RagChunk 关联 | 写入 `source_traces` 表 | 每条 WritingBlock 至少关联 1 条 SourceTrace |
| IS-015 | Source Trace 后端 API | `GET /api/writing/{block_id}/sources` | 返回该段落的所有 source trace | API 返回 JSON 数组 |
| IS-016 | Source Trace 前端面板 | 点击 [C{n}] | 弹出侧栏显示 chunk 详情 | 浏览器中验证 |

### 33.4 阶段 4：Feedback Rewrite（依赖：IS-016）

| ID | 故事 | 输入 | 输出 | 验收 |
|----|------|------|------|------|
| IS-017 | RewriteVersion 写入逻辑 | 改写请求 | 写入 `rewrite_versions` 表 | 改写后 `SELECT COUNT(*) FROM rewrite_versions WHERE writing_block_id=?` = 2+ |
| IS-018 | Web 端 Diff 组件 | 原始文本 + 改写文本 | 双栏对比视图（红删绿增） | 浏览器中验证 |
| IS-019 | 回滚功能 | 选择历史版本 → 回滚 | WritingBlock.content 恢复到历史版本 | 回滚后内容与历史版本一致 |

### 33.5 阶段 5：前端 + 清理（依赖：阶段 3-4 完成）

| ID | 故事 | 输入 | 输出 | 验收 |
|----|------|------|------|------|
| IS-020 | Semantic Scholar 搜索前端入口 | 搜索框 + 结果列表 + 导入按钮 | 用户可在文献发现页搜索和导入 | 浏览器中验证 |
| IS-021 | 新手引导组件 | 5 步引导 UI | 首次打开显示引导流程 | 清除 localStorage 后打开，显示引导 |
| IS-022 | 版本历史前端页面 | 版本列表 + diff 视图 + 回滚按钮 | 用户可查看和回滚版本 | 浏览器中验证 |
| IS-023 | Sources 清单导出 | 读取 source_traces → 格式化 → 追加到 DOCX | DOCX 末尾有 Sources 页 | 用 python-docx 读取验证 |
| IS-024 | 删除 PyQt6 代码 | `rm -rf app/ui/ main.py` | Web 端独立运行 | `npm run dev` + `uvicorn` 正常启动 |

### 33.6 故事依赖图

```
IS-001 ──┐
IS-002 ──┼── IS-004 ── IS-005 ── IS-006 ── IS-007
IS-003 ──┘                                    │
                                               ├── IS-008
                                               │
IS-009 ── IS-010 ── IS-011 ── IS-012
                                    │
IS-013 ── IS-014 ── IS-015 ── IS-016
                                    │
IS-017 ── IS-018 ── IS-019
                                    │
IS-020 ── IS-021 ── IS-022 ── IS-023 ── IS-024
```

**执行顺序：** 阶段 1 → 阶段 2 → 阶段 3 → 阶段 4 → 阶段 5。同一阶段内无依赖的故事可并行。

---

*PRD 结束。本 PRD 包含 33 个章节，覆盖产品定义、用户故事、竞品分析、架构设计、Agent 系统、稳定性保障、成功指标、分支路径、术语表、确认清单、协作规范和 P1 实现级开发者故事。P1/P2/P3 开发以本文档为唯一基准，P4/P5 为远期愿景。所有功能决策以本文档为准。*