"""Zero-context paper claim audit prompts — from paper-claim-audit (ARIS).

Fresh reviewer with NO prior context compares paper text against raw
result files. Catches rounding errors, best-seed cherry-picks, metric
misattribution, and scope overclaims.
"""

CLAIM_AUDIT_SYSTEM_PROMPT = """\
你是论文数据审计员。你对这项研究没有任何先验知识——你只看到论文文件和原始结果文件。
你的工作是验证论文中的每一个数字是否与原始证据完全一致。

【审计协议】

### A. 提取每一个定量声明
对论文中的每个数字、百分比、比较或范围声明：
- 位置（章节、表格、标题、正文）
- 确切的声明文本
- 被声称的数字或比较

### B. 将每个声明追溯到证据
对每个提取的声明，找到支持的原始数据：
- 哪个结果文件包含这个数字？
- 该文件中的确切值是什么？
- 匹配状态：exact_match / rounding_ok / mismatch

### C. 检查以下特定失败模式

1. **数字膨胀**: 论文说 85.3%，原始文件说 84.7%
   规则：只允许按显示精度进行标准四舍五入

2. **最佳种子挑选**: 论文说"达到 90.2%"但那是 5 个种子中最好的；均值是 87.1%
   规则：检查论文是否注明"平均"/"最佳"/"中位数"

3. **配置不匹配**: 论文比较方法 A vs 基线 B，但它们使用了不同的超参数/数据集/划分
   规则：验证配置文件显示比较方法使用相同设置

4. **聚合不匹配**: 论文说"5 个种子的平均"但结果文件只显示 3 次运行
   规则：计算实际运行次数 vs 声称次数

5. **增量错误**: 论文说"提升 15%"但实际增量是 (85.3 - 73.1) / 73.1 = 16.7%
   规则：验证所有相对改进的算术

6. **标题-表格不匹配**: 图表标题描述的内容与图表/表格实际显示的不同
   规则：交叉检查每个标题与其内容

7. **范围过度声称**: 论文说"持续优于"但只在 2 个数据集上测试
   规则：检查语言是否匹配实际评估范围

【输出格式】（每个声明）
- claim_id: 序号
- location: 章节/表格/图表
- paper_text: 论文中的确切引用
- paper_value: 声称的数字
- evidence_file: 哪个原始文件
- evidence_value: 实际数字
- status: exact_match | rounding_ok | ambiguous_mapping |
          missing_evidence | config_mismatch | aggregation_mismatch |
          number_mismatch | scope_overclaim | unsupported_claim
- details: 如果不是 exact_match 则解释

总体判定: PASS | WARN | FAIL"""


CLAIM_AUDIT_USER_PROMPT = """\
请审计以下论文中的所有定量声明，与原始结果文件进行比对。

【论文文件】
{paper_files_summary}

【原始结果文件】
{result_files_summary}

【论文内容（摘录）】
{paper_excerpt}

【结果数据（摘录）】
{results_excerpt}

请按审计协议逐一验证每个定量声明。"""


CLAIM_AUDIT_REPORT_TEMPLATE = """\
# 论文数据审计报告

**日期**: {date}
**审计员**: 零上下文跨模型审查员
**论文**: {paper_title}

## 总体判定: {verdict}

## 统计
- 已验证声明: {total_claims}
- exact_match: {exact_match}
- rounding_ok: {rounding_ok}
- ambiguous: {ambiguous}
- mismatch: {mismatch}

## 发现的问题

{issues_section}

## 所有声明详情

| # | 位置 | 论文值 | 证据值 | 状态 |
|---|------|--------|--------|------|
{claims_table}
"""


def build_claim_audit_system_prompt() -> str:
    """Return the zero-context claim audit system prompt."""
    return CLAIM_AUDIT_SYSTEM_PROMPT


def build_claim_audit_user_prompt(
    paper_files_summary: str,
    result_files_summary: str,
    paper_excerpt: str,
    results_excerpt: str,
) -> str:
    """Build the user prompt for paper-to-evidence audit."""
    return CLAIM_AUDIT_USER_PROMPT.format(
        paper_files_summary=paper_files_summary[:2000],
        result_files_summary=result_files_summary[:2000],
        paper_excerpt=paper_excerpt[:4000],
        results_excerpt=results_excerpt[:4000],
    )


def build_claim_audit_report(
    date: str,
    paper_title: str,
    verdict: str,
    total_claims: int,
    exact_match: int,
    rounding_ok: int,
    ambiguous: int,
    mismatch: int,
    issues_section: str = "",
    claims_table: str = "",
) -> str:
    """Build the final audit report from parsed results."""
    return CLAIM_AUDIT_REPORT_TEMPLATE.format(
        date=date,
        paper_title=paper_title,
        verdict=verdict,
        total_claims=total_claims,
        exact_match=exact_match,
        rounding_ok=rounding_ok,
        ambiguous=ambiguous,
        mismatch=mismatch,
        issues_section=issues_section or "无",
        claims_table=claims_table or "| - | - | - | - | - |",
    )
