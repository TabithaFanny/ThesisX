"""Literature Management page — real data from LiteratureService.

PRD mapping:
- LiteraturePage: import PDF, import BibTeX, view reference list, view detail
- LiteratureService: import_pdf, import_bibtex, list_references, search_references
"""

from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, _card_style


def _truncate(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class _RefItem(QListWidgetItem):
    """List item for a reference."""

    def __init__(self, ref_id: str, title: str, year: str, tags: list):
        super().__init__()
        self.ref_id = ref_id
        tag_str = " · ".join(tags[:2]) if tags else ""
        display = f"{title}  ·  {year}  {tag_str}"
        self.setText(display)
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsSelectable)


class LiteraturePage(QWidget):
    """Literature management with real LiteratureService data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._references: list = []  # list of Reference dicts
        self._active_ref_id: str | None = None
        self._init_ui()
        QTimer.single_shot(0, self._load_references)

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        header_row.addWidget(
            PageHeader("文献管理", "管理你的参考文献库，支持检索、标注和引用。")
        )
        header_row.addStretch()
        root.addLayout(header_row)

        # Main: sidebar + right panel
        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)

        # Left: category sidebar
        main_row.addWidget(self._create_sidebar(), 0)
        # Right: search + list + detail
        main_row.addWidget(self._create_right_panel(), 1)

        root.addLayout(main_row, 1)

    def _create_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(160)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        title = QLabel("文献库")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(title)

        # Category counts
        self._all_count_lbl = QLabel("全部文献 0")
        self._all_count_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
        )
        layout.addWidget(self._all_count_lbl)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        # List card
        list_card = QFrame()
        list_card.setStyleSheet(_card_style())
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        list_layout.setSpacing(Spacing.MD)

        # Search + import row
        top_row = QHBoxLayout()
        top_row.setSpacing(Spacing.MD)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索文献标题、作者、关键词...")
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }} "
            f"QLineEdit::placeholder {{ color: {L.TEXT_MUTED}; }}"
        )
        self._search_input.returnPressed.connect(self._on_search)
        top_row.addWidget(self._search_input, 1)

        import_btn = QPushButton("导入文献")
        import_btn.setFixedSize(80, 28)
        import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.PILL}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        import_btn.clicked.connect(self._on_show_import_menu)
        top_row.addWidget(import_btn)
        list_layout.addLayout(top_row)

        # Reference list
        self._ref_list = QListWidget()
        self._ref_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._ref_list.currentRowChanged.connect(self._on_ref_selected)
        list_layout.addWidget(self._ref_list, 1)

        # Empty state
        self._empty_label = QLabel("暂无文献\n\n导入 PDF 或 BibTeX 文件\n开始构建文献库")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; padding: {Spacing.MD}px;"
        )
        list_layout.addWidget(self._empty_label)

        layout.addWidget(list_card, 1)

        # Detail card
        layout.addWidget(self._create_detail_card())

        return panel

    def _create_detail_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        header = QHBoxLayout()
        self._detail_title = QLabel("选择一篇文献查看详情")
        self._detail_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        header.addWidget(self._detail_title)
        header.addStretch()
        layout.addLayout(header)

        # Detail scroll
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        detail_scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")
        detail_content = QWidget()
        detail_content.setStyleSheet("background: transparent;")
        detail_inner = QVBoxLayout(detail_content)
        detail_inner.setSpacing(Spacing.SM)

        # Authors + year
        self._detail_meta = QLabel("")
        self._detail_meta.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        detail_inner.addWidget(self._detail_meta)

        # Abstract
        abs_title = QLabel("摘要")
        abs_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        detail_inner.addWidget(abs_title)
        self._detail_abstract = QLabel("")
        self._detail_abstract.setWordWrap(True)
        self._detail_abstract.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px;"
        )
        detail_inner.addWidget(self._detail_abstract)

        # Citation
        cite_title = QLabel("引用格式")
        cite_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        detail_inner.addWidget(cite_title)
        self._detail_citation = QTextEdit()
        self._detail_citation.setReadOnly(True)
        self._detail_citation.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.SMALL}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; }}"
        )
        detail_inner.addWidget(self._detail_citation)

        # Tags
        tags_row = QHBoxLayout()
        tags_title = QLabel("标签")
        tags_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        tags_row.addWidget(tags_title)
        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText("添加标签...")
        self._tag_input.setStyleSheet(
            f"QLineEdit {{ border: 1px dashed {L.BORDER}; border-radius: {Radius.INPUT}px; "
            f"font-size: {FontSize.SECONDARY}px; padding: 2px 6px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }}"
        )
        self._tag_input.returnPressed.connect(self._on_add_tag)
        tags_row.addWidget(self._tag_input, 1)
        self._add_tag_btn = QPushButton("+")
        self._add_tag_btn.setFixedSize(24, 24)
        self._add_tag_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"font-size: {FontSize.BODY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; }}"
        )
        self._add_tag_btn.clicked.connect(self._on_add_tag)
        tags_row.addWidget(self._add_tag_btn)
        detail_inner.addLayout(tags_row)

        self._detail_tags = QLabel("")
        self._detail_tags.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY};"
        )
        detail_inner.addWidget(self._detail_tags)

        detail_inner.addStretch()
        detail_scroll.setWidget(detail_content)
        layout.addWidget(detail_scroll, 1)

        return card

    # -------------------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------------------

    def _load_references(self) -> None:
        try:
            from app.core.literature import LiteratureService

            svc = LiteratureService()
            raw = svc.list_references()
            self._references = [r.to_dict() if hasattr(r, "to_dict") else r for r in raw]
        except Exception:
            self._references = []
        self._refresh_list()
        self._update_counts()

    def _refresh_list(self) -> None:
        self._ref_list.clear()
        has_items = False
        for ref in self._references:
            title = ref.get("title", "Untitled")
            year = ref.get("year", "")
            tags = ref.get("tags", [])
            rid = ref.get("id", str(uuid.uuid4())[:8])
            item = _RefItem(rid, title, year, tags)
            item.setData(Qt.ItemDataRole.UserRole, ref)
            self._ref_list.addItem(item)
            has_items = True
        self._empty_label.setVisible(not has_items)
        self._ref_list.setVisible(has_items)

    def _update_counts(self) -> None:
        self._all_count_lbl.setText(f"全部文献 {len(self._references)}")

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def _on_show_import_menu(self) -> None:
        menu = QWidget()
        menu.setStyleSheet(f"background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; border-radius: {Radius.PANEL}px;")
        menu_layout = QVBoxLayout(menu)
        menu_layout.setSpacing(2)

        pdf_btn = QPushButton("导入 PDF")
        pdf_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; "
            f"border: none; padding: {Spacing.SM}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; text-align: left; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; }}"
        )
        pdf_btn.clicked.connect(self._on_import_pdf)
        menu_layout.addWidget(pdf_btn)

        bib_btn = QPushButton("导入 BibTeX (.bib)")
        bib_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; "
            f"border: none; padding: {Spacing.SM}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; text-align: left; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; }}"
        )
        bib_btn.clicked.connect(self._on_import_bibtex)
        menu_layout.addWidget(bib_btn)

        # Show as a dialog below the button
        from PyQt6.QtCore import QPoint
        btn = self.sender()
        if btn:
            pos = btn.mapToGlobal(QPoint(0, btn.height()))
            menu.popup(pos)

    def _on_import_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入 PDF", str(Path.home()), "PDF 文件 (*.pdf);;所有文件 (*.*)"
        )
        if not path:
            return
        self._import_pdf(path)

    def _import_pdf(self, path: str) -> None:
        try:
            from app.core.literature import LiteratureService

            svc = LiteratureService()
            ref = svc.import_pdf(path)
            ref_dict = ref.to_dict()
            self._references.insert(0, ref_dict)
            self._refresh_list()
            self._update_counts()
            QMessageBox.information(
                self, "导入成功", f"「{ref.title}」已导入。"
            )
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法导入 PDF：{e}")

    def _on_import_bibtex(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入 BibTeX", str(Path.home()), "BibTeX 文件 (*.bib);;所有文件 (*.*)"
        )
        if not path:
            return
        try:
            from app.core.literature import LiteratureService

            svc = LiteratureService()
            refs = svc.import_bibtex(path)
            if not refs:
                QMessageBox.warning(self, "导入失败", "未找到有效的 BibTeX 条目。")
                return
            for ref in reversed(refs):
                self._references.insert(0, ref.to_dict())
            self._refresh_list()
            self._update_counts()
            QMessageBox.information(
                self, "导入成功", f"成功导入 {len(refs)} 条文献记录。"
            )
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法导入 BibTeX：{e}")

    def _on_ref_selected(self, row: int) -> None:
        if row < 0:
            self._active_ref_id = None
            self._detail_title.setText("选择一篇文献查看详情")
            self._detail_meta.setText("")
            self._detail_abstract.setText("")
            self._detail_citation.setPlainText("")
            self._detail_tags.setText("")
            return

        item = self._ref_list.item(row)
        ref = item.data(Qt.ItemDataRole.UserRole)
        self._active_ref_id = ref.get("id")

        self._detail_title.setText(ref.get("title", "Untitled"))
        authors_str = ", ".join(ref.get("authors", []) or ["Unknown"])
        year_str = ref.get("year", "n.d.")
        journal_str = ref.get("journal") or ""
        self._detail_meta.setText(f"{authors_str} · {year_str}" + (f" · {journal_str}" if journal_str else ""))

        abstract = ref.get("abstract") or "（无摘要）"
        self._detail_abstract.setText(abstract)

        # Build citation
        try:
            from app.core.literature import Reference

            ref_obj = Reference.from_dict(ref)
            gbt = ref_obj.format_gbt7714()
        except Exception:
            gbt = f"{', '.join(ref.get('authors', ['Unknown']))}. {ref.get('title', '')}. {ref.get('year', '')}."
        self._detail_citation.setPlainText(gbt)

        tags = ref.get("tags", [])
        self._detail_tags.setText(" · ".join(tags) if tags else "（无标签）")

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            self._load_references()
            return
        try:
            from app.core.literature import LiteratureService

            svc = LiteratureService()
            raw = svc.search_references(query)
            self._references = [r.to_dict() if hasattr(r, "to_dict") else r for r in raw]
            self._refresh_list()
            self._update_counts()
        except Exception:
            pass

    def _on_add_tag(self) -> None:
        if not self._active_ref_id:
            return
        tag = self._tag_input.text().strip()
        if not tag:
            return
        try:
            from app.core.literature import LiteratureService

            svc = LiteratureService()
            svc.add_tag(self._active_ref_id, tag)
            # Update local state
            for ref in self._references:
                if ref.get("id") == self._active_ref_id:
                    if tag not in ref.get("tags", []):
                        ref["tags"].append(tag)
                    break
            self._refresh_list()
            self._tag_input.clear()
            # Update detail view
            self._detail_tags.setText(" · ".join(
                next((r.get("tags", []) for r in self._references if r.get("id") == self._active_ref_id), [])
            ))
        except Exception as e:
            QMessageBox.warning(self, "添加失败", f"无法添加标签：{e}")
