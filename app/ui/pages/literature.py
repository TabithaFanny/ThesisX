"""Literature Management page — real data from LiteratureService.

PRD mapping:
- LiteraturePage: import PDF, import BibTeX, view reference list, view detail
- LiteratureService: import_pdf, import_bibtex, list_references, search_references
"""

from __future__ import annotations

import uuid
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFormLayout,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
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
        ThemeManager.instance().theme_changed.connect(self.apply_theme)
        QTimer.singleShot(0, self._load_references)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header_row = QHBoxLayout()
        self._page_header = PageHeader("文献管理", "管理你的参考文献库，支持检索、标注和引用。")
        header_row.addWidget(self._page_header)
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
        L = get_theme()
        self._sidebar = QFrame()
        self._sidebar.setFixedWidth(160)
        self._sidebar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(self._sidebar)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        self._sidebar_title = QLabel("文献库")
        self._sidebar_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        layout.addWidget(self._sidebar_title)

        # Category counts
        self._all_count_lbl = QLabel("全部文献 0")
        self._all_count_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
        )
        layout.addWidget(self._all_count_lbl)

        layout.addStretch()
        return self._sidebar

    def _create_right_panel(self) -> QWidget:
        L = get_theme()
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        # List card
        self._list_card = QFrame()
        self._list_card.setStyleSheet(_card_style(L))
        list_layout = QVBoxLayout(self._list_card)
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

        self._import_btn = QPushButton("导入文献")
        self._import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._import_btn.clicked.connect(self._on_show_import_menu)
        top_row.addWidget(self._import_btn)

        self._add_btn = QPushButton("+ 手动添加")
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE}; color: {L.PRIMARY}; "
            f"border: 1px solid {L.PRIMARY}; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; }}"
        )
        self._add_btn.clicked.connect(self._on_add_reference)
        top_row.addWidget(self._add_btn)

        self._delete_ref_btn = QPushButton("删除")
        self._delete_ref_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.ERROR}; "
            f"border: 1px solid {L.ERROR}; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.ERROR_BG}; }}"
        )
        self._delete_ref_btn.clicked.connect(self._on_delete_reference)
        self._delete_ref_btn.setEnabled(False)
        top_row.addWidget(self._delete_ref_btn)
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

        layout.addWidget(self._list_card, 1)

        # Detail card
        layout.addWidget(self._create_detail_card())

        return panel

    def _create_detail_card(self) -> QFrame:
        L = get_theme()
        self._detail_card = QFrame()
        self._detail_card.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._detail_card)
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

        return self._detail_card

    # -------------------------------------------------------------------------
    # Theme support
    # -------------------------------------------------------------------------

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        # Header
        self._page_header.apply_theme()

        # Sidebar
        self._sidebar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._sidebar_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        self._all_count_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
        )

        # List card
        self._list_card.setStyleSheet(_card_style(L))
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }} "
            f"QLineEdit::placeholder {{ color: {L.TEXT_MUTED}; }}"
        )
        self._import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE}; color: {L.PRIMARY}; "
            f"border: 1px solid {L.PRIMARY}; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; }}"
        )
        self._delete_ref_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.ERROR}; "
            f"border: 1px solid {L.ERROR}; border-radius: {Radius.PILL}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.ERROR_BG}; }}"
        )
        self._ref_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; padding: {Spacing.MD}px;"
        )

        # Detail card
        self._detail_card.setStyleSheet(_card_style(L))
        self._detail_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        self._detail_meta.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._detail_abstract.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px;"
        )
        self._detail_citation.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.SMALL}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; }}"
        )
        self._tag_input.setStyleSheet(
            f"QLineEdit {{ border: 1px dashed {L.BORDER}; border-radius: {Radius.INPUT}px; "
            f"font-size: {FontSize.SECONDARY}px; padding: 2px 6px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }}"
        )
        self._add_tag_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY_LIGHT}; color: {L.PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"font-size: {FontSize.BODY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; }}"
        )
        self._detail_tags.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY};"
        )

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
        L = get_theme()
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: 4px; }} "
            f"QMenu::item {{ padding: {Spacing.SM}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QMenu::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        pdf_action = menu.addAction("📄 导入 PDF")
        pdf_action.triggered.connect(self._on_import_pdf)
        bib_action = menu.addAction("📚 导入 BibTeX (.bib)")
        bib_action.triggered.connect(self._on_import_bibtex)

        btn = self.sender()
        if btn:
            menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

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
            self._delete_ref_btn.setEnabled(False)
            return

        item = self._ref_list.item(row)
        ref = item.data(Qt.ItemDataRole.UserRole)
        self._active_ref_id = ref.get("id")
        self._delete_ref_btn.setEnabled(True)

        self._detail_title.setText(ref.get("title", "Untitled"))
        authors_str = ", ".join(ref.get("authors", []) or ["Unknown"])
        year_str = ref.get("year", "n.d.")
        journal_str = ref.get("journal") or ""
        self._detail_meta.setText(f"{authors_str} · {year_str}" + (f" · {journal_str}" if journal_str else ""))

        abstract = ref.get("abstract") or "（无摘要）"
        self._detail_abstract.setText(abstract)

        # Build citation with key
        try:
            from app.core.literature import Reference, LiteratureService
            ref_obj = Reference.from_dict(ref)
            key = LiteratureService.generate_citation_key(ref_obj)
            gbt = ref_obj.format_gbt7714()
        except Exception:
            gbt = f"{', '.join(ref.get('authors', ['Unknown']))}. {ref.get('title', '')}. {ref.get('year', '')}."
            key = ""
        display_text = f"Citation Key: {key}\n\n{gbt}" if key else gbt
        self._detail_citation.setPlainText(display_text)

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

    def _on_add_reference(self) -> None:
        dialog = _AddReferenceDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            from app.core.literature import Reference, LiteratureService
            svc = LiteratureService()
            ref = Reference.new(
                title=data["title"],
                authors=data["authors"],
                year=data["year"],
                journal=data["journal"],
                doi=data.get("doi"),
                abstract=data.get("abstract"),
            )
            ref.tags = data.get("tags", [])
            svc._save(ref)
            self._references.insert(0, ref.to_dict())
            self._refresh_list()
            self._update_counts()
            if self._ref_list.count() > 0:
                self._ref_list.setCurrentRow(0)
        except Exception as e:
            QMessageBox.warning(self, "添加失败", f"无法添加文献：{e}")

    def _on_delete_reference(self) -> None:
        if not self._active_ref_id:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            "删除后无法恢复。确定要删除这条文献吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from app.core.literature import LiteratureService
            svc = LiteratureService()
            svc.delete_reference(self._active_ref_id)
            self._references = [r for r in self._references if r.get("id") != self._active_ref_id]
            self._active_ref_id = None
            self._refresh_list()
            self._update_counts()
            self._delete_ref_btn.setEnabled(False)
            self._detail_title.setText("选择一篇文献查看详情")
            self._detail_meta.setText("")
            self._detail_abstract.setText("")
            self._detail_citation.setPlainText("")
            self._detail_tags.setText("")
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"无法删除文献：{e}")


# ── Add Reference Dialog ────────────────────────────────────────────────────


class _AddReferenceDialog(QDialog):
    """Dialog for manually adding an academic reference."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        L = get_theme()
        self.setWindowTitle("添加文献")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"_AddReferenceDialog {{ background-color: {L.SURFACE}; }}")
        self._init_ui()

    def _init_ui(self) -> None:
        L = get_theme()
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        form = QFormLayout()
        form.setSpacing(Spacing.SM)

        input_style = (
            f"QLineEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        lbl_style = f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};"

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("论文标题（必填）")
        self._title_input.setStyleSheet(input_style)
        l1 = QLabel("标题："); l1.setStyleSheet(lbl_style)
        form.addRow(l1, self._title_input)

        self._authors_input = QLineEdit()
        self._authors_input.setPlaceholderText("作者，用逗号分隔")
        self._authors_input.setStyleSheet(input_style)
        l2 = QLabel("作者："); l2.setStyleSheet(lbl_style)
        form.addRow(l2, self._authors_input)

        self._year_input = QLineEdit()
        self._year_input.setPlaceholderText("出版年份")
        self._year_input.setStyleSheet(input_style)
        l3 = QLabel("年份："); l3.setStyleSheet(lbl_style)
        form.addRow(l3, self._year_input)

        self._journal_input = QLineEdit()
        self._journal_input.setPlaceholderText("期刊/会议名称（可选）")
        self._journal_input.setStyleSheet(input_style)
        l4 = QLabel("期刊："); l4.setStyleSheet(lbl_style)
        form.addRow(l4, self._journal_input)

        self._doi_input = QLineEdit()
        self._doi_input.setPlaceholderText("DOI（可选）")
        self._doi_input.setStyleSheet(input_style)
        l5 = QLabel("DOI："); l5.setStyleSheet(lbl_style)
        form.addRow(l5, self._doi_input)

        self._abstract_edit = QTextEdit()
        self._abstract_edit.setPlaceholderText("摘要（可选）")
        self._abstract_edit.setMinimumHeight(80)
        self._abstract_edit.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        l6 = QLabel("摘要："); l6.setStyleSheet(lbl_style)
        form.addRow(l6, self._abstract_edit)

        self._tags_input = QLineEdit()
        self._tags_input.setPlaceholderText("标签，用逗号分隔（可选）")
        self._tags_input.setStyleSheet(input_style)
        l7 = QLabel("标签："); l7.setStyleSheet(lbl_style)
        form.addRow(l7, self._tags_input)

        layout.addLayout(form)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.BUTTON}px; padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QPushButton:hover {{ border-color: {L.PRIMARY}; }}"
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_accept(self) -> None:
        if not self._title_input.text().strip():
            QMessageBox.warning(self, "缺少标题", "请填写文献标题。")
            return
        self.accept()

    def get_data(self) -> dict:
        authors_raw = self._authors_input.text().strip()
        authors = [a.strip() for a in authors_raw.split(",") if a.strip()] if authors_raw else []
        tags_raw = self._tags_input.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        return {
            "title": self._title_input.text().strip(),
            "authors": authors,
            "year": self._year_input.text().strip(),
            "journal": self._journal_input.text().strip() or None,
            "doi": self._doi_input.text().strip() or None,
            "abstract": self._abstract_edit.toPlainText().strip() or None,
            "tags": tags,
        }
