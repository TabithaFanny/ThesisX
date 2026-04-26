"""
Math formula renderer — outputs KaTeX-compatible HTML.

LaTeX formulas ($...$, $$...$$) are converted to <span> elements with
`data-latex` attributes. The browser-side KaTeX library (loaded via CDN)
renders them into beautiful math. No matplotlib dependency needed for preview.
"""

import html as _html_mod
import logging
import re

logger = logging.getLogger(__name__)


# ─── 识别裸 LaTeX 的正则 ───
# 检测 LaTeX 反斜杠命令 (\frac, \alpha, \text 等，至少 2 个字母)
_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]{2,}")
# 检测裸下标/上标 (C_1, x^2, C_{12}, x^{n+1})
_SUB_SUP_RE = re.compile(r"[A-Za-z][_^](?:\{[^}]*\}|[A-Za-z0-9])")
# 匹配代码块 (``` ... ```) 以便跳过
_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
# 匹配已包裹的 $$...$$ 或 $...$
_ALREADY_WRAPPED_RE = re.compile(r"\$\$[\s\S]+?\$\$|\$(?!\$)[^$\n]+?\$(?!\$)")
# 按中文字符边界分割
_CJK_SPLIT_RE = re.compile(r"([\u4e00-\u9fff]+)")
# 占位符分割
_PLACEHOLDER_SPLIT_RE = re.compile(r"(<!--MATHPRESERVE\d+-->)")


def _has_latex(text: str) -> bool:
    """检查文本是否包含 LaTeX 标记 (\\command 或下标/上标)。"""
    return bool(_LATEX_CMD_RE.search(text)) or bool(_SUB_SUP_RE.search(text))


def _dollar_wrap_segment(seg: str) -> str:
    """将含 LaTeX 的非中文文本段包裹为 $...$，去掉首尾标点/空白。"""
    stripped = seg.lstrip(" \t，,：:；;。.、！!？?（）")
    lead = seg[: len(seg) - len(stripped)]
    stripped2 = stripped.rstrip(" \t，,：:；;。.、！!？?）")
    trail = stripped[len(stripped2) :]
    if stripped2:
        return f"{lead}${stripped2}${trail}"
    return seg


def _wrap_inline_segments(line: str) -> str:
    """在中文/公式混合行中，按中文边界拆分并包裹裸 LaTeX 片段。"""
    parts = _CJK_SPLIT_RE.split(line)
    result = []
    for part in parts:
        if not part:
            continue
        # 中文片段 — 原样保留
        if re.match(r"[\u4e00-\u9fff]", part):
            result.append(part)
            continue
        # 含占位符 — 按占位符进一步拆分，分别处理
        if "<!--MATHPRESERVE" in part:
            subs = _PLACEHOLDER_SPLIT_RE.split(part)
            for sub in subs:
                if not sub:
                    continue
                if sub.startswith("<!--MATHPRESERVE"):
                    result.append(sub)
                elif _has_latex(sub):
                    result.append(_dollar_wrap_segment(sub))
                else:
                    result.append(sub)
            continue
        # 普通非中文片段 — 若含 LaTeX 则包裹
        if _has_latex(part):
            result.append(_dollar_wrap_segment(part))
        else:
            result.append(part)
    return "".join(result)


def wrap_bare_latex(text: str) -> str:
    """
    检测并包裹裸 LaTeX 公式 (未使用 $...$ 或 $$...$$ 的)。
    - 整行公式 (几乎无中文，以公式字符开头) → $$...$$
    - 中文行内公式片段 → $...$
    跳过代码块和已包裹的公式。
    """
    # 1. 提取代码块和已包裹公式，用占位符替换
    preserved = {}
    counter = [0]

    def _preserve(m: re.Match) -> str:
        key = f"<!--MATHPRESERVE{counter[0]}-->"
        counter[0] += 1
        preserved[key] = m.group(0)
        return key

    text = _CODE_BLOCK_RE.sub(_preserve, text)
    text = _ALREADY_WRAPPED_RE.sub(_preserve, text)

    # 2. 逐行处理
    lines = text.split("\n")
    result_lines = []
    for line in lines:
        stripped = line.strip()
        # 跳过空行
        if not stripped:
            result_lines.append(line)
            continue
        # 无 LaTeX 标记 → 原样保留
        if not _has_latex(stripped):
            result_lines.append(line)
            continue

        chinese_count = len(re.findall(r"[\u4e00-\u9fff]", stripped))

        # Block: 几乎无中文 + 以公式字符开头 → 整行 $$...$$
        if (
            chinese_count <= 2
            and re.match(r"\s*[A-Za-z0-9\\({\[]", stripped)
            and not stripped.startswith("$$")
        ):
            result_lines.append(f"$${stripped}$$")
            continue

        # Inline: 按中文边界拆分，包裹公式片段
        result_lines.append(_wrap_inline_segments(line))

    text = "\n".join(result_lines)

    # 3. 恢复占位符
    for key, value in preserved.items():
        text = text.replace(key, value)

    return text


def preprocess_math(text: str) -> str:
    """
    Replace $$...$$ (block) and $...$ (inline) math expressions with
    KaTeX-compatible <span> elements (data-latex attribute).
    Must be called BEFORE markdown conversion.
    """
    # 先处理裸 LaTeX 公式
    text = wrap_bare_latex(text)
    # Process block math first ($$...$$)
    text = _replace_block_math(text)
    # Then inline math ($...$)
    text = _replace_inline_math(text)
    return text


def _replace_block_math(text: str) -> str:
    """Replace $$...$$ with KaTeX block-level HTML spans."""
    pattern = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

    def replace(m: re.Match) -> str:
        formula = m.group(1).strip()
        escaped = _html_mod.escape(formula, quote=True)
        return (
            f'\n\n<span class="math-formula math-formula-block" '
            f'contenteditable="false" '
            f'data-latex="{escaped}">{escaped}</span>\n\n'
        )

    return pattern.sub(replace, text)


def _replace_inline_math(text: str) -> str:
    """Replace $...$ (not $$) with KaTeX inline HTML spans."""
    # Use negative lookahead/behind to avoid matching $$ again
    pattern = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")

    def replace(m: re.Match) -> str:
        formula = m.group(1).strip()
        escaped = _html_mod.escape(formula, quote=True)
        return (
            f'<span class="math-formula" '
            f'contenteditable="false" '
            f'data-latex="{escaped}">{escaped}</span>'
        )

    return pattern.sub(replace, text)
