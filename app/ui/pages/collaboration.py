"""Collaboration page — discussion feed + task board mock."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea, QFrame,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import (
    PageHeader, TaskCard, ComingSoonBadge, StatusBadge, _card_style,
)
from app.ui.mock.pages_data import MOCK_COLLABORATION_MSGS, MOCK_TASKS


class CollaborationPage(QWidget):
    """Collaboration space mock — discussions + task board."""

    def __init__(self, parent=None):
        super().__init__(parent)
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def apply_theme(self) -> None:
        """Re-apply theme by rebuilding UI."""
        old = self.layout()
        if old is not None:
            QWidget().setLayout(old)
        self._init_ui()

    def _init_ui(self):
        L = get_theme()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        header_row = QHBoxLayout()
        header_row.addWidget(PageHeader("协作空间", "与导师和同学实时协作，管理讨论和任务。"))
        header_row.addWidget(ComingSoonBadge("V3 计划"))
        header_row.addStretch()
        layout.addLayout(header_row)

        # Two-column layout
        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)

        # Left: Discussion feed
        disc_panel = QFrame()
        disc_panel.setStyleSheet(_card_style())
        disc_layout = QVBoxLayout(disc_panel)
        disc_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        disc_layout.setSpacing(Spacing.MD)

        disc_title = QLabel("讨论")
        disc_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        disc_layout.addWidget(disc_title)

        for msg in MOCK_COLLABORATION_MSGS:
            msg_frame = QFrame()
            msg_frame.setStyleSheet(
                f"QFrame {{ background-color: {L.SURFACE_ALT}; border-radius: {Radius.BUTTON}px; "
                f"padding: {Spacing.SM}px; }}"
            )
            ml = QVBoxLayout(msg_frame)
            ml.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
            ml.setSpacing(Spacing.XS)

            sender = QLabel(msg["sender"])
            sender.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; font-weight: bold;"
            )
            ml.addWidget(sender)

            content_lbl = QLabel(msg["content"])
            content_lbl.setWordWrap(True)
            content_lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
            ml.addWidget(content_lbl)

            time_lbl = QLabel(msg["time"])
            time_lbl.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            ml.addWidget(time_lbl)

            disc_layout.addWidget(msg_frame)

        disc_layout.addStretch()
        cols.addWidget(disc_panel, 1)

        # Right: Task board
        task_panel = QFrame()
        task_panel.setStyleSheet(_card_style())
        task_layout = QVBoxLayout(task_panel)
        task_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        task_layout.setSpacing(Spacing.SM)

        task_title = QLabel("任务板")
        task_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        task_layout.addWidget(task_title)

        for task in MOCK_TASKS:
            card = TaskCard(
                title=task["title"],
                assignee=task["assignee"],
                priority=task["priority"],
            )
            task_layout.addWidget(card)

        task_layout.addStretch()
        cols.addWidget(task_panel)

        layout.addLayout(cols, 1)
        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
