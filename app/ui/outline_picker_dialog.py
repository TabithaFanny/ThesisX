"""OutlinePickerDialog — select AI-generated sections to insert into Editor."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing

logger = logging.getLogger(__name__)


class OutlinePickerDialog(QDialog):
    """Dialog to pick which AI-generated sections to insert into the Editor."""

    def __init__(self, previews: list, parent: QWidget | None = None):
        super().__init__(parent)
        self._previews = previews
        self._checks: list[QCheckBox] = []
        self._selected: set[str] = set()
        self._build_ui()
        self._select_all()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _build_ui(self) -> None:
        L = get_theme()

        self.setWindowTitle("选择要插入的章节")
        self.resize(560, 420)
        self.setStyleSheet(
            f"QDialog {{ background-color: {L.SURFACE}; }} "
            f"QLabel {{ color: {L.TEXT_PRIMARY}; font-family: "
            f"{{font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;}}"
            f"}} "
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Header
        self._header = QLabel("AI 生成的论文包含以下章节，请勾选要插入的内容：")
        self._header.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        self._header.setWordWrap(True)
        layout.addWidget(self._header)

        # Select all / deselect all bar
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(Spacing.SM)
        self._select_all_btn = QPushButton("全选")
        self._select_all_btn.clicked.connect(self._select_all)
        self._select_all_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; "
            f"background-color: {L.PRIMARY_LIGHT}; border: 1px solid {L.PRIMARY_BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_BORDER}; }}"
        )
        btn_bar.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton("取消全选")
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        self._deselect_all_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.BORDER}; }}"
        )
        btn_bar.addWidget(self._deselect_all_btn)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        # Scrollable section list
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; background-color: {L.SURFACE_ALT}; }}"
        )
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setSpacing(Spacing.SM)
        list_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        action_labels = {"append": "新增", "replace": "替换", "skip": "跳过"}
        action_colors = {
            "append": L.SUCCESS,
            "replace": L.PRIMARY,
            "skip": L.TEXT_MUTED,
        }

        for p in self._previews:
            row = QHBoxLayout()
            row.setSpacing(Spacing.SM)

            cb = QCheckBox()
            cb.setChecked(True)
            row.addWidget(cb)
            self._checks.append(cb)

            title_label = QLabel(p.section_title)
            title_label.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
            )
            row.addWidget(title_label)

            level_badge = QLabel(f"H{p.level}")
            level_badge.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED}; "
                f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                f"border-radius: {Radius.PILL}px; padding: 1px {Spacing.XS}px;"
            )
            row.addWidget(level_badge)

            action = p.action
            action_badge = QLabel(action_labels.get(action, action))
            action_badge.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {action_colors.get(action, L.TEXT_MUTED)}; "
                f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                f"border-radius: {Radius.PILL}px; padding: 1px {Spacing.XS}px;"
            )
            row.addWidget(action_badge)

            row.addStretch()

            # Preview snippet
            snippet = p.content[:60].replace("\n", " ")
            if len(p.content) > 60:
                snippet += "..."
            snippet_label = QLabel(snippet)
            snippet_label.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
            )
            row.addWidget(snippet_label)

            list_layout.addLayout(row)

        list_layout.addStretch()
        self._scroll.setWidget(list_widget)
        layout.addWidget(self._scroll, 1)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("插入选中章节")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        layout.addWidget(button_box)

    def apply_theme(self) -> None:
        """Re-apply stylesheets using the current theme tokens (light or dark)."""
        L = get_theme()

        self.setStyleSheet(
            f"QDialog {{ background-color: {L.SURFACE}; }} "
            f"QLabel {{ color: {L.TEXT_PRIMARY}; font-family: "
            f"{{font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;}}"
            f"}} "
        )

        self._header.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )

        self._select_all_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; "
            f"background-color: {L.PRIMARY_LIGHT}; border: 1px solid {L.PRIMARY_BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_BORDER}; }}"
        )

        self._deselect_all_btn.setStyleSheet(
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.BORDER}; }}"
        )

        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; background-color: {L.SURFACE_ALT}; }}"
        )

    def _select_all(self) -> None:
        for cb in self._checks:
            cb.setChecked(True)

    def _deselect_all(self) -> None:
        for cb in self._checks:
            cb.setChecked(False)

    def _on_accept(self) -> None:
        self._selected.clear()
        for i, cb in enumerate(self._checks):
            if cb.isChecked() and i < len(self._previews):
                self._selected.add(self._previews[i].section_title)
        self.accept()

    @property
    def selected_titles(self) -> set[str]:
        return self._selected
