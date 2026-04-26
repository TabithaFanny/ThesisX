"""
plagiarism_service.py — 论文查重与 AI 降重服务

提供：
  · 文本拆句（中英文混合）
  · AI 查重分析 prompt 构建与结果解析
  · AI 降重改写 prompt 构建
"""

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── 数据模型 ──


@dataclass
class Sentence:
    """一个待检句子。"""

    index: int  # 句子序号
    text: str  # 原文
    start: int  # 在全文中的起始偏移
    end: int  # 在全文中的结束偏移


@dataclass
class CheckResult:
    """单句查重结果。"""

    index: int
    text: str
    risk: str = "low"  # "high" / "medium" / "low"
    dup_type: str = ""  # 重复类型描述
    suggestion: str = ""  # 改写建议
    sources: list = field(
        default_factory=list
    )  # 真实匹配来源 [{"title", "url", "source", "authors", "year", "score", "snippet"}]


@dataclass
class RewriteContext:
    """降重上下文，包含查重结果信息，让 AI 针对性避开相似表述。"""

    original_text: str  # 原文
    risk_level: str = "low"  # high/medium/low
    dup_type: str = ""  # 重复类型
    matched_sources: list = field(default_factory=list)  # 匹配来源列表
    similarity_scores: list = field(default_factory=list)  # 各来源相似度
    matched_snippets: list = field(default_factory=list)  # 匹配的具体片段
    suggestion: str = ""  # AI 建议
    target_similarity: float = 0.15  # 目标相似度阈值


@dataclass
class IterativeRewriteConfig:
    """迭代降重配置。"""

    target_rate: float = 0.15  # 目标重复率 (15%)
    max_iterations: int = 3  # 最大迭代次数
    rewrite_threshold: str = "medium"  # 降重阈值 (high/medium)
    verify_after_rewrite: bool = True  # 降重后是否验证
    aggressive_mode: bool = False  # 激进模式（更大幅度改写）
    use_paper_db: bool = True  # 使用论文数据库增强


@dataclass
class IterativeRewriteResult:
    """迭代降重结果。"""

    iteration: int = 0  # 当前迭代次数
    original_rate: float = 0.0  # 原始重复率
    current_rate: float = 0.0  # 当前重复率
    target_rate: float = 0.15  # 目标重复率
    rewritten_count: int = 0  # 已改写句子数
    remaining_high_risk: int = 0  # 剩余高风险句子数
    is_complete: bool = False  # 是否达到目标
    rewrites: dict = field(default_factory=dict)  # {index: rewritten_text}


# ── 拆句 ──

_SPLIT_RE = re.compile(
    r"(?<=[。！？；\.\!\?\;])"  # 在中英文句末标点后断开
    r"|(?<=\n)"  # 在换行符后断开
)


def split_sentences(text: str) -> list:
    """将全文拆分为句子列表，跳过空白行。"""
    raw_parts = _SPLIT_RE.split(text)
    sentences = []
    offset = 0
    idx = 0
    for part in raw_parts:
        stripped = part.strip()
        if not stripped or len(stripped) < 6:
            # 太短的片段（标题、标号等）跳过
            offset += len(part)
            continue
        pos = text.find(stripped, offset)
        if pos == -1:
            pos = offset
        sentences.append(
            Sentence(
                index=idx,
                text=stripped,
                start=pos,
                end=pos + len(stripped),
            )
        )
        offset += len(part)
        idx += 1
    return sentences


# ── AI 查重 prompt ──

_SYSTEM_CHECK = (
    "论文查重系统。分析每句重复风险(模板句/通用表述/教材句式/独创性)。"
    '返回JSON数组:[{"index":序号,"risk":"high/medium/low",'
    '"dup_type":"重复类型","suggestion":"改写建议"}]。只返回JSON无其他文字。'
)


def build_check_messages(sentences: list) -> list:
    """构建 AI 查重分析消息列表。"""
    numbered = "\n".join(f"[{s.index}] {s.text}" for s in sentences)
    return [
        {"role": "system", "content": _SYSTEM_CHECK},
        {"role": "user", "content": f"请分析以下句子的重复风险：\n\n{numbered}"},
    ]


def parse_check_result(ai_response: str, sentences: list) -> list:
    """解析 AI 返回的查重 JSON，返回 CheckResult 列表。"""
    results = []
    # 尝试提取 JSON 部分（AI 可能包裹在 ```json ... ``` 中）
    text = ai_response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 尝试宽松提取
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                logger.warning("无法解析查重结果 JSON")
                return results
        else:
            logger.warning("查重结果中未找到 JSON 数组")
            return results

    sent_map = {s.index: s for s in sentences}
    for item in data:
        idx = item.get("index", -1)
        sent = sent_map.get(idx)
        if not sent:
            continue
        results.append(
            CheckResult(
                index=idx,
                text=sent.text,
                risk=item.get("risk", "low"),
                dup_type=item.get("dup_type", ""),
                suggestion=item.get("suggestion", ""),
            )
        )
    return results


# ── AI 降重 prompt（人性化改写，降 AIGC + 降查重） ──

# 核心策略：让 AI 改写的文本具有人类写作特征
# 1. 打破 AI 的完美句式，加入口语化/不规则表达
# 2. 加入主观判断词、语气词、过渡词
# 3. 使用专业领域的地道表达
# 4. 句子长短不一，避免整齐划一
# 5. 适当加入作者视角的评述

_SYSTEM_REWRITE = """论文降重专家。你的任务是改写句子，让它：
1. 完全不像 AI 写的（通过 AIGC 检测）
2. 与原文表述完全不同（降低查重率）

改写策略：
- 用口语化学术表达替代书面化模板句（如"笔者认为""从实践来看""值得注意的是"）
- 打乱原句结构，长句拆短、短句合并
- 同义词替换要地道，避免生硬的近义词堆砌
- 加入适当的主观评述词（"显然""不难发现""有趣的是"）
- 数据表述换种方式（百分比↔分数、约数↔精确数）
- 被动句↔主动句灵活切换
- 可适当调整信息顺序，先果后因或先因后果

禁止：
- 不要用"���先、其次、最后"这类模板连接词
- 不要每句都很工整，要有长有短
- 不要堆砌形容词
- 不要改变原意和关键数据

直接输出改写结果，不要解释。"""

_SYSTEM_BATCH_REWRITE = """论文降重专家。批量改写高重复句子，目标：
1. 通过 AIGC 检测（不像 AI 写的）
2. 降低查重率（与原文表述完全不同）

改写要求：
- 每句都要大幅改动结构，不是简单换词
- 用自然的学术口语替代模板句式
- 句子长短要有变化，避免整齐划一
- 加入"笔者""本研究""从...角度看"等人称视角
- 数据换种表述方式
- 保持原意，关键信息不能丢

返回JSON数组：[{"index":序号,"rewritten":"改写后句子"}]
只返回JSON，无其他文字。"""

# 针对选中文本的深度改写（更激进）
_SYSTEM_DEEP_REWRITE = """资深学术写作专家。对选中文本进行深度改写，要求：

【核心目标】
让改写后的文本 100% 像人类学者亲手写的，能通过任何 AIGC 检测和查重系统。

【改写策略】
1. 结构重组：完全打乱原文句子顺序和段落结构
2. 视角转换：加入作者主观视角（"笔者注意到""从本研究的角度""值得一提的是"）
3. 表达人性化：
   - 用"大约/接近/将近"替代精确数字
   - 用设问句、反问句增加互动感
   - 适当使用"然而""不过""当然"等转折
   - 加入"有学者指出""研究表明"等引述方式
4. 句式多样化：
   - 长短句交替，避免句子长度一致
   - 主动被动灵活切换
   - 偶尔用倒装或省略句
5. 学术口语化：
   - "进行了分析"→"分析了"
   - "具有重要意义"→"意义重大"/"很有价值"
   - "研究发现"→"我们发现"/"分析显示"

【禁止事项】
- 不要用"首先其次最后"等模板词
- 不要每段开头都用相同句式
- 不要堆砌同义词
- 不要改变核心观点和数据

直接输出改写后的完整文本，不要任何解释或标注。"""


def merge_results(ai_results: list, db_results: list) -> list:
    """合并 AI 分析结果和数据库搜索结果。

    ai_results: list[CheckResult] (from parse_check_result)
    db_results: list[SentenceDbResult] (from DbPlagiarismWorker)
    Returns: list[CheckResult] — 合并后的最终结果
    """
    # Build lookup for db results by sentence index
    db_map = {r.sentence_index: r for r in db_results}
    merged = []
    for ai_r in ai_results:
        db_r = db_map.get(ai_r.index)
        sources = []
        db_risk = "low"
        if db_r and db_r.matches:
            db_risk = db_r.risk
            for m in db_r.matches[:3]:  # 最多显示 3 条来源
                sources.append(
                    {
                        "title": m.title,
                        "url": m.url,
                        "source": m.source,
                        "authors": m.authors,
                        "year": m.year,
                        "score": m.score,
                    }
                )
        # 综合评估风险
        _risk_level = {"high": 3, "medium": 2, "low": 1}
        ai_level = _risk_level.get(ai_r.risk, 1)
        db_level = _risk_level.get(db_risk, 1)
        if db_level >= 3 or (ai_level >= 3 and db_level >= 2):
            final_risk = "high"
        elif db_level >= 2 or ai_level >= 3:
            final_risk = "medium"
        elif ai_level >= 2:
            # AI 标中但数据库无匹配 → 仍标 medium（AI 推测）
            final_risk = "medium"
        else:
            final_risk = "low"
        # 更新 dup_type 标注来源
        dup_type = ai_r.dup_type
        if sources:
            dup_type = f"数据库匹配 + {dup_type}" if dup_type else "数据库匹配"
        elif ai_r.dup_type:
            dup_type = f"AI分析: {dup_type}"
        merged.append(
            CheckResult(
                index=ai_r.index,
                text=ai_r.text,
                risk=final_risk,
                dup_type=dup_type,
                suggestion=ai_r.suggestion,
                sources=sources,
            )
        )
    return merged


def build_rewrite_messages(sentence: str, context: str = "") -> list:
    """构建单句降重改写消息列表。"""
    user_content = f"请改写以下句子：\n\n{sentence}"
    if context.strip():
        user_content += f"\n\n上下文参考：\n{context[:500]}"
    return [
        {"role": "system", "content": _SYSTEM_REWRITE},
        {"role": "user", "content": user_content},
    ]


def build_batch_rewrite_messages(flagged_sentences: list) -> list:
    """构建批量降重消息列表。flagged_sentences 为 CheckResult 列表。"""
    numbered = "\n".join(f"[{r.index}] {r.text}" for r in flagged_sentences)
    return [
        {"role": "system", "content": _SYSTEM_BATCH_REWRITE},
        {"role": "user", "content": f"请改写以下高重复风险句子：\n\n{numbered}"},
    ]


def parse_rewrite_result(ai_response: str) -> dict:
    """解析批量降重 JSON，返回 {index: rewritten_text}。"""
    text = ai_response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return {}
        else:
            return {}

    return {
        item["index"]: item["rewritten"] for item in data if "index" in item and "rewritten" in item
    }


def build_deep_rewrite_messages(text: str, context: str = "") -> list:
    """构建深度降重消息列表（用于选中文本的激进改写）。

    这个函数用于对较长的选中文本进行深度改写，
    目标是同时通过 AIGC 检测和降低查重率。

    Args:
        text: 需要改写的文本
        context: 上下文（可选），帮助 AI 理解语境

    Returns:
        消息列表
    """
    user_content = f"请对以下文本进行深度改写：\n\n{text}"
    if context.strip():
        user_content += f"\n\n【上下文参考】\n{context[:800]}"
    return [
        {"role": "system", "content": _SYSTEM_DEEP_REWRITE},
        {"role": "user", "content": user_content},
    ]


# ── 论文数据库增强的降重 prompt ──

_SYSTEM_PAPER_ENHANCED_REWRITE = """资深学术写作专家。参考真实论文的写作风格，对中文文本进行深度改写。

【核心目标】
1. 模仿真实学术论文的表达方式和句式结构
2. 让改写后的文本像人类学者亲手写的
3. 通过 AIGC 检测和查重系统
4. 输出必须是中文

【参考论文的表达方式（学习其句��结构，用中文模仿）】
{paper_expressions}

【改写策略】
1. 学习上述论文的句式结构，用地道的中文学术表达来模仿
2. 用学术界真实使用的中文表达替代模板句
3. ���入作者视角（"笔者认为""本研究发现""值得注意的是""从实践来看"）
4. 句子长短交替，避免整齐划一
5. 适当使用转折词（"然而""不过""当然""尽管如此"）
6. 数据表述多样化（百分比↔分数、约数↔精确数、"近半数"↔"47%"）
7. 主动被动灵活切换，不要全是被动句

【禁止事项】
- 不要用"首先其次最后"等模板词
- 不要每段开头都用相同句式
- 不要堆砌同义词
- 不要改变核心观点和数据
- 不要输出英文，必须全部是中文

直接输出改写后的完整中文文本，不要任何解释。"""


def build_paper_enhanced_rewrite_messages(text: str, paper_expressions: list = None) -> list:
    """构建论文增强的降重消息列表。

    使用真实论文的表达方式作为参考，让 AI 模仿学术写作风格。

    Args:
        text: 需要改写的文本
        paper_expressions: 从论文数据库提取的优质表达列表（英文，AI会学习其结构用中文表达）

    Returns:
        消息列表
    """
    # 格式化论文表达
    if paper_expressions:
        expr_text = "\n".join(f"- {expr}" for expr in paper_expressions[:10])
    else:
        expr_text = "（无参考表达，请使用通用学术写作风格）"

    system_prompt = _SYSTEM_PAPER_ENHANCED_REWRITE.format(paper_expressions=expr_text)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请参考上述论文的句式结构和表达习惯，用中文改写以下文本：\n\n{text}"},
    ]


def fetch_paper_expressions(text: str, limit: int = 10) -> list:
    """从论文数据库获取相关的优质表达。

    Args:
        text: 用户文本，用于提取关键词搜索
        limit: 返回表达数量

    Returns:
        优质表达片段列表
    """
    try:
        from app.core.paper_database import get_paper_expressions
        return get_paper_expressions(text, limit=limit)
    except Exception as e:
        logger.warning(f"获取论文表达失败: {e}")
        return []


def build_smart_rewrite_messages(text: str, use_paper_db: bool = True) -> list:
    """智能降重：自动决定是否使用论文数据库增强。

    Args:
        text: 需要改写的文本
        use_paper_db: 是否使用论文数据库（默认开启）

    Returns:
        消息列表
    """
    if use_paper_db:
        # 尝试获取论文表达
        expressions = fetch_paper_expressions(text)
        if expressions:
            logger.info(f"使用论文数据库增强，获取到 {len(expressions)} 个表达")
            return build_paper_enhanced_rewrite_messages(text, expressions)

    # 回退到普通深度改写
    return build_deep_rewrite_messages(text)


# ── 感知查重结果的降重 prompt（针对性避开相似来源） ──

_SYSTEM_CONTEXT_AWARE_REWRITE = """论文降重专家。你需要改写句子，同时避开已知的相似来源。

【查重结果】
{check_result_info}

【改写目标】
1. 与上述匹配来源的表述完全不同
2. 通过 AIGC 检测（像人写的）
3. 保持原意，关键数据不变

【改写策略】
- 分析匹配片段的表述方式，刻意使用不同的��式结构
- 如果原文与某论文摘要相似，换一个完全不同的角度表述
- 用口语化学术表达替代书面化模板句
- 加入作者视角（"笔者认为""本研究发现"）
- 数据表述换种方式（百分比↔分数、约数↔精确数）

直接输出改写结果，不要解释。"""


def build_context_aware_rewrite_messages(context: RewriteContext) -> list:
    """构建感知查重结果的降重消息，让 AI 针对性避开相似来源。

    Args:
        context: RewriteContext 包含原文、风险等级、匹配来源等信息

    Returns:
        消息列表
    """
    # 格式化匹配来源信息
    source_info = []
    for i, src in enumerate(context.matched_sources[:3]):
        score = context.similarity_scores[i] if i < len(context.similarity_scores) else 0
        snippet = context.matched_snippets[i] if i < len(context.matched_snippets) else ""
        source_info.append(
            f"- 来源{i+1}: {src.get('title', '未知')} (相似度: {score:.0%})\n"
            f"  匹配片段: {snippet[:100]}..." if snippet else f"- 来源{i+1}: {src.get('title', '未知')} (相似度: {score:.0%})"
        )

    check_result_info = f"""原文: {context.original_text}
风险等级: {context.risk_level}
重复类型: {context.dup_type}
匹配来源:
{chr(10).join(source_info) if source_info else '无具体匹配来源（AI 推测风险）'}
AI建议: {context.suggestion}"""

    system_prompt = _SYSTEM_CONTEXT_AWARE_REWRITE.format(check_result_info=check_result_info)

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请改写以下句子，确保与上述匹配来源完全不同：\n\n{context.original_text}"},
    ]


# ── 同时降 AIGC 和降重复的综合 prompt ──

_SYSTEM_ANTI_AIGC_ANTI_DUP = """资深学术写作专家。你的任务是改写文本，同时实现两个目标：

【目标1：降低 AIGC 检测率】
让改写后的文本具有人类写作的"不完美"特征：
- 句子长短不一（有的15字，有的50字），打破 AI 的整齐节奏
- 加入口语化学术表达（"笔者认为""从实践来看""有趣的是"）
- 适当使用设问句、反问句增加互动感
- 加入主观评述词（"显然""不难发现""遗憾的是"）
- 偶尔使用不太规范但人类常用的表达
- 禁止"首先、其次、最后"等模板连接词

【目标2：降低重复度】
{source_avoidance_rules}

【参考表达（学习其句式结构，用中文模仿）】
{paper_expressions}

【改写策略】
1. 先分析原文与匹配来源的相似点，刻意避开
2. 完全重组句子结构，不是简单换词
3. 换种角度表述同一观点
4. 数据表述换种方式（百分比↔分数、约数↔精确数）
5. 主动被动灵活切换
6. 保持原意，关键信息不能丢

直接输出改写结果，不要解释。"""

_SYSTEM_ANTI_AIGC_ANTI_DUP_AGGRESSIVE = """资深学术写作专家。你的任务是对文本进行激进改写，大幅降低重复率和 AIGC 检测率。

【核心目标】
1. 让改写后的文本 100% 像人类学者亲手写的
2. 与原文和匹配来源的表述完全不同
3. 通过任何 AIGC 检测和查重系统

【需要避开的相似来源】
{source_avoidance_rules}

【激进改写策略】
1. 完全重构：打乱原文的句子顺序和段落结构
2. 视角转换：从第三人称改为第一人称视角（"笔者""本研究""我们"）
3. 表达人性化：
   - 用"大约/接近/将近"替代精确数字
   - 用设问句、反问句增加互动感
   - 加入"然而""不过""当然""尽管如此"等转折
   - 使用"有学者指出""研究表明""从实践来看"等引述
4. 句式多样化：
   - 长短句交替（10字到60字不等）
   - 主动被动灵活切换
   - 偶尔用倒装或省略句
5. 学术口语化：
   - "进行了分析"→"分析了"
   - "具有重要意义"→"意义重大"/"很有价值"
   - "研究发现"→"我们发现"/"分析显示"

【参考表达】
{paper_expressions}

【禁止事项】
- 不要用"首先其次最后"等模板词
- 不要每段开头都用相同句式
- 不要堆砌同义词
- 不要改变核心观点和数据

直接输出改写后的完整文本，不要任何解释。"""


def build_anti_aigc_anti_dup_messages(
    text: str,
    check_result: CheckResult = None,
    paper_expressions: list = None,
    aggressive: bool = False
) -> list:
    """构建同时降 AIGC 检测率和降重复度的消息。

    Args:
        text: 需要改写的文本
        check_result: 查重结果（可选），包含匹配来源信息
        paper_expressions: 论文表达参考（可选）
        aggressive: 是否使用激进模式

    Returns:
        消息列表
    """
    # 构建来源规避规则
    if check_result and check_result.sources:
        source_rules = []
        for src in check_result.sources[:3]:
            title = src.get("title", "")
            snippet = src.get("snippet", "")
            if title:
                rule = f"- 避开与《{title}》相似的表述"
                if snippet:
                    rule += f"\n  相似片段: {snippet[:80]}..."
                source_rules.append(rule)
        source_avoidance_rules = "需要避开的相似来源：\n" + "\n".join(source_rules)
    else:
        source_avoidance_rules = "（无具体匹配来源，请大幅改变表述方式以降低潜在重复风险）"

    # 格式化论文表达
    if paper_expressions:
        expr_text = "\n".join(f"- {expr}" for expr in paper_expressions[:8])
    else:
        expr_text = "（无参考表达，请使用自然的学术写作风格）"

    # 选择 prompt
    if aggressive:
        system_prompt = _SYSTEM_ANTI_AIGC_ANTI_DUP_AGGRESSIVE.format(
            source_avoidance_rules=source_avoidance_rules,
            paper_expressions=expr_text
        )
    else:
        system_prompt = _SYSTEM_ANTI_AIGC_ANTI_DUP.format(
            source_avoidance_rules=source_avoidance_rules,
            paper_expressions=expr_text
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请改写以下文本：\n\n{text}"},
    ]


def build_batch_anti_aigc_anti_dup_messages(
    flagged_results: list,
    paper_expressions: list = None,
    aggressive: bool = False
) -> list:
    """构建批量降重消息，同时降 AIGC 和降重复。

    Args:
        flagged_results: CheckResult 列表（高风险句子）
        paper_expressions: 论文表达参考（可选）
        aggressive: 是否使用激进模式

    Returns:
        消息列表
    """
    # 构建每句的来源信息
    sentences_info = []
    for r in flagged_results:
        info = f"[{r.index}] {r.text}"
        if r.sources:
            sources_str = ", ".join(s.get("title", "")[:30] for s in r.sources[:2])
            info += f"\n    相似来源: {sources_str}"
        sentences_info.append(info)

    # 格式化论文表达
    if paper_expressions:
        expr_text = "\n".join(f"- {expr}" for expr in paper_expressions[:8])
    else:
        expr_text = "（无参考表达）"

    mode_desc = "激进" if aggressive else "标准"
    system_prompt = f"""论文降重专家。批量改写高重复句子，目标：
1. 通过 AIGC 检测（不像 AI 写的）
2. 降低查重率（与原文和匹配来源表述完全不同）

【{mode_desc}模式改写要求】
- 每句都要大幅改动结构，不是简单换词
- 针对每句的相似来源，刻意使用不同的表述方式
- 用自然的学术口语替代模板句式
- 句子长短要有变化，避免整齐划一
- 加入"笔者""本研究""从...角度看"等人称视角
- 数据换种表述方式
- 保持原意，关键信息不能丢

【参考表达】
{expr_text}

返回JSON数组：[{{"index":序号,"rewritten":"改写后句子"}}]
只返回JSON，无其他文字。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请改写以下高重复风险句子（注意避开各自的相似来源）：\n\n" + "\n".join(sentences_info)},
    ]


def calculate_duplication_rate(check_results: list) -> float:
    """计算重复率。

    Args:
        check_results: CheckResult 列表

    Returns:
        重复率 (0.0 - 1.0)
    """
    if not check_results:
        return 0.0

    total = len(check_results)
    high_count = sum(1 for r in check_results if r.risk == "high")
    medium_count = sum(1 for r in check_results if r.risk == "medium")

    # 高风险权重 1.0，中风险权重 0.5
    weighted = high_count * 1.0 + medium_count * 0.5
    return weighted / total


def filter_flagged_sentences(check_results: list, threshold: str = "medium") -> list:
    """筛选需要降重的句子。

    Args:
        check_results: CheckResult 列表
        threshold: 阈值 "high" 只选高风险，"medium" 选高+中风险

    Returns:
        需要降重的 CheckResult 列表
    """
    if threshold == "high":
        return [r for r in check_results if r.risk == "high"]
    else:
        return [r for r in check_results if r.risk in ("high", "medium")]


def create_rewrite_context_from_result(result: CheckResult) -> RewriteContext:
    """从 CheckResult 创建 RewriteContext。

    Args:
        result: 查重结果

    Returns:
        RewriteContext 对象
    """
    return RewriteContext(
        original_text=result.text,
        risk_level=result.risk,
        dup_type=result.dup_type,
        matched_sources=result.sources,
        similarity_scores=[s.get("score", 0) for s in result.sources],
        matched_snippets=[s.get("snippet", "") for s in result.sources],
        suggestion=result.suggestion
    )
