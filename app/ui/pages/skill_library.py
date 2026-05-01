"""Skill Library page — SVG-aligned skill catalog with detail sidebar."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.base import ComingSoonBadge, PageHeader, PreviewBadge, SkillCard, StatusBadge, _card_style
from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.mock.pages_data import MOCK_SKILL_CATEGORIES, MOCK_SKILL_DETAIL, MOCK_SKILLS


class SkillLibraryPage(QWidget):
    """Writing skill library with category sidebar, skill matrix, and detail panel."""

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
        header_row.addWidget(PageHeader("写作技能库", "展示技能卡片、使用说明与风险边界；当前仅为 mock / preview，不接真实 Skill Registry。"))
        header_row.addWidget(ComingSoonBadge("V2 计划"))
        header_row.addStretch()
        layout.addLayout(header_row)

        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)

        main_row.addWidget(self._create_category_panel())
        main_row.addWidget(self._create_skill_grid_panel(), 2)
        main_row.addWidget(self._create_detail_panel())

        layout.addLayout(main_row, 1)
        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _create_category_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(170)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("技能分类")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        for category in MOCK_SKILL_CATEGORIES:
            label = QLabel(f"{category['name']} {category['count']}")
            if category["active"]:
                label.setStyleSheet(
                    f"font-size: {FontSize.SMALL}px; color: {L.PRIMARY}; font-weight: 600; "
                    f"padding: {Spacing.XS}px 0;"
                )
            else:
                label.setStyleSheet(
                    f"font-size: {FontSize.SMALL}px; color: {L.TEXT_SECONDARY}; "
                    f"padding: {Spacing.XS}px 0;"
                )
            layout.addWidget(label)

        layout.addStretch()
        return panel

    def _create_skill_grid_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        title = QLabel("技能卡片矩阵")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(PreviewBadge("仅预览"))

        for text in ["查看说明", "启用技能", "安装技能"]:
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

        hint = QLabel("当前技能卡片仅用于界面预览，不代表技能已下载、已启用或可真实调用。")
        hint.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(Spacing.MD)
        for i, skill in enumerate(MOCK_SKILLS):
            card = SkillCard(
                name=skill["name"],
                description=skill["description"],
                usage_count=skill["usage_count"],
                rating=skill["rating"],
                enabled=False,
                category=skill["category"],
                tags=skill["tags"],
                status_text=skill["status"],
                status_type=skill["status_type"],
                risk_note=skill["risk_note"],
            )
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)

        return panel

    def _create_detail_panel(self) -> QFrame:
        detail = MOCK_SKILL_DETAIL

        panel = QFrame()
        panel.setFixedWidth(260)
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("技能详情")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        name_row = QHBoxLayout()
        name = QLabel(detail["title"])
        name.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        name_row.addWidget(name, 1)
        name_row.addWidget(StatusBadge(detail["status"], detail["status_type"]))
        layout.addLayout(name_row)

        summary = QLabel(detail["summary"])
        summary.setWordWrap(True)
        summary.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
        )
        layout.addWidget(summary)

        layout.addWidget(self._detail_block("适用场景", detail["use_cases"]))
        layout.addWidget(self._detail_block("输入说明", detail["input_schema"]))
        layout.addWidget(self._detail_block("输出说明", detail["output_schema"]))
        layout.addWidget(self._detail_block("风险提示", detail["risk_rules"], warning=True))

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
