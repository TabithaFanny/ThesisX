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
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.mock.pages_data import MOCK_VERSION_DIFFS, MOCK_VERSION_TIMELINE


class VersionHistoryPage(QWidget):
    """Version history page with timeline, diff preview, and version metadata."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_version = MOCK_VERSION_TIMELINE[0]["version"]
        self._active_diff_key = "v11\u2192v12"
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _init_ui(self):
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet(f"background-color: {L.CANVAS};")
        root = QVBoxLayout(self._content_widget)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        header_row = QHBoxLayout()
        self._header = PageHeader(
            "版本历史",
            "展示 mock 版本时间线、差异摘要与版本信息；当前未接入真实 Git、回滚或恢复链路。",
        )
        header_row.addWidget(self._header)
        self._coming_soon = ComingSoonBadge("V2 \u8ba1\u5212")
        header_row.addWidget(self._coming_soon)
        header_row.addStretch()
        root.addLayout(header_row)

        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)
        cols.addWidget(self._create_timeline_panel())
        cols.addWidget(self._create_diff_panel(), 1)
        cols.addWidget(self._create_info_panel())
        root.addLayout(cols, 1)

        self._scroll.setWidget(self._content_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll)

    def _create_timeline_panel(self) -> QFrame:
        L = get_theme()
        self._timeline_panel = QFrame()
        self._timeline_panel.setFixedWidth(220)
        self._timeline_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(self._timeline_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title_row = QHBoxLayout()
        self._timeline_title = QLabel("版本时间线")
        self._timeline_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        title_row.addWidget(self._timeline_title)
        title_row.addStretch()
        self._timeline_preview_badge = PreviewBadge("仅预览")
        title_row.addWidget(self._timeline_preview_badge)
        layout.addLayout(title_row)

        self._timeline_hint = QLabel("仅展示 mock 版本轨迹，不代表真实历史快照或可恢复记录。")
        self._timeline_hint.setWordWrap(True)
        self._timeline_hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
        layout.addWidget(self._timeline_hint)

        for version in MOCK_VERSION_TIMELINE:
            layout.addWidget(self._create_timeline_item(version))

        layout.addStretch()
        return self._timeline_panel

    def _create_timeline_item(self, version: dict[str, object]) -> QFrame:
        L = get_theme()
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
        L = get_theme()
        diff_data = MOCK_VERSION_DIFFS[self._active_diff_key]

        self._diff_panel = QFrame()
        self._diff_panel.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._diff_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        self._diff_title = QLabel(diff_data["title"])
        self._diff_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        top_row.addWidget(self._diff_title)
        top_row.addStretch()
        self._diff_preview_badge = PreviewBadge("仅预览")
        top_row.addWidget(self._diff_preview_badge)
        layout.addLayout(top_row)

        self._diff_hint = QLabel("Diff 区域仅展示 mock 对比摘要，不接真实版本比较算法、Git 历史或恢复操作。")
        self._diff_hint.setWordWrap(True)
        self._diff_hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
        layout.addWidget(self._diff_hint)

        self._diff_blocks: list[QFrame] = []
        block1 = self._create_diff_block(
            "删除内容",
            diff_data["deletions"],
            prefix="- ",
            text_color=L.ERROR,
            background=L.ERROR_BG,
            border=L.BORDER_SUBTLE,
            header_color=L.ERROR,
        )
        self._diff_blocks.append(block1)
        layout.addWidget(block1)

        block2 = self._create_diff_block(
            "新增内容",
            diff_data["additions"],
            prefix="+ ",
            text_color=L.SUCCESS,
            background=L.SUCCESS_BG,
            border=L.BORDER_SUBTLE,
            header_color=L.SUCCESS,
        )
        self._diff_blocks.append(block2)
        layout.addWidget(block2)

        self._reason_block = self._create_reason_block(diff_data["reason"])
        layout.addWidget(self._reason_block)

        action_row = QHBoxLayout()
        action_row.setSpacing(Spacing.SM)
        self._compare_btn = self._disabled_action_button("比较版本")
        action_row.addWidget(self._compare_btn)
        self._export_diff_btn = self._disabled_action_button("导出差异")
        action_row.addWidget(self._export_diff_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

        layout.addStretch()
        return self._diff_panel

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
        L = get_theme()
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
        L = get_theme()
        version = MOCK_VERSION_TIMELINE[0]

        self._info_panel = QFrame()
        self._info_panel.setFixedWidth(240)
        self._info_panel.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._info_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title_row = QHBoxLayout()
        self._info_title = QLabel("版本信息")
        self._info_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        title_row.addWidget(self._info_title)
        title_row.addStretch()
        self._info_badge = StatusBadge("Mock", "warning")
        title_row.addWidget(self._info_badge)
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
        self._restore_btn = self._disabled_action_button("恢复版本")
        action_row.addWidget(self._restore_btn)
        self._rollback_btn = self._disabled_action_button("回滚到此版本")
        action_row.addWidget(self._rollback_btn)
        layout.addLayout(action_row)

        self._export_btn = self._disabled_action_button("导出版本摘要")
        self._export_btn.setFixedHeight(28)
        layout.addWidget(self._export_btn)

        layout.addStretch()
        return self._info_panel

    def _info_field(self, label_text: str, value_text: str) -> QFrame:
        L = get_theme()
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
        L = get_theme()
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
        L = get_theme()
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

    def apply_theme(self) -> None:
        """Re-apply styles using current theme tokens."""
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")
        self._content_widget.setStyleSheet(f"background-color: {L.CANVAS};")
        self._header.apply_theme()
        self._coming_soon.apply_theme()

        # Timeline panel
        self._timeline_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._timeline_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._timeline_preview_badge.apply_theme()
        self._timeline_hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")

        # Diff panel
        self._diff_panel.setStyleSheet(_card_style(L))
        self._diff_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._diff_preview_badge.apply_theme()
        self._diff_hint.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};")
        # Rebuild diff blocks with current theme
        diff_data = MOCK_VERSION_DIFFS[self._active_diff_key]
        for block in self._diff_blocks:
            block.deleteLater()
        self._diff_blocks.clear()
        block1 = self._create_diff_block(
            "删除内容", diff_data["deletions"], prefix="- ",
            text_color=L.ERROR, background=L.ERROR_BG, border=L.BORDER_SUBTLE, header_color=L.ERROR,
        )
        self._diff_panel.layout().insertWidget(3, block1)
        self._diff_blocks.append(block1)
        block2 = self._create_diff_block(
            "新增内容", diff_data["additions"], prefix="+ ",
            text_color=L.SUCCESS, background=L.SUCCESS_BG, border=L.BORDER_SUBTLE, header_color=L.SUCCESS,
        )
        self._diff_panel.layout().insertWidget(4, block2)
        self._diff_blocks.append(block2)

        # Info panel
        self._info_panel.setStyleSheet(_card_style(L))
        self._info_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._info_badge.apply_theme()
