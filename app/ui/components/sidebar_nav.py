"""Sidebar navigation for switching between workspace pages."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QWidget

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


# Navigation items: (id, title, subtitle)
NAV_ITEMS = [
    ("home", "工作台 / 首页", "模块入口与状态摘要"),
    ("editor", "编辑器", "主要交互页"),
    ("research", "研究工作空间", "项目与问题定义"),
    ("literature", "文献管理", "文献库与详情预览"),
    ("knowledge", "知识库", "本地资料库与检索"),
    ("rag", "RAG 检索", "BM25 知识库语义搜索"),
    ("theory", "理论匹配", "研究问题与理论框架"),
    ("skills", "写作技能库", "技能卡片与调用入口"),
    ("evidence", "证据包", "Claim-Evidence 链管理"),
    ("export", "导出中心", "论文/引文/记录导出"),
    ("submission", "投稿与回复", "投稿表与回复计划"),
    ("quality", "质量仪表盘", "论文质量指标总览"),
    ("settings", "设置中心", "模型、偏好与连接器"),
    ("run_history", "运行历史", "本地运行记录与诊断"),
]


class _NavItem(QFrame):
    """Numbered navigation item aligned to the SVG navigation index."""

    clicked = pyqtSignal(str)

    def __init__(self, item_id: str, index: int, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._index = index
        self._active = False
        self._hovered = False
        self._init_ui(title, subtitle)
        self._apply_style()

    def _init_ui(self, title: str, subtitle: str) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        self._indicator = QFrame()
        self._indicator.setFixedWidth(3)
        self._indicator.setStyleSheet("background: transparent; border-radius: 1px;")
        layout.addWidget(self._indicator)

        self._badge = QLabel(str(self._index))
        self._badge.setFixedSize(20, 20)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._title = QLabel(title)
        self._title.setWordWrap(False)
        text_col.addWidget(self._title)

        self._subtitle = QLabel(subtitle)
        self._subtitle.setWordWrap(False)
        text_col.addWidget(self._subtitle)

        layout.addLayout(text_col, 1)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.clicked.emit(self._item_id)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def _apply_style(self) -> None:
        L = get_theme()
        if self._active:
            bg = L.PRIMARY_LIGHT
            border = L.PRIMARY_BORDER
            title_color = L.PRIMARY
            subtitle_color = L.TEXT_SECONDARY
            badge_fill = L.PRIMARY
            indicator_fill = L.PRIMARY
        elif self._hovered:
            bg = L.SURFACE_ALT
            border = L.BORDER_SUBTLE
            title_color = L.TEXT_PRIMARY
            subtitle_color = L.TEXT_SECONDARY
            badge_fill = L.PRIMARY_SOFT
            indicator_fill = L.PRIMARY_BORDER
        else:
            bg = "transparent"
            border = "transparent"
            title_color = L.TEXT_PRIMARY
            subtitle_color = L.TEXT_SECONDARY
            badge_fill = L.PRIMARY_SOFT
            indicator_fill = "transparent"

        self.setStyleSheet(
            f"QFrame {{ "
            f"background-color: {bg}; "
            f"border: 1px solid {border}; "
            f"border-radius: {Radius.PANEL}px; "
            f"}}"
        )
        self._indicator.setStyleSheet(
            f"background-color: {indicator_fill}; border-radius: 1px;"
        )
        self._badge.setStyleSheet(
            f"background-color: {badge_fill}; color: {L.TEXT_ON_PRIMARY}; "
            f"border-radius: 10px; font-size: {FontSize.MICRO}px; font-weight: 700;"
        )
        self._title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {title_color}; font-weight: 600;"
        )
        self._subtitle.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {subtitle_color};"
        )


class SidebarNav(QWidget):
    """Left sidebar navigation with numbered items and SVG-aligned shell."""

    page_selected = pyqtSignal(str)  # emits page id

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(252)
        self._buttons: dict[str, _NavItem] = {}
        self._current = "home"
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(
            f"background-color: {L.SURFACE}; "
            f"border: none; "
            f"border-radius: {Radius.PAGE}px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        brand_col = QVBoxLayout()
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(2)

        self._brand_label = QLabel("ThesisX")
        self._brand_label.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {L.PRIMARY};"
        )
        brand_col.addWidget(self._brand_label)

        self._tagline_label = QLabel("Academic Writing Workspace")
        self._tagline_label.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        brand_col.addWidget(self._tagline_label)
        layout.addLayout(brand_col)

        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background-color: {L.BORDER_SUBTLE}; border: none;")
        layout.addWidget(self._sep)

        items_col = QVBoxLayout()
        items_col.setContentsMargins(0, 0, 0, 0)
        items_col.setSpacing(Spacing.XS)

        for index, (item_id, title, subtitle) in enumerate(NAV_ITEMS, start=1):
            btn = self._create_nav_item(item_id, index, title, subtitle)
            items_col.addWidget(btn)

        layout.addLayout(items_col)
        layout.addStretch()

        self._footer = QFrame()
        self._footer.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        footer_layout = QVBoxLayout(self._footer)
        footer_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        footer_layout.setSpacing(2)

        self._footer_title = QLabel("Workspace Shell")
        self._footer_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        footer_layout.addWidget(self._footer_title)

        self._footer_status = QLabel("14 个页面导航")
        self._footer_status.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        footer_layout.addWidget(self._footer_status)
        layout.addWidget(self._footer)

        self._set_active("home")

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(
            f"background-color: {L.SURFACE}; "
            f"border: none; "
            f"border-radius: {Radius.PAGE}px;"
        )
        self._brand_label.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {L.PRIMARY};"
        )
        self._tagline_label.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        self._sep.setStyleSheet(f"background-color: {L.BORDER_SUBTLE}; border: none;")
        self._footer.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._footer_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        self._footer_status.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        # Re-apply styles on all nav items
        for btn in self._buttons.values():
            btn._apply_style()

    def _create_nav_item(self, item_id: str, index: int, title: str, subtitle: str) -> _NavItem:
        btn = _NavItem(item_id, index, title, subtitle)
        btn.clicked.connect(self._on_click)
        self._buttons[item_id] = btn
        return btn

    def _on_click(self, item_id: str) -> None:
        self._set_active(item_id)
        self.page_selected.emit(item_id)

    def _set_active(self, item_id: str) -> None:
        self._current = item_id
        for iid, btn in self._buttons.items():
            btn.set_active(iid == item_id)
