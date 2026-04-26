import os

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class FormattingActions:
    """Formatting actions that operate on the editable PreviewWidget via JS."""

    def __init__(self, preview):
        """Args: preview — a PreviewWidget instance."""
        self.preview = preview

    def toggle_bold(self):
        self.preview.exec_format_command("bold")

    def toggle_italic(self):
        self.preview.exec_format_command("italic")

    def toggle_underline(self):
        self.preview.exec_format_command("underline")

    def toggle_strikethrough(self):
        self.preview.exec_format_command("strikeThrough")

    def insert_heading(self, level: int):
        self.preview.exec_js(f"applyHeading({level});")

    def insert_code_block(self):
        self.preview.exec_js("insertCodeBlock();")

    def insert_quote(self):
        self.preview.exec_js("insertQuote();")

    def insert_link(self):
        dlg = QDialog()
        dlg.setWindowTitle("插入超链接")
        dlg.setFixedWidth(380)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(8)

        layout.addWidget(QLabel("链接地址 (URL):"))
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://example.com")
        layout.addWidget(url_input)

        layout.addWidget(QLabel("显示文字 (可留空用选中文字):"))
        text_input = QLineEdit()
        text_input.setPlaceholderText("链接文字")
        layout.addWidget(text_input)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        url_input.setFocus()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        url = url_input.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://", "ftp://", "//")):
            url = "https://" + url
        display = text_input.text().strip() or url
        escaped_url = url.replace("'", "\\'")
        escaped_display = display.replace("'", "\\'")
        self.preview.exec_js(f"insertLink('{escaped_url}', '{escaped_display}');")

    def insert_image(self):
        path, _ = QFileDialog.getOpenFileName(
            None,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp);;所有文件 (*)",
        )
        if path:
            from PyQt6.QtCore import QUrl

            file_url = QUrl.fromLocalFile(path).toString()
            alt = os.path.splitext(os.path.basename(path))[0]
            escaped_path = file_url.replace("'", "\\'")
            escaped_alt = alt.replace("'", "\\'")
            self.preview.exec_js(f"insertImage('{escaped_path}', '{escaped_alt}');")

    def insert_list(self):
        self.preview.exec_format_command("insertUnorderedList")

    def insert_ordered_list(self):
        self.preview.exec_format_command("insertOrderedList")

    def insert_horizontal_rule(self):
        self.preview.exec_js("insertHR();")

    def set_font_color(self, color: str):
        escaped = color.replace("'", "\\'")
        self.preview.exec_js(f"setFontColor('{escaped}');")

    def set_highlight_color(self, color: str):
        escaped = color.replace("'", "\\'")
        self.preview.exec_js(f"setHighlightColor('{escaped}');")

    def set_font_size(self, size_px: str):
        self.preview.exec_js(f"setFontSizePx('{size_px}');")

    def insert_superscript(self):
        self.preview.exec_format_command("superscript")

    def insert_subscript(self):
        self.preview.exec_format_command("subscript")

    def set_font_family(self, family: str):
        escaped = family.replace("'", "\\'")
        self.preview.exec_js(f"setFontFamily('{escaped}');")

    def clear_formatting(self):
        self.preview.exec_format_command("removeFormat")

    def indent(self):
        self.preview.exec_format_command("indent")

    def outdent(self):
        self.preview.exec_format_command("outdent")

    def set_text_align(self, align: str):
        self.preview.exec_js(f"setTextAlign('{align}');")

    def set_line_height(self, value: str):
        self.preview.exec_js(f"setLineHeight('{value}');")
