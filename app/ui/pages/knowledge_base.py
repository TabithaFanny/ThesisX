"""Knowledge Base page — personal academic knowledge management.

Features (Phase B minimum):
- Import files (txt/md/pdf/docx)
- View source list with status
- Keyword search across chunks
- Preview chunks for selected source
- Delete sources

 PRD mapping:
 - KnowledgeBasePage components: SourceImportPanel, SourceList,
   SourceDetailPanel, ChunkPreviewPanel, SearchBox, SearchResultList
 - KnowledgeService: import_file, list_sources, search, get_chunks, delete_source
"""

from __future__ import annotations

import uuid
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
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


class _SourceItem(QListWidgetItem):
    """List item for a knowledge source."""

    def __init__(self, source_id: str, title: str, status: str, chunk_count: int):
        super().__init__()
        self.source_id = source_id
        self.setText(f"{title}  ·  {status}  ·  {chunk_count} chunks")
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsSelectable)


class KnowledgeBasePage(QWidget):
    """Personal academic knowledge base — Phase B real implementation."""

    # Emitted when user selects sources to use in a paper run
    sources_selected = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sources: list = []  # list of KnowledgeSource dicts
        self._active_source_id: str | None = None
        self._chunks: list = []
        self._init_ui()
        self._load_sources()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        root = QVBoxLayout(content)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header = PageHeader(
            "知识库",
            "导入文献、笔记、PDF，构建个人学术资料库，支持检索和上下文注入。",
        )
        root.addWidget(header)

        # Main 3-column layout
        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)

        # Left: import + source list (260px)
        cols.addWidget(self._create_source_panel(), 0)
        # Middle: chunk preview (flex)
        cols.addWidget(self._create_preview_panel(), 1)
        # Right: search + results (280px)
        cols.addWidget(self._create_search_panel(), 0)

        root.addLayout(cols, 1)

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _create_source_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(260)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Panel title
        title = QLabel("资料库")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(title)

        # Import button
        self._import_btn = QPushButton("+ 导入文件")
        self._import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._import_btn.clicked.connect(self._on_import_file)
        layout.addWidget(self._import_btn)

        # Source list
        self._source_list = QListWidget()
        self._source_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._source_list.currentRowChanged.connect(self._on_source_selected)
        layout.addWidget(self._source_list, 1)

        # Empty state
        self._empty_label = QLabel("暂无资料\n\n导入 PDF、文档或笔记\n构建你的知识库")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"padding: {Spacing.MD}px;"
        )
        layout.addWidget(self._empty_label)

        # Delete button
        self._delete_btn = QPushButton("删除选中")
        self._delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.ERROR}; "
            f"border: 1px solid {L.ERROR}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.ERROR_BG}; }}"
        )
        self._delete_btn.clicked.connect(self._on_delete_source)
        self._delete_btn.setEnabled(False)
        layout.addWidget(self._delete_btn)

        return panel

    def _create_preview_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.MD)

        # Header row
        header_row = QHBoxLayout()
        self._preview_title = QLabel("选择一份资料查看")
        self._preview_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        header_row.addWidget(self._preview_title)
        header_row.addStretch()

        # Chunk count
        self._chunk_count_lbl = QLabel("")
        self._chunk_count_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        header_row.addWidget(self._chunk_count_lbl)
        layout.addLayout(header_row)

        # Chunk list (text items showing heading + text preview)
        self._chunk_list = QTextEdit()
        self._chunk_list.setReadOnly(True)
        self._chunk_list.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.BODY}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        self._chunk_list.setMinimumHeight(200)
        layout.addWidget(self._chunk_list, 1)

        # Use in run button
        self._use_in_run_btn = QPushButton("发送给 AI 使用")
        self._use_in_run_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._use_in_run_btn.clicked.connect(self._on_use_in_run)
        self._use_in_run_btn.setEnabled(False)
        layout.addWidget(self._use_in_run_btn)

        return panel

    def _create_search_panel(self) -> QFrame:
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Search title
        title = QLabel("全文检索")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(title)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索关键词...")
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }} "
            f"QLineEdit::placeholder {{ color: {L.TEXT_MUTED}; }}"
        )
        self._search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self._search_input)

        # Search button
        search_btn = QPushButton("检索")
        search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)

        # Results list
        results_title = QLabel("检索结果")
        results_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(results_title)

        self._results_list = QTextEdit()
        self._results_list.setReadOnly(True)
        self._results_list.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.SECONDARY}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; }} "
            f"font-family: 'PingFang SC', sans-serif;"
        )
        layout.addWidget(self._results_list, 1)

        return panel

    # -------------------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------------------

    def _load_sources(self) -> None:
        try:
            from app.core.knowledge import KnowledgeService

            svc = KnowledgeService()
            raw = svc.list_sources()
            # list_sources returns list[dict]
            self._sources = [s if isinstance(s, dict) else s.to_dict() for s in raw]
        except Exception as e:
            self._sources = []
        self._refresh_source_list()

    def _refresh_source_list(self) -> None:
        self._source_list.clear()
        has_items = False
        for src in self._sources:
            title = src.get("title", "未知")
            status = src.get("status", "?")
            chunks = src.get("chunk_count", 0)
            sid = src.get("id", str(uuid.uuid4())[:8])
            item = _SourceItem(sid, title, status, chunks)
            item.setData(Qt.ItemDataRole.UserRole, src)
            self._source_list.addItem(item)
            has_items = True

        self._empty_label.setVisible(not has_items)
        self._source_list.setVisible(has_items)

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def _on_import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入资料",
            str(Path.home()),
            "支持的格式 (*.txt *.md *.pdf *.docx);;所有文件 (*.*)",
        )
        if not path:
            return
        self._import_file(path)

    def _import_file(self, path: str) -> None:
        try:
            from app.core.knowledge import KnowledgeService

            svc = KnowledgeService()
            src = svc.import_file(path)
            # import_file may return a dict or object
            if hasattr(src, "to_dict"):
                src_dict = src.to_dict()
            else:
                src_dict = src
            self._sources.insert(0, src_dict)
            self._refresh_source_list()
            # Auto-select first item
            if self._source_list.count() > 0:
                self._source_list.setCurrentRow(0)
            QMessageBox.information(
                self,
                "导入成功",
                f"「{src_dict.get('title', Path(path).stem)}」已导入。\n"
                f"解析了 {src_dict.get('chunk_count', 0)} 个片段。",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "导入失败",
                f"无法导入文件：{e}",
            )

    def _on_source_selected(self, row: int) -> None:
        if row < 0:
            self._delete_btn.setEnabled(False)
            self._use_in_run_btn.setEnabled(False)
            self._active_source_id = None
            self._chunks = []
            self._preview_title.setText("选择一份资料查看")
            self._chunk_count_lbl.setText("")
            self._chunk_list.setPlainText("")
            return

        item = self._source_list.item(row)
        src = item.data(Qt.ItemDataRole.UserRole)
        self._active_source_id = src.get("id")
        self._delete_btn.setEnabled(True)
        self._use_in_run_btn.setEnabled(True)

        title = src.get("title", "未知")
        self._preview_title.setText(title)
        self._chunk_count_lbl.setText(f"{src.get('chunk_count', 0)} chunks")

        # Load chunks
        try:
            from app.core.knowledge import KnowledgeService

            svc = KnowledgeService()
            raw_chunks = svc.get_chunks(self._active_source_id)
            self._chunks = [c if isinstance(c, dict) else c.to_dict() for c in raw_chunks]
        except Exception:
            self._chunks = []

        self._refresh_chunks()

    def _refresh_chunks(self) -> None:
        lines = []
        for i, chunk in enumerate(self._chunks):
            heading = chunk.get("heading") or "(无标题)"
            text = chunk.get("text", "")
            preview = _truncate(text, 200)
            lines.append(f"[{i + 1}] {heading}\n{preview}\n")
        self._chunk_list.setPlainText("\n".join(lines) if lines else "（无片段）")

    def _on_delete_source(self) -> None:
        if not self._active_source_id:
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            "删除后无法恢复。确定要删除这条资料吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from app.core.knowledge import KnowledgeService

            svc = KnowledgeService()
            svc.delete_source(self._active_source_id)
            self._sources = [s for s in self._sources if s.get("id") != self._active_source_id]
            self._refresh_source_list()
            self._on_source_selected(-1)
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"删除失败：{e}")

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            return
        try:
            from app.core.knowledge import KnowledgeService

            svc = KnowledgeService()
            raw_results = svc.search(query, top_k=10)
            results = []
            for item in raw_results:
                if isinstance(item, tuple):
                    chunk, score = item
                    chunk_dict = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk
                else:
                    chunk_dict = item
                    score = None
                heading = chunk_dict.get("heading") or "(无标题)"
                text = chunk_dict.get("text", "")
                preview = _truncate(text, 150)
                score_str = f" (相关度 {score:.2f})" if score is not None else ""
                results.append(f"## {heading}{score_str}\n{preview}\n")

            if results:
                self._results_list.setPlainText("\n".join(results))
            else:
                self._results_list.setPlainText("未找到相关片段。")
        except Exception as e:
            self._results_list.setPlainText(f"检索出错：{e}")

    def _on_use_in_run(self) -> None:
        """Emit sources_selected signal for use in paper generation."""
        if not self._active_source_id:
            return
        self.sources_selected.emit([self._active_source_id])
        QMessageBox.information(
            self,
            "已选择",
            "资料已选中，将在下次论文生成时注入上下文。\n"
            "你也可以在 AI 论文助手中进一步选择范围。",
        )
