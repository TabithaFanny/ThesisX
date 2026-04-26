"""
shortcut_settings_dialog.py — 快捷键自定义对话框

允许用户查看和修改键盘快捷键绑定。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QKeySequenceEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

# Default shortcut definitions: (action_id, description, default_key)
DEFAULT_SHORTCUTS = [
    ("new_file", "新建文件", "Ctrl+N"),
    ("open_file", "打开文件", "Ctrl+O"),
    ("save_file", "保存文件", "Ctrl+S"),
    ("save_as", "另存为", "Ctrl+Shift+S"),
    ("undo", "撤销", "Ctrl+Z"),
    ("redo", "重做", "Ctrl+Y"),
    ("find", "查找", "Ctrl+F"),
    ("find_replace", "查找替换", "Ctrl+H"),
    ("bold", "加粗", "Ctrl+B"),
    ("italic", "斜体", "Ctrl+I"),
    ("ai_dialog", "AI 指令", "Ctrl+I"),
    ("export_pdf", "导出 PDF", "Ctrl+Shift+P"),
]


class ShortcutSettingsDialog(QDialog):
    """Dialog for viewing and editing keyboard shortcuts."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("快捷键设置")
        self.setMinimumSize(500, 400)
        self._init_ui()
        self._load_shortcuts()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel("双击「快捷键」列可修改快捷键绑定。留空表示禁用该快捷键。")
        hint.setStyleSheet("color: #888; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(hint)

        self._table = QTableWidget(len(DEFAULT_SHORTCUTS), 3)
        self._table.setHorizontalHeaderLabels(["操作", "默认快捷键", "当前快捷键"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_all)
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_shortcuts(self):
        overrides = self._config.get("shortcut_overrides", {})
        for row, (action_id, desc, default_key) in enumerate(DEFAULT_SHORTCUTS):
            # Action description (read-only)
            item_desc = QTableWidgetItem(desc)
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, item_desc)

            # Default key (read-only)
            item_default = QTableWidgetItem(default_key)
            item_default.setFlags(item_default.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, item_default)

            # Current key (editable)
            current = overrides.get(action_id, default_key)
            item_current = QTableWidgetItem(current)
            self._table.setItem(row, 2, item_current)

    def _reset_all(self):
        for row, (action_id, desc, default_key) in enumerate(DEFAULT_SHORTCUTS):
            self._table.item(row, 2).setText(default_key)

    def _save(self):
        overrides = {}
        for row, (action_id, desc, default_key) in enumerate(DEFAULT_SHORTCUTS):
            current = self._table.item(row, 2).text().strip()
            if current != default_key:
                overrides[action_id] = current
        self._config.set("shortcut_overrides", overrides)
        self._config.save()
        QMessageBox.information(self, "快捷键", "快捷键设置已保存。重启应用后生效。")
        self.accept()
