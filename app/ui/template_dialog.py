from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

from app.core.templates import TemplateManager


class TemplateDialog(QDialog):
    """Dialog for selecting a paper template."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择模板")
        self.setMinimumSize(500, 400)
        self._template_manager = TemplateManager()
        self._selected_content = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("选择论文模板:"))

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        layout.addWidget(QLabel("预览:"))
        self.preview = QTextBrowser()
        self.preview.setMaximumHeight(200)
        layout.addWidget(self.preview)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._load_templates()

    def _load_templates(self):
        for name, filepath in self._template_manager.get_template_list():
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, filepath)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_selection_changed(self, current, previous):
        if current:
            filepath = current.data(Qt.ItemDataRole.UserRole)
            try:
                content = self._template_manager.load_template(filepath)
                self._selected_content = content
                self.preview.setPlainText(content[:500] + ("..." if len(content) > 500 else ""))
            except Exception:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Failed to load template %s", filepath, exc_info=True)
                self._selected_content = ""
                self.preview.setPlainText("")

    def get_content(self) -> str:
        return self._selected_content
