"""Skill Library page — real SkillLoader-backed catalog (Vision 3.8)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.base import PageHeader, _card_style
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


def _badge_style(color: str, L=None) -> str:
    if L is None:
        L = get_theme()
    return (
        f"QLabel {{ background-color: {color}; color: white;"
        f" border-radius: 8px; padding: 2px 8px;"
        f" font-size: {FontSize.CAPTION}px; font-weight: 600; }}"
    )


def _label(size: int, color: str, weight: str = "normal") -> str:
    return f"QLabel {{ font-size: {size}px; color: {color}; font-weight: {weight}; }}"


_CATEGORY_COLORS: dict[str, str] = {
    "general": "#6B7280",
    "editing": "#059669",
    "research": "#7C3AED",
    "writing": "#2563EB",
    "analysis": "#D97706",
}

_CATEGORY_LABELS: dict[str, str] = {
    "general": "通用",
    "editing": "编辑",
    "research": "研究",
    "writing": "写作",
    "analysis": "分析",
}


class _SkillCard(QFrame):
    """Card displaying one skill with enable toggle."""

    toggled = pyqtSignal(str, bool)  # skill file_path, enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._file_path = ""
        self._badge_color = L.PRIMARY

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Top row: checkbox + name + category badge
        top = QHBoxLayout()
        top.setSpacing(Spacing.SM)

        self._checkbox = QCheckBox("")
        self._checkbox.stateChanged.connect(self._on_toggle)
        top.addWidget(self._checkbox)

        self._name_label = QLabel("")
        self._name_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        self._name_label.setWordWrap(True)
        top.addWidget(self._name_label, 1)

        self._cat_badge = QLabel("")
        self._cat_badge.setStyleSheet(_badge_style(L.PRIMARY))
        top.addWidget(self._cat_badge)

        layout.addLayout(top)

        # Description
        self._desc_label = QLabel("")
        self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._name_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        self._cat_badge.setStyleSheet(_badge_style(self._badge_color))
        self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))

    def set_skill(self, name: str, description: str, category: str,
                  file_path: str, enabled: bool) -> None:
        self._file_path = file_path
        self._name_label.setText(name)
        self._desc_label.setText(description)

        cat_label = _CATEGORY_LABELS.get(category, category)
        color = _CATEGORY_COLORS.get(category, get_theme().PRIMARY)
        self._badge_color = color
        self._cat_badge.setText(cat_label)
        self._cat_badge.setStyleSheet(_badge_style(color))

        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(enabled)
        self._checkbox.blockSignals(False)

    def _on_toggle(self, state: int) -> None:
        self.toggled.emit(self._file_path, state == Qt.CheckState.Checked.value)

    def file_path(self) -> str:
        return self._file_path


class SkillLibraryPage(QWidget):
    """Writing skill library using real SkillLoader data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        from app.core.skills.loader import SkillLoader
        from app.core.skills.enabled_store import EnabledSkillsStore

        self._loader = SkillLoader()
        self._enabled_store = EnabledSkillsStore()
        self._enabled: set[str] = self._enabled_store.load()
        self._skills: list = []
        self._cards: dict[str, _SkillCard] = {}
        self._selected_skill = None

        self._build_ui()
        self._reload()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    # ── UI build ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        L = get_theme()
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        self._page_header = PageHeader(
            "写作技能库",
            "管理和激活本地写作 Skill。启用的技能将注入 AI 写作上下文。",
        )
        header_row.addWidget(self._page_header)
        header_row.addStretch()

        self._enable_count = QLabel("")
        self._enable_count.setStyleSheet(_label(FontSize.SECONDARY, L.PRIMARY))
        header_row.addWidget(self._enable_count)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.clicked.connect(self._reload)
        header_row.addWidget(refresh_btn)

        root.addLayout(header_row)

        # Main area: skill list (left) + detail (right)
        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)

        # Left: skill list
        self._left_panel = QFrame()
        self._left_panel.setStyleSheet(_card_style(L))
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        left_layout.setSpacing(Spacing.SM)

        self._list_title = QLabel("技能列表")
        self._list_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        left_layout.addWidget(self._list_title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(Spacing.SM)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_container)
        left_layout.addWidget(self._scroll, 1)

        # Empty state
        self._empty_label = QLabel(
            "暂无本地技能。\n"
            "将 .json 或 .md 技能文件放入 ~/.wenbiao/skills/ 目录即可加载。"
        )
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)

        main_row.addWidget(self._left_panel, 3)

        # Right: detail panel
        self._detail_panel = QFrame()
        self._detail_panel.setFixedWidth(320)
        self._detail_panel.setStyleSheet(_card_style(L))
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        detail_layout.setSpacing(Spacing.SM)

        self._detail_title = QLabel("技能详情")
        self._detail_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        detail_layout.addWidget(self._detail_title)

        self._detail_name = QLabel("")
        self._detail_name.setStyleSheet(
            f"font-size: {FontSize.BODY}px; font-weight: 700; color: {L.TEXT_PRIMARY};"
        )
        self._detail_name.setWordWrap(True)
        detail_layout.addWidget(self._detail_name)

        self._detail_desc = QLabel("")
        self._detail_desc.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._detail_desc.setWordWrap(True)
        detail_layout.addWidget(self._detail_desc)

        self._detail_category = QLabel("")
        self._detail_category.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        detail_layout.addWidget(self._detail_category)

        self._prompt_header = QLabel("Prompt 内容：")
        self._prompt_header.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_PRIMARY, "bold"))
        detail_layout.addWidget(self._prompt_header)

        self._detail_prompt = QTextEdit()
        self._detail_prompt.setReadOnly(True)
        self._detail_prompt.setMinimumHeight(150)
        self._detail_prompt.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_SECONDARY};"
            f" border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px;"
            f" font-size: {FontSize.SECONDARY}px; padding: {Spacing.SM}px; }}"
        )
        detail_layout.addWidget(self._detail_prompt)

        detail_layout.addStretch()

        main_row.addWidget(self._detail_panel, 2)

        root.addLayout(main_row, 1)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._page_header.apply_theme()
        self._enable_count.setStyleSheet(_label(FontSize.SECONDARY, L.PRIMARY))
        self._left_panel.setStyleSheet(_card_style(L))
        self._list_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._detail_panel.setStyleSheet(_card_style(L))
        self._detail_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        self._detail_name.setStyleSheet(
            f"font-size: {FontSize.BODY}px; font-weight: 700; color: {L.TEXT_PRIMARY};"
        )
        self._detail_desc.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._detail_category.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        self._prompt_header.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_PRIMARY, "bold"))
        self._detail_prompt.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_SECONDARY};"
            f" border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px;"
            f" font-size: {FontSize.SECONDARY}px; padding: {Spacing.SM}px; }}"
        )
        for card in self._cards.values():
            card.apply_theme()

    # ── data ──────────────────────────────────────────────────────────────

    def _reload(self) -> None:
        self._skills = self._loader.load_local_skills()
        self._enabled = self._enabled_store.load()
        self._refresh_cards()
        self._refresh_status()

    def _refresh_status(self) -> None:
        total = len(self._skills)
        active = sum(1 for s in self._skills if self._enabled_store.is_enabled(s.name))
        self._enable_count.setText(f"已启用 {active} / {total} 个技能")

    def _refresh_cards(self) -> None:
        # Clear existing
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        if not self._skills:
            self._empty_label.setVisible(True)
            self._scroll.setVisible(False)
            return

        self._empty_label.setVisible(False)
        self._scroll.setVisible(True)

        for skill in self._skills:
            card = _SkillCard()
            enabled = self._enabled_store.is_enabled(skill.name)
            card.set_skill(
                name=skill.name,
                description=skill.description,
                category=skill.category,
                file_path=skill.file_path,
                enabled=enabled,
            )
            card.toggled.connect(self._on_skill_toggled)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = lambda e, s=skill: self._on_skill_clicked(s)
            self._cards[skill.file_path] = card
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _on_skill_toggled(self, file_path: str, enabled: bool) -> None:
        # Find the skill name from file_path
        for skill in self._skills:
            if skill.file_path == file_path:
                if enabled:
                    self._enabled_store.enable(skill.name)
                else:
                    self._enabled_store.disable(skill.name)
                break
        self._refresh_status()

    def _on_skill_clicked(self, skill) -> None:
        self._selected_skill = skill
        self._detail_name.setText(skill.name)
        self._detail_desc.setText(skill.description)
        cat_label = _CATEGORY_LABELS.get(skill.category, skill.category)
        self._detail_category.setText(f"分类: {cat_label}  |  文件: {skill.file_path}")
        self._detail_prompt.setPlainText(skill.prompt)
