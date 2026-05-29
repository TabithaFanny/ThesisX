"""Workspace container — sidebar navigation + page stack."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from app.ui.components.sidebar_nav import SidebarNav
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


class Workspace(QWidget):
    """Main workspace with sidebar navigation and stacked pages."""

    # Signals for real features
    open_paper_draft = pyqtSignal()  # Open AI paper draft dialog
    open_editor = pyqtSignal()       # Switch to editor mode

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._pages: dict[str, QWidget] = {}
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self._apply_theme)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        # Sidebar
        self._sidebar = SidebarNav()
        self._sidebar.page_selected.connect(self._on_page_selected)
        layout.addWidget(self._sidebar)

        # Content shell
        self._content_shell = QFrame()
        self._content_shell.setObjectName("workspaceContentShell")
        self._content_shell.setStyleSheet(
            f"QFrame#workspaceContentShell {{ background-color: {L.CANVAS}; border: none; }}"
        )
        content_layout = QVBoxLayout(self._content_shell)
        content_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        content_layout.setSpacing(Spacing.MD)

        self._shell_header = QFrame()
        self._shell_header.setObjectName("workspaceShellHeader")
        self._shell_header.setStyleSheet(
            f"QFrame#workspaceShellHeader {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        shell_header_layout = QHBoxLayout(self._shell_header)
        shell_header_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        shell_header_layout.setSpacing(Spacing.MD)

        self._shell_title = QLabel("ThesisX 工作台")
        self._shell_title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        shell_header_layout.addWidget(self._shell_title)
        shell_header_layout.addStretch()
        content_layout.addWidget(self._shell_header)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {L.CANVAS}; border: none; }}"
        )
        content_layout.addWidget(self._stack, 1)

        layout.addWidget(self._content_shell, 1)

    def _apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._content_shell.setStyleSheet(
            f"QFrame#workspaceContentShell {{ background-color: {L.CANVAS}; border: none; }}"
        )
        self._shell_header.setStyleSheet(
            f"QFrame#workspaceShellHeader {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._shell_title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {L.CANVAS}; border: none; }}"
        )
        # Propagate to child pages
        for page in self._pages.values():
            if hasattr(page, "apply_theme"):
                page.apply_theme()

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

    def page(self, page_id: str) -> QWidget | None:
        """Return the page widget for a given page_id, or None."""
        return self._pages.get(page_id)

    def switch_to(self, page_id: str) -> None:
        """Programmatically switch to a page."""
        self._sidebar._set_active(page_id)
        self._sidebar._on_click(page_id)
