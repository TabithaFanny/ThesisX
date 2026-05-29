"""DiffPreviewDialog — show rewrite diff and ask user to confirm or reject."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


class DiffPreviewDialog(QDialog):
    """Show a diff between original and rewritten text, with Confirm/Reject."""

    def __init__(self, original: str, rewritten: str, mode_label: str,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._original = original
        self._rewritten = rewritten
        self._mode_label = mode_label
        self._accepted = False
        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _build_ui(self) -> None:
        L = get_theme()

        self.setWindowTitle(f"局部改写预览 — {self._mode_label}")
        self.resize(700, 500)
        self.setStyleSheet(
            f"QDialog {{ background-color: {L.SURFACE}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Header
        self._header = QLabel(
            f"<b>改写模式：{self._mode_label}</b>"
            f"<br><span style='color:{L.TEXT_SECONDARY}; font-size:{FontSize.SECONDARY}px;'>"
            f"红色为删除，绿色为新增</span>"
        )
        self._header.setStyleSheet(f"color: {L.TEXT_PRIMARY}; font-size: {FontSize.BODY}px;")
        self._header.setWordWrap(True)
        layout.addWidget(self._header)

        # Diff display
        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setStyleSheet(
            f"QTextEdit {{ "
            f"background-color: {L.SURFACE_ALT}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; "
            f"padding: {Spacing.MD}px; "
            f"font-size: {FontSize.BODY}px; "
            f"color: {L.TEXT_PRIMARY}; "
            f"line-height: 1.6; "
            f"}}"
        )
        self._build_diff()
        layout.addWidget(self._diff_view)

        # Buttons
        button_box = QDialogButtonBox()
        self._confirm_btn = QPushButton("确认替换")
        self._confirm_btn.clicked.connect(self._on_accept)
        self._confirm_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.BODY}px; color: white; "
            f"background-color: {L.PRIMARY}; border: none; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px {Spacing.LG}px; "
            f"font-weight: 600; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        button_box.addButton(self._confirm_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        self._reject_btn = QPushButton("放弃")
        self._reject_btn.clicked.connect(self.reject)
        self._reject_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px {Spacing.LG}px; }} "
            f"QPushButton:hover {{ background-color: {L.BORDER}; }}"
        )
        button_box.addButton(self._reject_btn, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(button_box)

    def apply_theme(self) -> None:
        """Re-apply stylesheets using the current theme tokens (light or dark)."""
        L = get_theme()

        self.setStyleSheet(
            f"QDialog {{ background-color: {L.SURFACE}; }}"
        )

        self._header.setStyleSheet(f"color: {L.TEXT_PRIMARY}; font-size: {FontSize.BODY}px;")
        self._header.setText(
            f"<b>改写模式：{self._mode_label}</b>"
            f"<br><span style='color:{L.TEXT_SECONDARY}; font-size:{FontSize.SECONDARY}px;'>"
            f"红色为删除，绿色为新增</span>"
        )

        self._diff_view.setStyleSheet(
            f"QTextEdit {{ "
            f"background-color: {L.SURFACE_ALT}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; "
            f"padding: {Spacing.MD}px; "
            f"font-size: {FontSize.BODY}px; "
            f"color: {L.TEXT_PRIMARY}; "
            f"line-height: 1.6; "
            f"}}"
        )

        self._confirm_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.BODY}px; color: white; "
            f"background-color: {L.PRIMARY}; border: none; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px {Spacing.LG}px; "
            f"font-weight: 600; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )

        self._reject_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px {Spacing.LG}px; }} "
            f"QPushButton:hover {{ background-color: {L.BORDER}; }}"
        )

        # Rebuild diff with current theme color for default text
        self._diff_view.clear()
        self._build_diff()

    def _build_diff(self) -> None:
        """Simple word-level diff visualization."""
        import difflib
        orig_words = self._original.split()
        new_words = self._rewritten.split()
        sm = difflib.SequenceMatcher(None, orig_words, new_words)

        red_fmt = QTextCharFormat()
        red_fmt.setForeground(QColor("#c0392b"))
        red_fmt.setBackground(QColor("#fadbd8"))
        green_fmt = QTextCharFormat()
        green_fmt.setForeground(QColor("#27ae60"))
        green_fmt.setBackground(QColor("#d5f5e3"))
        default_fmt = QTextCharFormat()
        default_fmt.setForeground(QColor(get_theme().TEXT_PRIMARY))

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                self._diff_view.setCurrentCharFormat(default_fmt)
                self._diff_view.insertPlainText(" ".join(orig_words[i1:i2]) + " ")
            elif tag == "replace":
                self._diff_view.setCurrentCharFormat(red_fmt)
                self._diff_view.insertPlainText("[-" + " ".join(orig_words[i1:i2]) + "-] ")
                self._diff_view.setCurrentCharFormat(green_fmt)
                self._diff_view.insertPlainText("[+" + " ".join(new_words[j1:j2]) + "+] ")
            elif tag == "delete":
                self._diff_view.setCurrentCharFormat(red_fmt)
                self._diff_view.insertPlainText("[-" + " ".join(orig_words[i1:i2]) + "-] ")
            elif tag == "insert":
                self._diff_view.setCurrentCharFormat(green_fmt)
                self._diff_view.insertPlainText("[+" + " ".join(new_words[j1:j2]) + "+] ")

        self._diff_view.moveCursor(QTextCursor.MoveOperation.Start)

    def _on_accept(self) -> None:
        self._accepted = True
        self.accept()

    @property
    def is_accepted(self) -> bool:
        return self._accepted
