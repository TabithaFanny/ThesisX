"""
ai_input_bar.py — 轻量级 AI 指令输入条

按 Ctrl+I 弹出，支持多行输入。
用户输入指令后按 Enter 发送，Shift+Enter 换行，Esc 关闭。
"""

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QKeyEvent, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QWidget

_MIN_BAR_HEIGHT = 42
_MAX_BAR_HEIGHT = 160
_BAR_RADIUS = 10
_BG_COLOR = QColor(30, 30, 46)  # #1e1e2e
_BORDER_COLOR = QColor(98, 114, 164)  # #6272a4
_SHADOW_COLOR = QColor(0, 0, 0, 100)
_SHADOW_PADDING = 12


class AiTextEdit(QPlainTextEdit):
    """Enter 提交，Shift+Enter 换行的多行输入框。"""

    submitted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter: 插入换行
                super().keyPressEvent(event)
            else:
                # Enter: 提交
                self.submitted.emit()
            return
        super().keyPressEvent(event)


class AiInputBar(QWidget):
    """浮动在光标上方的 AI 指令输入条，支持自动换行和多行输入。"""

    instruction_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self._bar_height = _MIN_BAR_HEIGHT
        # 留出阴影绘制空间
        self.setFixedHeight(_MIN_BAR_HEIGHT + _SHADOW_PADDING)
        self.setMinimumWidth(460)

        self._init_ui()

    # ----- painting (round rect + shadow) -----

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 阴影
        shadow_rect = QRectF(4, 4, self.width() - 8, self._bar_height + 4)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(shadow_rect, _BAR_RADIUS, _BAR_RADIUS)
        p.fillPath(shadow_path, QBrush(_SHADOW_COLOR))

        # 背景
        bg_rect = QRectF(4, 2, self.width() - 8, self._bar_height)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(bg_rect, _BAR_RADIUS, _BAR_RADIUS)
        p.fillPath(bg_path, QBrush(_BG_COLOR))

        # 边框
        p.setPen(QPen(_BORDER_COLOR, 1))
        p.drawPath(bg_path)
        p.end()

    # ----- UI -----

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 4, 18, 14)  # bottom 留给阴影
        layout.setSpacing(8)

        self._icon_label = QLabel("✦ AI")
        self._icon_label.setFont(QFont("PingFang SC", 10, QFont.Weight.Bold))
        self._icon_label.setFixedWidth(36)
        layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._input = AiTextEdit()
        self._input.setPlaceholderText("输入 AI 指令，Enter 发送，Shift+Enter 换行，Esc 关闭")
        self._input.setFont(QFont("PingFang SC", 11))
        self._input.submitted.connect(self._on_submit)
        self._input.textChanged.connect(self._adjust_height)
        layout.addWidget(self._input)

        self.setStyleSheet("""
            QLabel {
                color: #a78bfa;
                background: transparent;
            }
            QPlainTextEdit {
                border: none;
                background: transparent;
                color: #f8f8f2;
                padding: 4px 0;
                font-size: 13px;
                selection-background-color: #44475a;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #44475a;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _adjust_height(self):
        """根据内容动态调整输入条高度。"""
        fm = self._input.fontMetrics()
        line_height = fm.lineSpacing()
        doc = self._input.document()

        # 统计可视行数（含自动换行）
        total_lines = 0
        block = doc.begin()
        while block.isValid():
            lc = block.layout().lineCount()
            total_lines += lc if lc > 0 else 1
            block = block.next()
        total_lines = max(1, total_lines)

        # 文本区高度 + 布局边距 (top=4 + bottom=14 = 18)
        needed_height = total_lines * line_height + 12 + 18
        new_bar_height = max(_MIN_BAR_HEIGHT, min(needed_height, _MAX_BAR_HEIGHT))

        # 超过最大高度时显示滚动条，否则隐藏
        if needed_height > _MAX_BAR_HEIGHT:
            self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        if new_bar_height != self._bar_height:
            self._bar_height = new_bar_height
            self.setFixedHeight(new_bar_height + _SHADOW_PADDING)
            self.update()

    def _on_submit(self):
        text = self._input.toPlainText().strip()
        if text:
            self.instruction_submitted.emit(text)
            self.hide()

    def show_and_focus(self):
        self._input.clear()
        self._bar_height = _MIN_BAR_HEIGHT
        self.setFixedHeight(_MIN_BAR_HEIGHT + _SHADOW_PADDING)
        self.show()
        self.raise_()
        self._input.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        """失去焦点时自动关闭（模拟 Popup 行为）。"""
        # 延迟检查，避免 IME 候选框导致误关
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(200, self._check_focus)
        super().focusOutEvent(event)

    def _check_focus(self):
        if not self.isActiveWindow() and not self._input.hasFocus():
            self.hide()

    def position_at_cursor(self, screen_x: int, screen_y: int, parent_widget: QWidget):
        """将输入条定位到光标上方，水平居中于编辑区。"""
        bar_w = min(500, parent_widget.width() - 40)
        self.setFixedWidth(bar_w)

        # 水平：居中于编辑区
        parent_global = parent_widget.mapToGlobal(parent_widget.rect().topLeft())
        x = parent_global.x() + (parent_widget.width() - bar_w) // 2

        # 垂直：光标上方，留 6px 间距
        y = screen_y - self.height() - 6
        # 如果太靠上就放光标下方
        if y < parent_global.y():
            y = screen_y + 6

        self.move(x, y)
