import html as _html
import json as _json
import re

import markdown
from pygments import highlight as _pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

try:
    from app.core.math_renderer import preprocess_math

    _MATH_AVAILABLE = True
except ImportError:
    _MATH_AVAILABLE = False


# ── 需要增强渲染的语言标签 ──
_JSON_LANGS = {"json", "json5", "jsonc"}
_XML_LANGS = {"xml", "html", "xhtml", "svg", "xsl", "xslt"}
_TERMINAL_LANGS = {
    "bash",
    "shell",
    "sh",
    "zsh",
    "console",
    "terminal",
    "cmd",
    "bat",
    "powershell",
    "ps1",
}
# 脚本类终端语言（终端 UI + 行号模式）
_TERMINAL_SCRIPT_LANGS = {"cmd", "bat", "powershell", "ps1"}
_SCRIPT_LANGS = {
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "ruby",
    "rb",
    "perl",
    "pl",
    "php",
    "go",
    "golang",
    "rust",
    "rs",
    "java",
    "c",
    "cpp",
    "csharp",
    "cs",
    "kotlin",
    "kt",
    "swift",
    "scala",
    "lua",
    "r",
    "sql",
    "yaml",
    "yml",
    "toml",
    "ini",
    "css",
    "scss",
    "less",
    "jsx",
    "tsx",
    "vue",
    "dart",
    "haskell",
    "hs",
    "makefile",
    "dockerfile",
    "groovy",
    "matlab",
}
_ENHANCED_LANGS = _JSON_LANGS | _XML_LANGS | _TERMINAL_LANGS | _SCRIPT_LANGS

# Regex to match fenced code blocks with language tag
_FENCE_RE = re.compile(
    r"^(`{3,}|~{3,})\s*(\w+)\s*\n(.*?)^\1\s*$",
    re.MULTILINE | re.DOTALL,
)

# ── 富文本标记：[COLOR:xxx]...[/COLOR]  [FONT:xxx]...[/FONT]  [SIZE:xx]...[/SIZE] ──
_COLOR_RE = re.compile(
    r"\[COLOR:(#?[\w,()\s]+)\](.*?)\[/COLOR\]",
    re.DOTALL,
)
_FONT_RE = re.compile(
    r"\[FONT:([^\]]+)\](.*?)\[/FONT\]",
    re.DOTALL,
)
_SIZE_RE = re.compile(
    r"\[SIZE:([\d.]+(?:px|pt|em|rem)?)\](.*?)\[/SIZE\]",
    re.DOTALL,
)
# 组合标记: [STYLE color=xx font=xx size=xx]...[/STYLE]
_STYLE_RE = re.compile(
    r"\[STYLE([^\]]+)\](.*?)\[/STYLE\]",
    re.DOTALL,
)


def _preprocess_rich_markers(text: str) -> str:
    """将 [COLOR:...][FONT:...][SIZE:...][STYLE ...] 标记转为 HTML <span>。"""

    def _color_repl(m):
        color = m.group(1).strip()
        inner = m.group(2)
        return f'<span style="color:{color}">{inner}</span>'

    def _font_repl(m):
        family = m.group(1).strip()
        inner = m.group(2)
        return f'<span style="font-family:{family}">{inner}</span>'

    def _size_repl(m):
        size = m.group(1).strip()
        # 如果只有数字没有单位，默认 px
        if size.replace(".", "").isdigit():
            size += "px"
        inner = m.group(2)
        return f'<span style="font-size:{size}">{inner}</span>'

    def _style_repl(m):
        attrs_str = m.group(1).strip()
        inner = m.group(2)
        parts = []
        # 解析 color=xx font=xx size=xx
        for pair in re.finditer(r'(\w+)\s*=\s*("[^"]*"|[^\s]+)', attrs_str):
            key = pair.group(1).lower()
            val = pair.group(2).strip('"')
            if key == "color":
                parts.append(f"color:{val}")
            elif key in ("font", "font-family"):
                parts.append(f"font-family:{val}")
            elif key in ("size", "font-size"):
                if val.replace(".", "").isdigit():
                    val += "px"
                parts.append(f"font-size:{val}")
            elif key == "bold":
                parts.append("font-weight:bold")
            elif key == "italic":
                parts.append("font-style:italic")
            elif key == "bg":
                parts.append(f"background-color:{val}")
        if not parts:
            return inner
        style = ";".join(parts)
        return f'<span style="{style}">{inner}</span>'

    # 多轮替换以支持嵌套
    for _ in range(3):
        prev = text
        text = _COLOR_RE.sub(_color_repl, text)
        text = _FONT_RE.sub(_font_repl, text)
        text = _SIZE_RE.sub(_size_repl, text)
        text = _STYLE_RE.sub(_style_repl, text)
        if text == prev:
            break
    return text


# ======================================================================
# JSON 美化渲染
# ======================================================================


def _render_json_value(val, indent=0):
    """递归渲染 JSON 值为带颜色 + 可折叠的 HTML。"""
    sp = "  " * indent
    if isinstance(val, dict):
        if not val:
            return '<span class="jv-brace">{}</span>'
        items = []
        keys = list(val.keys())
        for i, k in enumerate(keys):
            comma = '<span class="jv-comma">,</span>' if i < len(keys) - 1 else ""
            v_html = _render_json_value(val[k], indent + 1)
            items.append(
                f'{sp}  <span class="jv-key">&quot;{_html.escape(str(k))}&quot;</span>'
                f'<span class="jv-colon">: </span>{v_html}{comma}'
            )
        inner = "\n".join(items)
        return (
            f'<span class="jv-toggle" onclick="jvToggle(this)">▼</span>'
            f'<span class="jv-brace">{{</span>'
            f'<span class="jv-collapsible">\n{inner}\n{sp}</span>'
            f'<span class="jv-brace">}}</span>'
        )
    elif isinstance(val, list):
        if not val:
            return '<span class="jv-bracket">[]</span>'
        items = []
        for i, v in enumerate(val):
            comma = '<span class="jv-comma">,</span>' if i < len(val) - 1 else ""
            v_html = _render_json_value(v, indent + 1)
            items.append(f"{sp}  {v_html}{comma}")
        inner = "\n".join(items)
        return (
            f'<span class="jv-toggle" onclick="jvToggle(this)">▼</span>'
            f'<span class="jv-bracket">[</span>'
            f'<span class="jv-collapsible">\n{inner}\n{sp}</span>'
            f'<span class="jv-bracket">]</span>'
        )
    elif isinstance(val, str):
        return f'<span class="jv-string">&quot;{_html.escape(val)}&quot;</span>'
    elif isinstance(val, bool):
        return f'<span class="jv-bool">{"true" if val else "false"}</span>'
    elif val is None:
        return '<span class="jv-null">null</span>'
    elif isinstance(val, (int, float)):
        return f'<span class="jv-number">{val}</span>'
    else:
        return f'<span class="jv-string">{_html.escape(str(val))}</span>'


def _build_json_viewer(code: str) -> str:
    """将 JSON 代码转为美化的交互式 viewer HTML。"""
    try:
        data = _json.loads(code)
    except _json.JSONDecodeError:
        # 无法解析时回退到普通代码块
        return ""
    body = _render_json_value(data)
    # 行号
    lines = body.split("\n")
    numbered = "\n".join(
        f'<span class="jv-line"><span class="jv-ln">{i + 1}</span>{line}</span>'
        for i, line in enumerate(lines)
    )
    return (
        '<div class="json-viewer">'
        '<div class="jv-header">'
        '<span class="jv-icon">{ }</span>'
        '<span class="jv-title">JSON</span>'
        '<button class="jv-copy-btn" onclick="copyCodeBlock(this)">📋 复制</button>'
        "</div>"
        f'<pre class="jv-body"><code>{numbered}</code></pre>'
        "</div>"
    )


# ======================================================================
# XML 美化渲染
# ======================================================================

_XML_TAG_RE = re.compile(r"(<[!?/]?)([\w:.-]+)")
_XML_ATTR_RE = re.compile(r'([\w:.-]+)(\s*=\s*)(["\'])(.*?)\3')
_XML_COMMENT_RE = re.compile(r"(<!--.*?-->)", re.DOTALL)


def _colorize_xml_line(line: str) -> str:
    """对单行 XML 进行语法着色。"""
    # 注释
    line = _XML_COMMENT_RE.sub(
        lambda m: f'<span class="xv-comment">{_html.escape(m.group(1))}</span>',
        line,
    )
    # 属性
    line = _XML_ATTR_RE.sub(
        lambda m: (
            f'<span class="xv-attr">{_html.escape(m.group(1))}</span>'
            f"{m.group(2)}"
            f'<span class="xv-attrval">{m.group(3)}{_html.escape(m.group(4))}{m.group(3)}</span>'
        ),
        line,
    )
    # 标签名
    line = _XML_TAG_RE.sub(
        lambda m: f'{m.group(1)}<span class="xv-tag">{_html.escape(m.group(2))}</span>',
        line,
    )
    return line


def _prettify_xml(code: str) -> str:
    """将紧凑 XML 格式化为缩进形式（简单实现）。"""
    import xml.dom.minidom as minidom

    try:
        dom = minidom.parseString(code)
        pretty = dom.toprettyxml(indent="  ")
        # 去掉 xml declaration
        lines = pretty.split("\n")
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        return "\n".join(l for l in lines if l.strip())
    except Exception:
        return code


def _build_xml_viewer(code: str) -> str:
    """将 XML 代码转为美化 viewer HTML。"""
    pretty = _prettify_xml(code)
    escaped = _html.escape(pretty)
    lines = escaped.split("\n")
    colored = []
    for i, line in enumerate(lines):
        cl = _colorize_xml_line(line)
        colored.append(f'<span class="xv-line"><span class="xv-ln">{i + 1}</span>{cl}</span>')
    body = "\n".join(colored)
    return (
        '<div class="xml-viewer">'
        '<div class="xv-header">'
        '<span class="xv-icon">&lt;/&gt;</span>'
        '<span class="xv-title">XML</span>'
        '<button class="xv-copy-btn" onclick="copyCodeBlock(this)">📋 复制</button>'
        "</div>"
        f'<pre class="xv-body"><code>{body}</code></pre>'
        "</div>"
    )


# ======================================================================
# 终端 UI 渲染
# ======================================================================


def _colorize_term_line(line: str) -> str:
    """对一行终端命令进行语法着色（先 escape，再用 re.sub 上色）。"""
    s = _html.escape(line)

    # 1) 字符串 "..." / '...'
    s = re.sub(
        r"(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)",
        r'<span class="term-str">\1</span>',
        s,
    )
    # 2) 管道 / 重定向 / 连接符  >>  >  <  &&  ||  |  ;
    #    长匹配优先，避免把 HTML 实体拆开
    s = re.sub(
        r"(&gt;&gt;|&gt;|&lt;|&amp;&amp;|\|\||[|;])",
        r'<span class="term-op">\1</span>',
        s,
    )
    # 3) 变量  $VAR  ${VAR}  %VAR%
    s = re.sub(
        r"(\$[\w{][\w}]*|%[\w]+%)",
        r'<span class="term-var">\1</span>',
        s,
    )
    # 4) 参数/选项  -x  --flag  /s  (whitespace 后紧跟 -/ 开头)
    s = re.sub(
        r"(?<=\s)([-/][-\w/=:]+)",
        r'<span class="term-flag">\1</span>',
        s,
    )
    # 5) 数字
    s = re.sub(
        r"(?<=\s)(\d[\d.]*)",
        r'<span class="term-num">\1</span>',
        s,
    )
    # 6) 命令名 — 每个管道段的第一个词
    #    先处理行首命令
    s = re.sub(
        r"^(\s*)([\w][-\w.+]*)",
        r'\1<span class="term-cmd-name">\2</span>',
        s,
        count=1,
    )
    #    再处理管道后的命令名  (| 后第一个词)
    s = re.sub(
        r'(<span class="term-op">[|]</span>\s*)([\w][-\w.+]*)',
        r'\1<span class="term-cmd-name">\2</span>',
        s,
    )
    return s


# Pygments lexer 名称映射
_TERM_LEXER_MAP = {
    "bash": "bash",
    "shell": "bash",
    "sh": "bash",
    "zsh": "bash",
    "console": "bash",
    "terminal": "bash",
    "cmd": "batch",
    "bat": "batch",
    "powershell": "powershell",
    "ps1": "powershell",
}


def _build_terminal_ui(code: str, lang: str = "bash") -> str:
    """将 shell 命令代码转为终端 UI HTML（使用 Pygments 语法高亮）。"""
    is_script = lang in _TERMINAL_SCRIPT_LANGS
    lexer_name = _TERM_LEXER_MAP.get(lang, "bash")
    try:
        lexer = get_lexer_by_name(lexer_name)
        formatter = HtmlFormatter(nowrap=True, noclasses=True, style="monokai")
        _use_pygments = True
    except Exception:
        _use_pygments = False

    lines = code.rstrip("\n").split("\n")
    body_lines = []

    if is_script:
        # 脚本模式：用 Pygments 高亮整块代码，显示行号
        if _use_pygments:
            highlighted = _pygments_highlight(code.rstrip("\n"), lexer, formatter).rstrip("\n")
            split_lines = _split_html_lines(highlighted)
        else:
            split_lines = [_html.escape(l) for l in lines]
        for i, line_html in enumerate(split_lines):
            content = line_html if line_html.strip() else "&nbsp;"
            body_lines.append(
                f'<span class="term-line">'
                f'<span class="term-ln">{i + 1}</span>'
                f"{content}"
                f"</span>"
            )
    else:
        # 命令模式：每行前缀 $ 提示符
        for line in lines:
            stripped = line.strip()
            if not stripped:
                body_lines.append(
                    '<span class="term-line"><span class="term-empty">&nbsp;</span></span>'
                )
            elif (
                stripped.startswith("#")
                or stripped.startswith("REM ")
                or stripped.startswith("rem ")
            ):
                body_lines.append(
                    f'<span class="term-line"><span class="term-comment">{_html.escape(line)}</span></span>'
                )
            else:
                if _use_pygments:
                    colored = _pygments_highlight(line, lexer, formatter).rstrip("\n")
                else:
                    colored = _colorize_term_line(line)
                body_lines.append(
                    f'<span class="term-line">'
                    f'<span class="term-prompt">$</span>'
                    f"{colored}"
                    f"</span>"
                )

    body = "\n".join(body_lines)
    _SHELL_LABELS = {
        "cmd": "CMD",
        "bat": "CMD",
        "powershell": "PowerShell",
        "ps1": "PowerShell",
    }
    shell_label = _SHELL_LABELS.get(lang, "Terminal")
    return (
        '<div class="terminal-ui">'
        '<div class="term-header">'
        '<span class="term-dots">'
        '<span class="term-dot term-dot-red"></span>'
        '<span class="term-dot term-dot-yellow"></span>'
        '<span class="term-dot term-dot-green"></span>'
        "</span>"
        f'<span class="term-title">{shell_label}</span>'
        '<button class="term-copy-btn" onclick="copyCodeBlock(this)">📋 复制</button>'
        "</div>"
        f'<pre class="term-body"><code>{body}</code></pre>'
        "</div>"
    )


# ======================================================================
# 编辑器风格代码展示（脚本语言）
# ======================================================================

_SCRIPT_LEXER_ALIAS = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "rb": "ruby",
    "pl": "perl",
    "golang": "go",
    "rs": "rust",
    "cs": "csharp",
    "kt": "kotlin",
    "hs": "haskell",
    "ex": "elixir",
    "clj": "clojure",
    "yml": "yaml",
}

_LANG_DISPLAY = {
    "python": "Python",
    "py": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "ruby": "Ruby",
    "rb": "Ruby",
    "perl": "Perl",
    "pl": "Perl",
    "php": "PHP",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "rs": "Rust",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "csharp": "C#",
    "cs": "C#",
    "kotlin": "Kotlin",
    "kt": "Kotlin",
    "swift": "Swift",
    "scala": "Scala",
    "lua": "Lua",
    "r": "R",
    "sql": "SQL",
    "css": "CSS",
    "scss": "SCSS",
    "less": "Less",
    "yaml": "YAML",
    "yml": "YAML",
    "toml": "TOML",
    "ini": "INI",
    "jsx": "JSX",
    "tsx": "TSX",
    "vue": "Vue",
    "dart": "Dart",
    "haskell": "Haskell",
    "hs": "Haskell",
    "makefile": "Makefile",
    "dockerfile": "Dockerfile",
    "groovy": "Groovy",
    "matlab": "MATLAB",
}


def _split_html_lines(html_str: str) -> list:
    """将 Pygments 生成的 HTML 按行拆分，正确处理跨行 <span>。"""
    raw_lines = html_str.split("\n")
    result = []
    open_tags = []  # 当前未关闭的 <span ...> 标签栈

    for raw in raw_lines:
        prefix = "".join(open_tags)
        # 跟踪本行 span 开闭
        local = list(open_tags)
        for m in re.finditer(r"(<span[^>]*>)|(</span>)", raw):
            if m.group(1):
                local.append(m.group(1))
            elif m.group(2) and local:
                local.pop()
        suffix = "</span>" * len(local)
        result.append(prefix + raw + suffix)
        open_tags = local

    return result


def _build_code_editor(code: str, lang: str) -> str:
    """将脚本代码转为编辑器风格的 HTML（行号 + Pygments 语法高亮）。"""
    alias = _SCRIPT_LEXER_ALIAS.get(lang, lang)
    try:
        lexer = get_lexer_by_name(alias, stripall=True)
    except Exception:
        return ""  # 回退到默认代码块

    formatter = HtmlFormatter(nowrap=True, noclasses=True, style="monokai")
    highlighted = _pygments_highlight(code.rstrip("\n"), lexer, formatter).rstrip("\n")

    lines = _split_html_lines(highlighted)
    numbered = []
    for i, line in enumerate(lines):
        content = line if line.strip() else "&nbsp;"
        numbered.append(
            f'<span class="ce-line">' f'<span class="ce-ln">{i + 1}</span>' f"{content}" f"</span>"
        )
    body = "\n".join(numbered)

    display = _LANG_DISPLAY.get(lang, lang.upper())

    return (
        '<div class="code-editor">'
        '<div class="ce-header">'
        f'<span class="ce-icon">📄</span>'
        f'<span class="ce-title">{_html.escape(display)}</span>'
        '<button class="ce-copy-btn" onclick="copyCodeBlock(this)">📋 复制</button>'
        "</div>"
        f'<pre class="ce-body"><code>{body}</code></pre>'
        "</div>"
    )


class MarkdownRenderer:
    """Converts Markdown text to HTML.

    Uses a class-level shared instance so that callers (main window,
    exporter, etc.) reuse the same renderer instead of creating
    separate instances.
    """

    _shared_instance = None

    @classmethod
    def instance(cls) -> "MarkdownRenderer":
        """Return the shared singleton renderer."""
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    def __init__(self):
        self._extensions = [
            "tables",
            "fenced_code",
            "codehilite",
            "footnotes",
            "toc",
            "nl2br",
            "sane_lists",
        ]
        self._extension_configs = {
            "codehilite": {
                "css_class": "highlight",
                "linenums": False,
                "guess_lang": True,
            },
            "toc": {
                "permalink": False,
            },
        }
        # Reusable Markdown instance — call .reset() before each render
        self._md = markdown.Markdown(
            extensions=self._extensions,
            extension_configs=self._extension_configs,
        )

    def render(self, text: str) -> str:
        # Pre-process math before markdown parsing
        if _MATH_AVAILABLE:
            text = preprocess_math(text)

        # ── 预处理：富文本标记 [COLOR:...] [FONT:...] [SIZE:...] [STYLE ...] ──
        text = _preprocess_rich_markers(text)

        # ── 预处理：提取增强代码块，替换为占位符 ──
        placeholders = {}
        counter = [0]

        def _replace_fence(m):
            lang = m.group(2).lower()
            code = m.group(3)
            if lang not in _ENHANCED_LANGS:
                return m.group(0)  # 不处理，保留原样
            # 生成增强 HTML
            if lang in _JSON_LANGS:
                enhanced = _build_json_viewer(code)
            elif lang in _XML_LANGS:
                enhanced = _build_xml_viewer(code)
            elif lang in _TERMINAL_LANGS:
                enhanced = _build_terminal_ui(code, lang)
            elif lang in _SCRIPT_LANGS:
                enhanced = _build_code_editor(code, lang)
            else:
                return m.group(0)
            if not enhanced:
                return m.group(0)  # 解析失败，回退
            # 使用 HTML 注释作占位符，避免 Markdown 将 __xx__ 解析为粗体
            key = f"<!--EBLOCK{counter[0]}-->"
            counter[0] += 1
            placeholders[key] = enhanced
            return f"\n\n{key}\n\n"

        text = _FENCE_RE.sub(_replace_fence, text)

        self._md.reset()
        html = self._md.convert(text)

        # ── 后处理：替换占位符为增强 HTML ──
        for key, enhanced_html in placeholders.items():
            html = html.replace(key, enhanced_html)

        return html

    @staticmethod
    def get_pygments_css() -> str:
        return HtmlFormatter(style="default").get_style_defs(".highlight")
