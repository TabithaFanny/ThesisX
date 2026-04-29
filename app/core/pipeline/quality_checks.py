"""Static quality checks for generated paper markdown.

All checks are deterministic — no LLM calls, no network requests.
"""

from __future__ import annotations

import re

from .models import QualityCheckResult


def count_words(text: str) -> int:
    """Rough Chinese + English word count.

    Chinese characters count as 1 word each.
    English words (space-separated) count as 1 word each.
    """
    # Count Chinese characters
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    # Remove Chinese chars, count remaining English words
    text_without_chinese = re.sub(r"[\u4e00-\u9fff]+", " ", text)
    english_words = len(text_without_chinese.split())
    return chinese_chars + english_words


def has_section(text: str, *keywords: str) -> bool:
    """Check if any keyword appears as a heading or in the text."""
    for kw in keywords:
        if re.search(rf"#{1,6}\s*{re.escape(kw)}", text):
            return True
        if kw in text:
            return True
    return False


def count_marker(text: str, marker: str) -> int:
    """Count occurrences of a bracketed marker like [引用待核查]."""
    return text.count(marker)


def build_quality_report(markdown: str) -> QualityCheckResult:
    """Run all static quality checks on the generated paper.

    Returns a QualityCheckResult with findings and warnings.
    """
    warnings: list[str] = []

    word_count = count_words(markdown)
    abstract = has_section(markdown, "摘要")
    keywords = has_section(markdown, "关键词")
    introduction = has_section(markdown, "引言", "一、", "一.")
    conclusion = has_section(markdown, "结论", "结语")
    references = has_section(markdown, "参考文献")

    citation_warnings = count_marker(markdown, "[引用待核查]")
    data_missing = count_marker(markdown, "[数据待补充]")

    if word_count < 3000:
        warnings.append(f"论文字数偏少（{word_count} 字），建议扩充至 5000+ 字")
    if not abstract:
        warnings.append("未检测到摘要章节")
    if not keywords:
        warnings.append("未检测到关键词")
    if not introduction:
        warnings.append("未检测到引言章节")
    if not conclusion:
        warnings.append("未检测到结论章节")
    if not references:
        warnings.append("未检测到参考文献章节")
    if citation_warnings > 0:
        warnings.append(f"有 {citation_warnings} 处 [引用待核查] 标记需人工验证")
    if data_missing > 0:
        warnings.append(f"有 {data_missing} 处 [数据待补充] 标记需补充数据")

    warnings.append("参考文献真实性需人工核查")

    return QualityCheckResult(
        word_count=word_count,
        has_abstract=abstract,
        has_keywords=keywords,
        has_introduction=introduction,
        has_conclusion=conclusion,
        has_references=references,
        citation_warning_count=citation_warnings,
        data_missing_count=data_missing,
        warnings=warnings,
    )
