"""Research Workspace page — Vision 3.0.

Displays project list, research question, and quick actions.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QScrollArea, QLineEdit, QTextEdit,
    QGridLayout, QFrame, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QSizePolicy,
)
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.core.project.service import ProjectService
from app.core.project.models import Project, ResearchQuestion


def _card_style(bg: str | None = None, radius: int = Radius.PANEL, pad: int = Spacing.MD):
    if bg is None:
        bg = get_theme().SURFACE
    return f"""
        QFrame {{
            background-color: {bg};
            border-radius: {radius}px;
            padding: {pad}px;
        }}
    """


class _NewProjectDialog(QDialog):
    """Simple dialog to create a new project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("项目名称："))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：数字治理研究")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("研究问题（可选）："))
        self.rq_edit = QTextEdit()
        self.rq_edit.setPlaceholderText("描述你的研究问题或方向...")
        self.rq_edit.setMaximumHeight(80)
        layout.addWidget(self.rq_edit)

        layout.addWidget(QLabel("学科领域（可选）："))
        self.discipline_edit = QLineEdit()
        self.discipline_edit.setPlaceholderText("例如：公共管理")
        layout.addWidget(self.discipline_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {
            "name": self.name_edit.text().strip(),
            "research_question": self.rq_edit.toPlainText().strip() or None,
            "discipline": self.discipline_edit.text().strip() or None,
        }


class _ProjectCard(QFrame):
    """Card showing a project summary."""

    clicked = pyqtSignal(str)  # project_id

    def __init__(self, project: Project, rq: ResearchQuestion | None, parent=None):
        super().__init__(parent)
        self.project = project
        self.rq = rq
        self._labels: list[QLabel] = []
        self._build_ui()

    def _build_ui(self):
        L = get_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        self.setStyleSheet(_card_style(L.SURFACE))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        name_label = QLabel(self.project.name)
        name_label.setStyleSheet(f"font-size: {FontSize.CARD_TITLE}px; font-weight: 600; color: {L.TEXT_PRIMARY};")
        self._labels.append(name_label)
        layout.addWidget(name_label)

        if self.rq:
            rq_label = QLabel(self.rq.question)
            rq_label.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};")
            rq_label.setWordWrap(True)
            self._labels.append(rq_label)
            layout.addWidget(rq_label)

            if self.rq.keywords:
                kw_label = QLabel(" · ".join(self.rq.keywords))
                kw_label.setStyleSheet(f"font-size: {FontSize.CAPTION}px; color: {L.PRIMARY};")
                self._labels.append(kw_label)
                layout.addWidget(kw_label)
        elif self.project.research_question:
            rq_label = QLabel(self.project.research_question)
            rq_label.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};")
            rq_label.setWordWrap(True)
            self._labels.append(rq_label)
            layout.addWidget(rq_label)

        status_label = QLabel(f"状态：{self.project.status}")
        status_label.setStyleSheet(f"font-size: {FontSize.CAPTION}px; color: {L.TEXT_SECONDARY};")
        self._labels.append(status_label)
        layout.addWidget(status_label)

        self.setMinimumHeight(100)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L.SURFACE))

    def mousePressEvent(self, event):
        self.clicked.emit(self.project.id)
        super().mousePressEvent(event)


class ResearchWorkspacePage(QWidget):
    """Main Research Workspace page — Vision 3.0."""

    navigate_to = pyqtSignal(str)  # emits page_id for navigation
    project_selected = pyqtSignal(str)  # emits project_id

    def __init__(self):
        super().__init__()
        self._svc = ProjectService()
        self._projects: list[Project] = []
        self._rq_map: dict[str, ResearchQuestion | None] = {}
        self._cards: list[_ProjectCard] = []
        self._build_ui()
        self._reload()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        """Build the page UI."""
        L = get_theme()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        outer.setSpacing(Spacing.MD)

        # Header
        header = QHBoxLayout()
        self._title_label = QLabel("研究工作空间")
        self._title_label.setStyleSheet(f"font-size: {FontSize.PAGE_TITLE}px; font-weight: 700; color: {L.TEXT_PRIMARY};")
        header.addWidget(self._title_label)
        header.addStretch()

        self._new_btn = QPushButton("+ 新建项目")
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.clicked.connect(self._on_new_project)
        self._new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {L.PRIMARY};
                color: white;
                border-radius: {Radius.INPUT}px;
                padding: {Spacing.SM} {Spacing.MD}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        header.addWidget(self._new_btn)
        outer.addLayout(header)

        # Empty state or project list
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("border: none; background-color: transparent;")
        self._content = QWidget()
        self._grid = QGridLayout(self._content)
        self._grid.setSpacing(Spacing.MD)
        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll)

    def apply_theme(self) -> None:
        L = get_theme()
        self._title_label.setStyleSheet(f"font-size: {FontSize.PAGE_TITLE}px; font-weight: 700; color: {L.TEXT_PRIMARY};")
        self._new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {L.PRIMARY};
                color: white;
                border-radius: {Radius.INPUT}px;
                padding: {Spacing.SM} {Spacing.MD}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        for card in self._cards:
            card.apply_theme()

    def _reload(self):
        """Reload projects from database."""
        self._projects = self._svc.list_projects()
        self._rq_map = {p.id: self._svc.get_research_question(p.id) for p in self._projects}
        self._refresh_cards()

    def _refresh_cards(self):
        # Clear existing cards
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._cards = []
        if not self._projects:
            empty = QLabel("暂无项目，点击右上角「新建项目」开始")
            empty.setStyleSheet(f"color: {get_theme().TEXT_SECONDARY}; font-size: {FontSize.SECONDARY}px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(empty, 0, 0)
        else:
            for i, (project, rq) in enumerate(zip(self._projects, [self._rq_map.get(p.id) for p in self._projects])):
                card = _ProjectCard(project, rq)
                card.clicked.connect(self._on_project_click)
                self._cards.append(card)
                row, col = i // 2, i % 2
                self._grid.addWidget(card, row, col)

    def _on_new_project(self):
        dlg = _NewProjectDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            if vals["name"]:
                p = self._svc.create_project(**vals)
                rq = self._svc.create_research_question(p.id, vals["research_question"] or "待定义")
                self._reload()

    def _on_project_click(self, project_id: str):
        self.project_selected.emit(project_id)
        self.navigate_to.emit("evidence")