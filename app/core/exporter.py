import os

from PyQt6.QtCore import QEventLoop, QMarginsF
from PyQt6.QtGui import QPageLayout, QPageSize

from app.core.docx_exporter import DocxExporter
from app.core.docx_exporter_v2 import TABLE_STYLE_THREELINE, EnhancedDocxExporter
from app.core.markdown_renderer import MarkdownRenderer
from app.core.pptx_exporter import PptxExporter


class Exporter:

    def __init__(self):
        self._renderer = MarkdownRenderer.instance()
        self._docx_exporter = DocxExporter()
        self._enhanced_exporter = EnhancedDocxExporter()
        self._pptx_exporter = PptxExporter()
        self._css = ""

    def set_css(self, css: str):
        self._css = css

    def export_html(self, markdown_text: str, output_path: str):
        html = self._renderer.render(markdown_text)
        pygments_css = MarkdownRenderer.get_pygments_css()
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Document</title>
<style>
{self._css}
{pygments_css}
</style>
</head>
<body>
{html}
</body>
</html>"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)

    def export_pdf(self, markdown_text: str, output_path: str):
        from PyQt6.QtWebEngineWidgets import QWebEngineView

        html = self._renderer.render(markdown_text)
        pygments_css = MarkdownRenderer.get_pygments_css()
        full_html = (
            "<!DOCTYPE html><html lang='zh-CN'>"
            "<head><meta charset='utf-8'>"
            f"<style>{self._css}\n{pygments_css}</style>"
            f"</head><body>{html}</body></html>"
        )

        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(15, 15, 15, 15),
        )

        loop = QEventLoop()
        view = QWebEngineView()
        view.resize(794, 1123)  # A4 @ 96dpi

        def _on_load(ok):
            view.page().printToPdf(output_path, page_layout)

        def _on_pdf_done(path, success):
            loop.quit()

        view.page().pdfPrintingFinished.connect(_on_pdf_done)
        view.loadFinished.connect(_on_load)
        view.setHtml(full_html)
        loop.exec()
        view.deleteLater()

    def export_docx(self, markdown_text: str, output_path: str):
        self._docx_exporter.export(markdown_text, output_path)

    def export_pptx(
        self,
        markdown_text: str,
        output_path: str,
        style: str = "academic",
        title: str = "",
        author: str = "",
    ):
        self._pptx_exporter.export(
            markdown_text,
            output_path,
            style=style,
            title=title,
            author=author,
        )

    def export_docx_enhanced(
        self,
        markdown_text: str,
        output_path: str,
        *,
        style: str = "academic",
        title: str = "",
        author: str = "",
        add_cover: bool = False,
        add_toc: bool = False,
        add_page_numbers: bool = True,
        table_style: str = TABLE_STYLE_THREELINE,
        file_dir: str = "",
    ):
        self._enhanced_exporter.export(
            markdown_text,
            output_path,
            style=style,
            title=title,
            author=author,
            add_cover=add_cover,
            add_toc=add_toc,
            add_page_numbers=add_page_numbers,
            table_style=table_style,
            file_dir=file_dir,
        )
