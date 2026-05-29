# Agent Execution Rules — Agent 执行规则

> 给所有后续 Agent（和 Codex）用的执行规则。违反以下任何一条，Codex 有权 BLOCK。
> 这些规则与 PRODUCT_DECISIONS.md、AGENT_VISION_ROADMAP.md 配套使用。

---

## 总则

**ThesisX 不是一个"论文生成器"，而是一个本地优先、知识驱动、可追溯的论文 AI 工作台。**

所有 agent 必须：
1. 理解这个产品定位
2. 按照 PRODUCT_DECISIONS.md 中的技术决策执行
3. 按照 AGENT_VISION_ROADMAP.md 中的阶段推进
4. 按照本文档的规则执行

---

## 禁止事项（当前版本不包含 / 15 条）

以下 15 条是**当前版本不包含**，违反任何一条会导致 Codex BLOCK 并要求 revert：

### 代码质量（当前版本不包含）

**[B1] 不把 mock 说成真实功能**
```python
# ❌ 错误：把 preview 页面当真实功能汇报
# "Literature 页面可以使用了"
```
- preview/coming soon 页面的任何代码修改都不能声称"完成某功能"
- 判断标准：FRONTEND_INTERFACE_MAPPING.md 中标为 "真实可用" 的才是真的

**[B2] 不破坏已有功能**
```python
# ❌ 错误：修改 Main Editor 的 FormattingToolbar 导致格式丢失
# ❌ 错误：删除 AgentTeamDialog 的取消功能
```
- 每次修改后跑 `pytest tests/ -x -q`，全部通过才能提交
- 特别注意：Main Editor、AgentTeamDialog、RunHistory 是核心功能，不能破坏

**[B3] 不跳过测试**
```bash
# ❌ 错误：因为赶时间跳过测试
pytest tests/ -x -q
```
- 测试失败 = 立即修复，不跳过
- 如果测试本身有问题，标记为 `blocked` 并报告

**[B4] 不修改外部 Agent Team**
```bash
# ❌ 错误：修改 /Volumes/E/agent team/ 下的任何文件
```
- Agent Team 仓库是外部依赖，不能改
- 如需调整接口，写 adapter 层

**[B5] 不删除旧数据**
```python
# ❌ 错误：删除 ~/.wenbiao/runs/ 下的历史记录
# ❌ 错误：修改 SessionStore 的历史文件格式
```
- 已有 runs 是用户资产，只能读不能改

### 产品规范（当前版本不包含）

**[B6] 不声称 preview 功能已接通**
```
# ❌ 错误：
"Evidence Pack 功能已实现"

# ✅ 正确：
"Evidence Pack preview 页面 UI 已完成，但底层数据层尚未接通"
```
- 每个 Vision 的交付物必须与 FRONTEND_INTERFACE_MAPPING.md 的状态一致
- Vision 3.x 实现不能把 preview 页面算作"完成"

**[B7] 不把 Runtime 闭环当成完整产品交付**
```
# ❌ 错误：报告"ThesisX v3.0 Beta 发布完成，产品完整可用"

# ✅ 正确：
"Vision 2.x Runtime Beta 已就绪，Vision 3.1 正在推进"
```
- Runtime 可跑 ≠ 产品可用
- 参考 RUNTIME_CLOSED_LOOP_REPORT.md 的准确定位

**[B8] 不绕过决策文档**
```python
# ❌ 错误：因为觉得 SQLite 太复杂，改用 JSON 做主存储
# （违背了 3.1-D2 的决策）
```
- PRODUCT_DECISIONS.md 中已决策的内容，后续 agent 必须遵守
- 如有充分理由需要更改，发 issue 讨论，不能自行推翻

**[B9] 不继续 Runtime/UI 精修**
```
# ❌ 错误：继续优化 SVG 对齐 / Runtime 诊断 / UI 细节

# ✅ 正确：
# "Runtime 已闭环，核心问题是 Knowledge Base 未实现，
#  建议按 Vision 3.1 推进"
```
- Vision 3.1+ 的 agent 应该专注于功能实现，不是在 Runtime 层继续优化

### 数据与隐私（当前版本不包含）

**[B10] 不在 Skill prompt 中保存 API key**
```yaml
# ❌ 错误（skill.yaml）：
prompt: |
  使用 OpenAI API Key: sk-xxxx 生成内容

# ✅ 正确：
prompt: |
  使用用户配置的 Provider API 生成内容
```
- Skill 只能引用环境变量或用户配置的 Provider，不能内嵌 key
- 导入时必须检测并阻止

**[B11] 不把用户数据发给未授权的 Provider**
```python
# ❌ 错误：在 Real 模式下不显示发送了什么数据
```
- Real 模式前必须显示隐私摘要（研究问题/选中的知识片段/任务 prompt）
- 不发送：未选中的文件/API key/整个 vault

**[B12] 不修改 Zotero/Obsidian 原始文件**
```python
# ❌ 错误：Zotero 连接器自动修改 note 内容后写回

# ✅ 正确：
# "Zotero 连接器默认只读。写回需要用户显式确认。"
```
- 连接器默认只读，任何写回操作必须用户主动开启并逐项确认

### 工程（当前版本不包含）

**[B13] 不使用 unsafe-inline（安全规则）**
```html
<!-- ❌ 错误 -->
<script src="https://cdn.jsdelivr.net" nonce=""></script>

# ✅ 正确：必须使用 per-request nonce
<script nonce="<RANDOM>" src="https://cdn.jsdelivr.net"></script>
```

**[B14] 不在 main/master 分支直接开发**
```bash
# ❌ 错误：在 main 分支直接 commit
git checkout main
git commit -m "feat: ..."

# ✅ 正确：feature 分支开发完成后合并
git checkout -b vision-3.1-kb
# ... 开发 ...
git checkout main
git merge vision-3.1-kb
```
- 所有新开发在 feature 分支
- main 分支保持稳定可发布状态

**[B15] 不在未确认的情况下决定重大架构**
```
# ❌ 错误：agent 自行决定用 ChromaDB 做向量存储

# ✅ 正确：
# "向量存储方案（3.5-D1）是重大架构决策，
#  需要用户在 PRODUCT_DECISIONS.md §3.5-D1 中确认"
```
- 27 个决策卡点中标记为"重大架构决策"的项目，必须先确认再执行

---

## 执行流程规则（7 条）

**[R1] 每个 Vision 前先 review 文档**
在开始任何 Vision 实现前，必须读：
1. `docs/PRODUCT_DECISIONS.md`（技术决策）
2. `docs/PRODUCT_ROADMAP.md`（阶段目标）
3. `docs/06_AGENT/AGENT_VISION_ROADMAP.md`（本 Vision 的具体要求）
4. `docs/04_FRONTEND/FRONTEND_INTERFACE_MAPPING.md`（页面状态）
5. `docs/07_REPORTS/`（已有报告，了解当前进度）

**[R2] 每个 Vision 内可自动执行**
决策点已确认后，实现工作可连续执行，不需要每次停下来问。

**[R3] 每个 Vision 后必须跑测试**
```bash
cd /Volumes/E/ThesisX
.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="
# 全部通过才能提交
```

**[R4] 高风险任务必须停下来**
遇到以下情况，立即发报告，不自行决定：
- 发现安全漏洞（XSS/SQL 注入/key 泄露）
- 发现破坏现有功能的 regression
- 发现决策文档之间的冲突

**[R5] 报告必须诚实标注真实/preview**
每份报告必须明确标注：
- 哪些是真实接通的功能
- 哪些是 preview/coming soon
- 哪些是未实现的计划

**[R6] 测试覆盖率目标**
- 最终 Beta（4.0）：≥ 80%
- Vision 3.1 实现时：≥ 70%（KnowledgeStore 相关）
- 不达标不允许发布

**[R7] 每次 commit 前检查**
```bash
git status
git diff --stat
pytest tests/ -x -q --override-ini="addopts="
```
只有全部通过才能 commit。

---

## Vision 执行顺序规则

```
3.1 Knowledge Base ──────┐
                         ↓
3.2 Literature ──────────┤
                         ↓
3.3 Theory Matcher ──────┼──→ 这三个可以独立推进
                         │     但 3.5（RAG）依赖 3.1 的数据
3.4 Evidence Pack ───────┘
                         ↓
3.5 RAG（依赖 3.1 数据）
        ↓
3.6 Editor 闭环（依赖 3.1+3.5）
        ↓
3.7 Zotero/Obsidian（独立）
        ↓
3.8 Skill Library（独立）
        ↓
3.9 Export（依赖 3.1+3.6）
        ↓
4.0 Product Beta（全链路验收）
```

**规则：**
- 3.5（RAG）不能先于 3.1（Knowledge Base）实现
- 3.6（Editor 闭环）需要 3.1+3.5 的数据基础
- 3.7/3.8 独立于主链路，可以并行

---

## 违规处理

| 违规类型 | 处理方式 |
|---------|---------|
| B1-B5（代码质量） | Codex BLOCK → 必须修复或 revert |
| B6-B9（产品规范） | Codex BLOCK → 必须纠正描述 |
| B10-B12（数据隐私） | 立即停止 → 发 security 报告 |
| B13-B15（工程安全） | Codex BLOCK → 必须修复架构 |
| R1-R7（流程规则） | 违反后补做，不 BLOCK 但需报告 |

---

## 与其他文档的关系

| 文档 | 关系 |
|------|------|
| PRODUCT_DECISIONS.md | 技术决策基准（违反 = B8） |
| PRODUCT_ROADMAP.md | 阶段目标基准 |
| AGENT_VISION_ROADMAP.md | 本 Vision 具体执行要求 |
| FRONTEND_INTERFACE_MAPPING.md | 页面状态基准（违反 = B6） |
| RUNTIME_CLOSED_LOOP_REPORT.md | 当前版本定位（违反 = B7） |

---

*本文档是所有后续 Agent 的执行规则基准。*
*Codex 有权基于本文档对任何实现提出 BLOCK。*