"""Run History page — read-only view of all ThesisX local runs.

Three-panel layout:
- Left (220px): run list from RunHistoryReader.list_runs()
- Middle (flex): paper.md preview (QTextEdit read-only)
- Right (260px): metadata + diagnostics from RunDiagnostics
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.base import PageHeader, StatusBadge, _card_style
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


class RunHistoryPage(QWidget):
    """Read-only run history browser."""

    # Signal emitted when user wants to open paper in editor, carries markdown content
    open_in_editor = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._runs: list = []  # list of RunSummary
        self._active_id: str | None = None
        self._current_paper_path: str | None = None
        self._init_ui()
        self._load_runs()
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
        root = QVBoxLayout(self._content_widget)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        self._header = PageHeader(
            "运行历史",
            "ThesisX 本地运行记录。只读视图，不修改任何文件。",
        )
        root.addWidget(self._header)

        # Three-column layout
        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)
        cols.addWidget(self._create_list_panel(), 0)
        cols.addWidget(self._create_preview_panel(), 1)
        cols.addWidget(self._create_info_panel(), 0)
        root.addLayout(cols, 1)

        self._scroll.setWidget(self._content_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll)

    def _create_list_panel(self) -> QFrame:
        L = get_theme()
        self._list_panel = QFrame()
        self._list_panel.setFixedWidth(240)
        self._list_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(self._list_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        self._list_title_label = QLabel("运行记录")
        self._list_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._list_title_label)

        self._run_list_container = QVBoxLayout()
        self._run_list_container.setSpacing(Spacing.XS)
        layout.addLayout(self._run_list_container)

        self._empty_label = QLabel("暂无运行记录")
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._empty_label)

        layout.addStretch()
        return self._list_panel

    def _create_preview_panel(self) -> QFrame:
        L = get_theme()
        self._preview_panel = QFrame()
        self._preview_panel.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._preview_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        top_row = QHBoxLayout()
        self._preview_title = QLabel("选择一条记录查看")
        self._preview_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        top_row.addWidget(self._preview_title)
        top_row.addStretch()
        self._preview_badge = StatusBadge("等待选择", "neutral")
        top_row.addWidget(self._preview_badge)
        self._preview_top_row = top_row
        layout.addLayout(top_row)

        self._preview_area = QTextEdit()
        self._preview_area.setReadOnly(True)
        self._preview_area.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; border-radius: {Radius.PANEL}px; "
            f"padding: {Spacing.MD}px; font-size: {FontSize.BODY}px; }}"
        )
        layout.addWidget(self._preview_area, 1)

        # Action row: Open in Editor button
        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(Spacing.SM)
        self._action_row.addStretch()
        self._open_editor_btn = QPushButton("\U0001f4dd 打开到编辑器")
        self._open_editor_btn.setEnabled(False)
        self._open_editor_btn.setFixedHeight(28)
        self._open_editor_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: 0 {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: 600; }} "
            f"QPushButton:disabled {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
            f"border: 1px dashed {L.BORDER}; }} "
            f"QPushButton:hover:enabled {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._open_editor_btn.clicked.connect(self._on_open_editor)
        self._action_row.addWidget(self._open_editor_btn)
        layout.addLayout(self._action_row)
        return self._preview_panel

    def _create_info_panel(self) -> QFrame:
        L = get_theme()
        self._info_panel = QFrame()
        self._info_panel.setFixedWidth(280)
        self._info_panel.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._info_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title_row = QHBoxLayout()
        self._info_title_label = QLabel("运行详情")
        self._info_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        title_row.addWidget(self._info_title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Tabbed interface: Info | Events | Messages | 诊断
        self._info_tabs = QTabWidget()
        self._info_tabs.setStyleSheet(f"QTabWidget {{ border: none; }}")
        self._info_tabs.addTab(self._make_info_tab(), "基本信息")
        self._info_tabs.addTab(self._make_events_tab(), "Events")
        self._info_tabs.addTab(self._make_messages_tab(), "Messages")
        self._info_tabs.addTab(self._make_diagnostics_tab(), "诊断报告")
        layout.addWidget(self._info_tabs, 1)

        return self._info_panel

    def _make_info_tab(self) -> QWidget:
        L = get_theme()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, Spacing.SM, 0, 0)
        layout.setSpacing(Spacing.XS)
        self._info_container = QVBoxLayout()
        self._info_container.setSpacing(Spacing.XS)
        layout.addLayout(self._info_container)
        self._info_empty = QLabel("选择一条记录查看")
        self._info_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._info_empty)
        layout.addStretch()
        return w

    def _make_events_tab(self) -> QWidget:
        L = get_theme()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, Spacing.SM, 0, 0)
        layout.setSpacing(Spacing.XS)
        self._events_area = QScrollArea()
        self._events_area.setWidgetResizable(True)
        self._events_area.setFrameShape(QFrame.Shape.NoFrame)
        self._events_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._events_content = QWidget()
        self._events_content.setStyleSheet("background: transparent;")
        self._events_layout = QVBoxLayout(self._events_content)
        self._events_layout.setSpacing(Spacing.XS)
        self._events_area.setWidget(self._events_content)
        layout.addWidget(self._events_area)
        self._events_empty = QLabel("无 Events 记录")
        self._events_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._events_empty)
        return w

    def _make_messages_tab(self) -> QWidget:
        L = get_theme()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, Spacing.SM, 0, 0)
        layout.setSpacing(Spacing.XS)
        self._messages_area = QScrollArea()
        self._messages_area.setWidgetResizable(True)
        self._messages_area.setFrameShape(QFrame.Shape.NoFrame)
        self._messages_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._messages_content = QWidget()
        self._messages_content.setStyleSheet("background: transparent;")
        self._messages_layout = QVBoxLayout(self._messages_content)
        self._messages_layout.setSpacing(Spacing.XS)
        self._messages_area.setWidget(self._messages_content)
        layout.addWidget(self._messages_area)
        self._messages_empty = QLabel("无 Messages 记录")
        self._messages_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._messages_empty)
        return w

    def _make_diagnostics_tab(self) -> QWidget:
        L = get_theme()
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, Spacing.SM, 0, 0)
        layout.setSpacing(Spacing.XS)
        self._diagnostics_area = QScrollArea()
        self._diagnostics_area.setWidgetResizable(True)
        self._diagnostics_area.setFrameShape(QFrame.Shape.NoFrame)
        self._diagnostics_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._diagnostics_content = QWidget()
        self._diagnostics_content.setStyleSheet("background: transparent;")
        self._diagnostics_layout = QVBoxLayout(self._diagnostics_content)
        self._diagnostics_layout.setSpacing(Spacing.XS)
        self._diagnostics_area.setWidget(self._diagnostics_content)
        layout.addWidget(self._diagnostics_area)
        self._diagnostics_empty = QLabel("选择一条记录查看诊断")
        self._diagnostics_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._diagnostics_empty)
        return w

    def _load_runs(self) -> None:
        from app.core.pipeline.run_history import RunHistoryReader

        try:
            reader = RunHistoryReader()
            self._runs = reader.list_runs(limit=50)
        except Exception as e:
            self._runs = []

        # Clear existing list items
        while self._run_list_container.count():
            child = self._run_list_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._runs:
            self._empty_label.setVisible(True)
            self._run_list_container.addWidget(self._empty_label)
            return

        self._empty_label.setVisible(False)

        for summary in self._runs:
            item = self._create_run_item(summary)
            self._run_list_container.addWidget(item)

        self._run_list_container.addStretch()

    def _create_run_item(self, summary) -> QFrame:
        L = get_theme()
        is_active = summary.session_id == self._active_id
        bg = L.PRIMARY_LIGHT if is_active else L.SURFACE
        border = L.PRIMARY_BORDER if is_active else L.BORDER_SUBTLE

        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 1px solid {border}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)

        # Topic
        topic = (summary.topic or "?")[:30]
        topic_lbl = QLabel(topic)
        topic_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
        )
        topic_lbl.setWordWrap(True)
        layout.addWidget(topic_lbl)

        # Meta row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(Spacing.XS)

        status_map = {"completed": "success", "partial": "warning", "unknown": "neutral"}
        badge = StatusBadge(summary.status or "unknown", status_map.get(summary.status, "neutral"))
        meta_row.addWidget(badge)

        mode_lbl = QLabel(summary.run_mode or "-")
        mode_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        meta_row.addWidget(mode_lbl)
        meta_row.addStretch()

        has_paper = QLabel("📄" if summary.has_paper else "")
        has_paper.setStyleSheet(f"font-size: {FontSize.MICRO}px;")
        meta_row.addWidget(has_paper)

        layout.addLayout(meta_row)

        # Session ID + time
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(Spacing.XS)

        sid_lbl = QLabel(summary.session_id[:12])
        sid_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED}; font-family: monospace;"
        )
        bottom_row.addWidget(sid_lbl)
        bottom_row.addStretch()

        time_lbl = QLabel(self._format_time(summary.updated_at or summary.created_at))
        time_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
        )
        bottom_row.addWidget(time_lbl)
        layout.addLayout(bottom_row)

        card.mousePressEvent = lambda e, s=summary.session_id: self._select_run(s)  # type: ignore[method-assign]
        return card

    def _select_run(self, session_id: str) -> None:
        self._active_id = session_id
        from app.core.pipeline.run_history import RunHistoryReader
        from app.core.pipeline.run_diagnostics import RunDiagnostics

        reader = RunHistoryReader()
        diagnostics = RunDiagnostics(reader=reader)

        # Refresh list items
        for i in range(self._run_list_container.count() - 1):
            item = self._run_list_container.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        for summary in self._runs:
            self._run_list_container.insertWidget(i, self._create_run_item(summary))
        self._run_list_container.addStretch()

        detail = reader.get_run(session_id)
        summary = detail.summary

        # Update preview title
        topic = (summary.topic or "?")[:40]
        self._preview_title.setText(topic)

        status_map = {"completed": "success", "partial": "warning", "unknown": "neutral"}
        # Remove old badge and replace with new one
        self._preview_badge.setParent(None)
        self._preview_top_row.removeWidget(self._preview_badge)
        self._preview_badge = StatusBadge(summary.status or "unknown", status_map.get(summary.status, "neutral"))
        self._preview_top_row.addWidget(self._preview_badge)

        # Load paper content
        paper_path = detail.output_files.get("paper_md", "")
        if paper_path and Path(paper_path).exists():
            self._current_paper_path = paper_path
            try:
                content = Path(paper_path).read_text(encoding="utf-8")
                self._preview_area.setPlainText(content)
            except Exception:
                self._preview_area.setPlainText("(无法读取 paper.md)")
            self._open_editor_btn.setEnabled(True)
        else:
            self._current_paper_path = None
            self._open_editor_btn.setEnabled(False)
            outline_path = detail.output_files.get("outline_json", "")
            if outline_path and Path(outline_path).exists():
                self._preview_area.setPlainText("(仅生成到 outline，暂无 paper.md)")
            else:
                self._preview_area.setPlainText("(无输出文件)")

        # Update info panel
        self._refresh_info_panel(detail, diagnostics)

    def _refresh_info_panel(self, detail, diagnostics) -> None:
        L = get_theme()
        summary = detail.summary
        health = detail.health

        # --- Tab 1: Basic Info ---
        while self._info_container.count():
            child = self._info_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._info_empty.setVisible(False)

        fields = [
            ("Session", summary.session_id[:16]),
            ("Topic", summary.topic or "-"),
            ("Journal", summary.journal or "-"),
            ("Mode", summary.run_mode or "-"),
            ("Status", summary.status or "-"),
            ("Has Paper", "Yes" if summary.has_paper else "No"),
            ("Events", str(detail.event_count)),
            ("Messages", str(detail.message_count)),
            ("Health", health.status),
        ]

        for label, value in fields:
            field = self._info_field(label, str(value)[:40])
            self._info_container.addWidget(field)

        if health.notes:
            notes_frame = QFrame()
            notes_frame.setStyleSheet(
                f"QFrame {{ background-color: {L.WARNING_BG}; border: 1px solid {L.WARNING_BORDER}; "
                f"border-radius: {Radius.INPUT}px; }}"
            )
            notes_layout = QVBoxLayout(notes_frame)
            notes_layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
            notes_layout.setSpacing(Spacing.XS)
            notes_title = QLabel("诊断备注")
            notes_title.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.WARNING}; font-weight: 700;"
            )
            notes_layout.addWidget(notes_title)
            for note in health.notes:
                note_lbl = QLabel(f"• {note}")
                note_lbl.setWordWrap(True)
                note_lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
                )
                notes_layout.addWidget(note_lbl)
            self._info_container.addWidget(notes_frame)
        self._info_container.addStretch()

        # --- Tab 2: Events ---
        self._refresh_events_tab(detail)

        # --- Tab 3: Messages ---
        self._refresh_messages_tab(detail)

        # --- Tab 4: Diagnostics ---
        self._refresh_diagnostics_tab(diagnostics)

    def _refresh_events_tab(self, detail) -> None:
        while self._events_layout.count():
            child = self._events_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        events = detail.events
        if not events:
            self._events_empty.setVisible(True)
            self._events_layout.addWidget(self._events_empty)
            return
        self._events_empty.setVisible(False)

        # Show last 50 events
        for ev in events[-50:]:
            ev_frame = self._event_item(ev)
            self._events_layout.addWidget(ev_frame)
        self._events_layout.addStretch()

    def _event_item(self, ev: dict) -> QFrame:
        L = get_theme()
        ev_type = str(ev.get("type", "-"))
        stage = str(ev.get("stage", "-"))
        message = str(ev.get("message", ""))[:80]
        agent = str(ev.get("agent", "") or "")

        color = {
            "state": L.PRIMARY,
            "token": L.TEXT_SECONDARY,
            "message": L.SUCCESS,
            "cost": L.WARNING,
            "artifact": L.PRIMARY_SOFT,
            "error": L.ERROR,
            "completion": L.SUCCESS,
        }.get(ev_type, L.TEXT_MUTED)

        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(Spacing.XS)
        type_lbl = QLabel(f"[{ev_type}]")
        type_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {color}; font-weight: 700;"
        )
        header.addWidget(type_lbl)
        if agent:
            agent_lbl = QLabel(f"@{agent}")
            agent_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
            )
            header.addWidget(agent_lbl)
        if stage and stage != "-":
            stage_lbl = QLabel(stage)
            stage_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.PRIMARY_SOFT};"
            )
            header.addWidget(stage_lbl)
        header.addStretch()
        layout.addLayout(header)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
            )
            layout.addWidget(msg_lbl)

        return frame

    def _refresh_messages_tab(self, detail) -> None:
        while self._messages_layout.count():
            child = self._messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        messages = detail.messages
        if not messages:
            self._messages_empty.setVisible(True)
            self._messages_layout.addWidget(self._messages_empty)
            return
        self._messages_empty.setVisible(False)

        for msg in messages[-30:]:
            msg_frame = self._message_item(msg)
            self._messages_layout.addWidget(msg_frame)
        self._messages_layout.addStretch()

    def _message_item(self, msg: dict) -> QFrame:
        L = get_theme()
        role = str(msg.get("role", "-"))
        content = str(msg.get("content", ""))[:120]

        role_color = {
            "user": L.PRIMARY,
            "assistant": L.SUCCESS,
            "system": L.WARNING,
        }.get(role, L.TEXT_MUTED)

        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(2)

        role_lbl = QLabel(f"{role}:")
        role_lbl.setStyleSheet(
            f"font-size: {FontSize.MICRO}px; color: {role_color}; font-weight: 700;"
        )
        layout.addWidget(role_lbl)

        if content:
            content_lbl = QLabel(content)
            content_lbl.setWordWrap(True)
            content_lbl.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
            )
            layout.addWidget(content_lbl)

        return frame

    def _refresh_diagnostics_tab(self, diagnostics) -> None:
        L = get_theme()
        while self._diagnostics_layout.count():
            child = self._diagnostics_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        report = diagnostics.diagnose_run(self._active_id)
        md_text = diagnostics.render_report_markdown(report)

        # Render simple markdown to QLabel/frames
        lines = md_text.splitlines()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("# "):
                lbl = QLabel(stripped.replace("# ", ""))
                lbl.setStyleSheet(
                    f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; "
                    f"font-weight: 700; margin-top: {Spacing.SM}px;"
                )
            elif stripped.startswith("## "):
                lbl = QLabel(stripped.replace("## ", ""))
                lbl.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.PRIMARY}; font-weight: 700;"
                )
            elif stripped.startswith("-"):
                lbl = QLabel(stripped)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
                )
            elif "```" in stripped:
                lbl = QLabel(stripped)
                lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED}; "
                    f"font-family: monospace;"
                )
            else:
                lbl = QLabel(stripped)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(
                    f"font-size: {FontSize.MICRO}px; color: {L.TEXT_SECONDARY};"
                )
            self._diagnostics_layout.addWidget(lbl)

        self._diagnostics_layout.addStretch()

        self._info_container.addStretch()

    def _info_field(self, label_text: str, value_text: str) -> QFrame:
        L = get_theme()
        field = QFrame()
        field.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; }}"
        )
        layout = QVBoxLayout(field)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(2)

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

    def apply_theme(self) -> None:
        """Re-apply styles using current theme tokens."""
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")
        self._content_widget.setStyleSheet(f"background-color: {L.CANVAS};")
        self._header.apply_theme()

        # List panel
        self._list_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._list_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )

        # Preview panel
        self._preview_panel.setStyleSheet(_card_style(L))
        self._preview_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._preview_badge.apply_theme()
        self._preview_area.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; "
            f"border: 1px solid {L.BORDER_SUBTLE}; border-radius: {Radius.PANEL}px; "
            f"padding: {Spacing.MD}px; font-size: {FontSize.BODY}px; }}"
        )
        self._open_editor_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: 0 {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: 600; }} "
            f"QPushButton:disabled {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_MUTED}; "
            f"border: 1px dashed {L.BORDER}; }} "
            f"QPushButton:hover:enabled {{ background-color: {L.PRIMARY_HOVER}; }}"
        )

        # Info panel
        self._info_panel.setStyleSheet(_card_style(L))
        self._info_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._info_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._events_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._messages_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._diagnostics_empty.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )

        # Re-populate run list and info panel if loaded
        if self._runs:
            self._load_runs()
            if self._active_id:
                # Re-select to refresh info panels
                self._select_run(self._active_id)

    @staticmethod
    def _format_time(iso_time: str) -> str:
        if not iso_time:
            return "-"
        try:
            # ISO format: 2026-05-01T14:30:00 or 2026-05-01T14:30:00+08:00
            if "T" in iso_time:
                date, hm = iso_time.split("T", 1)
                if "+" in hm:
                    hm = hm.split("+")[0]
                elif "-" in hm and len(hm.split("-")[1]) <= 2:
                    hm = hm.split("-")[0]
                return f"{date} {hm[:5]}"
            return iso_time[:16]
        except Exception:
            return iso_time[:16]

    def _on_open_editor(self) -> None:
        """Open the current paper.md in the Main Editor via signal."""
        if not self._current_paper_path:
            return
        try:
            content = Path(self._current_paper_path).read_text(encoding="utf-8")
        except Exception:
            return
        self.open_in_editor.emit(content)
