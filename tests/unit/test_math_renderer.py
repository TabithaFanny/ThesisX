"""math_renderer 单元测试

覆盖：preprocess_math, wrap_bare_latex 纯函数。
"""
import pytest

from app.core.math_renderer import preprocess_math, wrap_bare_latex


# ── preprocess_math ───────────────────────────────────────────────


class TestPreprocessMath:
    """preprocess_math 测试"""

    def test_inline_math(self):
        """$...$ 内联公式转为 span"""
        text = "公式 $E=mc^2$ 在这里"
        result = preprocess_math(text)
        assert '<span class="math-formula"' in result
        assert 'data-latex="E=mc^2"' in result

    def test_block_math(self):
        """$$...$$ 块级公式转为 span"""
        text = "$$E=mc^2$$"
        result = preprocess_math(text)
        assert 'math-formula-block' in result
        assert 'data-latex="E=mc^2"' in result

    def test_no_math_unchanged(self):
        """无数学公式文本不变"""
        text = "这是一段普通文本"
        result = preprocess_math(text)
        assert result == text

    def test_multiple_inline(self):
        """多个内联公式"""
        text = "$a$ 和 $b$ 和 $c$"
        result = preprocess_math(text)
        assert result.count('class="math-formula"') == 3

    def test_mixed_inline_and_block(self):
        """混合内联和块级公式"""
        text = "行内 $x$ 和块级 $$y=z$$"
        result = preprocess_math(text)
        assert 'math-formula-block' in result
        assert 'class="math-formula"' in result

    def test_empty_text(self):
        """空文本"""
        result = preprocess_math("")
        assert result == ""

    def test_dollar_sign_in_text(self):
        """文本中的美元符号（非公式）不被误处理"""
        text = "价格是 $100"
        result = preprocess_math(text)
        # 只有一个 $ 不应被当作公式
        assert 'data-latex' not in result


# ── wrap_bare_latex ───────────────────────────────────────────────


class TestWrapBareLatex:
    """wrap_bare_latex 裸 LaTeX 包裹测试"""

    def test_bare_frac_wrapped(self):
        """裸 \\frac 命令被包裹为 $$...$$"""
        text = "\\frac{a}{b}"
        result = wrap_bare_latex(text)
        assert "$$" in result
        assert "\\frac{a}{b}" in result

    def test_already_wrapped_unchanged(self):
        """已包裹的公式不变"""
        text = "$E=mc^2$"
        result = wrap_bare_latex(text)
        assert result == text

    def test_block_already_wrapped_unchanged(self):
        """已包裹的块级公式不变"""
        text = "$$E=mc^2$$"
        result = wrap_bare_latex(text)
        assert result == text

    def test_code_block_preserved(self):
        """代码块中的 LaTeX 不被处理"""
        text = "```python\n\\frac{a}{b}\n```"
        result = wrap_bare_latex(text)
        assert "\\frac{a}{b}" in result
        # 代码块内的 LaTeX 不应被包裹
        lines = result.split("\n")
        for line in lines:
            if "\\frac" in line:
                assert "$$" not in line or "```" in line

    def test_chinese_text_with_inline_latex(self):
        """中文行内的 LaTeX 片段被包裹为 $...$"""
        text = "设 $x$ 为变量"
        result = wrap_bare_latex(text)
        # 已经包裹的应保持不变
        assert "$x$" in result

    def test_empty_text(self):
        """空文本"""
        result = wrap_bare_latex("")
        assert result == ""

    def test_no_latex_unchanged(self):
        """无 LaTeX 的文本不变"""
        text = "这是普通中文文本"
        result = wrap_bare_latex(text)
        assert result == text
