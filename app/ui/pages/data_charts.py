"""Data & Charts page — SVG-aligned dataset and chart preview workspace."""

from __future__ import annotations

from PyQt6.QtCore import Qt
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

from app.ui.components.base import ComingSoonBadge, PageHeader, PreviewBadge, StatusBadge, _card_style
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.mock.pages_data import MOCK_CHARTS, MOCK_DATASET_CATEGORIES, MOCK_DATASETS


class DataChartsPage(QWidget):
    """Data & Charts preview page with categories, file table, and chart thumbnails."""

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
        header_row.addWidget(PageHeader("数据图表", "管理研究数据集和图表资产；当前仅提供预览结构，不接真实分析链路。"))
        header_row.addWidget(ComingSoonBadge("V2 计划"))
        header_row.addStretch()
        layout.addLayout(header_row)

        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)

        sidebar = self._create_category_panel()
        main_row.addWidget(sidebar)

        right_col = QVBoxLayout()
        right_col.setSpacing(Spacing.MD)

        right_col.addWidget(self._create_files_panel())
        right_col.addWidget(self._create_chart_panel())

        main_row.addLayout(right_col, 1)
        layout.addLayout(main_row, 1)

        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _create_category_panel(self) -> QFrame:
        L = get_theme()
        panel = QFrame()
        panel.setFixedWidth(164)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("数据集")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        for category in MOCK_DATASET_CATEGORIES:
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

    def _create_files_panel(self) -> QFrame:
        L = get_theme()
        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.SM)

        title = QLabel("数据文件")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(PreviewBadge("仅预览"))

        for text in ["新建图表", "上传数据", "生成论文图表"]:
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

        hint = QLabel("当前为 mock 数据文件表，仅用于页面结构预览，不提供真实上传、解析或分析。")
        hint.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(hint)

        header = self._table_row("文件名", "类型", "大小", "更新时间", "状态", header=True)
        layout.addWidget(header)

        for dataset in MOCK_DATASETS:
            row = self._table_row(
                dataset["name"],
                dataset["file_type"],
                dataset["size"],
                dataset["updated"],
                dataset["status"],
                status_type=dataset["status_type"],
            )
            layout.addWidget(row)

        return panel

    def _table_row(
        self,
        name: str,
        file_type: str,
        size: str,
        updated: str,
        status: str,
        *,
        header: bool = False,
        status_type: str = "muted",
    ) -> QFrame:
        L = get_theme()
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background-color: {'transparent' if header else L.SURFACE}; "
            f"border-bottom: 1px solid {L.BORDER_SUBTLE}; }}"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        text_color = L.TEXT_MUTED if header else L.TEXT_PRIMARY
        text_weight = "600" if header else "400"
        meta_color = L.TEXT_MUTED if header else L.TEXT_SECONDARY

        name_label = QLabel(name)
        name_label.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {text_color}; font-weight: {text_weight};"
        )
        layout.addWidget(name_label, 3)

        type_label = QLabel(file_type)
        type_label.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {meta_color}; font-weight: {text_weight};"
        )
        layout.addWidget(type_label, 1)

        size_label = QLabel(size)
        size_label.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {meta_color}; font-weight: {text_weight};"
        )
        layout.addWidget(size_label, 1)

        updated_label = QLabel(updated)
        updated_label.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {meta_color}; font-weight: {text_weight};"
        )
        layout.addWidget(updated_label, 2)

        if header:
            status_label = QLabel(status)
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setStyleSheet(
                f"font-size: {FontSize.SMALL}px; color: {L.TEXT_MUTED}; font-weight: 600;"
            )
            layout.addWidget(status_label, 1)
        else:
            layout.addWidget(StatusBadge(status, status_type), 1)

        return row

    def _create_chart_panel(self) -> QFrame:
        L = get_theme()
        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        title_row = QHBoxLayout()
        title = QLabel("图表缩略预览")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(PreviewBadge("Mock 图表"))
        layout.addLayout(title_row)

        grid = QGridLayout()
        grid.setSpacing(Spacing.MD)

        for index, chart in enumerate(MOCK_CHARTS):
            grid.addWidget(self._chart_card(chart), index // 4, index % 4)

        layout.addLayout(grid)
        return panel

    def _chart_card(self, chart: dict) -> QFrame:
        L = get_theme()
        card = QFrame()
        card.setMinimumHeight(124)
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        preview = QFrame()
        preview.setMinimumHeight(70)
        preview.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        preview_layout.setSpacing(0)
        self._populate_chart_preview(preview_layout, chart["preview"])
        layout.addWidget(preview)

        title = QLabel(chart["title"])
        title.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        layout.addWidget(title)

        meta = QHBoxLayout()
        meta.setSpacing(Spacing.SM)

        chart_type = QLabel(chart["type"])
        chart_type.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
        )
        meta.addWidget(chart_type)
        meta.addStretch()
        meta.addWidget(StatusBadge(chart["status"], chart["status_type"]))
        layout.addLayout(meta)

        return card

    def _populate_chart_preview(self, layout: QVBoxLayout, preview_type: str) -> None:
        L = get_theme()
        if preview_type == "bar":
            row = QHBoxLayout()
            row.setSpacing(Spacing.XS)
            for height in (22, 40, 18, 48):
                bar = QFrame()
                bar.setFixedWidth(8)
                bar.setFixedHeight(height)
                bar.setStyleSheet(
                    f"QFrame {{ background-color: {L.PRIMARY_SOFT}; border-radius: 2px; }}"
                )
                row.addWidget(bar, 0, Qt.AlignmentFlag.AlignBottom)
            row.addStretch()
            layout.addStretch()
            layout.addLayout(row)
        elif preview_type == "line":
            line = QLabel("╱╲╱╲")
            line.setAlignment(Qt.AlignmentFlag.AlignCenter)
            line.setStyleSheet(
                f"font-size: 24px; color: {L.PRIMARY}; font-weight: 700;"
            )
            layout.addStretch()
            layout.addWidget(line)
            layout.addStretch()
        elif preview_type == "pie":
            pie = QLabel("◔")
            pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pie.setStyleSheet(
                f"font-size: 34px; color: {L.WARNING};"
            )
            layout.addStretch()
            layout.addWidget(pie)
            layout.addStretch()
        else:
            for colors in (
                (L.PRIMARY_LIGHT, L.PRIMARY_SOFT, L.PRIMARY, L.PRIMARY_LIGHT),
                (L.PRIMARY_SOFT, L.PRIMARY, L.PRIMARY_LIGHT, L.PRIMARY_SOFT),
                (L.PRIMARY, L.PRIMARY_LIGHT, L.PRIMARY_SOFT, L.PRIMARY),
            ):
                row = QHBoxLayout()
                row.setSpacing(Spacing.XS)
                for color in colors:
                    cell = QFrame()
                    cell.setFixedSize(10, 10)
                    cell.setStyleSheet(
                        f"QFrame {{ background-color: {color}; border-radius: 1px; }}"
                    )
                    row.addWidget(cell)
                row.addStretch()
                layout.addLayout(row)
            layout.addStretch()
