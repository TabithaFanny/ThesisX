"""
editor_widget.py — 轻视觉写作区

特性:
  · 无行号 — 移除代码编辑器观感
  · 比例字体 (Microsoft YaHei 14pt) — 中文阅读友好
  · 增强高亮器:
      - 标题行字号变大 (H1=1.6x, H2=1.35x, H3=1.15x)
      - # 标记变淡灰，内容保持深色
      - **粗体** 实际显示 Bold，标记变灰
      - *斜体* 实际显示 Italic，标记变灰
      - 代码块整行灰底
  · 空白时显示 "开始写作..." 占位文字
  · 当前行柔和高亮
  · 自动补全括号 / 列表续写
"""

import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit

from app.constants import EDITOR_FONT_FAMILY, EDITOR_FONT_SIZE

# ======================================================================
# Enhanced Markdown Highlighter
# ======================================================================


class MarkdownHighlighter(QSyntaxHighlighter):
    """
    Visual-writing highlighter: real font sizes for headings,
    dimmed markers, bold/italic rendering, code-block shading.
    """

    def __init__(self, document: QTextDocument, base_size: int = EDITOR_FONT_SIZE):
        super().__init__(document)
        self._base_size = base_size
        self._build_rules()

    def _build_rules(self):
        bs = self._base_size

        # ── Headings ──
        # We handle headings specially in highlightBlock for per-group
        # formatting (marker vs content).  Store only formats here.
        self._h_marker = QTextCharFormat()
        self._h_marker.setForeground(QColor("#c0c0c0"))  # dimmed

        self._h_formats = {}
        for level, scale, color in [
            (1, 1.60, "#1a1a1a"),
            (2, 1.35, "#1a1a1a"),
            (3, 1.15, "#1a1a1a"),
            (4, 1.05, "#333333"),
            (5, 1.00, "#333333"),
            (6, 1.00, "#555555"),
        ]:
            fmt = QTextCharFormat()
            fmt.setFontPointSize(bs * scale)
            fmt.setFontWeight(QFont.Weight.Bold)
            fmt.setForeground(QColor(color))
            self._h_formats[level] = fmt

        # ── Inline rules: (pattern, whole_fmt, marker_fmt) ──
        # marker_fmt applies to the wrapping markers; content_fmt to content.
        self._inline_rules = []

        # Bold **...**
        bold_content = QTextCharFormat()
        bold_content.setFontWeight(QFont.Weight.Bold)
        bold_content.setForeground(QColor("#1a1a1a"))
        bold_marker = QTextCharFormat()
        bold_marker.setForeground(QColor("#c0c0c0"))
        bold_marker.setFontWeight(QFont.Weight.Normal)
        self._inline_rules.append(
            (re.compile(r"\*\*(.+?)\*\*"), bold_content, bold_marker, 2)  # marker_len
        )
        # Also __...__
        self._inline_rules.append((re.compile(r"__(.+?)__"), bold_content, bold_marker, 2))

        # Italic *...*
        italic_content = QTextCharFormat()
        italic_content.setFontItalic(True)
        italic_content.setForeground(QColor("#444444"))
        italic_marker = QTextCharFormat()
        italic_marker.setForeground(QColor("#c0c0c0"))
        self._inline_rules.append(
            (re.compile(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)"), italic_content, italic_marker, 1)
        )

        # Inline code `...`
        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor("#d63384"))
        code_fmt.setFontFamily("Consolas")
        code_fmt.setBackground(QColor("#f0f4f8"))
        code_marker = QTextCharFormat()
        code_marker.setForeground(QColor("#c0c0c0"))
        self._inline_rules.append((re.compile(r"`([^`]+)`"), code_fmt, code_marker, 1))

        # Strikethrough ~~...~~
        strike_fmt = QTextCharFormat()
        strike_fmt.setFontStrikeOut(True)
        strike_fmt.setForeground(QColor("#999999"))
        strike_marker = QTextCharFormat()
        strike_marker.setForeground(QColor("#c0c0c0"))
        self._inline_rules.append((re.compile(r"~~(.+?)~~"), strike_fmt, strike_marker, 2))

        # ── Simple line-level rules ──
        self._line_rules = []

        # Link [text](url)
        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor("#1a73e8"))
        link_fmt.setFontUnderline(True)
        self._line_rules.append((re.compile(r"\[([^\]]+)\]\([^\)]+\)"), link_fmt))

        # Blockquote
        quote_fmt = QTextCharFormat()
        quote_fmt.setForeground(QColor("#6a737d"))
        self._line_rules.append((re.compile(r"^>\s.*$"), quote_fmt))

        # List markers
        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor("#e36209"))
        list_fmt.setFontWeight(QFont.Weight.Bold)
        self._line_rules.append((re.compile(r"^\s*[-*+]\s"), list_fmt))
        self._line_rules.append((re.compile(r"^\s*\d+\.\s"), list_fmt))

        # Table pipes
        table_fmt = QTextCharFormat()
        table_fmt.setForeground(QColor("#6f42c1"))
        self._line_rules.append((re.compile(r"\|"), table_fmt))

        # Footnote [^1]
        fn_fmt = QTextCharFormat()
        fn_fmt.setForeground(QColor("#b08800"))
        self._line_rules.append((re.compile(r"\[\^[^\]]+\]"), fn_fmt))

        # Math
        math_fmt = QTextCharFormat()
        math_fmt.setForeground(QColor("#2e7d32"))
        math_fmt.setFontFamily("Consolas")
        self._line_rules.append((re.compile(r"\$\$[^$]+\$\$"), math_fmt))
        self._line_rules.append((re.compile(r"(?<!\$)\$(?!\$)[^$\n]+\$(?!\$)"), math_fmt))

        # ── Code fence / block state ──
        self._fence_fmt = QTextCharFormat()
        self._fence_fmt.setForeground(QColor("#6a737d"))
        self._fence_fmt.setFontFamily("Consolas")

        self._code_block_fmt = QTextCharFormat()
        self._code_block_fmt.setForeground(QColor("#2d3748"))
        self._code_block_fmt.setFontFamily("Consolas")
        self._code_block_fmt.setBackground(QColor("#f5f5f5"))

    # ------------------------------------------------------------------
    # Main highlight entry
    # ------------------------------------------------------------------

    def highlightBlock(self, text: str):
        # --- Code-block state machine ---
        prev_state = self.previousBlockState()
        in_code = prev_state == 1

        if text.strip().startswith("```"):
            self.setFormat(0, len(text), self._fence_fmt)
            if in_code:
                # Closing fence
                self.setCurrentBlockState(0)
            else:
                # Opening fence
                self.setCurrentBlockState(1)
            return

        if in_code:
            self.setFormat(0, len(text), self._code_block_fmt)
            self.setCurrentBlockState(1)
            return

        self.setCurrentBlockState(0)

        # --- Heading ---
        m = re.match(r"^(#{1,6})\s+(.+)$", text)
        if m:
            level = len(m.group(1))
            h_fmt = self._h_formats.get(level, self._h_formats[6])
            marker_end = m.start(2)
            # Dim the # markers
            marker_fmt = QTextCharFormat(self._h_marker)
            marker_fmt.setFontPointSize(h_fmt.fontPointSize())
            self.setFormat(0, marker_end, marker_fmt)
            # Bold heading content
            self.setFormat(marker_end, len(text) - marker_end, h_fmt)
            return

        # --- Line-level rules (applied first, can be overridden by inline) ---
        for pattern, fmt in self._line_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

        # --- Inline rules with marker dimming ---
        for pattern, content_fmt, marker_fmt, mlen in self._inline_rules:
            for match in pattern.finditer(text):
                s, e = match.start(), match.end()
                # Opening marker
                self.setFormat(s, mlen, marker_fmt)
                # Content
                self.setFormat(s + mlen, e - s - 2 * mlen, content_fmt)
                # Closing marker
                self.setFormat(e - mlen, mlen, marker_fmt)


# ======================================================================
# Editor Widget
# ======================================================================


class EditorWidget(QPlainTextEdit):
    content_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_font()
        self._setup_appearance()
        self._highlighter = MarkdownHighlighter(self.document(), EDITOR_FONT_SIZE)

        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(self.content_changed.emit)

        self._highlight_current_line()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_font(self):
        font = QFont(EDITOR_FONT_FAMILY, EDITOR_FONT_SIZE)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)

    def _setup_appearance(self):
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setPlaceholderText("开始写作...")
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: none;
                selection-background-color: #b3d9ff;
                selection-color: #000000;
                padding: 20px 28px;
            }
        """)

    # ------------------------------------------------------------------
    # Current line highlight
    # ------------------------------------------------------------------

    def _highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#f5f8ff"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    # ------------------------------------------------------------------
    # Keyboard: auto-pair, auto-list
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._handle_auto_list():
                return
        elif self._handle_auto_pair(event):
            return
        super().keyPressEvent(event)

    def _handle_auto_pair(self, event) -> bool:
        key = event.key()
        cursor = self.textCursor()
        has_sel = cursor.hasSelection()

        PAIRS = {
            Qt.Key.Key_BraceLeft: ("{", "}"),
            Qt.Key.Key_BracketLeft: ("[", "]"),
            Qt.Key.Key_ParenLeft: ("(", ")"),
        }

        CLOSING = {"}": "{", "]": "[", ")": "("}
        text_key = event.text()
        if text_key in CLOSING and not has_sel:
            cur = self.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            next_char = cur.selectedText()
            if next_char == text_key:
                cur2 = self.textCursor()
                cur2.movePosition(QTextCursor.MoveOperation.Right)
                self.setTextCursor(cur2)
                return True

        if key in PAIRS:
            open_ch, close_ch = PAIRS[key]
            if has_sel:
                sel = cursor.selectedText()
                cursor.insertText(f"{open_ch}{sel}{close_ch}")
            else:
                pos = cursor.position()
                cursor.insertText(f"{open_ch}{close_ch}")
                cursor.setPosition(pos + 1)
                self.setTextCursor(cursor)
            return True

        if text_key in ("*", "`") and not has_sel:
            pos = cursor.position()
            cursor.insertText(text_key + text_key)
            cursor.setPosition(pos + 1)
            self.setTextCursor(cursor)
            return True

        if text_key in ("*", "`") and has_sel:
            sel = cursor.selectedText()
            cursor.insertText(f"{text_key}{sel}{text_key}")
            return True

        return False

    def _handle_auto_list(self) -> bool:
        cursor = self.textCursor()
        line_text = cursor.block().text()

        match = re.match(r"^(\s*)([-*+])\s(.*)$", line_text)
        if match:
            indent, marker, content = match.groups()
            if not content.strip():
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                return True
            cursor.insertText(f"\n{indent}{marker} ")
            return True

        match = re.match(r"^(\s*)(\d+)\.\s(.*)$", line_text)
        if match:
            indent, num, content = match.groups()
            if not content.strip():
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                return True
            cursor.insertText(f"\n{indent}{int(num)+1}. ")
            return True

        match = re.match(r"^(\s*>+\s?)(.*)$", line_text)
        if match:
            prefix, content = match.groups()
            if not content.strip():
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                return True
            cursor.insertText(f"\n{prefix}")
            return True

        return False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_cursor_position(self):
        cursor = self.textCursor()
        return cursor.blockNumber() + 1, cursor.columnNumber() + 1
