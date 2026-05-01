"""Workspace container — sidebar navigation + page stack."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from app.ui.components.sidebar_nav import SidebarNav
from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing


class Workspace(QWidget):
    """Main workspace with sidebar navigation and stacked pages."""

    # Signals for real features
    open_paper_draft = pyqtSignal()  # Open AI paper draft dialog
    open_editor = pyqtSignal()       # Switch to editor mode

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._pages: dict[str, QWidget] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        # Sidebar
        self._sidebar = SidebarNav()
        self._sidebar.page_selected.connect(self._on_page_selected)
        layout.addWidget(self._sidebar)

        # Content shell
        content_shell = QFrame()
        content_shell.setObjectName("workspaceContentShell")
        content_shell.setStyleSheet(
            f"QFrame#workspaceContentShell {{ background-color: {L.CANVAS}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PAGE}px; }}"
        )
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        content_layout.setSpacing(Spacing.MD)

        shell_header = QFrame()
        shell_header.setObjectName("workspaceShellHeader")
        shell_header.setStyleSheet(
            f"QFrame#workspaceShellHeader {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        shell_header_layout = QHBoxLayout(shell_header)
        shell_header_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        shell_header_layout.setSpacing(Spacing.MD)

        shell_title = QLabel("Workspace")
        shell_title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        shell_header_layout.addWidget(shell_title)

        shell_subtitle = QLabel("Unified shell for preview pages")
        shell_subtitle.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        shell_header_layout.addWidget(shell_subtitle)
        shell_header_layout.addStretch()

        shell_badge = QLabel("Preview")
        shell_badge.setStyleSheet(
            f"color: {L.PRIMARY}; background-color: {L.PRIMARY_LIGHT}; "
            f"border: 1px solid {L.PRIMARY_BORDER}; border-radius: {Radius.PILL}px; "
            f"padding: 2px {Spacing.SM}px; font-size: {FontSize.MICRO}px; font-weight: 700;"
        )
        shell_header_layout.addWidget(shell_badge)
        content_layout.addWidget(shell_header)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {L.CANVAS}; border: none; }}"
        )
        content_layout.addWidget(self._stack, 1)

        layout.addWidget(content_shell, 1)

    def add_page(self, page_id: str, widget: QWidget) -> None:
        """Add a page to the stack."""
        self._pages[page_id] = widget
        self._stack.addWidget(widget)

    def _on_page_selected(self, page_id: str) -> None:
        """Handle sidebar navigation."""
        if page_id == "editor":
            # Editor is special — emit signal to switch to editor mode
            self.open_editor.emit()
            return
        if page_id in self._pages:
            self._stack.setCurrentWidget(self._pages[page_id])

    def switch_to(self, page_id: str) -> None:
        """Programmatically switch to a page."""
        self._sidebar._set_active(page_id)
        self._sidebar._on_click(page_id)
