"""Submission & Rebuttal page — SVG-aligned submission table and reply plan mock."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.base import ComingSoonBadge, PageHeader, PreviewBadge, StatusBadge, _card_style
from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.mock.pages_data import MOCK_REBUTTAL_DETAIL, MOCK_SUBMISSIONS, MOCK_SUBMISSION_STATS


class SubmissionPage(QWidget):
    """Submission tracking mock page with submission table and rebuttal plan sidebar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._init_ui()

    def _init_ui(self):
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
        header_row.addWidget(PageHeader("投稿与回复", "展示 mock 投稿记录、审稿状态和 Rebuttal 计划；当前未接入真实投稿系统。"))
        header_row.addWidget(ComingSoonBadge("V3 计划"))
        header_row.addStretch()
        layout.addLayout(header_row)

        layout.addLayout(self._create_stats_row())

        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)
        main_row.addWidget(self._create_submission_table(), 2)
        main_row.addWidget(self._create_rebuttal_panel())
        layout.addLayout(main_row, 1)

        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _create_stats_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(Spacing.MD)

        for stat in MOCK_SUBMISSION_STATS:
            card = QFrame()
            card.setStyleSheet(_card_style())
            card.setMinimumWidth(100)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
            layout.setSpacing(Spacing.XS)

            count = QLabel(str(stat["count"]))
            count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count.setStyleSheet(
                f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
            )
            layout.addWidget(count)

            label = QLabel(stat["label"])
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
            )
            layout.addWidget(label)

            row.addWidget(card)

        row.addStretch()
        return row

    def _create_submission_table(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        top_row = QHBoxLayout()
        title = QLabel("投稿记录")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(PreviewBadge("仅预览"))

        for text in ["新增投稿", "导出计划", "同步状态"]:
            btn = QPushButton(text)
            btn.setEnabled(False)
            btn.setFixedHeight(28)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
                f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
                f"padding: 0 {Spacing.MD}px; font-size: {FontSize.SECONDARY}px; }} "
                f"QPushButton:disabled {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
                f"border: 1px dashed {L.BORDER}; }}"
            )
            top_row.addWidget(btn)
        layout.addLayout(top_row)

        hint = QLabel("当前表格仅用于 UI 预览，不接真实期刊/会议 API、邮件发送或状态同步。")
        hint.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(hint)

        layout.addWidget(self._table_row("会议/期刊", "论文标题", "状态", "投稿时间", "轮次", "操作", header=True))

        for record in MOCK_SUBMISSIONS:
            layout.addWidget(
                self._table_row(
                    record["journal"],
                    record["paper"],
                    record["status"],
                    record["submitted"],
                    record["round"],
                    record["action"],
                    status_type=record["status_type"],
                )
            )

        return panel

    def _table_row(
        self,
        venue: str,
        paper: str,
        status: str,
        submitted: str,
        round_text: str,
        action_text: str,
        *,
        header: bool = False,
        status_type: str = "muted",
    ) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background-color: {'transparent' if header else L.SURFACE}; "
            f"border-bottom: 1px solid {L.BORDER_SUBTLE}; }}"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        primary_color = L.TEXT_MUTED if header else L.TEXT_PRIMARY
        secondary_color = L.TEXT_MUTED if header else L.TEXT_SECONDARY
        weight = "600" if header else "400"

        venue_lbl = QLabel(venue)
        venue_lbl.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {primary_color}; font-weight: {weight};"
        )
        layout.addWidget(venue_lbl, 2)

        paper_lbl = QLabel(paper)
        paper_lbl.setWordWrap(True)
        paper_lbl.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {primary_color}; font-weight: {weight};"
        )
        layout.addWidget(paper_lbl, 3)

        if header:
            status_lbl = QLabel(status)
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_lbl.setStyleSheet(
                f"font-size: {FontSize.SMALL}px; color: {L.TEXT_MUTED}; font-weight: 600;"
            )
            layout.addWidget(status_lbl, 1)
        else:
            layout.addWidget(StatusBadge(status, status_type), 1)

        submitted_lbl = QLabel(submitted)
        submitted_lbl.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {secondary_color}; font-weight: {weight};"
        )
        layout.addWidget(submitted_lbl, 1)

        round_lbl = QLabel(round_text)
        round_lbl.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {secondary_color}; font-weight: {weight};"
        )
        layout.addWidget(round_lbl, 1)

        if header:
            action_lbl = QLabel(action_text)
            action_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_lbl.setStyleSheet(
                f"font-size: {FontSize.SMALL}px; color: {L.TEXT_MUTED}; font-weight: 600;"
            )
            layout.addWidget(action_lbl, 1)
        else:
            action_btn = QPushButton(action_text)
            action_btn.setEnabled(False)
            action_btn.setFixedHeight(24)
            action_btn.setStyleSheet(
                f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
                f"border: 1px dashed {L.BORDER}; border-radius: {Radius.BUTTON}px; "
                f"font-size: {FontSize.MICRO}px; padding: 0 {Spacing.SM}px; }}"
            )
            layout.addWidget(action_btn, 1)

        return row

    def _create_rebuttal_panel(self) -> QFrame:
        detail = MOCK_REBUTTAL_DETAIL

        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("审稿意见 / Rebuttal 计划")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(title)

        name = QLabel(detail["title"])
        name.setWordWrap(True)
        name.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(name)

        decision_row = QHBoxLayout()
        decision_label = QLabel("审稿结论")
        decision_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; font-weight: 600;"
        )
        decision_row.addWidget(decision_label)
        decision_row.addStretch()
        decision_row.addWidget(StatusBadge(detail["decision"], detail["decision_type"]))
        layout.addLayout(decision_row)

        layout.addWidget(self._detail_block("主要问题", detail["main_issues"]))
        layout.addWidget(self._detail_block("回复计划", detail["response_plan"]))
        layout.addWidget(self._detail_block("待补材料", detail["materials"]))
        layout.addWidget(self._detail_block("风险提示", detail["risk_notes"], warning=True))

        layout.addStretch()
        return panel

    def _detail_block(self, title: str, lines: list[str], warning: bool = False) -> QFrame:
        panel = QFrame()
        if warning:
            panel.setStyleSheet(
                f"QFrame {{ background-color: {L.WARNING_BG}; border: 1px solid {L.WARNING}; "
                f"border-radius: {Radius.INPUT}px; }}"
            )
        else:
            panel.setStyleSheet(
                f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                f"border-radius: {Radius.INPUT}px; }}"
            )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        header = QLabel(title)
        header.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY if not warning else L.WARNING}; font-weight: 700;"
        )
        layout.addWidget(header)

        for line in lines:
            item = QLabel(f"• {line}")
            item.setWordWrap(True)
            item.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
            )
            layout.addWidget(item)

        return panel
