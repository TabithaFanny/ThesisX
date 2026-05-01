"""Version History page — SVG-aligned diff preview with safe disabled actions."""

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
from app.ui.mock.pages_data import MOCK_VERSION_DIFFS, MOCK_VERSION_TIMELINE


class VersionHistoryPage(QWidget):
    """Version history page with timeline, diff preview, and version metadata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._active_version = MOCK_VERSION_TIMELINE[0]["version"]
        self._active_diff_key = "v11→v12"
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        root = QVBoxLayout(content)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        header_row = QHBoxLayout()
        header_row.addWidget(
            PageHeader(
                "版本历史",
                "展示 mock 版本时间线、差异摘要与版本信息；当前未接入真实 Git、回滚或恢复链路。",
            )
        )
        header_row.addWidget(ComingSoonBadge("V2 计划"))
        header_row.addStretch()
        root.addLayout(header_row)

        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)
        cols.addWidget(self._create_timeline_panel())
        cols.addWidget(self._create_diff_panel(), 1)
        cols.addWidget(self._create_info_panel())
        root.addLayout(cols, 1)

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _create_timeline_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(220)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title_row = QHBoxLayout()
        title = QLabel("版本时间线")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(PreviewBadge("仅预览"))
        layout.addLayout(title_row)

        hint = QLabel("仅展示 mock 版本轨迹，不代表真实历史快照或可恢复记录。")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
        layout.addWidget(hint)

        for version in MOCK_VERSION_TIMELINE:
            layout.addWidget(self._create_timeline_item(version))

        layout.addStretch()
        return panel

    def _create_timeline_item(self, version: dict[str, object]) -> QFrame:
        active = bool(version["active"])
        border_color = L.PRIMARY_BORDER if active else L.BORDER_SUBTLE
        background = L.PRIMARY_LIGHT if active else L.SURFACE
        indicator = L.PRIMARY if active else L.BORDER

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {background}; border: 1px solid {border_color}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        top = QHBoxLayout()
        top.setSpacing(Spacing.SM)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background-color: {indicator}; border-radius: 5px; border: 1px solid {indicator};"
        )
        top.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)

        header_col = QVBoxLayout()
        header_col.setSpacing(0)

        version_label = QLabel(f"{version['version']} {version['label']}")
        version_label.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.PRIMARY if active else L.TEXT_PRIMARY}; "
            f"font-weight: 700;"
        )
        header_col.addWidget(version_label)

        summary = QLabel(str(version["summary"]))
        summary.setWordWrap(True)
        summary.setStyleSheet(
            f"font-size: {FontSize.CAPTION}px; color: {L.TEXT_SECONDARY};"
        )
        header_col.addWidget(summary)

        top.addLayout(header_col, 1)
        layout.addLayout(top)

        bottom = QHBoxLayout()
        bottom.setSpacing(Spacing.SM)

        source = QLabel(str(version["source"]))
        source.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        bottom.addWidget(source)
        bottom.addStretch()

        time_label = QLabel(str(version["time"]))
        time_label.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        bottom.addWidget(time_label)
        layout.addLayout(bottom)

        return card

    def _create_diff_panel(self) -> QFrame:
        diff_data = MOCK_VERSION_DIFFS[self._active_diff_key]

        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        title = QLabel(diff_data["title"])
        title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(PreviewBadge("仅预览"))
        layout.addLayout(top_row)

        hint = QLabel("Diff 区域仅展示 mock 对比摘要，不接真实版本比较算法、Git 历史或恢复操作。")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
        layout.addWidget(hint)

        layout.addWidget(
            self._create_diff_block(
                "删除内容",
                diff_data["deletions"],
                prefix="- ",
                text_color=L.ERROR,
                background=L.ERROR_BG,
                border=L.BORDER_SUBTLE,
                header_color=L.ERROR,
            )
        )
        layout.addWidget(
            self._create_diff_block(
                "新增内容",
                diff_data["additions"],
                prefix="+ ",
                text_color=L.SUCCESS,
                background=L.SUCCESS_BG,
                border=L.BORDER_SUBTLE,
                header_color=L.SUCCESS,
            )
        )
        layout.addWidget(self._create_reason_block(diff_data["reason"]))

        action_row = QHBoxLayout()
        action_row.setSpacing(Spacing.SM)
        action_row.addWidget(self._disabled_action_button("比较版本"))
        action_row.addWidget(self._disabled_action_button("导出差异"))
        action_row.addStretch()
        layout.addLayout(action_row)

        layout.addStretch()
        return panel

    def _create_diff_block(
        self,
        title: str,
        lines: list[str],
        *,
        prefix: str,
        text_color: str,
        background: str,
        border: str,
        header_color: str,
    ) -> QFrame:
        block = QFrame()
        block.setStyleSheet(
            f"QFrame {{ background-color: {background}; border: 1px solid {border}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(block)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        header = QLabel(title)
        header.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {header_color}; font-weight: 700;"
        )
        layout.addWidget(header)

        for text in lines:
            line = QLabel(f"{prefix}{text}")
            line.setWordWrap(True)
            line.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {text_color}; font-weight: 500;"
            )
            layout.addWidget(line)

        return block

    def _create_reason_block(self, reason: str) -> QFrame:
        block = QFrame()
        block.setStyleSheet(
            f"QFrame {{ background-color: {L.PRIMARY_LIGHT}; border: 1px solid {L.PRIMARY_BORDER}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(block)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        header = QLabel("修改原因")
        header.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(header)

        text = QLabel(reason)
        text.setWordWrap(True)
        text.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
        )
        layout.addWidget(text)

        return block

    def _create_info_panel(self) -> QFrame:
        version = MOCK_VERSION_TIMELINE[0]

        panel = QFrame()
        panel.setFixedWidth(240)
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title_row = QHBoxLayout()
        title = QLabel("版本信息")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(StatusBadge("Mock", "warning"))
        layout.addLayout(title_row)

        fields = [
            ("版本号", version["version"]),
            ("生成来源", version["source"]),
            ("使用 Agent", version["agent"]),
            ("调用 Skill", version["skill"]),
            ("审稿结论", version["review"]),
            ("费用", version["cost"]),
            ("Token 信息", version["tokens"]),
            ("创建时间", version["time"]),
        ]
        for label, value in fields:
            layout.addWidget(self._info_field(str(label), str(value)))

        layout.addWidget(self._risk_panel(version["risk_notes"]))

        action_row = QHBoxLayout()
        action_row.setSpacing(Spacing.SM)
        action_row.addWidget(self._disabled_action_button("恢复版本"))
        action_row.addWidget(self._disabled_action_button("回滚到此版本"))
        layout.addLayout(action_row)

        export_btn = self._disabled_action_button("导出版本摘要")
        export_btn.setFixedHeight(28)
        layout.addWidget(export_btn)

        layout.addStretch()
        return panel

    def _info_field(self, label_text: str, value_text: str) -> QFrame:
        field = QFrame()
        field.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        layout = QVBoxLayout(field)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.XS)

        label = QLabel(label_text)
        label.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED}; font-weight: 600;"
        )
        layout.addWidget(label)

        value = QLabel(value_text)
        value.setWordWrap(True)
        value.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        layout.addWidget(value)

        return field

    def _risk_panel(self, notes: list[str]) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.WARNING_BG}; border: 1px solid {L.WARNING}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        title = QLabel("风险提示")
        title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.WARNING}; font-weight: 700;"
        )
        layout.addWidget(title)

        for note in notes:
            label = QLabel(f"• {note}")
            label.setWordWrap(True)
            label.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
            )
            layout.addWidget(label)

        return panel

    def _disabled_action_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setEnabled(False)
        btn.setFixedHeight(24)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
            f"border: 1px dashed {L.BORDER}; border-radius: {Radius.PILL}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: 600; padding: 0 {Spacing.MD}px; }} "
            f"QPushButton:disabled {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
            f"border: 1px dashed {L.BORDER}; }}"
        )
        return btn
