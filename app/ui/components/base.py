"""Reusable UI base components for ThesisX workspace pages.

All components use design tokens from design_tokens.py for consistent theming.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QGridLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _card_style() -> str:
    """Standard card frame style."""
    return (
        f"QFrame {{ "
        f"background-color: {L.SURFACE}; "
        f"border: 1px solid {L.BORDER}; "
        f"border-radius: {Radius.PANEL}px; "
        f"}}"
    )


def _input_style() -> str:
    """Standard input style."""
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


def _label(size: int, color: str = "", weight: str = "") -> str:
    """Label style helper."""
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.PAGE_TITLE, L.TEXT_PRIMARY, "bold"))
        layout.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            s.setWordWrap(True)
            layout.addWidget(s)


# ---------------------------------------------------------------------------
# Status Badge
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "primary": (L.PRIMARY, L.PRIMARY_LIGHT),
    "success": (L.SUCCESS, L.SUCCESS_BG),
    "warning": (L.WARNING, L.WARNING_BG),
    "error": (L.ERROR, L.ERROR_BG),
    "muted": (L.TEXT_MUTED, L.SURFACE_ALT),
    "info": (L.PRIMARY, L.PRIMARY_LIGHT),
}


class StatusBadge(QLabel):
    """Pill-shaped status badge with color coding."""

    def __init__(self, text: str, status_type: str = "muted", parent=None):
        super().__init__(text, parent)
        fg, bg = _STATUS_COLORS.get(status_type, _STATUS_COLORS["muted"])
        self.setStyleSheet(
            f"color: {fg}; background-color: {bg}; "
            f"border: 1px solid {fg}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; "
            f"font-weight: bold;"
        )
        self.setFixedWidth(80)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


# ---------------------------------------------------------------------------
# Coming Soon Badge
# ---------------------------------------------------------------------------

class ComingSoonBadge(QLabel):
    """Badge for future features marked as coming soon."""

    def __init__(self, text: str = "Coming Soon", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {L.TEXT_MUTED}; background-color: {L.SURFACE_ALT}; "
            f"border: 1px dashed {L.BORDER}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.CAPTION}px;"
        )
        self.setFixedWidth(90)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


# ---------------------------------------------------------------------------
# Preview Badge
# ---------------------------------------------------------------------------

class PreviewBadge(QLabel):
    """Badge for preview/mock content."""

    def __init__(self, text: str = "Preview", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color: {L.WARNING}; background-color: {L.WARNING_BG}; "
            f"border: 1px solid {L.WARNING}; "
            f"border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.CAPTION}px; font-weight: bold;"
        )
        self.setFixedWidth(70)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


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
        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        title_row.addWidget(t, 1)
        if status_text:
            title_row.addWidget(StatusBadge(status_text, status_type))
        layout.addLayout(title_row)

        # Subtitle
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            s.setWordWrap(True)
            layout.addWidget(s)

        # Meta
        if meta:
            m = QLabel(meta)
            m.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
            layout.addWidget(m)


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
        n = QLabel(name)
        n.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        info.addWidget(n)
        r = QLabel(role)
        r.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        info.addWidget(r)
        layout.addLayout(info, 1)

        status_map = {
            "idle": ("空闲", "muted"),
            "active": ("活跃", "primary"),
            "busy": ("忙碌", "warning"),
        }
        text, stype = status_map.get(status, (status, "muted"))
        layout.addWidget(StatusBadge(text, stype))


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

        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_PRIMARY, "bold"))
        t.setWordWrap(True)
        layout.addWidget(t)

        bottom = QHBoxLayout()
        if assignee:
            a = QLabel(assignee)
            a.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
            bottom.addWidget(a)
        bottom.addWidget(StatusBadge(priority, priority))
        bottom.addStretch()
        layout.addLayout(bottom)


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        # Name + status
        top = QHBoxLayout()
        n = QLabel(name)
        n.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        top.addWidget(n, 1)
        if status_text:
            top.addWidget(StatusBadge(status_text, status_type))
        layout.addLayout(top)

        if category or tags:
            chips = QHBoxLayout()
            chips.setSpacing(Spacing.XS)
            if category:
                category_lbl = QLabel(category)
                category_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY}; "
                    f"background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; "
                    f"padding: 1px 6px; font-weight: 600;"
                )
                chips.addWidget(category_lbl)
            for tag in (tags or [])[:2]:
                tag_lbl = QLabel(tag)
                tag_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY}; "
                    f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                    f"border-radius: {Radius.BAR}px; padding: 1px 6px;"
                )
                chips.addWidget(tag_lbl)
            chips.addStretch()
            layout.addLayout(chips)

        # Description
        d = QLabel(description)
        d.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        d.setWordWrap(True)
        layout.addWidget(d)

        # Meta row
        meta = QHBoxLayout()
        u = QLabel(f"调用 {usage_count} 次")
        u.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(u)
        r = QLabel(f"★ {rating:.1f}")
        r.setStyleSheet(_label(FontSize.CAPTION, L.WARNING))
        meta.addWidget(r)
        state = QLabel("Mock" if enabled else "Preview")
        state.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(state)
        meta.addStretch()
        layout.addLayout(meta)

        if risk_note:
            risk = QLabel(f"边界：{risk_note}")
            risk.setWordWrap(True)
            risk.setStyleSheet(_label(FontSize.MICRO, L.TEXT_MUTED))
            layout.addWidget(risk)


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

        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        t.setWordWrap(True)
        layout.addWidget(t)

        meta = QHBoxLayout()
        a = QLabel(authors)
        a.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        meta.addWidget(a, 2)
        y = QLabel(year)
        y.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        meta.addWidget(y)
        s = QLabel(source)
        s.setStyleSheet(_label(FontSize.CAPTION, L.PRIMARY))
        meta.addWidget(s)
        meta.addStretch()
        layout.addLayout(meta)


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

        v = QLabel(version)
        v.setStyleSheet(
            f"color: {L.TEXT_ON_PRIMARY}; background-color: {L.PRIMARY}; "
            f"border-radius: {Radius.PILL}px; padding: 2px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold;"
        )
        v.setFixedWidth(50)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(v)

        info = QVBoxLayout()
        info.setSpacing(Spacing.XS)
        d = QLabel(description)
        d.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY, "bold"))
        info.addWidget(d)
        m = QLabel(f"{author}  ·  {time_str}")
        m.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        info.addWidget(m)
        layout.addLayout(info, 1)


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

        t = QLabel(text)
        t.setStyleSheet(_label(FontSize.BODY, L.TEXT_PRIMARY))
        t.setWordWrap(True)
        layout.addWidget(t)

        bottom = QHBoxLayout()
        s = QLabel(source)
        s.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_MUTED))
        bottom.addWidget(s)
        bottom.addWidget(StatusBadge(confidence, confidence))
        bottom.addStretch()
        layout.addLayout(bottom)


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

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        mono = "Menlo" if __import__('sys').platform == "darwin" else "Consolas"
        self._text.setStyleSheet(
            f"QTextEdit {{ "
            f"background-color: {L.SURFACE_ALT}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; "
            f"padding: {Spacing.SM}px; "
            f"font-family: '{mono}', monospace; "
            f"font-size: {FontSize.SMALL}px; "
            f"color: {L.TEXT_PRIMARY}; "
            f"}}"
        )
        layout.addWidget(self._text)

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

        i = QLabel(icon)
        i.setStyleSheet(f"font-size: 48px;")
        i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(i)

        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(t)

        if description:
            d = QLabel(description)
            d.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            d.setWordWrap(True)
            layout.addWidget(d)


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
        bar = QProgressBar()
        bar.setRange(0, 0)  # Indeterminate
        bar.setFixedWidth(200)
        bar.setStyleSheet(
            f"QProgressBar {{ border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
            f"background-color: {L.SURFACE_ALT}; text-align: center; font-size: {FontSize.SECONDARY}px; }} "
            f"QProgressBar::chunk {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
        )
        layout.addWidget(bar)

        m = QLabel(message)
        m.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        m.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(m)


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

        t = QLabel(title)
        t.setStyleSheet(_label(FontSize.CARD_TITLE, L.ERROR, "bold"))
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(t)

        if description:
            d = QLabel(description)
            d.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
            d.setAlignment(Qt.AlignmentFlag.AlignCenter)
            d.setWordWrap(True)
            layout.addWidget(d)


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

        header = QLabel(title)
        header.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        layout.addWidget(header)

        for label_text, field_type, default in fields:
            row = QHBoxLayout()
            row.setSpacing(Spacing.MD)

            lbl = QLabel(label_text)
            lbl.setFixedWidth(120)
            lbl.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
            row.addWidget(lbl)

            if field_type == "input":
                w = QLineEdit(str(default))
                w.setStyleSheet(_input_style())
                row.addWidget(w, 1)
            elif field_type == "combo":
                w = QComboBox()
                w.addItems(default if isinstance(default, list) else [str(default)])
                w.setStyleSheet(_input_style())
                row.addWidget(w, 1)
            elif field_type == "spin":
                w = QDoubleSpinBox()
                w.setRange(0, 1000)
                w.setValue(float(default))
                w.setStyleSheet(_input_style())
                row.addWidget(w, 1)
            elif field_type == "check":
                w = QCheckBox()
                w.setChecked(bool(default))
                w.setStyleSheet(f"font-size: {FontSize.BODY}px;")
                row.addWidget(w)
                row.addStretch()

            layout.addLayout(row)
