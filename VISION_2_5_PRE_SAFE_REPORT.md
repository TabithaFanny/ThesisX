# Vision 2.5-pre / 2.5-safe 自动推进报告

> 执行时间：2026-05-02
> 执行范围：Vision 2.5-pre (tui_runner 前置确认) + Vision 2.5-safe (Real 模式安全门)
> 最终测试：357 passed

---

## 1. 修改/新增文件

### 修改

| 文件 | 改动 |
|------|------|
| `app/core/pipeline/agent_team_runner.py` | +85 行。新增 `_validate_real_mode_gate()` 安全门；paper.md 空内容 fallback；Real 模式前置校验 |
| `tests/unit/test_pipeline_v2_dry_run.py` | 修复 monkeypatch（`cls` 参数 + gate bypass） |
| `tests/unit/test_real_mode_safety_gate.py` | 修复 `test_unsupported_contract` 预期（pipeline_v2 不再阻断） |

### 新增

| 文件 | 行数 |
|------|------|
| `tests/unit/test_real_mode_safety_gate.py` | 10 个测试覆盖安全门全部路径 |

### 新增 venv 依赖

| 包 | 原因 |
|----|------|
| `autogen-core==0.7.5` | Candidate 4 tui_runner 的 `pipeline_real.py → autogen_adapter.py` 链需要 |
| `autogen-agentchat` | 同上 |

这些是 Candidate 4 的间接依赖。ThesisX 代码未修改外部仓库，只是在自身 venv 中安装了缺失的包。

---

## 2. Candidate 4 import 结果

```
✓ import successful
  - PipelineConfig fields: base_dir, topic, journal, run_mode, budget_cap_cny,
    use_mock, model_overrides, interrupt_manager, api_key, base_url, model
  - SequentialRunner: <class 'academic_agent_team.tui.runner.SequentialRunner'>
  - Events: TokenStreamEvent, StateUpdateEvent, CostUpdateEvent,
    AgentMessageEvent, ErrorEvent, CompletionEvent, HumanInterruptEvent
```

**运行时依赖链：**
```
tui/runner.py → pipeline_real.py → autogen_adapter.py → autogen_core, autogen_agentchat
```

两个包已在 ThesisX venv 中安装（`pip install autogen-core autogen-agentchat`）。

---

## 3. Mock/Dry-Run 是否跑通

### Candidate-4 tui_runner mock (use_mock=True)

```
✓ CompatAdapter 成功 import 并驱动
✓ 29 events produced (state, token, cost, message, completion)
✓ 0 errors
✓ paper.md generated (external output dir)
```

### AgentTeamRunner 全链路 (real mode → CompatAdapter → tui_runner mock)

```
✓ 39 events (state, artifact, token, cost, message, completion)
✓ 0 errors
✓ Full runs/ directory structure:
  runs/<session_id>/
    request.json, metadata.json
    output/outline.json, paper.md, quality_report.json
    logs/events.jsonl (7547B), messages.jsonl (2913B)
    context/paper_request.md, runtime_instructions.md,
      user_constraints.md, selected_skills.md
```

**Paper.md fallback:** Candidate 4 的 MockClient 产出空 paper.md。ThesisX 自动检测并生成本地 mock 论文作为占位（1115 chars）。

---

## 4. Real 配置安全门结果

### `_validate_real_mode_gate()` 检查项

| # | 检查项 | 失败码 | 阻断? |
|---|--------|--------|-------|
| 1 | agent_team_path 非空且非 "未选择" | AGENT_PATH_EMPTY | ✓ |
| 2 | 路径存在 + 包含 academic_agent_team 包 | AGENT_PATH_INVALID | ✓ |
| 3 | 契约受支持 | CONTRACT_UNSUPPORTED | ✓ |
| 4 | 契约非 tui_runner → 警告 "dry-run only" | — | ✗ (仅警告) |
| 5 | API key 已配置 | API_KEY_MISSING | ✓ |
| 6 | base_url 已显式设置 | — | ✗ (仅警告) |
| 7 | model 已显式设置 | — | ✗ (仅警告) |
| 8 | budget_cap_cny > 0 | — | ✗ (仅警告) |

**设计原则：** 只阻断必须在执行前解决的问题（无路径、无 key、契约不兼容）。非 tui_runner 契约不阻断（因为 CompatAdapter 支持 dry-run 适配）。

---

## 5. 是否发真实 API？

**否。所有测试和验证都使用 `use_mock=True` 或 dry-run 模式。零 API 调用。**

---

## 6. 测试结果

```
357 passed in 14.75s
```

| 测试组 | 数量 | 状态 |
|--------|------|------|
| 原有测试 | 347 | all passing |
| test_real_mode_safety_gate.py | 10 | all passing |
| test_pipeline_v2_dry_run.py (修复) | 7 | all passing |
| **合计** | **357** | **all passing** |

---

## 7. 当前是否能进入真实 Real 最小验证？

**技术上已就绪，但仍有缺口：**

### 已就绪
- ✓ Candidate 4 tui_runner import + mock run 验证通过
- ✓ CompatAdapter 驱动翻译正常
- ✓ Session 记录完整（events, messages, metadata, paper.md）
- ✓ RunDiagnostics 可诊断
- ✓ Real 配置安全门已实现（清晰错误码 + 中文错误消息）
- ✓ 配置缺失时不会伪装成功
- ✓ 357 tests passing

### 待用户提供/确认
1. **API Key** — 当前 `OPENAI_API_KEY` 未设置（环境变量为空）
2. **Agent Team 路径** — 确认使用 Candidate 4 (`/Volumes/E/agent team 2/wt-1488343317639991428/`)
3. **预算** — 确认预算上限
4. **费用承担** — 确认同意 API 费用

---

## 8. 进入 Vision 2.5 (Real) 时会做什么？

### 最小 Real 验证步骤
1. 用户设置 `OPENAI_API_KEY` 环境变量
2. 在 ThesisX 中设置 `agent_team_path = Candidate 4`
3. 打开 AgentTeamDialog，切 Real 模式
4. 填写简短 topic（如"测试课题"）
5. 预算设为 ¥1.00
6. 点击"开始生成"
7. 预期：ArchitectNode 发一次 API → tui_runner SequentialRunner 执行 → 产生 paper.md → 写入 runs/

### 会不会发送论文内容？
- ArchitectNode 会发送 system prompt + topic 到 API（约 3-5KB）
- tui_runner 的 advisor/researcher/writer/reviewer/polisher 各阶段都会发送 prompt 到 API
- 总 token 消耗取决于预算限制

### 会不会产生费用？
- **会。** Real 模式会调用真实 LLM API 产生费用。
- 费用在预算上限（budget_cap_cny）内控制。
- 最小验证建议预算 ¥1-5。

### Provider
- 默认使用 `OPENAI_BASE_URL`（如设置）或 Agent Team 内部默认（通常 OpenAI）
- 可通过 `OPENAI_MODEL` 控制模型

---

## 9. 判断

**Vision 2.5-pre 和 2.5-safe 均已完成。当前状态：**
- ✅ Real Agent Team 前置确认完成（Candidate 4 import + mock 验证）
- ✅ Real 模式安全门已实现
- ✅ 357 tests passing
- ❌ 未进入真实 API 调用
- ⏸️ 等待用户确认是否进入 Vision 2.5 (Real)

**下一步必须用户确认。**
