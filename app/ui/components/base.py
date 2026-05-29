"""Reusable UI base components for ThesisX workspace pages.

All components use design tokens from design_tokens.py for consistent theming.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox,
)

from app.ui.design_tokens import get_theme, FontSize, Radius, Spacing


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _card_style(L=None) -> str:
    """Standard card frame style."""
    if L is None:
        L = get_theme()
    return (
        f"QFrame {{ "
        f"background-color: {L.SURFACE}; "
        f"border: 1px solid {L.BORDER}; "
        f"border-radius: {Radius.PANEL}px; "
        f"}}"
    )


def _input_style(L=None) -> str:
    """Standard input style."""
    if L is None:
        L = get_theme()
    return (
        f"QLineEdit, QComboBox, QDoubleSpinBox {{ "
        f"background-color: {L.SURFACE}; "
        f"border: 1px solid {L.BORDER}; "
        f"border-radius: {Radius.INPUT}px; "
        f"padding: {Spacing.SM}px; "
        f"font-size: {FontSize.BODY}px; "
        f"color: {L.TEXT_PRIMARY}; "
        f"}}"
    )


def _label(size: int, color: str = "", weight: str = "", L=None) -> str:
    """Label style helper."""
    if L is None:
        L = get_theme()
    c = color or L.TEXT_PRIMARY
    w = f"font-weight: {weight};" if weight else ""
    return f"font-size: {size}px; color: {c}; {w}"


# ---------------------------------------------------------------------------
# Page Header
# ---------------------------------------------------------------------------

class PageHeader(QWidget):
    """Page title + subtitle header block."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._subtitle_text = subtitle
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        L = get_theme()
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.PAGE_TITLE, L.TEXT_PRIMARY, "bold"))
        layout.addWidget(self._title_label)

        self._subtitle_label = None
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            self._subtitle_label.setWordWrap(True)
            layout.addWidget(self._subtitle_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self._title_label.setStyleSheet(_label(FontSize.PAGE_TITLE, L.TEXT_PRIMARY, "bold"))
        if self._subtitle_label:
            self._subtitle_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))


# ---------------------------------------------------------------------------
# Status Badge
# ---------------------------------------------------------------------------

def _status_colors(L=None):
    """Return status color mapping for current theme."""
    if L is None:
        L = get_theme()
    return {
        "primary": (L.PRIMARY, L.PRIMARY_LIGHT),
        "success": (L.SUCCESS, L.SUCCESS_BG),
        "warning": (L.WARNING, L.WARNING_BG),
        "error": (L.ERROR, L.ERROR_BG),
        "muted": (L.TEXT_MUTED, L.SURFACE_ALT),
        "neutral": (L.TEXT_MUTED, L.SURFACE_ALT),
        "info": (L.PRIMARY, L.PRIMARY_LIGHT),
    }


class StatusBadge(QLabel):
    """Pill-shaped status badge with color coding."""

    def __init__(self, text: str, status_type: str = "muted", parent=None):
        super().__init__(text, parent)
        _valid = {"primary", "success", "warning", "error", "muted", "neutral", "info"}
        self._status_type = status_type if status_type in _valid else "muted"
        self.apply_theme()
        self.setFixedWidth(80)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def apply_theme(self) -> None:
        L = get_theme()
        fg, bg = _status_colors(L)[self._status_type]
        self.setStyleSheet(
            f"color: {fg}; background-color: {bg}; "
            f"border: 1px solid {fg}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; "
            f"font-weight: bold;"
        )


# ---------------------------------------------------------------------------
# Coming Soon Badge
# ---------------------------------------------------------------------------

class ComingSoonBadge(QLabel):
    """Badge for future features marked as coming soon."""

    def __init__(self, text: str = "Coming Soon", parent=None):
        super().__init__(text, parent)
        self._badge_text = text
        self.apply_theme()
        self.setFixedWidth(90)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(
            f"color: {L.TEXT_MUTED}; background-color: {L.SURFACE_ALT}; "
            f"border: 1px dashed {L.BORDER}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.CAPTION}px;"
        )


# ---------------------------------------------------------------------------
# Preview Badge
# ---------------------------------------------------------------------------

class PreviewBadge(QLabel):
    """Badge for preview/mock content."""

    def __init__(self, text: str = "Preview", parent=None):
        super().__init__(text, parent)
        self._badge_text = text
        self.apply_theme()
        self.setFixedWidth(70)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(
            f"color: {L.WARNING}; background-color: {L.WARNING_BG}; "
            f"border: 1px solid {L.WARNING}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.CAPTION}px; font-weight: bold;"
        )


# ---------------------------------------------------------------------------
# Workspace Card
# ---------------------------------------------------------------------------

class WorkspaceCard(QFrame):
    """Project/workspace card with title, subtitle, status, and meta info."""

    def __init__(self, title: str, subtitle: str = "", status_text: str = "",
                 status_type: str = "muted", meta: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Title row
        title_row = QHBoxLayout()
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, get_theme().TEXT_PRIMARY, "bold"))
        title_row.addWidget(self._title_label, 1)
        self._status_badge = None
        if status_text:
            self._status_badge = StatusBadge(status_text, status_type)
            title_row.addWidget(self._status_badge)
        layout.addLayout(title_row)

        # Subtitle
        self._subtitle_label = None
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setStyleSheet(_label(FontSize.SECONDARY, get_theme().TEXT_SECONDARY))
            self._subtitle_label.setWordWrap(True)
            layout.addWidget(self._subtitle_label)

        # Meta
        self._meta_label = None
        if meta:
            self._meta_label = QLabel(meta)
            self._meta_label.setStyleSheet(_label(FontSize.CAPTION, get_theme().TEXT_MUTED))
            layout.addWidget(self._meta_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        if self._subtitle_label:
            self._subtitle_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        if self._meta_label:
            self._meta_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        if self._status_badge:
            self._status_badge.apply_theme()


# ---------------------------------------------------------------------------
# Agent Card
# ---------------------------------------------------------------------------

class AgentCard(QFrame):
    """Agent card showing name, role, and status."""

    def __init__(self, name: str, role: str, status: str = "idle", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        info = QVBoxLayout()
        info.setSpacing(Spacing.XS)
        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(_label(FontSize.BODY, get_theme().TEXT_PRIMARY, "bold"))
        info.addWidget(self._name_label)
        self._role_label = QLabel(role)
        self._role_label.setStyleSheet(_label(FontSize.CAPTION, get_theme().TEXT_SECONDARY))
        info.addWidget(self._role_label)
        layout.addLayout(info, 1)

        status_map = {
            "idle": ("空闲", "muted"),
            "active": ("活跃", "primary"),
            "busy": ("忙碌", "warning"),
        }
        text, stype = status_map.get(status, (status, "muted"))
        self._status_badge = StatusBadge(text, stype)
        layout.addWidget(self._status_badge)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._name_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        self._role_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        if self._status_badge:
            self._status_badge.apply_theme()


# ---------------------------------------------------------------------------
# Task Card
# ---------------------------------------------------------------------------

class TaskCard(QFrame):
    """Task card for kanban boards."""

    def __init__(self, title: str, assignee: str = "", priority: str = "muted", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        self.setFixedHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.SECONDARY, get_theme().TEXT_PRIMARY, "bold"))
        self._title_label.setWordWrap(True)
        layout.addWidget(self._title_label)

        bottom = QHBoxLayout()
        self._assignee_label = None
        if assignee:
            self._assignee_label = QLabel(assignee)
            self._assignee_label.setStyleSheet(_label(FontSize.CAPTION, get_theme().TEXT_MUTED))
            bottom.addWidget(self._assignee_label)
        priority_map = {"高": "error", "中": "warning", "低": "muted", "urgent": "error", "medium": "warning", "low": "muted"}
        status_type = priority_map.get(priority, "muted")
        self._priority_badge = StatusBadge(priority, status_type)
        bottom.addWidget(self._priority_badge)
        bottom.addStretch()
        layout.addLayout(bottom)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._title_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_PRIMARY, "bold"))
        if self._assignee_label:
            self._assignee_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        self._priority_badge.apply_theme()


# ---------------------------------------------------------------------------
# Skill Card
# ---------------------------------------------------------------------------

class SkillCard(QFrame):
    """Skill card with name, description, usage count, and rating."""

    def __init__(
        self,
        name: str,
        description: str = "",
        usage_count: int = 0,
        rating: float = 0.0,
        enabled: bool = True,
        category: str = "",
        tags: list[str] | None = None,
        status_text: str = "",
        status_type: str = "muted",
        risk_note: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        self.setMinimumHeight(156)
        self._skill_name = name
        self._skill_desc = description
        self._skill_usage = usage_count
        self._skill_rating = rating
        self._skill_enabled = enabled
        self._skill_category = category
        self._skill_tags = tags or []
        self._skill_status_text = status_text
        self._skill_status_type = status_type
        self._skill_risk_note = risk_note

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        # Name + status
        top = QHBoxLayout()
        L = get_theme()
        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        top.addWidget(self._name_label, 1)
        self._status_badge = None
        if status_text:
            self._status_badge = StatusBadge(status_text, status_type)
            top.addWidget(self._status_badge)
        layout.addLayout(top)

        # Chips
        self._chip_labels: list[QLabel] = []
        if category or tags:
            chips = QHBoxLayout()
            chips.setSpacing(Spacing.XS)
            if category:
                cat_lbl = QLabel(category)
                cat_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY}; "
                    f"background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; "
                    f"padding: 1px 6px; font-weight: 600;"
                )
                self._chip_labels.append(cat_lbl)
                chips.addWidget(cat_lbl)
            for tag in self._skill_tags[:2]:
                tag_lbl = QLabel(tag)
                tag_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY}; "
                    f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                    f"border-radius: {Radius.BAR}px; padding: 1px 6px;"
                )
                self._chip_labels.append(tag_lbl)
                chips.addWidget(tag_lbl)
            chips.addStretch()
            layout.addLayout(chips)

        # Description
        self._desc_label = QLabel(description)
        self._desc_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

        # Meta row
        meta = QHBoxLayout()
        self._usage_label = QLabel(f"调用 {usage_count} 次")
        self._usage_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(self._usage_label)
        self._rating_label = QLabel(f"★ {rating:.1f}")
        self._rating_label.setStyleSheet(_label(FontSize.CAPTION, L.WARNING))
        meta.addWidget(self._rating_label)
        self._state_label = QLabel("Mock" if enabled else "Preview")
        self._state_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(self._state_label)
        meta.addStretch()
        layout.addLayout(meta)

        self._risk_label = None
        if risk_note:
            self._risk_label = QLabel(f"边界：{risk_note}")
            self._risk_label.setWordWrap(True)
            self._risk_label.setStyleSheet(_label(FontSize.MICRO, L.TEXT_MUTED))
            layout.addWidget(self._risk_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._name_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        if self._status_badge:
            self._status_badge.apply_theme()
        if self._chip_labels:
            for lbl in self._chip_labels:
                if lbl.text() == self._skill_category:
                    lbl.setStyleSheet(
                        f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY}; "
                        f"background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; "
                        f"padding: 1px 6px; font-weight: 600;"
                    )
                else:
                    lbl.setStyleSheet(
                        f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY}; "
                        f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                        f"border-radius: {Radius.BAR}px; padding: 1px 6px;"
                    )
        self._desc_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        self._usage_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        self._rating_label.setStyleSheet(_label(FontSize.CAPTION, L.WARNING))
        self._state_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        if self._risk_label:
            self._risk_label.setStyleSheet(_label(FontSize.MICRO, L.TEXT_MUTED))


# ---------------------------------------------------------------------------
# Literature Card
# ---------------------------------------------------------------------------

class LiteratureCard(QFrame):
    """Literature entry card."""

    def __init__(self, title: str, authors: str = "", year: str = "",
                 source: str = "", status_type: str = "muted", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        L = get_theme()
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        self._title_label.setWordWrap(True)
        layout.addWidget(self._title_label)

        meta = QHBoxLayout()
        self._author_label = QLabel(authors)
        self._author_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        meta.addWidget(self._author_label, 2)
        self._year_label = QLabel(year)
        self._year_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(self._year_label)
        self._source_label = QLabel(source)
        self._source_label.setStyleSheet(_label(FontSize.CAPTION, L.PRIMARY))
        meta.addWidget(self._source_label)
        meta.addStretch()
        layout.addLayout(meta)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._title_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        self._author_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        self._year_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        self._source_label.setStyleSheet(_label(FontSize.CAPTION, L.PRIMARY))


# ---------------------------------------------------------------------------
# Version Card
# ---------------------------------------------------------------------------

class VersionCard(QFrame):
    """Version history entry card."""

    def __init__(self, version: str, description: str = "", author: str = "",
                 time_str: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.SM)

        L = get_theme()
        self._version_label = QLabel(version)
        self._version_label.setStyleSheet(
            f"color: {L.TEXT_ON_PRIMARY}; background-color: {L.PRIMARY}; "
            f"border-radius: {Radius.PILL}px; padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold;"
        )
        self._version_label.setFixedWidth(50)
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._version_label)

        info = QVBoxLayout()
        info.setSpacing(Spacing.XS)
        self._desc_label = QLabel(description)
        self._desc_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        info.addWidget(self._desc_label)
        self._meta_label = QLabel(f"{author}  ·  {time_str}")
        self._meta_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        info.addWidget(self._meta_label)
        layout.addLayout(info, 1)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._version_label.setStyleSheet(
            f"color: {L.TEXT_ON_PRIMARY}; background-color: {L.PRIMARY}; "
            f"border-radius: {Radius.PILL}px; padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold;"
        )
        self._desc_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        self._meta_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))


# ---------------------------------------------------------------------------
# Evidence Card
# ---------------------------------------------------------------------------

class EvidenceCard(QFrame):
    """Evidence/review annotation card."""

    def __init__(self, text: str, source: str = "", confidence: str = "muted", parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        L = get_theme()
        self._text_label = QLabel(text)
        self._text_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY))
        self._text_label.setWordWrap(True)
        layout.addWidget(self._text_label)

        bottom = QHBoxLayout()
        self._source_label = QLabel(source)
        self._source_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        bottom.addWidget(self._source_label)
        self._confidence_badge = StatusBadge(confidence, confidence)
        bottom.addWidget(self._confidence_badge)
        bottom.addStretch()
        layout.addLayout(bottom)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._text_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY))
        self._source_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        self._confidence_badge.apply_theme()


# ---------------------------------------------------------------------------
# Log Console
# ---------------------------------------------------------------------------

class LogConsole(QFrame):
    """Styled log/console output area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_card_style())
        from PyQt6.QtWidgets import QTextEdit
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        self._mono = "Menlo" if __import__('sys').platform == "darwin" else "Consolas"
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._apply_text_style()
        layout.addWidget(self._text)

    def _apply_text_style(self) -> None:
        L = get_theme()
        self._text.setStyleSheet(
            f"QTextEdit {{ "
            f"background-color: {L.SURFACE_ALT}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; "
            f"padding: {Spacing.SM}px; "
            f"font-family: '{self._mono}', monospace; "
            f"font-size: {FontSize.SMALL}px; "
            f"color: {L.TEXT_PRIMARY}; "
            f"}}"
        )

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._apply_text_style()

    def append(self, text: str) -> None:
        self._text.append(text)

    def clear(self) -> None:
        self._text.clear()


# ---------------------------------------------------------------------------
# Empty State
# ---------------------------------------------------------------------------

class EmptyState(QWidget):
    """Empty state placeholder with icon, title, and description."""

    def __init__(self, icon: str, title: str, description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        L = get_theme()
        i = QLabel(icon)
        i.setStyleSheet(f"font-size: 48px;")
        i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(i)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        self._desc_label = None
        if description:
            self._desc_label = QLabel(description)
            self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._desc_label.setWordWrap(True)
            layout.addWidget(self._desc_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        if self._desc_label:
            self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))


# ---------------------------------------------------------------------------
# Loading State
# ---------------------------------------------------------------------------

class LoadingState(QWidget):
    """Loading state placeholder."""

    def __init__(self, message: str = "加载中...", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from PyQt6.QtWidgets import QProgressBar
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setFixedWidth(200)
        layout.addWidget(self._bar)

        L = get_theme()
        self._msg_label = QLabel(message)
        self._msg_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._msg_label)
        self._apply_bar_style()

    def _apply_bar_style(self) -> None:
        L = get_theme()
        self._bar.setStyleSheet(
            f"QProgressBar {{ border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
            f"background-color: {L.SURFACE_ALT}; text-align: center; font-size: {FontSize.SECONDARY}px; }} "
            f"QProgressBar::chunk {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
        )

    def apply_theme(self) -> None:
        L = get_theme()
        self._msg_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._apply_bar_style()


# ---------------------------------------------------------------------------
# Error State
# ---------------------------------------------------------------------------

class ErrorState(QWidget):
    """Error state placeholder."""

    def __init__(self, title: str = "出错了", description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        i = QLabel("⚠️")
        i.setStyleSheet("font-size: 48px;")
        i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(i)

        L = get_theme()
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.ERROR, "bold"))
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        self._desc_label = None
        if description:
            self._desc_label = QLabel(description)
            self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._desc_label.setWordWrap(True)
            layout.addWidget(self._desc_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self._title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.ERROR, "bold"))
        if self._desc_label:
            self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))


# ---------------------------------------------------------------------------
# Settings Section
# ---------------------------------------------------------------------------

class SettingsSection(QFrame):
    """Settings form section with labeled fields."""

    def __init__(self, title: str, fields: list[tuple], parent=None):
        """fields: list of (label, type, default) where type is 'input'|'combo'|'spin'|'check'."""
        super().__init__(parent)
        self.setStyleSheet(_card_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        L = get_theme()
        self._header = QLabel(title)
        self._header.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        layout.addWidget(self._header)

        self._rows: list[tuple[QLabel, QWidget]] = []
        for label_text, field_type, default in fields:
            row = QHBoxLayout()
            row.setSpacing(Spacing.MD)

            lbl = QLabel(label_text)
            lbl.setFixedWidth(120)
            lbl.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
            row.addWidget(lbl)

            if field_type == "input":
                w = QLineEdit(str(default))
                w.setStyleSheet(_input_style(L))
                row.addWidget(w, 1)
            elif field_type == "combo":
                w = QComboBox()
                w.addItems(default if isinstance(default, list) else [str(default)])
                w.setStyleSheet(_input_style(L))
                row.addWidget(w, 1)
            elif field_type == "spin":
                w = QDoubleSpinBox()
                w.setRange(0, 1000)
                w.setValue(float(default))
                w.setStyleSheet(_input_style(L))
                row.addWidget(w, 1)
            elif field_type == "check":
                w = QCheckBox()
                w.setChecked(bool(default))
                w.setStyleSheet(f"font-size: {FontSize.BODY}px;")
                row.addWidget(w)
                row.addStretch()

            self._rows.append((lbl, w))
            layout.addLayout(row)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._header.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        for lbl, w in self._rows:
            lbl.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
            if isinstance(w, (QLineEdit, QComboBox, QDoubleSpinBox)):
                w.setStyleSheet(_input_style(L))
