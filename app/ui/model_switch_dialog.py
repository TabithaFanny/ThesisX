"""
model_switch_dialog.py — AI 模型切换对话框

提供可视化的模型选择界面，支持三种大模型：
  · Claude 4.6 Opus (Anthropic)
  · GPT 5.3 Codex (OpenAI)
  · Gemini 3 Pro (Google)
"""

from PyQt6.QtCore import QByteArray, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons import icon_model_claude, icon_model_gemini, icon_model_gpt

# Model definitions: (key, display_name, subtitle, model_id, brand_color, icon_func)
MODELS = [
    (
        "claude",
        "Claude 4.6 Opus",
        "Anthropic · 深度推理 & 长文写作",
        "claude-opus-4-6-thinking",
        "#D4A574",
        icon_model_claude,
    ),
    (
        "gpt",
        "GPT 5.3 Codex",
        "OpenAI · 全能写作 & 代码生成",
        "gpt-5.3-codex",
        "#10A37F",
        icon_model_gpt,
    ),
    (
        "gemini",
        "Gemini 3 Pro",
        "Google · 多模态 & 知识检索",
        "gemini-3-pro-preview",
        "#1A73E8",
        icon_model_gemini,
    ),
]


class _ModelCard(QWidget):
    """A single clickable model card."""

    clicked = pyqtSignal(str)  # emits model key

    def __init__(self, key, name, subtitle, brand_color, icon: QIcon, parent=None):
        super().__init__(parent)
        self._key = key
        self._brand_color = brand_color
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(380, 80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(QSize(48, 48)))
        icon_label.setFixedSize(48, 48)
        layout.addWidget(icon_label)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        name_label = QLabel(name)
        name_label.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: #222; background: transparent;")
        text_col.addWidget(name_label)

        sub_label = QLabel(subtitle)
        sub_label.setFont(QFont("Microsoft YaHei", 10))
        sub_label.setStyleSheet("color: #888; background: transparent;")
        text_col.addWidget(sub_label)

        layout.addLayout(text_col)
        layout.addStretch()

        # Check indicator (hidden by default)
        self._check = QLabel("✓")
        self._check.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self._check.setStyleSheet(f"color: {brand_color}; background: transparent;")
        self._check.setVisible(False)
        layout.addWidget(self._check)

        self._apply_style()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._check.setVisible(selected)
        self._apply_style()

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                _ModelCard {{
                    background-color: {self._brand_color}11;
                    border: 2px solid {self._brand_color};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet("""
                _ModelCard {
                    background-color: #FFFFFF;
                    border: 1.5px solid #E8E8E8;
                    border-radius: 12px;
                }
                _ModelCard:hover {
                    border-color: #C0C0C0;
                    background-color: #FAFAFA;
                }
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self._key)
        super().mousePressEvent(event)


class ModelSwitchDialog(QDialog):
    """AI model selection dialog."""

    model_selected = pyqtSignal(str, str)  # (model_key, model_id)

    def __init__(self, current_model_key: str = "gpt", parent=None):
        super().__init__(parent)
        self.setWindowTitle("切换 AI 模型")
        self.setFixedSize(440, 420)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._current_key = current_model_key
        self._cards: dict[str, _ModelCard] = {}
        self._init_ui()
        self._update_selection()

    def _init_ui(self):
        # Outer layout for shadow margin
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        # Main card container
        container = QWidget()
        container.setObjectName("modelDialogContainer")
        container.setStyleSheet("""
            #modelDialogContainer {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E0E0E0;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 20)
        main_layout.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("🔄 切换 AI 模型")
        title.setFont(QFont("Microsoft YaHei", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a1a1a;")
        title_row.addWidget(title)
        title_row.addStretch()

        # Close button with SVG × icon
        _close_svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
            b'<line x1="4" y1="4" x2="12" y2="12" stroke="#999" stroke-width="1.6"'
            b' stroke-linecap="round"/>'
            b'<line x1="12" y1="4" x2="4" y2="12" stroke="#999" stroke-width="1.6"'
            b' stroke-linecap="round"/>'
            b"</svg>"
        )
        _close_pix = QPixmap(28, 28)
        _close_pix.fill(Qt.GlobalColor.transparent)
        _renderer = QSvgRenderer(QByteArray(_close_svg))
        _p = QPainter(_close_pix)
        _p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _renderer.render(_p)
        _p.end()

        close_btn = QPushButton()
        close_btn.setIcon(QIcon(_close_pix))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #FFEBEE;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(close_btn)
        main_layout.addLayout(title_row)

        # Subtitle
        subtitle = QLabel("选择一个模型用于 AI 写作助手")
        subtitle.setFont(QFont("Microsoft YaHei", 10))
        subtitle.setStyleSheet("color: #999; margin-bottom: 8px;")
        main_layout.addWidget(subtitle)

        # Model cards
        for key, name, sub, model_id, color, icon_func in MODELS:
            card = _ModelCard(key, name, sub, color, icon_func(48))
            card.clicked.connect(self._on_card_clicked)
            self._cards[key] = card
            main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        main_layout.addSpacing(8)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #F5F5F5;
                border: 1px solid #DDD;
                border-radius: 8px;
                font-size: 13px;
                color: #555;
            }
            QPushButton:hover {
                background: #EAEAEA;
                border-color: #CCC;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("确认切换")
        confirm_btn.setFixedSize(100, 34)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #2563EB);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #1D4ED8);
            }
            QPushButton:pressed {
                background: #1D4ED8;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        main_layout.addLayout(btn_layout)
        outer.addWidget(container)

    def _on_card_clicked(self, key: str):
        self._current_key = key
        self._update_selection()

    def _update_selection(self):
        for k, card in self._cards.items():
            card.set_selected(k == self._current_key)

    def _on_confirm(self):
        for key, name, sub, model_id, color, icon_func in MODELS:
            if key == self._current_key:
                self.model_selected.emit(key, model_id)
                break
        self.accept()

    def get_selected_model(self) -> tuple[str, str]:
        """Return (model_key, model_id) of current selection."""
        for key, name, sub, model_id, color, icon_func in MODELS:
            if key == self._current_key:
                return key, model_id
        return "gpt", "gpt-5.3-codex"

    # Allow dragging the frameless dialog
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_pos") and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
