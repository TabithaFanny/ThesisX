"""Workspace Home page — aligned with page_01_workspace_home.svg.

SVG layout:
- Greeting "晚上好，张同学"
- Search bar (mock)
- 3 progress cards with progress bars
- Recent edits (left) + Todo with circle checkboxes (right)
- Quick actions kept as secondary footer (AI初稿助手 entry preserved)
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QGridLayout,
    QScrollArea, QFrame, QPushButton,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import _card_style
from app.ui.mock.workspace_data import MOCK_TODO_ITEMS


class _HomeData:
    """Lazy-loaded home page data."""

    def __init__(self):
        self._runs: list = []
        self._health_summary: dict = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        try:
            from app.core.pipeline.run_history import RunHistoryReader
            from app.core.providers.detector import generate_provider_health_report

            reader = RunHistoryReader()
            self._runs = reader.list_runs(limit=20)
            report = generate_provider_health_report()
            self._health_summary = {
                "total": len(self._runs),
                "completed": sum(1 for r in self._runs if r.status == "completed"),
                "with_paper": sum(1 for r in self._runs if r.has_paper),
                "mock": sum(1 for r in self._runs if r.run_mode == "mock"),
                "real": sum(1 for r in self._runs if r.run_mode in ("real", "dry_run")),
                "health_ok": report.overall_ok,
            }
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to load runs or health report", exc_info=True)
            self._runs = []
            self._health_summary = {"total": 0, "completed": 0, "with_paper": 0}
        self._loaded = True

    @property
    def runs(self) -> list:
        return self._runs

    @property
    def summary(self) -> dict:
        return self._health_summary


_data = _HomeData()



class WorkspaceHomePage(QWidget):
    """Workspace home with greeting, search, progress cards, recent files, todo."""

    navigate_to = pyqtSignal(str)  # emits page_id for navigation
    open_paper_draft = pyqtSignal()  # open AI paper draft dialog

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        _data.load()
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet(f"background-color: {L.CANVAS};")
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # --- Greeting (SVG: "晚上好，张同学" at 18px bold) ---
        self._greeting = QLabel("晚上好，张同学")
        self._greeting.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(self._greeting)

        # --- Search bar (SVG: 250x12 rounded placeholder) ---
        self._search_bar = QFrame()
        self._search_bar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.PILL}px; padding: {Spacing.SM}px {Spacing.MD}px; }}"
        )
        self._search_bar.setFixedHeight(36)
        search_row = QHBoxLayout(self._search_bar)
        search_row.setContentsMargins(Spacing.SM, 0, Spacing.SM, 0)
        self._search_lbl = QLabel("搜索论文、文献、技能...")
        self._search_lbl.setStyleSheet(f"color: {L.TEXT_MUTED}; font-size: {FontSize.BODY}px;")
        search_row.addWidget(self._search_lbl)
        layout.addWidget(self._search_bar)

        # --- Progress cards (real data from runs) ---
        summary = _data.summary
        self._progress_cards = self._build_progress_cards(summary)
        grid = QGridLayout()
        grid.setSpacing(Spacing.MD)
        for i, card in enumerate(self._progress_cards):
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)

        # --- Bottom section: Recent runs (left) + Todo (right) ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(Spacing.MD)

        # Left: Recent runs from history
        self._recent_card = QFrame()
        self._recent_card.setStyleSheet(_card_style())
        recent_layout = QVBoxLayout(self._recent_card)
        recent_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        recent_layout.setSpacing(Spacing.SM)

        self._recent_title = QLabel("最近运行")
        self._recent_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        recent_layout.addWidget(self._recent_title)

        self._recent_run_data: list = []
        runs = _data.runs[:5]
        if runs:
            for run in runs:
                run_row = QHBoxLayout()
                run_row.setSpacing(Spacing.SM)
                # Status dot
                dot = QLabel("●")
                color = L.SUCCESS if run.has_paper else L.WARNING
                dot.setStyleSheet(f"color: {color}; font-size: {FontSize.BODY}px;")
                run_row.addWidget(dot)
                # Topic truncated
                topic = (run.topic or "?")[:28]
                topic_lbl = QLabel(topic)
                topic_lbl.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
                )
                run_row.addWidget(topic_lbl, 1)
                # Mode badge
                mode_lbl = QLabel(run.run_mode or "-")
                mode_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
                )
                run_row.addWidget(mode_lbl)
                recent_layout.addLayout(run_row)
                self._recent_run_data.append((dot, topic_lbl, mode_lbl, run))
        else:
            self._recent_empty_lbl = QLabel("暂无运行记录")
            self._recent_empty_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
            )
            recent_layout.addWidget(self._recent_empty_lbl)
        recent_layout.addStretch()
        bottom_row.addWidget(self._recent_card)

        # Right: Todo with circle checkboxes (SVG: empty circle r=5, stroke #D7E3F5)
        self._todo_card = QFrame()
        self._todo_card.setStyleSheet(_card_style())
        todo_layout = QVBoxLayout(self._todo_card)
        todo_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        todo_layout.setSpacing(Spacing.SM)

        self._todo_title = QLabel("待办事项")
        self._todo_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        todo_layout.addWidget(self._todo_title)

        self._todo_items: list[tuple[QLabel, QLabel]] = []
        for item in MOCK_TODO_ITEMS:
            row = QHBoxLayout()
            row.setSpacing(Spacing.SM)
            # Circle checkbox (SVG: empty circle, r=5, stroke #D7E3F5)
            checkbox = QLabel("○")
            checkbox.setFixedWidth(16)
            checkbox.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.BORDER}; "
                f"border: 1.5px solid {L.BORDER}; border-radius: 8px; "
                f"qproperty-alignment: AlignCenter;"
            )
            row.addWidget(checkbox)
            lbl = QLabel(item["text"])
            lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
            row.addWidget(lbl, 1)
            self._todo_items.append((checkbox, lbl))
            todo_layout.addLayout(row)
        todo_layout.addStretch()
        bottom_row.addWidget(self._todo_card)

        layout.addLayout(bottom_row)

        # --- Secondary: Quick actions (not in SVG, but preserve AI初稿助手 entry) ---
        self._actions_frame = QFrame()
        self._actions_frame.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px dashed {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        actions_layout = QHBoxLayout(self._actions_frame)
        actions_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        actions_layout.setSpacing(Spacing.SM)

        self._actions_hint = QLabel("快捷操作：")
        self._actions_hint.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};")
        actions_layout.addWidget(self._actions_hint)

        self._ai_btn = QPushButton("AI 初稿助手")
        self._ai_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._ai_btn.clicked.connect(self._open_paper_draft)
        actions_layout.addWidget(self._ai_btn)

        self._action_btns: list[QPushButton] = []
        _actions = [
            ("新建论文", self.open_paper_draft.emit),
            ("导入文献", lambda: self.navigate_to.emit("literature")),
            ("知识库", lambda: self.navigate_to.emit("knowledge")),
        ]
        for text, handler in _actions:
            btn = QPushButton(text)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {L.SURFACE}; color: {L.TEXT_SECONDARY}; "
                f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
                f"padding: {Spacing.XS}px {Spacing.MD}px; "
                f"font-size: {FontSize.SECONDARY}px; }} "
                f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; }}"
            )
            btn.clicked.connect(handler)
            self._action_btns.append(btn)
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(self._actions_frame)

        layout.addStretch()
        self._scroll.setWidget(self._content_widget)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._scroll)

    # ── theme ─────────────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        """Re-apply all widget styles using current theme tokens."""
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._content_widget.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )
        self._greeting.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        self._search_bar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.PILL}px; padding: {Spacing.SM}px {Spacing.MD}px; }}"
        )
        self._search_lbl.setStyleSheet(
            f"color: {L.TEXT_MUTED}; font-size: {FontSize.BODY}px;"
        )
        # Progress cards
        for card in self._progress_cards:
            card.setStyleSheet(_card_style())
            if hasattr(card, '_pc_title_lbl'):
                card._pc_title_lbl.setStyleSheet(
                    f"font-size: {FontSize.CAPTION}px; font-weight: 600; color: {L.TEXT_PRIMARY};"
                )
            if hasattr(card, '_pc_bar_bg'):
                card._pc_bar_bg.setStyleSheet(
                    f"QFrame {{ background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; }}"
                )
            if hasattr(card, '_pc_bar_fill'):
                card._pc_bar_fill.setStyleSheet(
                    f"QFrame {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
                )
            if hasattr(card, '_pc_pct_lbl'):
                card._pc_pct_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
                )
        # Recent runs card
        self._recent_card.setStyleSheet(_card_style())
        self._recent_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        for dot, topic_lbl, mode_lbl, run in self._recent_run_data:
            color = L.SUCCESS if run.has_paper else L.WARNING
            dot.setStyleSheet(f"color: {color}; font-size: {FontSize.BODY}px;")
            topic_lbl.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
            )
            mode_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
            )
        if getattr(self, '_recent_empty_lbl', None):
            self._recent_empty_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
            )
        # Todo card
        self._todo_card.setStyleSheet(_card_style())
        self._todo_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        for checkbox, lbl in self._todo_items:
            checkbox.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.BORDER}; "
                f"border: 1.5px solid {L.BORDER}; border-radius: 8px; "
                f"qproperty-alignment: AlignCenter;"
            )
            lbl.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};"
            )
        # Quick actions
        self._actions_frame.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px dashed {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._actions_hint.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._ai_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        for btn in self._action_btns:
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {L.SURFACE}; color: {L.TEXT_SECONDARY}; "
                f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
                f"padding: {Spacing.XS}px {Spacing.MD}px; "
                f"font-size: {FontSize.SECONDARY}px; }} "
                f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; }}"
            )

    def _build_progress_cards(self, summary: dict) -> list[QFrame]:
        total = summary.get("total", 0)
        completed = summary.get("completed", 0)
        with_paper = summary.get("with_paper", 0)
        mock = summary.get("mock", 0)
        real = summary.get("real", 0)

        # Derive percentages: completed/total, papers/total, mock ratio
        pct_complete = int(100 * completed / total) if total > 0 else 0
        pct_paper = int(100 * with_paper / total) if total > 0 else 0
        pct_mock = int(100 * mock / total) if total > 0 else 50

        return [
            self._create_progress_card("完成率", pct_complete),
            self._create_progress_card("已生成论文", pct_paper),
            self._create_progress_card("Mock / Real", pct_mock),
        ]

    def _create_progress_card(self, title: str, percent: int) -> QFrame:
        """Create a progress card matching SVG: white card, title, progress bar."""
        L = get_theme()
        card = QFrame()
        card.setFixedHeight(76)
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        # Title (SVG: 11px/600)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: {FontSize.CAPTION}px; font-weight: 600; color: {L.TEXT_PRIMARY};"
        )
        card._pc_title_lbl = title_lbl
        layout.addWidget(title_lbl)

        # Progress bar (SVG: 6px tall, track #EEF5FF, fill #2563EB, rx=3)
        bar_bg = QFrame()
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet(
            f"QFrame {{ background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; }}"
        )
        card._pc_bar_bg = bar_bg
        bar_fill = QFrame(bar_bg)
        fill_width = max(2, int(92 * percent / 100))  # SVG bar width ~92px
        bar_fill.setFixedHeight(6)
        bar_fill.setFixedWidth(fill_width)
        bar_fill.setStyleSheet(
            f"QFrame {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
        )
        card._pc_bar_fill = bar_fill
        layout.addWidget(bar_bg)

        # Percentage label
        pct_lbl = QLabel(f"{percent}%")
        pct_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        card._pc_pct_lbl = pct_lbl
        layout.addWidget(pct_lbl)

        return card

    def _open_paper_draft(self):
        """Open AI paper draft dialog via parent chain."""
        window = self.window()
        if hasattr(window, "_show_agent_paper_dialog"):
            window._show_agent_paper_dialog()
