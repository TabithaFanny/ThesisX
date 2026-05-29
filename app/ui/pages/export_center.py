"""Export Center page — Vision 3.9.

Provides export cards for: DOCX, citation formats, session ZIP archive.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, _card_style


def _label(size: int, color: str, weight: str = "normal") -> str:
    return f"QLabel {{ font-size: {size}px; color: {color}; font-weight: {weight}; }}"


def _button(text: str, primary: bool = False, L=None) -> str:
    if L is None:
        L = get_theme()
    if primary:
        return (
            f"QPushButton {{ background-color: {L.PRIMARY}; color: white;"
            f" border: none; border-radius: {Radius.BUTTON}px;"
            f" padding: 6px 16px; font-size: {FontSize.SECONDARY}px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
    return (
        f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_PRIMARY};"
        f" border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px;"
        f" padding: 6px 16px; font-size: {FontSize.SECONDARY}px; }}"
        f"QPushButton:hover {{ background-color: {L.SURFACE}; }}"
    )


class _ExportCard(QFrame):
    """Export option card with format selector and action button."""

    exported = pyqtSignal(str, str)  # format, file path

    def __init__(self, title: str, desc: str, icon: str = ""):
        super().__init__()
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._format = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        header = QHBoxLayout()
        self._icon_label = None
        if icon:
            self._icon_label = QLabel(icon)
            self._icon_label.setStyleSheet(
                f"font-size: 28px; border: none; background: transparent;"
            )
            header.addWidget(self._icon_label)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        header.addWidget(self._title_label, 1)
        layout.addLayout(header)

        self._desc_label = QLabel(desc)
        self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

        self._controls = QHBoxLayout()
        self._controls.addStretch()
        layout.addLayout(self._controls)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._title_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        self._desc_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        if self._icon_label:
            self._icon_label.setStyleSheet(
                f"font-size: 28px; border: none; background: transparent;"
            )

    def add_control(self, widget: QWidget) -> None:
        if isinstance(widget, QHBoxLayout):
            self._controls.insertLayout(self._controls.count() - 1, widget)
        else:
            self._controls.insertWidget(self._controls.count() - 1, widget)


class ExportCenterPage(QWidget):
    """Export center with cards for each export format."""

    def __init__(self):
        super().__init__()
        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    # ── UI build ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        L = get_theme()
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        self._page_header = PageHeader(
            "导出中心",
            "将论文、参考文献和运行记录导出为多种格式。",
        )
        root.addWidget(self._page_header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {L.CANVAS}; }}")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(Spacing.MD)

        # Card 1: DOCX export
        self._card1 = _ExportCard("DOCX 导出", "将论文 Markdown 正文导出为 Word 文档，保留标题层级、加粗和列表。", "\U0001f4dd")
        self._docx_input = QTextEdit()
        self._docx_input.setPlaceholderText("在此粘贴论文 Markdown 内容...")
        self._docx_input.setMaximumHeight(80)
        self._docx_input.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_PRIMARY};"
            f" border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px;"
            f" padding: 6px; font-size: {FontSize.SECONDARY}px; }}"
        )
        content_layout.addWidget(self._docx_input)

        self._docx_btn = QPushButton("导出 DOCX")
        self._docx_btn.setStyleSheet(_button("导出 DOCX", primary=True, L=L))
        self._docx_btn.setMinimumHeight(32)
        self._docx_btn.clicked.connect(self._on_export_docx)
        self._card1.add_control(self._docx_btn)
        content_layout.addWidget(self._card1)

        # Card 2: Citation export
        self._card2 = _ExportCard("引文导出", "将文献库中的参考文献导出为 BibTeX、RIS 或 CSL JSON 格式。", "\U0001f4da")

        controls_row = QHBoxLayout()
        controls_row.setSpacing(Spacing.SM)

        self._citation_format = QComboBox()
        self._citation_format.addItems(["BibTeX (.bib)", "RIS (.ris)", "CSL JSON (.json)"])
        self._citation_format.setMinimumHeight(32)
        controls_row.addWidget(self._citation_format)

        self._cite_btn = QPushButton("导出引文")
        self._cite_btn.setStyleSheet(_button("导出引文", primary=True, L=L))
        self._cite_btn.setMinimumHeight(32)
        self._cite_btn.clicked.connect(self._on_export_citations)
        controls_row.addWidget(self._cite_btn)

        controls_row.addStretch()
        self._card2.add_control(controls_row)
        content_layout.addWidget(self._card2)

        # Card 3: Session archive
        self._card3 = _ExportCard("Session 打包", "将运行记录（events, output, context）打包为 ZIP 归档。", "\U0001f4e6")

        controls_row2 = QHBoxLayout()
        controls_row2.setSpacing(Spacing.SM)

        self._session_id_input = QLineEdit()
        self._session_id_input.setPlaceholderText("输入 Session ID...")
        self._session_id_input.setMinimumHeight(32)
        controls_row2.addWidget(self._session_id_input)

        self._session_btn = QPushButton("打包 ZIP")
        self._session_btn.setStyleSheet(_button("打包 ZIP", primary=True, L=L))
        self._session_btn.setMinimumHeight(32)
        self._session_btn.clicked.connect(self._on_export_session)
        controls_row2.addWidget(self._session_btn)

        controls_row2.addStretch()
        self._card3.add_control(controls_row2)
        content_layout.addWidget(self._card3)

        content_layout.addStretch()

        self._scroll.setWidget(content)
        root.addWidget(self._scroll, 1)

    def apply_theme(self) -> None:
        L = get_theme()
        self._page_header.apply_theme()
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {L.CANVAS}; }}")
        self._docx_input.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_PRIMARY};"
            f" border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px;"
            f" padding: 6px; font-size: {FontSize.SECONDARY}px; }}"
        )
        self._docx_btn.setStyleSheet(_button("导出 DOCX", primary=True, L=L))
        self._cite_btn.setStyleSheet(_button("导出引文", primary=True, L=L))
        self._session_btn.setStyleSheet(_button("打包 ZIP", primary=True, L=L))
        self._card1.apply_theme()
        self._card2.apply_theme()
        self._card3.apply_theme()

    # ── export handlers ───────────────────────────────────────────────────

    def _on_export_docx(self) -> None:
        md = self._docx_input.toPlainText().strip()
        if not md:
            QMessageBox.warning(self, "内容为空", "请先粘贴 Markdown 内容再导出。")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 DOCX", str(Path.home() / "Desktop" / "论文.docx"),
            "Word 文档 (*.docx)",
        )
        if not path:
            return

        try:
            from app.core.export.docx_exporter import DocxExporter
            DocxExporter.export(md, Path(path))
            QMessageBox.information(self, "导出成功", f"DOCX 已保存到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _on_export_citations(self) -> None:
        fmt_idx = self._citation_format.currentIndex()
        suffix = ["bib", "ris", "json"][fmt_idx]
        fmt_label = ["BibTeX", "RIS", "CSL JSON"][fmt_idx]

        path, _ = QFileDialog.getSaveFileName(
            self, f"导出 {fmt_label}",
            str(Path.home() / "Desktop" / f"references.{suffix}"),
            f"{fmt_label} (*.{suffix})",
        )
        if not path:
            return

        try:
            from app.core.export.citation_export import CitationExporter, Ref
            from app.core.literature.service import LiteratureService

            svc = LiteratureService()
            refs = svc.list_references()

            export_refs = []
            for r in refs:
                cite_key = svc.generate_citation_key(r)
                export_refs.append(Ref(
                    key=r.id,
                    title=r.title or "",
                    authors=" and ".join(r.authors) if r.authors else "",
                    year=r.year or "",
                    journal=r.journal or "",
                    doi=r.doi or "",
                    abstract=r.abstract or "",
                    cite_key=cite_key,
                ))

            if fmt_idx == 0:
                content = CitationExporter.to_bibtex(export_refs)
            elif fmt_idx == 1:
                content = CitationExporter.to_ris(export_refs)
            else:
                content = CitationExporter.to_csl_json(export_refs)

            Path(path).write_text(content, encoding="utf-8")
            QMessageBox.information(self, "导出成功", f"{fmt_label} 已保存到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _on_export_session(self) -> None:
        session_id = self._session_id_input.text().strip()
        if not session_id:
            QMessageBox.warning(self, "ID 为空", "请输入要打包的 Session ID。")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "打包 Session ZIP",
            str(Path.home() / "Desktop" / f"session_{session_id}.zip"),
            "ZIP 归档 (*.zip)",
        )
        if not path:
            return

        try:
            from app.core.export.session_exporter import SessionExporter
            result = SessionExporter.archive(session_id, Path(path))
            QMessageBox.information(self, "打包成功", f"ZIP 已保存到:\n{result}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Session 未找到", f"找不到 Session: {session_id}")
        except Exception as e:
            QMessageBox.critical(self, "打包失败", str(e))
