from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class FindReplaceDialog(QDialog):
    """Non-modal Find & Replace dialog.

    Works with the editable PreviewWidget via its JS find/replace API.
    """

    def __init__(self, preview, parent=None):
        super().__init__(parent)
        self._preview = preview  # PreviewWidget instance
        self.setWindowTitle("查找与替换")
        self.setModal(False)
        self.setMinimumWidth(420)
        self._init_ui()
        # Keep on top of main window but allow editing
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Find row
        find_group = QGroupBox("查找")
        find_layout = QHBoxLayout(find_group)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入要查找的内容...")
        self.find_input.returnPressed.connect(self.find_next)
        find_layout.addWidget(self.find_input)
        layout.addWidget(find_group)

        # Replace row
        replace_group = QGroupBox("替换为")
        replace_layout = QHBoxLayout(replace_group)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("输入替换内容...")
        replace_layout.addWidget(self.replace_input)
        layout.addWidget(replace_group)

        # Options
        opt_layout = QHBoxLayout()
        self.case_check = QCheckBox("区分大小写")
        opt_layout.addWidget(self.case_check)
        opt_layout.addStretch()
        layout.addLayout(opt_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        self.find_prev_btn = QPushButton("↑ 向上查找")
        self.find_prev_btn.clicked.connect(self.find_prev)
        btn_layout.addWidget(self.find_prev_btn)

        self.find_next_btn = QPushButton("↓ 向下查找")
        self.find_next_btn.clicked.connect(self.find_next)
        btn_layout.addWidget(self.find_next_btn)

        btn_layout.addStretch()

        self.replace_btn = QPushButton("替换")
        self.replace_btn.clicked.connect(self.replace_one)
        btn_layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("全部替换")
        self.replace_all_btn.clicked.connect(self._replace_all)
        btn_layout.addWidget(self.replace_all_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.status_label)

    # ------------------------------------------------------------------
    # Actions (delegate to PreviewWidget JS)
    # ------------------------------------------------------------------

    def find_next(self):
        needle = self.find_input.text()
        if not needle:
            self.status_label.setText("请输入查找内容")
            return
        cs = self.case_check.isChecked()
        self._preview.find_text(
            needle, case_sensitive=cs, backward=False, callback=self._on_find_result
        )

    def find_prev(self):
        needle = self.find_input.text()
        if not needle:
            self.status_label.setText("请输入查找内容")
            return
        cs = self.case_check.isChecked()
        self._preview.find_text(
            needle, case_sensitive=cs, backward=True, callback=self._on_find_result
        )

    def _on_find_result(self, found):
        if found:
            self.status_label.setText("")
        else:
            needle = self.find_input.text()
            self.status_label.setText(f'未找到 "{needle}"')

    def replace_one(self):
        needle = self.find_input.text()
        replacement = self.replace_input.text()
        if not needle:
            return

        def _on_replaced(success):
            if success:
                self.status_label.setText("已替换 1 处")
                # Find next
                self.find_next()
            else:
                # No selection matched — find first
                self.find_next()

        self._preview.replace_selection(replacement, callback=_on_replaced)

    def _replace_all(self):
        needle = self.find_input.text()
        replacement = self.replace_input.text()
        if not needle:
            return
        cs = self.case_check.isChecked()

        def _on_count(count):
            if count and count > 0:
                self.status_label.setText(f"共替换 {int(count)} 处")
            else:
                self.status_label.setText(f'未找到 "{needle}"')

        self._preview.replace_all(needle, replacement, case_sensitive=cs, callback=_on_count)

    # ------------------------------------------------------------------
    # Focus helpers
    # ------------------------------------------------------------------

    def show_and_focus(self, mode: str = "find"):
        """Show dialog."""
        self.show()
        self.raise_()
        if mode == "replace":
            self.replace_input.setFocus()
        else:
            self.find_input.selectAll()
            self.find_input.setFocus()
