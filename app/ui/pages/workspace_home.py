"""Workspace Home page — aligned with page_01_workspace_home.svg.

SVG layout:
- Greeting "晚上好，张同学"
- Search bar (mock)
- 3 progress cards with progress bars
- Recent edits (left) + Todo with circle checkboxes (right)
- Quick actions kept as secondary footer (AI初稿助手 entry preserved)
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QGridLayout,
    QScrollArea, QFrame, QPushButton,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
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

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        _data.load()
        self._init_ui()

    def _init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        # --- Greeting (SVG: "晚上好，张同学" at 18px bold) ---
        greeting = QLabel("晚上好，张同学")
        greeting.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(greeting)

        # --- Search bar (SVG: 250x12 rounded placeholder) ---
        search_bar = QFrame()
        search_bar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.PILL}px; padding: {Spacing.SM}px {Spacing.MD}px; }}"
        )
        search_bar.setFixedHeight(36)
        search_row = QHBoxLayout(search_bar)
        search_row.setContentsMargins(Spacing.SM, 0, Spacing.SM, 0)
        search_lbl = QLabel("搜索论文、文献、技能...")
        search_lbl.setStyleSheet(f"color: {L.TEXT_MUTED}; font-size: {FontSize.BODY}px;")
        search_row.addWidget(search_lbl)
        layout.addWidget(search_bar)

        # --- Progress cards (real data from runs) ---
        summary = _data.summary
        cards = self._build_progress_cards(summary)
        grid = QGridLayout()
        grid.setSpacing(Spacing.MD)
        for i, card in enumerate(cards):
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)

        # --- Bottom section: Recent runs (left) + Todo (right) ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(Spacing.MD)

        # Left: Recent runs from history
        recent_card = QFrame()
        recent_card.setStyleSheet(_card_style())
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        recent_layout.setSpacing(Spacing.SM)

        recent_title = QLabel("最近运行")
        recent_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        recent_layout.addWidget(recent_title)

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
        else:
            empty_lbl = QLabel("暂无运行记录")
            empty_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
            )
            recent_layout.addWidget(empty_lbl)
        recent_layout.addStretch()
        bottom_row.addWidget(recent_card)

        # Right: Todo with circle checkboxes (SVG: empty circle r=5, stroke #D7E3F5)
        todo_card = QFrame()
        todo_card.setStyleSheet(_card_style())
        todo_layout = QVBoxLayout(todo_card)
        todo_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        todo_layout.setSpacing(Spacing.SM)

        todo_title = QLabel("待办事项")
        todo_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        todo_layout.addWidget(todo_title)

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
            todo_layout.addLayout(row)
        todo_layout.addStretch()
        bottom_row.addWidget(todo_card)

        layout.addLayout(bottom_row)

        # --- Secondary: Quick actions (not in SVG, but preserve AI初稿助手 entry) ---
        actions_frame = QFrame()
        actions_frame.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px dashed {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        actions_layout.setSpacing(Spacing.SM)

        hint = QLabel("快捷操作：")
        hint.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};")
        actions_layout.addWidget(hint)

        ai_btn = QPushButton("AI 初稿助手")
        ai_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        ai_btn.clicked.connect(self._open_paper_draft)
        actions_layout.addWidget(ai_btn)

        for text in ["新建论文", "导入文献", "数据图表"]:
            btn = QPushButton(text)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {L.SURFACE}; color: {L.TEXT_SECONDARY}; "
                f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
                f"padding: {Spacing.XS}px {Spacing.MD}px; "
                f"font-size: {FontSize.SECONDARY}px; }} "
                f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; }}"
            )
            actions_layout.addWidget(btn)
        actions_layout.addStretch()
        layout.addWidget(actions_frame)

        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

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
        layout.addWidget(title_lbl)

        # Progress bar (SVG: 6px tall, track #EEF5FF, fill #2563EB, rx=3)
        bar_bg = QFrame()
        bar_bg.setFixedHeight(6)
        bar_bg.setStyleSheet(
            f"QFrame {{ background-color: {L.PRIMARY_LIGHT}; border-radius: {Radius.BAR}px; }}"
        )
        bar_fill = QFrame(bar_bg)
        fill_width = max(2, int(92 * percent / 100))  # SVG bar width ~92px
        bar_fill.setFixedHeight(6)
        bar_fill.setFixedWidth(fill_width)
        bar_fill.setStyleSheet(
            f"QFrame {{ background-color: {L.PRIMARY}; border-radius: {Radius.BAR}px; }}"
        )
        layout.addWidget(bar_bg)

        # Percentage label
        pct_lbl = QLabel(f"{percent}%")
        pct_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(pct_lbl)

        return card

    def _open_paper_draft(self):
        """Open AI paper draft dialog via parent chain."""
        window = self.window()
        if hasattr(window, "_show_agent_paper_dialog"):
            window._show_agent_paper_dialog()
