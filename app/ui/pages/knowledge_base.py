"""Knowledge Base page — personal academic knowledge management.

Features:
- Import files (txt/md/pdf/docx) → parsed sources + chunks
- Manual catalog items (literature/note/theory/evidence) → SQLite store
- Type filtering, search, preview, delete
- Batch Markdown/BibTeX import

PRD: PRD_KNOWLEDGE_BASE.md (Vision 3.1)
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
        self._sources: list[dict[str, Any]] = []
        self._items: list[dict[str, Any]] = []
        self._active_source_id: str | None = None
        self._active_item_id: str | None = None
        self._chunks: list = []
        self._mode: str = "sources"  # "sources" | "items"
        self._store = None  # KnowledgeStore, lazy init
        self._item_filter_type: str | None = None
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)
        QTimer.singleShot(0, self._load_all)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )

        self._content = QWidget()
        self._content.setStyleSheet(f"background-color: {L.CANVAS};")
        root = QVBoxLayout(self._content)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        self._header = PageHeader(
            "知识库",
            "导入文献、笔记、PDF，构建个人学术资料库，支持检索和上下文注入。",
        )
        root.addWidget(self._header)

        # Mode switcher
        mode_row = QHBoxLayout()
        self._mode_label = QLabel("视图模式：")
        self._mode_label.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
        )
        mode_row.addWidget(self._mode_label)
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("📁 文件资料", "sources")
        self._mode_combo.addItem("📋 目录条目", "items")
        self._mode_combo.setStyleSheet(
            f"QComboBox {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; min-width: 160px; }} "
            f"QComboBox:hover {{ border-color: {L.PRIMARY}; }} "
            f"QComboBox::drop-down {{ border: none; subcontrol-origin: padding; "
            f"subcontrol-position: top right; width: 20px; }}"
        )
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._mode_combo)
        mode_row.addStretch()
        root.addLayout(mode_row)

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

        self._scroll.setWidget(self._content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll)

    def _create_source_panel(self) -> QFrame:
        L = get_theme()
        self._source_panel = QFrame()
        self._source_panel.setFixedWidth(260)
        self._source_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(self._source_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Panel title
        self._src_title_label = QLabel("资料库")
        self._src_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._src_title_label)

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

        # --- Item mode: type filter + add button ---
        self._item_controls = QWidget()
        ic = QVBoxLayout(self._item_controls)
        ic.setContentsMargins(0, 0, 0, 0)
        ic.setSpacing(Spacing.SM)
        # Type filter combo
        type_row = QHBoxLayout()
        type_row.setSpacing(Spacing.XS)
        self._type_filter = QComboBox()
        self._type_filter.addItem("全部类型", None)
        self._type_filter.addItem("📄 文献", "literature")
        self._type_filter.addItem("📝 笔记", "note")
        self._type_filter.addItem("🔬 理论", "theory")
        self._type_filter.addItem("📊 证据", "evidence")
        self._type_filter.setStyleSheet(
            f"QComboBox {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: 2px 4px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; }}"
        )
        self._type_filter.currentIndexChanged.connect(self._on_item_type_changed)
        type_row.addWidget(self._type_filter)
        ic.addLayout(type_row)
        # Add item button
        self._add_item_btn = QPushButton("+ 添加条目")
        self._add_item_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._add_item_btn.clicked.connect(self._on_add_item)
        ic.addWidget(self._add_item_btn)
        # Import BibTeX / Markdown batch
        self._batch_import_btn = QPushButton("📥 批量导入 Markdown/BibTeX")
        self._batch_import_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.PRIMARY}; "
            f"border: 1px solid {L.PRIMARY}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SMALL}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; }}"
        )
        self._batch_import_btn.clicked.connect(self._on_batch_import)
        ic.addWidget(self._batch_import_btn)
        self._item_controls.setVisible(False)
        layout.addWidget(self._item_controls)

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

        # Item list (separate, toggled by mode)
        self._item_list = QListWidget()
        self._item_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._item_list.currentRowChanged.connect(self._on_item_selected)
        self._item_list.setVisible(False)
        layout.addWidget(self._item_list, 1)

        # Empty state
        self._empty_label = QLabel("暂无资料\n\n导入 PDF、文档或笔记\n构建你的知识库")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"padding: {Spacing.MD}px;"
        )
        layout.addWidget(self._empty_label)

        # Item empty state
        self._item_empty_label = QLabel("暂无条目\n\n手动添加或批量导入\n文献、笔记、理论、证据")
        self._item_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._item_empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"padding: {Spacing.MD}px;"
        )
        self._item_empty_label.setVisible(False)
        layout.addWidget(self._item_empty_label)

        # Delete button
        self._delete_btn = QPushButton("删除选中")
        self._delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.ERROR}; "
            f"border: 1px solid {L.ERROR}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.ERROR_BG}; }}"
        )
        self._delete_btn.clicked.connect(self._on_delete)
        self._delete_btn.setEnabled(False)
        layout.addWidget(self._delete_btn)

        return self._source_panel

    def _create_preview_panel(self) -> QFrame:
        L = get_theme()
        self._preview_panel = QFrame()
        self._preview_panel.setStyleSheet(_card_style(L))
        layout = QVBoxLayout(self._preview_panel)
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

        return self._preview_panel

    def _create_search_panel(self) -> QFrame:
        L = get_theme()
        self._search_panel = QFrame()
        self._search_panel.setFixedWidth(280)
        self._search_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        layout = QVBoxLayout(self._search_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Search title
        self._search_title_label = QLabel("全文检索")
        self._search_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._search_title_label)

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
        self._search_btn = QPushButton("检索")
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._search_btn.clicked.connect(self._on_search)
        layout.addWidget(self._search_btn)

        # Results list
        self._results_title_label = QLabel("检索结果")
        self._results_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._results_title_label)

        self._results_list = QTextEdit()
        self._results_list.setReadOnly(True)
        self._results_list.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.SECONDARY}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; }} "
            f"font-family: 'PingFang SC', sans-serif;"
        )
        layout.addWidget(self._results_list, 1)

        return self._search_panel

    # -------------------------------------------------------------------------
    # Theme support
    # -------------------------------------------------------------------------

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )
        self._content.setStyleSheet(f"background-color: {L.CANVAS};")

        # Header
        self._header.apply_theme()

        # Mode label + combo
        self._mode_label.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
        )
        self._mode_combo.setStyleSheet(
            f"QComboBox {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; min-width: 160px; }} "
            f"QComboBox:hover {{ border-color: {L.PRIMARY}; }} "
            f"QComboBox::drop-down {{ border: none; subcontrol-origin: padding; "
            f"subcontrol-position: top right; width: 20px; }}"
        )

        # Source panel
        self._source_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._src_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._import_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._type_filter.setStyleSheet(
            f"QComboBox {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: 2px 4px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; }}"
        )
        self._add_item_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._batch_import_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.PRIMARY}; "
            f"border: 1px solid {L.PRIMARY}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SMALL}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_LIGHT}; }}"
        )
        self._source_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._item_list.setStyleSheet(
            f"QListWidget {{ background-color: transparent; border: none; "
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY}; "
            f"outline: none; }} "
            f"QListWidget::item {{ padding: {Spacing.XS}px 0; }}"
            f"QListWidget::item:selected {{ background-color: {L.PRIMARY_LIGHT}; "
            f"color: {L.PRIMARY}; border-radius: {Radius.INPUT}px; }}"
        )
        self._empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"padding: {Spacing.MD}px;"
        )
        self._item_empty_label.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; "
            f"padding: {Spacing.MD}px;"
        )
        self._delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {L.ERROR}; "
            f"border: 1px solid {L.ERROR}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.ERROR_BG}; }}"
        )

        # Preview panel
        self._preview_panel.setStyleSheet(_card_style(L))
        self._preview_title.setStyleSheet(
            f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._chunk_count_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        self._chunk_list.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.BODY}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        self._use_in_run_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )

        # Search panel
        self._search_panel.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.PANEL}px; }}"
        )
        self._search_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }} "
            f"QLineEdit:focus {{ border-color: {L.PRIMARY}; }} "
            f"QLineEdit::placeholder {{ color: {L.TEXT_MUTED}; }}"
        )
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.MD}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._results_title_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._results_list.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; font-size: {FontSize.SECONDARY}px; "
            f"color: {L.TEXT_SECONDARY}; padding: {Spacing.SM}px; }} "
            f"font-family: 'PingFang SC', sans-serif;"
        )

    # -------------------------------------------------------------------------
    # Data loading
    # -------------------------------------------------------------------------

    def _get_store(self):
        if self._store is None:
            from app.core.knowledge.store import KnowledgeStore
            self._store = KnowledgeStore()
        return self._store

    def _load_all(self) -> None:
        self._load_sources()
        self._load_items()

    def _load_sources(self) -> None:
        try:
            from app.core.knowledge import KnowledgeService
            svc = KnowledgeService()
            raw = svc.list_sources()
            self._sources = [s if isinstance(s, dict) else s.to_dict() for s in raw]
        except Exception:
            self._sources = []
        self._refresh_source_list()

    def _load_items(self) -> None:
        try:
            store = self._get_store()
            raw = store.list(item_type=self._item_filter_type)
            self._items = [it.to_dict() for it in raw]
        except Exception:
            self._items = []
        if self._mode == "items":
            self._refresh_item_list()

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
        # Disable import button and show loading feedback
        self._import_btn.setEnabled(False)
        self._import_btn.setText("导入中...")
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
        finally:
            self._import_btn.setEnabled(True)
            self._import_btn.setText("+ 导入文件")

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
            if self._mode == "items":
                self._search_items(query)
            else:
                self._search_sources(query)
        except Exception as e:
            self._results_list.setPlainText(f"检索出错：{e}")

    def _search_sources(self, query: str) -> None:
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

    def _search_items(self, query: str) -> None:
        store = self._get_store()
        raw = store.search(query, limit=10)
        results = []
        type_icons = {"literature": "📄", "note": "📝", "theory": "🔬", "evidence": "📊"}
        for it in raw:
            icon = type_icons.get(it.item_type, "📋")
            title = it.title
            tags = ", ".join(it.tags[:5]) if it.tags else ""
            tag_str = f" [{tags}]" if tags else ""
            content_preview = _truncate(it.content, 120) if it.content else "(无内容)"
            results.append(
                f"## {icon} {title}{tag_str}\n"
                f"类型: {it.item_type} | 来源: {it.external_source}\n"
                f"{content_preview}\n"
            )
        if results:
            self._results_list.setPlainText("\n".join(results))
        else:
            self._results_list.setPlainText("未找到匹配的条目。")

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

    # ── Mode switching ───────────────────────────────────────────────────

    def _on_mode_changed(self, index: int) -> None:
        mode = self._mode_combo.currentData()
        if mode == self._mode:
            return
        self._mode = mode
        is_items = mode == "items"

        # Toggle visibility
        self._source_list.setVisible(not is_items)
        self._import_btn.setVisible(not is_items)
        self._empty_label.setVisible(not is_items and not self._sources)
        self._item_controls.setVisible(is_items)
        self._item_list.setVisible(is_items)
        self._item_empty_label.setVisible(is_items and not self._items)

        # Clear selection
        self._active_source_id = None
        self._active_item_id = None
        self._chunks = []
        self._delete_btn.setEnabled(False)
        self._use_in_run_btn.setEnabled(False)
        self._preview_title.setText("选择一份资料查看")
        self._chunk_count_lbl.setText("")
        self._chunk_list.setPlainText("")
        self._results_list.setPlainText("")

        # Reload if needed
        if is_items and not self._items:
            self._load_items()

    def _on_delete(self) -> None:
        if self._mode == "items":
            self._on_delete_item()
        else:
            self._on_delete_source()

    # ── Item mode handlers ───────────────────────────────────────────────

    def _on_item_type_changed(self, _index: int) -> None:
        self._item_filter_type = self._type_filter.currentData()
        self._load_items()

    def _refresh_item_list(self) -> None:
        self._item_list.clear()
        has_items = False
        type_icons = {"literature": "📄", "note": "📝", "theory": "🔬", "evidence": "📊"}
        for item in self._items:
            itype = item.get("item_type", "note")
            icon = type_icons.get(itype, "📋")
            title = item.get("title", "无标题")
            tags = item.get("tags", [])
            tag_str = f"  [{', '.join(tags[:3])}]" if tags else ""
            list_item = QListWidgetItem(f"{icon} {title}{tag_str}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self._item_list.addItem(list_item)
            has_items = True

        self._item_empty_label.setVisible(not has_items)
        self._item_list.setVisible(has_items)

    def _on_item_selected(self, row: int) -> None:
        if row < 0:
            self._delete_btn.setEnabled(False)
            self._use_in_run_btn.setEnabled(False)
            self._active_item_id = None
            self._preview_title.setText("选择一条目查看")
            self._chunk_count_lbl.setText("")
            self._chunk_list.setPlainText("")
            return

        item = self._item_list.item(row).data(Qt.ItemDataRole.UserRole)
        self._active_item_id = item.get("id")
        self._delete_btn.setEnabled(True)
        self._use_in_run_btn.setEnabled(False)

        title = item.get("title", "无标题")
        itype = item.get("item_type", "")
        type_icons = {"literature": "📄", "note": "📝", "theory": "🔬", "evidence": "📊"}
        icon = type_icons.get(itype, "")
        self._preview_title.setText(f"{icon} {title}")

        lines = []
        lines.append(f"类型: {itype}")
        tags = item.get("tags", [])
        if tags:
            lines.append(f"标签: {', '.join(tags)}")
        source = item.get("source_file", "")
        if source:
            lines.append(f"来源文件: {source}")
        external = item.get("external_source", "")
        if external and external != "manual":
            lines.append(f"来源: {external}")
        created = item.get("created_at", "")
        if created:
            lines.append(f"创建: {created[:16]}")
        lines.append("")
        content = item.get("content", "")
        if content:
            lines.append(content)
        else:
            lines.append("（无内容）")
        self._chunk_list.setPlainText("\n".join(lines))
        self._chunk_count_lbl.setText("")

    def _on_add_item(self) -> None:
        dialog = _AddItemDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        try:
            from app.core.knowledge.models import KnowledgeItem
            store = self._get_store()
            item = KnowledgeItem.create(
                item_type=data["item_type"],
                title=data["title"],
                content=data["content"],
                tags=data["tags"],
                external_source="manual",
            )
            store.add(item)
            item_dict = item.to_dict()
            self._items.insert(0, item_dict)
            if self._mode == "items":
                self._refresh_item_list()
                if self._item_list.count() > 0:
                    self._item_list.setCurrentRow(0)
        except Exception as e:
            QMessageBox.warning(self, "添加失败", f"添加条目失败：{e}")

    def _on_delete_item(self) -> None:
        if not self._active_item_id:
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            "删除后无法恢复。确定要删除这条目吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            store = self._get_store()
            store.delete(self._active_item_id)
            self._items = [i for i in self._items if i.get("id") != self._active_item_id]
            self._active_item_id = None
            self._delete_btn.setEnabled(False)
            self._preview_title.setText("选择一条目查看")
            self._chunk_count_lbl.setText("")
            self._chunk_list.setPlainText("")
            self._refresh_item_list()
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"删除失败：{e}")

    def _on_batch_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "批量导入 Markdown / BibTeX",
            str(Path.home()),
            "支持的文件 (*.md *.bib);;Markdown (*.md);;BibTeX (*.bib);;所有文件 (*.*)",
        )
        if not path:
            return
        filepath = Path(path)
        try:
            suffix = filepath.suffix.lower()
            if suffix in (".md", ".markdown"):
                from app.core.knowledge.importers import MarkdownImporter
                parsed = MarkdownImporter.parse_file(filepath)
            elif suffix == ".bib":
                from app.core.knowledge.importers import BibTeXImporter
                parsed = BibTeXImporter.parse_file(filepath)
            else:
                QMessageBox.warning(self, "格式不支持", f"不支持的文件格式：{filepath.suffix}")
                return

            if not parsed:
                QMessageBox.information(self, "无内容", "文件中未找到可导入的内容。")
                return

            store = self._get_store()
            count = 0
            for item in parsed:
                store.add(item)
                self._items.insert(0, item.to_dict())
                count += 1

            QMessageBox.information(
                self,
                "导入完成",
                f"成功导入 {count} 条记录。",
            )
            if self._mode == "items":
                self._refresh_item_list()
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"批量导入出错：{e}")


# ── Add Item Dialog ───────────────────────────────────────────────────────


class _AddItemDialog(QDialog):
    """Dialog for manually adding a knowledge catalog item."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        L = get_theme()
        self.setWindowTitle("添加知识条目")
        self.setMinimumWidth(480)
        self.setStyleSheet(
            f"_AddItemDialog {{ background-color: {L.SURFACE}; }}"
        )
        self._init_ui()

    def _init_ui(self) -> None:
        L = get_theme()
        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)

        form = QFormLayout()
        form.setSpacing(Spacing.SM)

        # Item type
        self._type_combo = QComboBox()
        self._type_combo.addItem("📄 文献", "literature")
        self._type_combo.addItem("📝 笔记", "note")
        self._type_combo.addItem("🔬 理论", "theory")
        self._type_combo.addItem("📊 证据", "evidence")
        self._type_combo.setStyleSheet(
            f"QComboBox {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        type_label = QLabel("类型：")
        type_label.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        form.addRow(type_label, self._type_combo)

        # Title
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("条目标题")
        self._title_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        title_label = QLabel("标题：")
        title_label.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        form.addRow(title_label, self._title_input)

        # Content
        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("内容（可选）")
        self._content_edit.setMinimumHeight(120)
        self._content_edit.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        content_label = QLabel("内容：")
        content_label.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        form.addRow(content_label, self._content_edit)

        # Tags
        self._tags_input = QLineEdit()
        self._tags_input.setPlaceholderText("标签，用逗号分隔（可选）")
        self._tags_input.setStyleSheet(
            f"QLineEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; }}"
        )
        tags_label = QLabel("标签：")
        tags_label.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        form.addRow(tags_label, self._tags_input)

        layout.addLayout(form)

        # Button box
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
        title = self._title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "缺少标题", "请填写条目标题。")
            return
        self.accept()

    def get_data(self) -> dict:
        tags_raw = self._tags_input.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        return {
            "item_type": self._type_combo.currentData(),
            "title": self._title_input.text().strip(),
            "content": self._content_edit.toPlainText().strip(),
            "tags": tags,
        }
