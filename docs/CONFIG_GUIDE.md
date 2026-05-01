# ThesisX Agent Team 配置指南

## 配置来源优先级

ThesisX 从三个来源读取配置，优先级从高到低：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 (最高) | 环境变量 | `OPENAI_API_KEY` / `AI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` |
| 2 | `~/.wenbiao/config.json` | `custom_ai_api_key` / `custom_ai_api_url` / `custom_ai_model` / `agent_team_path` |
| 3 (默认) | 内置默认值 | `base_url=https://api.openai.com/v1`, `model=gpt-4o-mini` |

环境变量会覆盖 `config.json` 中的对应字段。

## 关键配置项

| 配置项 | 环境变量 | config.json 字段 | 默认值 |
|--------|---------|-----------------|--------|
| API Key | `OPENAI_API_KEY` 或 `AI_API_KEY` | `custom_ai_api_key` | 空（Mock 模式不需要） |
| Base URL | `OPENAI_BASE_URL` | `custom_ai_api_url` | `https://api.openai.com/v1` |
| Model | `OPENAI_MODEL` | `custom_ai_model` | `gpt-4o-mini` |
| Agent Team 路径 | — | `agent_team_path` | 空（需手动选择） |
| 默认期刊 | — | `agent_team_default_journal` | `中文核心` |
| 默认模式 | — | `agent_team_default_mode` | `mock` |
| 默认预算 | — | `agent_team_default_budget_cny` | `10.0` |

## Agent Team 路径配置

Agent Team 路径应指向包含 `academic_agent_team/` 包的目录。

支持的契约类型：
- `tui_runner`：完整真实执行支持（需 `tui/runner.py` + `tui/events.py`）
- `pipeline_v2`：当前走 dry-run 适配（支持事件流，但不调用真实 API）
- `pipeline_function`：当前走 dry-run 适配（同上）

### 示例

```bash
# 设置 API Key（方式一：环境变量，推荐）
export OPENAI_API_KEY="sk-your-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o"

# 或在 config.json 中设置（方式二）
# ~/.wenbiao/config.json
{
  "agent_team_path": "/Volumes/E/agent team 2/academic-agent-team/",
  "custom_ai_api_key": "sk-your-key-here",
  "custom_ai_api_url": "https://api.openai.com/v1",
  "custom_ai_model": "gpt-4o",
  "agent_team_default_mode": "mock",
  "agent_team_default_journal": "中文核心",
  "agent_team_default_budget_cny": 10.0
}
```

## 配置验证

在 AI 论文初稿助手对话框中点击"检测配置"按钮，ThesisX 会检查：
- Agent Team 路径是否存在
- API Key 是否已配置
- Base URL 和 Model 是否已设置
- 契约类型是否支持

验证过程**不会发送真实 API 请求**，不会产生费用。

## Mock vs Real 模式

| 模式 | API Key | Agent Team 路径 | 费用 | 说明 |
|------|---------|----------------|------|------|
| Mock | 不需要 | 不需要 | ¥0 | 使用模拟数据，仅用于流程预览 |
| Real | 需要 | 需要 | 按量计费 | 调用真实 LLM API，受预算上限控制 |

**注意：** Real 模式当前仅 `tui_runner` 契约支持完整真实执行。`pipeline_v2` 和 `pipeline_function` 契约走 dry-run 适配（产生事件流但不调用真实 API）。
