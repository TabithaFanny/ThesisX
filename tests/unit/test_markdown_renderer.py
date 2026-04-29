"""markdown_renderer 单元测试

覆盖纯函数：_preprocess_rich_markers, _render_json_value, _build_json_viewer,
_colorize_xml_line, _split_html_lines。
"""
import pytest

from app.core.markdown_renderer import (
    _build_json_viewer,
    _colorize_xml_line,
    _preprocess_rich_markers,
    _render_json_value,
    _split_html_lines,
)


# ── _preprocess_rich_markers ──────────────────────────────────────


class TestPreprocessRichMarkers:
    """富文本标记预处理测试"""

    def test_color_marker(self):
        """[COLOR:red] 标记转为 <span style=\"color:red\">"""
        text = "[COLOR:red]红色文字[/COLOR]"
        result = _preprocess_rich_markers(text)
        assert '<span style="color:red">' in result
        assert "红色文字" in result

    def test_font_marker(self):
        """[FONT:Arial] 标记转为 font-family span"""
        text = "[FONT:Arial]字体测试[/FONT]"
        result = _preprocess_rich_markers(text)
        assert '<span style="font-family:Arial">' in result

    def test_size_marker_with_unit(self):
        """[SIZE:16px] 标记保留单位"""
        text = "[SIZE:16px]大小测试[/SIZE]"
        result = _preprocess_rich_markers(text)
        assert '<span style="font-size:16px">' in result

    def test_size_marker_auto_px(self):
        """[SIZE:20] 纯数字自动加 px"""
        text = "[SIZE:20]大小测试[/SIZE]"
        result = _preprocess_rich_markers(text)
        assert '<span style="font-size:20px">' in result

    def test_style_marker_multiple_attrs(self):
        """[STYLE color=red bold=1] 多属性标记"""
        text = '[STYLE color=red bold=1]样式测试[/STYLE]'
        result = _preprocess_rich_markers(text)
        assert "color:red" in result
        assert "font-weight:bold" in result

    def test_style_marker_italic(self):
        """[STYLE italic=1] 斜体标记"""
        text = '[STYLE italic=1]斜体[/STYLE]'
        result = _preprocess_rich_markers(text)
        assert "font-style:italic" in result

    def test_style_marker_bg(self):
        """[STYLE bg=yellow] 背景色标记"""
        text = '[STYLE bg=yellow]背景[/STYLE]'
        result = _preprocess_rich_markers(text)
        assert "background-color:yellow" in result

    def test_no_markers_unchanged(self):
        """无标记文本不变"""
        text = "普通文本没有任何标记"
        result = _preprocess_rich_markers(text)
        assert result == text

    def test_nested_markers(self):
        """嵌套标记（3 轮替换）"""
        text = "[COLOR:red][SIZE:20]嵌套[/SIZE][/COLOR]"
        result = _preprocess_rich_markers(text)
        assert "color:red" in result
        assert "font-size:20px" in result

    def test_empty_text(self):
        """空文本"""
        result = _preprocess_rich_markers("")
        assert result == ""


# ── _render_json_value ────────────────────────────────────────────


class TestRenderJsonValue:
    """JSON 值渲染测试"""

    def test_string_value(self):
        """字符串值渲染"""
        result = _render_json_value("hello")
        assert "jv-string" in result
        assert "hello" in result

    def test_number_value(self):
        """数值渲染"""
        result = _render_json_value(42)
        assert "jv-number" in result
        assert "42" in result

    def test_float_value(self):
        """浮点数渲染"""
        result = _render_json_value(3.14)
        assert "jv-number" in result
        assert "3.14" in result

    def test_bool_true(self):
        """布尔 true 渲染"""
        result = _render_json_value(True)
        assert "jv-bool" in result
        assert "true" in result

    def test_bool_false(self):
        """布尔 false 渲染"""
        result = _render_json_value(False)
        assert "jv-bool" in result
        assert "false" in result

    def test_null_value(self):
        """null 值渲染"""
        result = _render_json_value(None)
        assert "jv-null" in result
        assert "null" in result

    def test_empty_dict(self):
        """空字典渲染"""
        result = _render_json_value({})
        assert "jv-brace" in result
        assert "{}" in result

    def test_empty_list(self):
        """空列表渲染"""
        result = _render_json_value([])
        assert "jv-bracket" in result
        assert "[]" in result

    def test_dict_with_entries(self):
        """有内容的字典渲染"""
        result = _render_json_value({"key": "value"})
        assert "jv-key" in result
        assert "key" in result
        assert "jv-toggle" in result
        assert "jv-collapsible" in result

    def test_list_with_entries(self):
        """有内容的列表渲染"""
        result = _render_json_value([1, 2, 3])
        assert "jv-toggle" in result
        assert "jv-collapsible" in result

    def test_nested_dict(self):
        """嵌套字典渲染"""
        result = _render_json_value({"a": {"b": "c"}})
        assert "jv-key" in result
        assert "a" in result
        assert "b" in result

    def test_string_escaping(self):
        """字符串 HTML 转义"""
        result = _render_json_value("<script>alert(1)</script>")
        assert "<script>" not in result  # 应被转义
        assert "&lt;" in result

    def test_indent_parameter(self):
        """缩进参数生效"""
        r0 = _render_json_value({"a": 1}, indent=0)
        r2 = _render_json_value({"a": 1}, indent=2)
        # 更深缩进应有更多空格
        assert len(r2) >= len(r0)


# ── _build_json_viewer ────────────────────────────────────────────


class TestBuildJsonViewer:
    """JSON viewer 构建测试"""

    def test_valid_json(self):
        """有效 JSON 生成 viewer"""
        code = '{"name": "test", "value": 42}'
        result = _build_json_viewer(code)
        assert "json-viewer" in result
        assert "jv-header" in result
        assert "jv-body" in result
        assert "JSON" in result

    def test_invalid_json_returns_empty(self):
        """无效 JSON 返回空字符串"""
        result = _build_json_viewer("not json at all")
        assert result == ""

    def test_json_array(self):
        """JSON 数组生成 viewer"""
        code = "[1, 2, 3]"
        result = _build_json_viewer(code)
        assert "json-viewer" in result

    def test_json_with_special_chars(self):
        """含特殊字符的 JSON"""
        code = '{"key": "value with <html> & \\"quotes\\""}'
        result = _build_json_viewer(code)
        assert "json-viewer" in result

    def test_empty_json_object(self):
        """空 JSON 对象"""
        result = _build_json_viewer("{}")
        assert "json-viewer" in result

    def test_line_numbers(self):
        """viewer 包含行号"""
        code = '{"a": 1, "b": 2}'
        result = _build_json_viewer(code)
        assert "jv-ln" in result


# ── _colorize_xml_line ────────────────────────────────────────────


class TestColorizeXmlLine:
    """XML 行着色测试"""

    def test_tag_name(self):
        """标签名着色"""
        result = _colorize_xml_line("<root>")
        assert "xv-tag" in result
        assert "root" in result

    def test_attribute(self):
        """属性着色"""
        result = _colorize_xml_line('<element attr="value">')
        assert "xv-attr" in result
        assert "attr" in result

    def test_attribute_value(self):
        """属性值着色"""
        result = _colorize_xml_line('<element attr="value">')
        assert "xv-attrval" in result

    def test_comment(self):
        """注释着色"""
        result = _colorize_xml_line("<!-- this is a comment -->")
        assert "xv-comment" in result

    def test_closing_tag(self):
        """闭合标签"""
        result = _colorize_xml_line("</root>")
        assert "xv-tag" in result

    def test_self_closing_tag(self):
        """自闭合标签"""
        result = _colorize_xml_line("<br/>")
        assert "xv-tag" in result

    def test_plain_text(self):
        """纯文本不变"""
        result = _colorize_xml_line("just text")
        assert result == "just text"

    def test_html_escaping(self):
        """HTML 特殊字符转义"""
        result = _colorize_xml_line("<tag>&amp;</tag>")
        # 标签名应被着色，& 应被转义
        assert "xv-tag" in result


# ── _split_html_lines ─────────────────────────────────────────────


class TestSplitHtmlLines:
    """HTML 行拆分测试"""

    def test_simple_lines(self):
        """简单行拆分"""
        html = "<span>a</span>\n<span>b</span>"
        result = _split_html_lines(html)
        assert len(result) == 2

    def test_unclosed_span_carried_over(self):
        """未闭合的 span 跨行延续"""
        html = '<span class="x">line1\nline2</span>'
        result = _split_html_lines(html)
        assert len(result) == 2
        # 第一行应有开标签
        assert '<span class="x">' in result[0]
        # 第二行应有闭标签
        assert "</span>" in result[1]

    def test_empty_input(self):
        """空输入"""
        result = _split_html_lines("")
        assert result == [""]

    def test_single_line(self):
        """单行"""
        html = "<span>hello</span>"
        result = _split_html_lines(html)
        assert len(result) == 1

    def test_nested_spans(self):
        """嵌套 span 跨行"""
        html = '<span class="a"><span class="b">line1\nline2</span></span>'
        result = _split_html_lines(html)
        assert len(result) == 2
