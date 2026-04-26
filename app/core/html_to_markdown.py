"""
html_to_markdown.py — 将 contentEditable HTML 转换回 Markdown

使用 markdownify 库，增加对特殊标签的处理：
  · <u> 下划线
  · <sup> / <sub> 上下标
  · <span style="color:..."> 字体颜色
  · <span style="background-color:..."> 高亮
  · <span style="font-size:..."> 字号
  · <div class="chart-container" data-chart-type="..." data-chart-config="..."> 数据图
"""

import re

from markdownify import MarkdownConverter
from markdownify import markdownify as md

# ── 图表容器正则：提取整个 chart-container div ──
_CHART_CONTAINER_RE = re.compile(
    r'<div\s[^>]*class="chart-container"[^>]*data-chart-type="[^"]+"[^>]*>.*?</div>',
    re.DOTALL,
)


class _WtzConverter(MarkdownConverter):
    """自定义转换器，处理文表智联使用的特殊 HTML 标签。"""

    def convert_u(self, el, text, parent_tags):
        return f"<u>{text}</u>"

    def convert_sup(self, el, text, parent_tags):
        return f"<sup>{text}</sup>"

    def convert_sub(self, el, text, parent_tags):
        return f"<sub>{text}</sub>"

    def convert_div(self, el, text, parent_tags):
        """处理 <div>：若为 chart-container 则保留原始 HTML。"""
        raw = el.get("class", [])
        classes = raw if isinstance(raw, list) else str(raw).split()
        if "chart-container" in classes and el.get("data-chart-type"):
            # 保留完整 HTML（含 data 属性），作为 Markdown 原始 HTML 块
            return f"\n\n{str(el)}\n\n"
        # 其他 div：正常转换子节点
        return f"\n\n{text}\n\n" if text.strip() else ""

    def convert_span(self, el, text, parent_tags):
        style = el.get("style", "")
        if not style:
            return text

        # 字体颜色
        color_match = re.search(r'color\s*:\s*([^;"\s]+)', style)
        bg_match = re.search(r'background-color\s*:\s*([^;"\s]+)', style)
        size_match = re.search(r"font-size\s*:\s*(\d+)px", style)

        if bg_match:
            return f'<span style="background-color: {bg_match.group(1)}">{text}</span>'
        if color_match and not bg_match:
            return f'<span style="color: {color_match.group(1)}">{text}</span>'
        if size_match:
            return f'<span style="font-size: {size_match.group(1)}px">{text}</span>'

        return text

    def convert_del(self, el, text, parent_tags):
        return f"~~{text}~~"

    convert_s = convert_del


def html_to_markdown(html: str) -> str:
    """将 HTML 转换为 Markdown 文本。

    Args:
        html: contentEditable 产出的 HTML 片段

    Returns:
        对应的 Markdown 文本
    """
    if not html or not html.strip():
        return ""

    # ── 第一步：提取并保护图表容器，防止 markdownify 破坏 ──
    chart_placeholders = {}
    counter = [0]

    def _protect_chart(m):
        key = f"__CHART_PLACEHOLDER_{counter[0]}__"
        chart_placeholders[key] = m.group(0)
        counter[0] += 1
        return key

    html = _CHART_CONTAINER_RE.sub(_protect_chart, html)

    # 清理 contentEditable 产出的常见垃圾
    # 移除空的 <br> 在块级元素末尾
    html = re.sub(
        r"<br\s*/?\s*>\s*</(?:div|p|li|h[1-6])>", lambda m: "</" + m.group(0).split("</")[1], html
    )

    result = _WtzConverter(
        heading_style="atx",
        bullets="-",
        strong_em_symbol="*",
        newline_style="backslash",
        code_language="",
        escape_misc=False,
        escape_underscores=False,
    ).convert(html)

    # ── 还原图表容器原始 HTML ──
    for key, original_html in chart_placeholders.items():
        result = result.replace(key, f"\n\n{original_html}\n\n")

    # 后处理：清理多余空行
    result = re.sub(r"\n{3,}", "\n\n", result)
    # 清理行尾空格
    result = re.sub(r" +\n", "\n", result)

    return result.strip()
