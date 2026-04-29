"""Tests for app.core.pipeline.quality_checks — static quality checks."""

from app.core.pipeline.quality_checks import build_quality_report, count_marker, count_words, has_section


class TestCountWords:
    def test_chinese_text(self):
        assert count_words("这是一段中文测试文本") == 10

    def test_english_text(self):
        assert count_words("hello world test") == 3

    def test_mixed_text(self):
        # Chinese chars + English words
        result = count_words("这是 hello 世界 world")
        assert result == 6  # 4 Chinese + 2 English

    def test_empty(self):
        assert count_words("") == 0


class TestHasSection:
    def test_heading_match(self):
        text = "# 摘要\nThis is the abstract."
        assert has_section(text, "摘要") is True

    def test_inline_match(self):
        text = "本文的摘要部分如下"
        assert has_section(text, "摘要") is True

    def test_no_match(self):
        text = "This is just some text."
        assert has_section(text, "摘要") is False

    def test_multiple_keywords(self):
        text = "一、引言\nIntroduction text"
        assert has_section(text, "引言", "一、") is True


class TestCountMarker:
    def test_count_marker_found(self):
        text = "这里需要[引用待核查]，另一处也是[引用待核查]"
        assert count_marker(text, "[引用待核查]") == 2

    def test_count_marker_not_found(self):
        text = "This is clean text."
        assert count_marker(text, "[引用待核查]") == 0

    def test_data_marker(self):
        text = "数据[数据待补充]在这里"
        assert count_marker(text, "[数据待补充]") == 1


class TestBuildQualityReport:
    def test_full_paper(self):
        md = """\
# 摘要
本文研究了...

## 关键词
关键词1; 关键词2

# 一、引言
引言内容...

# 二、文献综述
文献内容...

# 六、结论
结论内容...

# 参考文献
[1] Author, Title, Journal, 2024.
"""
        result = build_quality_report(md)
        assert result.has_abstract is True
        assert result.has_keywords is True
        assert result.has_introduction is True
        assert result.has_conclusion is True
        assert result.has_references is True
        assert result.citation_warning_count == 0
        assert result.data_missing_count == 0
        # Should always have the "需人工核查" warning
        assert any("人工核查" in w for w in result.warnings)

    def test_minimal_paper(self):
        md = "Just some text without any structure."
        result = build_quality_report(md)
        assert result.has_abstract is False
        assert result.has_keywords is False
        assert result.has_introduction is False
        assert result.has_conclusion is False
        assert result.has_references is False
        assert result.word_count < 3000
        # Should have multiple warnings
        assert len(result.warnings) >= 2

    def test_paper_with_markers(self):
        md = """\
# 摘要
摘要内容

# 一、引言
引言内容 [引用待核查]

# 二、文献综述
文献 [引用待核查] 内容 [数据待补充]

# 六、结论
结论

# 参考文献
[1] Some reference
""" + "内容" * 2000  # Make it long enough
        result = build_quality_report(md)
        assert result.citation_warning_count == 2
        assert result.data_missing_count == 1
        assert any("引用待核查" in w for w in result.warnings)

    def test_short_paper_warning(self):
        md = "# 摘要\n短文\n# 参考文献\n"
        result = build_quality_report(md)
        assert any("偏少" in w for w in result.warnings)
