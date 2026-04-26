from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.table_handler import TableHandler


class TableDialog(QDialog):
    """Dialog for creating and editing tables."""

    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("表格编辑器")
        self.setMinimumSize(600, 450)
        self._result_markdown = ""
        self._init_ui(initial_data)

    def _init_ui(self, initial_data):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Visual editor
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("行数:"))
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 100)
        self.rows_spin.setValue(3)
        size_layout.addWidget(self.rows_spin)

        size_layout.addWidget(QLabel("列数:"))
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 20)
        self.cols_spin.setValue(3)
        size_layout.addWidget(self.cols_spin)

        apply_size_btn = QPushButton("应用大小")
        apply_size_btn.clicked.connect(self._apply_size)
        size_layout.addWidget(apply_size_btn)
        size_layout.addStretch()

        editor_layout.addLayout(size_layout)

        self.table_widget = QTableWidget(3, 3)
        self._set_default_headers(3)
        editor_layout.addWidget(self.table_widget)

        tabs.addTab(editor_tab, "可视化编辑")

        # Tab 2: Import
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)

        self.import_text = QTextEdit()
        self.import_text.setPlaceholderText("粘贴 CSV/TSV 数据，或点击下方按钮导入文件...")
        import_layout.addWidget(self.import_text)

        import_btn_layout = QHBoxLayout()
        csv_btn = QPushButton("导入 CSV")
        csv_btn.clicked.connect(lambda: self._import_file("CSV 文件 (*.csv)"))
        import_btn_layout.addWidget(csv_btn)

        excel_btn = QPushButton("导入 Excel")
        excel_btn.clicked.connect(lambda: self._import_file("Excel 文件 (*.xlsx *.xls)"))
        import_btn_layout.addWidget(excel_btn)

        parse_btn = QPushButton("解析文本")
        parse_btn.clicked.connect(self._parse_import_text)
        import_btn_layout.addWidget(parse_btn)

        import_layout.addLayout(import_btn_layout)
        tabs.addTab(import_tab, "导入数据")

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        if initial_data:
            self._load_data(initial_data)

    def _set_default_headers(self, col_count: int, start_col: int = 0):
        """Set default column names in header row for newly added columns."""
        for c in range(start_col, col_count):
            if not self.table_widget.item(0, c):
                self.table_widget.setItem(0, c, QTableWidgetItem(f"列{c + 1}"))

    def _apply_size(self):
        old_cols = self.table_widget.columnCount()
        self.table_widget.setRowCount(self.rows_spin.value())
        self.table_widget.setColumnCount(self.cols_spin.value())
        new_cols = self.cols_spin.value()
        if new_cols > old_cols:
            self._set_default_headers(new_cols, old_cols)

    def _load_data(self, rows):
        self.table_widget.setRowCount(len(rows))
        if rows:
            self.table_widget.setColumnCount(len(rows[0]))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table_widget.setItem(r, c, QTableWidgetItem(str(val)))
        self.rows_spin.setValue(len(rows))
        if rows:
            self.cols_spin.setValue(len(rows[0]))

    def _import_file(self, file_filter):
        path, _ = QFileDialog.getOpenFileName(self, "导入文件", "", file_filter)
        if not path:
            return
        if path.endswith((".xlsx", ".xls")):
            md = TableHandler.from_excel(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                md = TableHandler.from_csv_text(f.read())
        if md:
            rows = TableHandler.parse_markdown_table(md)
            if rows:
                self._load_data(rows)

    def _parse_import_text(self):
        text = self.import_text.toPlainText()
        if not text.strip():
            return
        md = TableHandler.from_clipboard_text(text)
        if md:
            rows = TableHandler.parse_markdown_table(md)
            if rows:
                self._load_data(rows)

    def _accept(self):
        rows = []
        for r in range(self.table_widget.rowCount()):
            row = []
            for c in range(self.table_widget.columnCount()):
                item = self.table_widget.item(r, c)
                text = item.text().strip() if item else ""
                # Ensure header row always has a non-empty label
                if r == 0 and not text:
                    text = f"列{c + 1}"
                row.append(text)
            rows.append(row)
        if rows:
            self._result_markdown = TableHandler._rows_to_markdown(rows)
        self.accept()

    def get_markdown(self) -> str:
        return self._result_markdown

    def get_table_html(self) -> str:
        """Generate an HTML <table> directly, bypassing Markdown."""
        rows = self.table_widget.rowCount()
        cols = self.table_widget.columnCount()
        if rows == 0 or cols == 0:
            return ""

        def _cell_text(r, c):
            item = self.table_widget.item(r, c)
            return item.text().strip() if item else ""

        parts = ["<table>"]
        # Header
        parts.append("<thead><tr>")
        for c in range(cols):
            text = _cell_text(0, c) or f"\u5217{c + 1}"
            parts.append(f"<th>{text}</th>")
        parts.append("</tr></thead>")
        # Body
        parts.append("<tbody>")
        for r in range(1, rows):
            parts.append("<tr>")
            for c in range(cols):
                text = _cell_text(r, c)
                parts.append(f'<td>{text if text else "<br>"}</td>')
            parts.append("</tr>")
        parts.append("</tbody></table>")
        return "\n".join(parts)
