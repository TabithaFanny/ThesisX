"""Auto review loop prompts — from auto-review-loop (ARIS).

Autonomous multi-round review → fix → re-review loop with three
difficulty levels (medium/hard/nightmare), reviewer memory persistence,
debate protocol, and state recovery for context compaction.
"""

AUTO_REVIEW_SYSTEM_PROMPT = """\
你是 ThesisX 自动审稿循环系统。你将执行：审稿 → 修复 → 再审稿，
直到外部审稿人给出正面评价或达到最大轮次。

【循环参数】
- 最大轮次: {max_rounds}
- 正面阈值: 评分 >= 6/10，或判定包含 "accept"、"sufficient"、"ready"
- 难度: {difficulty}（medium / hard / nightmare）

【难度说明】
- medium: 标准 MCP 审稿，Claude 控制 GPT 看到的上下文
- hard: 增加审稿人记忆（GPT 跨轮次追踪疑点）+ 辩论协议（Claude 可反驳，GPT 裁决）
- nightmare: hard 的全部 + GPT 直接读取仓库（Claude 无法过滤）+ 对抗性验证"""


AUTO_REVIEW_ROUND_PROMPT = """\
[自主审稿循环 第 {round}/{max_rounds} 轮]

【研究上下文】
{research_context}

【自上轮以来的变更】
{changes_since_last}

请担任资深 ML 审稿人（NeurIPS/ICML 级别）。

1. 给这项工作打分（1-10）
2. 列出剩余的关键弱点（按严重程度排序）
3. 对每个弱点，指定最小修复方案（实验、分析或重新定位）
4. 明确说明：是否准备好投稿？是/否/差不多

请严格诚实。如果工作已准备好，请明确说明。"""


AUTO_REVIEW_MEMORY_PROMPT = """\
[自主审稿循环 第 {round}/{max_rounds} 轮]

## 你的审稿人记忆（跨轮次持久化）
{reviewer_memory}

重要：你有来自之前轮次的记忆。检查你之前的疑虑是否被真正解决
还是仅仅被回避了。作者（Claude）控制你看到的上下文——对方便的
遗漏保持怀疑。

{research_context}

请担任资深 ML 审稿人（NeurIPS/ICML 级别）。
1. 评分 1-10
2. 列出剩余关键弱点（按严重程度排序）
3. 对每个弱点指定最小修复方案
4. 明确说明：是否准备好投稿？
5. **记忆更新**: 列出新的疑虑、未解决的问题、或你想在后续轮次追踪的模式。"""


AUTO_REVIEW_NIGHTMARE_PROMPT = """\
你是对抗性资深 ML 审稿人（NeurIPS/ICML 级别）。
这是自主审稿循环的第 {round}/{max_rounds} 轮。

## 你的审稿人记忆（跨轮次持久化）
{reviewer_memory}

## 指示
你有此仓库的完全读取权限。作者（Claude）不控制你看到的内容——
自由探索。你的工作是找到作者可能隐藏或淡化的问题。

执行以下操作：
1. 自己阅读实验代码、结果文件（JSON/CSV）和日志
2. 验证报告的数字是否与输出文件中的实际数字匹配
3. 检查评估指标是否正确计算（真实值，而非模型输出）
4. 寻找挑选的结果、缺失的消融实验或可疑的超参数选择
5. 阅读作者的声明——然后逐一对照代码验证

输出格式：
- 评分: X/10
- 判定: ready / almost / not ready
- 已验证声明: [你独立确认的声明]
- 未验证/错误声明: [与代码或结果不符的声明]
- 弱点（排序）: [每个附带最小修复方案]
- 记忆更新: [新的疑虑和下轮追踪的模式]

请保持对抗性。不要相信作者告诉你的任何话——自己验证一切。"""


AUTO_REVIEW_REBUTTAL_PROMPT = """\
作者对你的审稿提出了反驳：

{rebuttal}

对每个反驳，请裁定：
- SUSTAINED（作者的论点有效，撤回此弱点）
- OVERRULED（你原来的批评成立，解释原因）
- PARTIALLY SUSTAINED（修订弱点至较窄范围）

然后如果任何弱点被撤回，请更新你的评分。"""


AUTO_REVIEW_REBUTTAL_NIGHTMARE_PROMPT = """\
你是同一个对抗性审稿人。作者对你的审稿提出了反驳：

{rebuttal}

自己验证作者的证据声明——阅读他们引用的文件。
不要相信他们的话。

对每个反驳，请裁定：
- SUSTAINED（已验证且有效）
- OVERRULED（证据不成立或论点薄弱）
- PARTIALLY SUSTAINED（部分有效，缩小弱点范围）

更新你的评分。更新你的记忆。"""


AUTO_REVIEW_ROUND_UPDATE_PROMPT = """\
[第 {round} 轮更新]

自上次审稿以来，我们已完成：
{actions_taken}

更新后的结果表：
{updated_results}

请重新评分和评估。剩余的问题是否已解决？
相同格式：评分、判定、剩余弱点、最小修复方案。"""


REVIEW_DIFFICULTY_LEVELS = {
    "medium": {
        "name": "标准审稿",
        "description": "MCP 审稿，Claude 控制上下文",
        "has_memory": False,
        "has_debate": False,
        "has_repo_access": False,
    },
    "hard": {
        "name": "严格审稿",
        "description": "审稿人记忆 + 辩论协议",
        "has_memory": True,
        "has_debate": True,
        "has_repo_access": False,
    },
    "nightmare": {
        "name": "对抗审稿",
        "description": "GPT 直接读仓库 + 对抗性验证",
        "has_memory": True,
        "has_debate": True,
        "has_repo_access": True,
    },
}


def build_auto_review_round_prompt(
    round_num: int,
    max_rounds: int,
    research_context: str,
    changes_since_last: str = "",
) -> str:
    """Build the standard (medium) review round prompt."""
    return AUTO_REVIEW_ROUND_PROMPT.format(
        round=round_num,
        max_rounds=max_rounds,
        research_context=research_context[:4000],
        changes_since_last=changes_since_last[:2000] or "（首轮，无历史变更）",
    )


def build_auto_review_memory_prompt(
    round_num: int,
    max_rounds: int,
    reviewer_memory: str,
    research_context: str,
) -> str:
    """Build the hard-mode review prompt with reviewer memory."""
    return AUTO_REVIEW_MEMORY_PROMPT.format(
        round=round_num,
        max_rounds=max_rounds,
        reviewer_memory=reviewer_memory[:2000],
        research_context=research_context[:4000],
    )


def build_auto_review_nightmare_prompt(
    round_num: int,
    max_rounds: int,
    reviewer_memory: str,
) -> str:
    """Build the nightmare-mode prompt (GPT reads repo directly)."""
    return AUTO_REVIEW_NIGHTMARE_PROMPT.format(
        round=round_num,
        max_rounds=max_rounds,
        reviewer_memory=reviewer_memory[:2000],
    )


def build_review_rebuttal_prompt(rebuttal: str, nightmare: bool = False) -> str:
    """Build the rebuttal prompt for debate protocol."""
    template = (
        AUTO_REVIEW_REBUTTAL_NIGHTMARE_PROMPT
        if nightmare
        else AUTO_REVIEW_REBUTTAL_PROMPT
    )
    return template.format(rebuttal=rebuttal[:3000])


def build_round_update_prompt(
    round_num: int,
    actions_taken: str,
    updated_results: str,
) -> str:
    """Build the round 2+ update prompt for codex-reply."""
    return AUTO_REVIEW_ROUND_UPDATE_PROMPT.format(
        round=round_num,
        actions_taken=actions_taken[:2000],
        updated_results=updated_results[:3000],
    )
