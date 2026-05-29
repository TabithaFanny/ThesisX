# ThesisX 最终产品蓝图

> 本文档定义 ThesisX 最终长什么样、解决什么问题、用户如何完整使用。
> 后续所有 PRD、技术架构、功能实现都必须与本文档一致。

---

## 1. 产品定位

**ThesisX** 是一个本地优先、知识驱动、可追溯、可配置、多 Provider 的**论文 AI 工作台**。

它不是"论文生成器"。它帮助用户从模糊研究问题出发，逐步完成知识积累、文献整理、理论匹配、证据组织、AI 辅助写作、人工编辑、引用管理、导出与历史追踪。

**一句话定位：** 你的私人论文研究助理——本地运行，知识可控，来源可溯。

---

## 2. 目标用户

| 用户类型 | 需求 |
|---------|------|
| 研究生（MPhil/PhD） | 从零开始做研究，需要理论框架和文献管理 |
| 社会科学/公共管理学生 | 论文写作，需要实证支持和引用管理 |
| 高校教师 | 申报课题、写期刊论文 |
| 独立研究者 | 无机构支持，需要独立完成高质量论文 |

**核心画像：** 有明确研究问题（或方向），需要系统化管理文献、理论、证据，并生成结构化论文。

---

## 3. 核心使用场景

### 场景 A：从零开始研究
1. 用户输入研究问题（模糊概念）
2. 系统推荐相关理论（Theory Matcher）
3. 用户从知识库/Obsidian/Zotero 导入文献
4. 用户用 Evidence Pack 组织证据
5. RAG 辅助写作（基于真实文献）
6. AI 生成大纲/初稿
7. 结构化插入 Main Editor
8. 局部改写和编辑
9. 导出 docx/markdown

### 场景 B：基于已有材料写作
1. 用户已有 Obsidian vault / Zotero 库
2. 导入现有文献和笔记到 ThesisX 知识库
3. 绑定到新论文项目
4. 使用 Theory Matcher 匹配理论框架
5. RAG 检索已有材料辅助写作
6. AI 生成 + Main Editor 编辑闭环
7. 导出并追踪历史版本

### 场景 C：继续未完成论文
1. 用户打开历史 Run
2. 查看 paper.md 和诊断报告
3. 从上次中断处继续
4. 基于已有知识库继续写作

---

## 4. 完整用户旅程（15 步）

```
[创建项目] → [Research Workspace] → [知识库] → [文献管理]
  → [理论匹配] → [证据包] → [RAG检索] → [AI写作]
  → [Editor编辑] → [质量看板] → [引用与导出] → [Run历史追踪]
```

**Step 0：创建论文项目（Vision 3.0）**
- 输入研究问题 / 题目 / 研究方向（模糊概念输入）
- 选择学科领域（影响后续理论推荐）
- 建立项目空间（Project container）
- 定义研究目标和研究方向

**Step 1：Research Workspace 核心（Vision 3.0）**
- 在项目内组织研究材料
- 绑定已有知识对象到项目
- 跟踪项目进度和研究方向
- 管理项目内 Run 和上下文

**Step 2：搭建知识库（Vision 3.1）**
- 导入 Markdown / Obsidian 笔记
- 导入文献元数据（手动 / Zotero）
- 导入理论材料
- 导入案例/数据材料
- 标签化、项目绑定

**Step 3：使用 Theory Matcher（Vision 3.3）**
- 输入研究问题描述
- 接收理论推荐（附适配理由、边界、误用风险）
- 选择理论写入论文框架
- 经典文献推荐

**Step 4：文献管理（Vision 3.2）**
- 管理全局文献库
- citation key 自动生成（authorYearShortTitle）
- 阅读状态跟踪
- 文献-项目绑定粒度控制

**Step 5：创建 Evidence Pack（Vision 3.4）**
- 定义 Claim（核心论点）
- 定义 Subclaim（子论点）
- 绑定 EvidenceItem（证据）
- 记录 quote / page / source
- 分析证据缺口

**Step 6：RAG 检索（Vision 3.5）**
- 自然语言查询知识库
- 精确 + 语义混合检索
- 结果显示来源（可追溯）
- Context Bundle 注入写作

**Step 7：AI 生成初稿（Vision 3.6）**
- 配置 Provider（Local CLI / Remote API / Agent Team）
- 选择 Skill（学术润色 / 逻辑审查等）
- 生成大纲 / 各章节 / 局部改写
- 实时进度和 token 消耗显示

**Step 8：结构化插入 Editor（Vision 3.4.5）**
- 按标题层级插入章节（不是全文覆盖）
- 插入到当前光标 / 替换选中文本 / 新建章节
- 保留格式（标题层级、粗体、列表、引用）
- AI 结果安全插入流程

**Step 9：局部改写（Vision 3.6）**
- 选中部分文本发送给 AI
- 选择改写模式（润色/扩写/补理论/补证据）
- 查看 AI diff
- 一键回滚（Undo stack + AI snapshots）

**Step 10：质量看板（Vision 3.10）**
- 追踪写作进度
- Claim 覆盖率检查
- 证据完整性检查
- 导出质量预检

**Step 11：引用管理**
- citation key 自动生成（authorYearShortTitle）
- 支持 CSL 引用格式（APA / Chicago / GB/T 7714）
- 引用绑定到论文段落

**Step 12：导出（Vision 3.9）**
- DOCX 导出（支持模板：通用 / 学位论文 / 期刊）
- Markdown 导出
- BibTeX / RIS 导出
- Session Archive（运行记录打包）
- 诊断报告

**Step 13：Run 历史追踪**
- 查看历史 Run（paper.md / events / messages）
- 查看诊断报告
- 对比不同 Run
- 从历史 Run 继续编辑

**Step 14：版本历史**
- 编辑器版本快照
- 段落级 diff
- 回滚到任意版本

---

## 5. 核心功能地图

```
├── Workspace Home           ← 项目入口、状态总览、快捷跳转
├── Main Editor              ← 真实 WYSIWYG 编辑器
├── AI Draft Assistant       ← 三阶段：配置→进度→结果
├── Research Workspace（3.0）← 项目容器、研究方向、进度跟踪
├── Knowledge Base（3.1）     ← 全局知识资产库
│   ├── Literature（3.2）    ← 文献管理
│   ├── Theory Matcher（3.3）← 理论推荐
│   └── Evidence Pack（3.4）← 证据包
├── RAG Search（3.5）        ← 混合检索
├── Quality Dashboard（3.10）← 写作质量追踪
├── Runtime                  ← Run History / Diagnostics / Provider
├── Tools                    ← Skill Library / Export Center
└── Settings                 ← Provider / Connectors / Theme
```

---

## 6. 产品信息架构

```
ThesisX
├── 本地数据层（SQLite + FTS5 + 文件）
├── 知识服务层（KnowledgeStore / LiteratureService / TheoryMatcher / EvidencePack / RagService）
├── Runtime 层（SessionStore / RunHistoryReader / ProviderService）
├── Agent 层（AgentTeamRunner / SkillLoader）
└── UI 层（PyQt6 Workspace + Main Editor + AgentTeamDialog）
```

---

## 7. 页面结构总览

| 一级入口 | 子页面 | 状态 |
|---------|-------|------|
| Workspace Home | — | 真实可用 |
| Research Workspace | — | **3.0 实现** |
| Main Editor | — | 真实可用 |
| AI Draft Assistant | — | 真实可用（Mock+Real） |
| Knowledge Base | Literature | **3.2 实现** |
| Knowledge Base | Note Items | 3.1 实现 |
| Knowledge Base | Theory Matcher | **3.3 实现** |
| Knowledge Base | Evidence Pack | **3.4 实现** |
| RAG Search | — | **3.5 实现** |
| Quality Dashboard | — | **3.10 实现** |
| Runtime | Run History | 真实可用（部分） |
| Runtime | Runtime Diagnostics | 真实可用 |
| Runtime | Provider Settings | 部分真实 |
| Tools | Skill Library | preview |
| Tools | Export Center | 部分真实 |
| Settings | Connectors | 3.7 |
| Settings | General | 部分真实 |

---

## 8. 数据对象总览

### 核心实体
```
Project              ← 论文项目（Vision 3.0）
  ├── ResearchQuestion  ← 研究问题（Vision 3.0）
  ├── ResearchDirection ← 研究方向（Vision 3.0）
  └── ResearchGoal      ← 研究目标（Vision 3.0）
KnowledgeObject  ← 全局知识资产基类
  └── LiteratureItem / NoteItem / TheoryItem / EvidenceItem
Claim             ← 论点（Vision 3.4）
  └── EvidenceItem  ← 证据（Vision 3.4）
ProjectKnowledgeLink  ← 项目-知识绑定（多对多）
ObjectRelation   ← 对象间关系（双链/引用）
Tag              ← 标签
Citation         ← 引用记录
Skill            ← Skill 定义
SkillBinding     ← Skill-项目-任务绑定
Run              ← 运行记录
```

### 存储位置
```
~/.wenbiao/
  thesisx.db         ← SQLite 主库（所有表）
  knowledge/
    imports/         ← 导入的 Markdown/PDF/BibTeX
    exports/         ← 导出的文件
    files/           ← 附件（PDF 等）
    embeddings/      ← 向量索引
  runs/              ← Run session 数据
  providers.json     ← Provider 配置
```

---

## 9. 技术架构总览

| 层级 | 技术 |
|------|------|
| 桌面 UI | PyQt6 |
| 主语言 | Python 3.14 |
| 本地主库 | SQLite + FTS5 |
| 向量检索 | 本地向量表 / FAISS（可选） |
| 文档解析 | markdown-it-py / python-frontmatter / PyYAML |
| PDF 元数据 | pypdf |
| Zotero | pyzotero（后续） |
| Obsidian | 文件系统扫描 |
| Agent | AgentTeamRunner / AgentTeamCompatAdapter |
| Provider | LocalCLIProvider / RemoteAPIProvider / AgentTeamProvider |
| 导出 | python-docx |
| 测试 | pytest |

---

## 10. 最终 Beta 验收标准（Vision 4.0）

| # | 标准 |
|---|------|
| 1 | 从空白项目到完整论文导出，全链路可走通 |
| 2 | 知识库、文献、理论、证据不全是 mock |
| 3 | RAG 检索有实际效果（不是空结果） |
| 4 | Skill Library 与 Run 真正绑定 |
| 5 | Zotero/Obsidian 可导入真实数据 |
| 6 | 导出 docx 格式可用 |
| 7 | USER_GUIDE.md 完整 |
| 8 | 隐私说明清晰 |
| 9 | 测试覆盖率 ≥ 80% |

---

## 11. 分阶段实现路径

| 阶段 | 状态 | 说明 |
|------|------|------|
| v2.x Runtime Beta | **当前** | Runtime 可跑，Mock/Real 最小链路，SessionStore/RunHistory/Diagnostics |
| v3.0 Research Workspace | **下一阶段** | Project container + ResearchQuestion/Direction/Goal 模型 |
| v3.1 Knowledge Base | 3.1 | SQLite + KnowledgeObject + 导入 + FTS5 |
| v3.2 Literature Intelligence | 3.2 | citation key + 项目绑定 + CSL 导出 |
| v3.3 Theory Matcher | 3.3 | 规则+语义混合匹配，30→120 理论库 |
| v3.4 Evidence & Argument Pack | 3.4 | Claim-Evidence 绑定，缺口分析 |
| v3.4.5 AI→Editor Safe Insert | 3.4.5 | 结构化插入，格式保留，diff+回滚 |
| v3.5 RAG Context Engine | 3.5 | FTS5+Embedding+Metadata+Rerank |
| v3.5.1 PDF Full-text Parsing | 3.5.1 | PDF 内容解析（后续版本规划） |
| v3.6 Editor AI Loop | 3.6 | 局部改写，Undo stack，AI snapshots |
| v3.7 Connectors | 3.7 | Zotero + Obsidian（只读） |
| v3.8 Skill Runtime | 3.8 | Skill 文件 + 绑定 UI |
| v3.9 Export & Delivery | 3.9 | 多模板 docx + 隐私说明 |
| v3.10 Quality Dashboard | 3.10 | 写作质量追踪，Claim 覆盖率 |
| v4.0 Final Product Beta | 4.0 | 全链路完整，测试 ≥ 80% |
| v4.1-4.7 Advanced | 4.x | 高级 intelligence 功能 |
| v5.0 Collaboration | 5.0 | 协作/云同步（后续版本规划） |

---

*本文档与 PRD_OVERVIEW、TECHNICAL_ARCHITECTURE、DATA_MODEL 配套使用。*
*所有技术决策以 PRODUCT_DECISIONS.md 为准。*