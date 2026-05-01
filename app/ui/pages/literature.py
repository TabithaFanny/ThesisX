"""Literature Management page — aligned with page_04_literature_management.svg.

SVG layout:
- Left category sidebar (全部文献 512 / 我的收藏 126 / 回收站 32)
- Right: search bar + "导入文献" blue pill button + literature table with tags
- Detail panel (below): abstract, citation, scores, tags for selected literature
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea, QFrame,
    QPushButton, QGridLayout,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, ComingSoonBadge, _card_style
from app.ui.mock.pages_data import MOCK_LITERATURE, MOCK_LIT_DETAILS
from app.ui.mock.workspace_data import MOCK_LIT_CATEGORIES


class LiteraturePage(QWidget):
    """Literature management mock page — SVG-aligned layout with detail panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(PageHeader("文献管理", "管理你的参考文献库，支持检索、标注和引用。"))
        header_row.addWidget(ComingSoonBadge("V3 计划"))
        header_row.addStretch()
        root.addLayout(header_row)

        # Main content: sidebar + right panel
        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)

        # --- Left category sidebar (SVG: 118px wide, #F9FBFF bg) ---
        sidebar = QFrame()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        side_layout.setSpacing(Spacing.SM)

        side_title = QLabel("文献库")
        side_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        side_layout.addWidget(side_title)

        for cat in MOCK_LIT_CATEGORIES:
            cat_row = QHBoxLayout()
            cat_row.setSpacing(Spacing.SM)
            name = QLabel(cat["name"])
            if cat["active"]:
                name.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.PRIMARY}; font-weight: bold;"
                )
            else:
                name.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
                )
            cat_row.addWidget(name)
            count = QLabel(str(cat["count"]))
            if cat["active"]:
                count.setStyleSheet(
                    f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY};"
                )
            else:
                count.setStyleSheet(
                    f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
                )
            cat_row.addWidget(count)
            cat_row.addStretch()
            side_layout.addLayout(cat_row)

        side_layout.addStretch()
        main_row.addWidget(sidebar)

        # --- Right content area ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(Spacing.MD)

        # Top: search + import button
        list_card = QFrame()
        list_card.setStyleSheet(_card_style())
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        list_layout.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.MD)

        search_bar = QFrame()
        search_bar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; }}"
        )
        search_bar.setFixedHeight(32)
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(Spacing.SM, 0, Spacing.SM, 0)
        search_lbl = QLabel("搜索文献标题、作者、关键词...")
        search_lbl.setStyleSheet(f"color: {L.TEXT_MUTED}; font-size: {FontSize.SECONDARY}px;")
        search_layout.addWidget(search_lbl)
        top_row.addWidget(search_bar, 1)

        # Import button (SVG: 72x28, rx=14, #2563EB fill, white text "导入文献")
        import_btn = QPushButton("导入文献")
        import_btn.setFixedSize(80, 28)
        import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.PILL}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        top_row.addWidget(import_btn)
        list_layout.addLayout(top_row)

        # Literature table (SVG: rows with title + tag)
        for i, lit in enumerate(MOCK_LITERATURE):
            row = self._create_lit_row(lit, i == len(MOCK_LITERATURE) - 1)
            list_layout.addLayout(row)

        list_layout.addStretch()
        right_layout.addWidget(list_card, 1)

        # --- Detail panel (below list) ---
        detail_card = QFrame()
        detail_card.setStyleSheet(_card_style())
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        detail_layout.setSpacing(Spacing.MD)

        # Header row
        detail_header = QHBoxLayout()
        detail_title = QLabel("文献详情 — Attention Is All You Need")
        detail_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        detail_header.addWidget(detail_title, 1)
        detail_header.addWidget(ComingSoonBadge("仅预览"))
        detail_layout.addLayout(detail_header)

        # Two-column detail
        detail_cols = QHBoxLayout()
        detail_cols.setSpacing(Spacing.LG)

        # Left: abstract + citation
        left_detail = QVBoxLayout()
        left_detail.setSpacing(Spacing.SM)

        abstract_title = QLabel("摘要")
        abstract_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        left_detail.addWidget(abstract_title)

        abstract_text = QLabel(MOCK_LIT_DETAILS["abstract"])
        abstract_text.setWordWrap(True)
        abstract_text.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px;"
        )
        left_detail.addWidget(abstract_text)

        # Citation format
        citation_title = QLabel("引用格式 (GB/T 7714)")
        citation_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold; "
            f"margin-top: {Spacing.SM}px;"
        )
        left_detail.addWidget(citation_title)

        citation_text = QLabel(MOCK_LIT_DETAILS["citation_gb"])
        citation_text.setWordWrap(True)
        citation_text.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_SECONDARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px;"
        )
        left_detail.addWidget(citation_text)
        left_detail.addStretch()

        detail_cols.addLayout(left_detail, 2)

        # Right: scores + source + tags
        right_detail = QVBoxLayout()
        right_detail.setSpacing(Spacing.SM)

        scores_title = QLabel("评分维度")
        scores_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        right_detail.addWidget(scores_title)

        for dim, score in MOCK_LIT_DETAILS["scores"].items():
            score_row = QHBoxLayout()
            score_row.setSpacing(Spacing.SM)

            dim_lbl = QLabel(dim)
            dim_lbl.setFixedWidth(50)
            dim_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
            )
            score_row.addWidget(dim_lbl)

            # Progress bar
            bar_bg = QFrame()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet(
                f"QFrame {{ background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; }}"
            )
            bar_fill = QFrame(bar_bg)
            fill_width = max(2, int(80 * score / 100))
            bar_fill.setFixedHeight(6)
            bar_fill.setFixedWidth(fill_width)
            bar_fill.setStyleSheet(
                f"QFrame {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
            )
            score_row.addWidget(bar_bg, 1)

            score_val = QLabel(f"{score}")
            score_val.setFixedWidth(30)
            score_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            score_val.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; font-weight: bold;"
            )
            score_row.addWidget(score_val)

            right_detail.addLayout(score_row)

        # Source status
        source_title = QLabel("来源状态")
        source_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold; "
            f"margin-top: {Spacing.SM}px;"
        )
        right_detail.addWidget(source_title)

        source_val = QLabel(MOCK_LIT_DETAILS["source_status"])
        source_val.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.SUCCESS}; font-weight: bold;"
        )
        right_detail.addWidget(source_val)

        # Tags
        tags_title = QLabel("标签")
        tags_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold; "
            f"margin-top: {Spacing.SM}px;"
        )
        right_detail.addWidget(tags_title)

        tags_row = QHBoxLayout()
        tags_row.setSpacing(Spacing.SM)
        for tag in MOCK_LIT_DETAILS["tags"]:
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY}; font-weight: bold; "
                f"background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; "
                f"padding: 1px 6px;"
            )
            tags_row.addWidget(tag_lbl)
        tags_row.addStretch()
        right_detail.addLayout(tags_row)

        right_detail.addStretch()
        detail_cols.addLayout(right_detail, 1)

        detail_layout.addLayout(detail_cols)
        right_layout.addWidget(detail_card)

        main_row.addWidget(right_panel, 1)
        root.addLayout(main_row, 1)

    def _create_lit_row(self, lit: dict, is_last: bool) -> QHBoxLayout:
        """Create a literature row matching SVG: title + blue tag."""
        row = QHBoxLayout()
        row.setSpacing(Spacing.MD)

        # Title (SVG: 10px/400, text #1E293B)
        title = QLabel(lit["title"])
        title.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY};"
        )
        row.addWidget(title, 3)

        # Tag (SVG: 9px, #2563EB blue text)
        tag = QLabel(lit.get("tag", ""))
        tag.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY}; font-weight: bold; "
            f"background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; "
            f"padding: 1px 6px;"
        )
        row.addWidget(tag)

        # Source + year (secondary info)
        source = QLabel(f"{lit['source']} {lit['year']}")
        source.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        source.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(source, 1)

        return row
