import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QStatusBar


class StatusBar(QStatusBar):
    """Custom status bar showing word count, cursor position, file info, etc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(True)

        # Left side: file path (stretching)
        self.file_label = QLabel("未命名文档")
        self.file_label.setObjectName("statusLabel")
        self.file_label.setMinimumWidth(120)
        self.file_label.setMaximumWidth(360)
        self.addWidget(self.file_label)  # non-permanent = left side

        # Modified indicator
        self.modified_label = QLabel("")
        self.modified_label.setObjectName("statusLabel")
        self.modified_label.setFixedWidth(16)
        self.modified_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.addWidget(self.modified_label)

        # Autosave status
        self.autosave_label = QLabel("")
        self.autosave_label.setObjectName("statusLabel")
        self.autosave_label.setMinimumWidth(80)
        self.addWidget(self.autosave_label)

        # Right side: stats + position + encoding
        self.word_label = QLabel("字数: 0")
        self.word_label.setObjectName("statusLabel")
        self.addPermanentWidget(self.word_label)

        self.char_label = QLabel("字符: 0")
        self.char_label.setObjectName("statusLabel")
        self.addPermanentWidget(self.char_label)

        self.pos_label = QLabel("行 1, 列 1")
        self.pos_label.setObjectName("statusLabel")
        self.addPermanentWidget(self.pos_label)

        self.encoding_label = QLabel("UTF-8")
        self.encoding_label.setObjectName("statusLabel")
        self.addPermanentWidget(self.encoding_label)

    def update_stats(self, words: int, chars: int):
        self.word_label.setText(f"字数: {words:,}")
        self.char_label.setText(f"字符: {chars:,}")

    def update_position(self, line: int, col: int):
        self.pos_label.setText(f"行 {line}, 列 {col}")

    def update_file_info(self, file_path: str, is_modified: bool):
        """Update file path display and modified indicator."""
        if file_path:
            # Show truncated path; full path as tooltip
            name = os.path.basename(file_path)
            self.file_label.setText(name)
            self.file_label.setToolTip(file_path)
        else:
            self.file_label.setText("未命名文档")
            self.file_label.setToolTip("")
        self.modified_label.setText("●" if is_modified else "")

    def show_autosave_status(self, message: str):
        """Briefly show autosave status (caller should clear after a delay)."""
        self.autosave_label.setText(message)

    def clear_autosave_status(self):
        self.autosave_label.setText("")
