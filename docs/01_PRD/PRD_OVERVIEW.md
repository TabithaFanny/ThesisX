# PRD — ThesisX 总产品需求说明

> 定义 ThesisX 的产品级需求总说明：背景、用户痛点、产品目标、非目标、用户角色、核心场景、核心模块、边界、风险。

---

## 1. 背景

ThesisX 起源于一个真实需求：**研究生和研究者需要一个能管理文献、理论、证据，并生成可追溯论文的本地工具**。

现有工具的问题：
- Zotero 只管文献，不管写作
- Notion / Obsidian 是笔记工具，不是论文工具
- ChatGPT / Claude 可以写，但来源不可控、难追溯
- 现有"AI 论文生成器"大多直接输出不可信的文本

ThesisX 的机会：**做一个本地优先的论文 AI 工作台，把知识管理和 AI 写作深度整合，让 AI 写作基于真实文献和证据，而不是自由发挥。**

---

## 2. 用户痛点（8 条）

| # | 痛点 | ThesisX 解决方案 |
|---|------|-----------------|
| P1 | 不知道如何从模糊研究问题找到合适理论 | Theory Matcher：研究问题 → 理论推荐（附理由+边界） |
| P2 | 文献、笔记、证据分散在不同工具里 | 统一 Knowledge Base：文献/笔记/理论/证据集中管理 |
| P3 | AI 写作容易胡编文献和来源 | Evidence Pack + RAG：AI 写作必须基于可追溯证据 |
| P4 | 生成的论文无法追溯引用来源 | citation key 规范 + 引用绑定段落 |
| P5 | AI 生成结果和编辑器割裂 | Editor 闭环：结构化插入+局部改写+diff+回滚 |
| P6 | 导出 docx 格式不稳定 | Export Center：模板化 docx 导出 |
| P7 | 多 Provider 配置复杂 | Provider Settings：统一管理 Local CLI/Remote API/Agent Team |
| P8 | 不知道 AI 发送了什么数据 | 隐私说明：每次 Real 任务前显示数据边界 |

---

## 3. 产品目标

### 3.1 最终产品目标

**让用户能从模糊研究问题出发，完成完整链路：**

```
创建项目 → Research Workspace → 知识库 → 文献管理 → 理论匹配 →
证据组织 → RAG 检索 → AI 写作 → Editor 闭环 →
质量看板 → 引用管理 → 导出 → Run/版本历史追踪
```

### 3.2 MVP 阶段目标（v2.x）

Runtime 最小闭环：
- AI Draft Assistant Mock/Real 可跑
- SessionStore 持久化
- RunHistory 可查看历史
- Provider 配置链路可用

### 3.3 非目标（当前版本不包含）

当前版本不包含以下功能（后续版本可能规划）：
- ~~在线论文数据库（版权风险，维持用户导入模型）~~
- ~~自动选题（用户的研究问题必须自己定）~~
- ~~全自动论文（用户必须参与写作和编辑）~~
- ~~跨团队协作（第一版是本地单人工具）~~
- ~~PDF 全文解析（3.5.1 及后续版本规划）~~
- ~~实时网络检索（当前版本不做）~~
- ~~RAG-Fusion 等高级检索（4.2 及后续版本规划）~~

---

## 4. 用户角色

| 角色 | 描述 | 主要任务 |
|------|------|---------|
| **研究生（MPhil/PhD）** | 有导师指导，需要系统化管理研究材料 | 知识积累、文献管理、AI 辅助写作 |
| **社会科学/公共管理学生** | 需要实证支持，引用管理要求高 | Theory Matcher、Evidence Pack、citation |
| **独立研究者** | 无机构支持，独立完成高质量论文 | 全链路，特别是隐私和本地化 |
| **高校教师** | 申报课题、写期刊论文 | AI 辅助写作、导出模板 |

**第一版本画像：** 有明确研究问题（或方向），本科三年级以上的学生或研究者，英文或中文论文写作经验，对引用规范有基本了解。

---

## 5. 核心场景（6 个）

### 场景 1：从零开始做研究
1. 用户创建新论文项目，输入研究问题
2. 使用 Theory Matcher 找理论框架
3. 导入相关文献（Zotero / Markdown / 手动）
4. 用 Evidence Pack 组织论点-证据链
5. RAG 检索知识库，AI 生成大纲
6. AI 生成各章节初稿，结构化插入 Editor
7. 局部改写和人工编辑
8. 导出 docx / markdown

### 场景 2：基于已有材料写作
1. 用户已有 Obsidian vault / Zotero 库
2. 通过连接器导入现有材料到 ThesisX 知识库
3. 绑定到新论文项目
4. 使用 Theory Matcher 匹配已有材料中的理论
5. RAG 检索已有材料辅助写作
6. AI 生成 + Main Editor 编辑闭环
7. 引用现有文献（citation key 自动生成）
8. 导出并追踪历史版本

### 场景 3：继续未完成的论文
1. 用户打开历史 Run
2. 查看 paper.md 和诊断报告（为什么上次中断）
3. 从上次中断处继续 AI 写作
4. 基于已有的知识库和证据包继续
5. 保存为新版本 Run

### 场景 4：诊断和修复问题
1. Real 模式失败
2. 用户查看 Runtime Diagnostics
3. 系统显示 Provider 健康状态、错误原因
4. 用户根据诊断修复配置
5. 重跑任务

### 场景 5：配置和切换 Provider
1. 用户打开 Provider Settings
2. 系统发现本地 CLI（codex/claude）
3. 用户配置 Remote API（DeepSeek/OpenAI）
4. 系统检测 Agent Team 契约路径
5. 用户切换默认 Provider
6. 验证健康状态

### 场景 6：管理 Skill 和写作模板
1. 用户打开 Skill Library
2. 查看本地 Skill 列表
3. 启用"学术润色" Skill
4. 绑定到"学术写作"任务类型
5. Skill 注入 AI Draft Assistant context
6. 运行结果反映 Skill 影响

---

## 6. 核心模块（12 个）

| # | 模块 | PRD 文档 | 对应 Vision |
|---|------|---------|------------|
| 1 | Research Workspace | `PRD_RESEARCH_WORKSPACE.md` | **3.0** |
| 2 | Knowledge Base | `PRD_KNOWLEDGE_BASE.md` | 3.1 |
| 3 | Literature Intelligence | `PRD_LITERATURE_INTELLIGENCE.md` | 3.2 |
| 4 | Theory Matcher | `PRD_THEORY_MATCHER.md` | 3.3 |
| 5 | Evidence & Argument Pack | `PRD_EVIDENCE_ARGUMENT_PACK.md` | 3.4 |
| 6 | AI→Editor Safe Insert | `PRD_EDITOR_LOOP.md` | 3.4.5 |
| 7 | RAG Context Engine | `PRD_RAG_CONTEXT_ENGINE.md` | 3.5 |
| 8 | Editor AI Loop | `PRD_EDITOR_LOOP.md` | 3.6 |
| 9 | Connectors | `PRD_CONNECTORS.md` | 3.7 |
| 10 | Skill Runtime | `PRD_SKILL_LIBRARY.md` | 3.8 |
| 11 | Export & Delivery | `PRD_EXPORT_DELIVERY.md` | 3.9 |
| 12 | Quality Dashboard | `PRD_QUALITY_DASHBOARD.md` | **3.10** |

---

## 7. 成功指标

### 7.1 产品成功指标

| 指标 | 目标值 |
|------|--------|
| 用户能完整走通红框链路（场景1） | ≥ 80% 完成率 |
| AI 生成结果有可追溯来源 | 100%（citation key + 段落绑定） |
| Real 模式稳定可用 | ≥ 95% 成功率（配置正确情况下） |
| 导出 docx 格式正确 | ≥ 90%（主流模板） |
| 测试覆盖率 | ≥ 80% |

### 7.2 技术成功指标

| 指标 | 目标值 |
|------|--------|
| 冷启动时间 | < 3s |
| AI Run 启动时间 | < 5s（不含模型响应） |
| 知识库检索延迟 | < 500ms（FTS5 单次） |
| UI 响应时间 | < 100ms |

---

## 8. 产品边界

### 8.1 数据边界
- **本地优先：** 所有数据默认存在 `~/.wenbiao/`
- **API 调用可选：** Real 模式需要网络，但不强制
- **用户数据不上传：** 除 Real 模式必要数据外，不上传用户文件

### 8.2 功能边界
- **不提供在线论文数据库：** 维持用户导入模型
- **不自动选题：** 用户研究问题自主
- **不全自动论文：** 用户参与写作和编辑
- **不跨团队协作：** 本地单人工具（v1）

### 8.3 地理边界
- **不限制地区：** 中英文均支持
- **不限制学科：** 理论库覆盖多个学科

---

## 9. 风险控制

| # | 风险 | 严重度 | 缓解措施 |
|---|------|--------|---------|
| R1 | 用户用 AI 生成的论文当作自己写的 | 高 | 明确告知 AI 辅助工具，合规声明，每次 Real 前提示来源 |
| R2 | Real 模式泄露用户数据（文献/笔记） | 高 | 隐私说明明确，Real 前显示摘要，Provider 可切换 |
| R3 | 引用不准确（citation key 错误） | 中 | citation key 规范明确，CSL 校验 |
| R4 | Zotero/Obsidian 写回破坏用户原始文件 | 高 | 默认只读，写回必须显式确认 |
| R5 | 导出 docx 格式不符合学校要求 | 中 | 模板化导出，支持自定义模板 |
| R6 | API 费用超出预期 | 中 | 预算控制（80% 警告，100% 停止），费用实时显示 |
| R7 | Skill prompt 中泄露 API key | 高 | 导入时扫描检测，高置信度阻止启用 |

---

## 10. 分阶段实现路径

| 阶段 | PRD 覆盖 |
|------|---------|
| v2.x Runtime Beta | 核心模块：Run History、Provider Settings、SessionStore |
| v3.1 Knowledge Base | PRD_KNOWLEDGE_BASE.md 完整实现 |
| v3.2 Literature | PRD_LITERATURE_MANAGEMENT.md + Run History 完善 |
| v3.3 Theory Matcher | PRD_THEORY_MATCHER.md |
| v3.4 Evidence Pack | PRD_EVIDENCE_PACK.md |
| v3.5 RAG | PRD_RAG.md |
| v3.6 Editor Loop | PRD_EDITOR_LOOP.md |
| v3.7 Connectors | PRD_CONNECTORS.md |
| v3.8 Skill Library | PRD_SKILL_LIBRARY.md |
| v3.0 Research Workspace | PRD_RESEARCH_WORKSPACE.md — 项目容器、研究问题模型 |
| v3.1 Knowledge Base | PRD_KNOWLEDGE_BASE.md — SQLite + KnowledgeObject + FTS5 |
| v3.2 Literature Intelligence | PRD_LITERATURE_INTELLIGENCE.md — citation key + CSL 导出 |
| v3.3 Theory Matcher | PRD_THEORY_MATCHER.md — 规则+语义混合匹配 |
| v3.4 Evidence & Argument Pack | PRD_EVIDENCE_ARGUMENT_PACK.md — Claim-Evidence 链 |
| v3.4.5 AI→Editor Safe Insert | PRD_EDITOR_LOOP.md — 结构化插入+diff+回滚 |
| v3.5 RAG Context Engine | PRD_RAG_CONTEXT_ENGINE.md — FTS5+Embedding+Rerank |
| v3.5.1 PDF Full-text | PDF 内容解析（后续版本规划） |
| v3.6 Editor AI Loop | PRD_EDITOR_LOOP.md — 局部改写+Undo stack |
| v3.7 Connectors | PRD_CONNECTORS.md — Zotero + Obsidian（只读） |
| v3.8 Skill Runtime | PRD_SKILL_LIBRARY.md — Skill 文件 + 绑定 UI |
| v3.9 Export & Delivery | PRD_EXPORT_DELIVERY.md — 多模板 docx |
| v3.10 Quality Dashboard | PRD_QUALITY_DASHBOARD.md — 写作质量追踪 |
| v4.0 Final Product Beta | 所有模块完成，USER_GUIDE + 隐私说明，测试 ≥ 80% |

---

*本文档是 ThesisX 总 PRD，各模块详细需求见对应 PRD 文档。*
*产品决策以 PRODUCT_DECISIONS.md 为准。*