"""RAG Search page — Vision 3.5.

BM25-powered search over KnowledgeStore chunks.
- Build chunk index from KnowledgeStore items
- Search with type filter
- Context bundle export for AI writing
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, _card_style


def _badge_style(color: str) -> str:
    return (
        f"QLabel {{ background-color: {color}; color: white;"
        f" border-radius: 8px; padding: 2px 8px;"
        f" font-size: {FontSize.CAPTION}px; font-weight: 600; }}"
    )


def _label(size: int, color: str, weight: str = "normal") -> str:
    return f"QLabel {{ font-size: {size}px; color: {color}; font-weight: {weight}; }}"


_ITEM_TYPE_COLORS: dict[str, str] = {
    "literature": "#7C3AED",
    "note": "#059669",
    "theory": "#D97706",
    "evidence": "#DC2626",
}

_ITEM_TYPE_LABELS: dict[str, str] = {
    "": "全部类型",
    "literature": "文献",
    "note": "笔记",
    "theory": "理论",
    "evidence": "证据",
}


class _RagResultCard(QFrame):
    """Card displaying one RAG search result."""

    def __init__(self, parent=None):
        super().__init__(parent)
        L = get_theme()
        self._badge_color = L.PRIMARY
        self.setStyleSheet(_card_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Header row: title + score + type badge
        header = QHBoxLayout()
        header.setSpacing(Spacing.SM)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        self.title_label.setWordWrap(True)
        header.addWidget(self.title_label, 1)

        self.type_badge = QLabel("")
        self.type_badge.setStyleSheet(_badge_style(L.PRIMARY))
        header.addWidget(self.type_badge)

        self.score_label = QLabel("")
        self.score_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        header.addWidget(self.score_label)

        layout.addLayout(header)

        # Source
        self.source_label = QLabel("")
        self.source_label.setStyleSheet(_label(FontSize.SMALL, L.PRIMARY))
        self.source_label.setWordWrap(True)
        layout.addWidget(self.source_label)

        # Snippet
        self.snippet_label = QLabel("")
        self.snippet_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self.snippet_label.setWordWrap(True)
        layout.addWidget(self.snippet_label)

    def set_result(self, title: str, source_id: str, score: float,
                   item_type: str, snippet: str) -> None:
        self.title_label.setText(title)
        self.source_label.setText(f"来源: {source_id}")
        self.score_label.setText(f"{score:.2f}")

        type_label = _ITEM_TYPE_LABELS.get(item_type, item_type)
        color = _ITEM_TYPE_COLORS.get(item_type, get_theme().PRIMARY)
        self._badge_color = color
        self.type_badge.setText(type_label)
        self.type_badge.setStyleSheet(_badge_style(color))

        # Truncate snippet for display
        display = snippet[:400].replace("\n", " ")
        if len(snippet) > 400:
            display += "..."
        self.snippet_label.setText(display)

    def apply_theme(self) -> None:
        """Re-apply styles using current theme tokens."""
        L = get_theme()
        self.setStyleSheet(_card_style())
        self.title_label.setStyleSheet(_label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold"))
        self.type_badge.setStyleSheet(_badge_style(getattr(self, '_badge_color', L.PRIMARY)))
        self.score_label.setStyleSheet(_label(FontSize.CAPTION, L.TEXT_SECONDARY))
        self.source_label.setStyleSheet(_label(FontSize.SMALL, L.PRIMARY))
        self.snippet_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))


class RagSearchPage(QWidget):
    """BM25 RAG search interface over KnowledgeStore chunks."""

    context_ready = pyqtSignal(str)  # emits context markdown bundle

    def __init__(self):
        super().__init__()
        from app.core.rag.service import RagService
        self._svc = RagService()
        self._results: list = []
        self._build_ui()
        self._reload()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    # ── UI build ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        L = get_theme()
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        self._header = PageHeader(
            "RAG 检索",
            "基于 BM25 的知识库语义搜索。索引来自知识库条目的 chunk，按关键词覆盖度评分。",
        )
        root.addWidget(self._header)

        # Search bar row
        search_row = QHBoxLayout()
        search_row.setSpacing(Spacing.SM)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入自然语言查询...")
        self._search_input.setMinimumHeight(36)
        self._search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self._search_input, 1)

        self._type_filter = QComboBox()
        self._type_filter.addItem(_ITEM_TYPE_LABELS[""], "")
        for tkey in ["literature", "note", "theory", "evidence"]:
            self._type_filter.addItem(_ITEM_TYPE_LABELS.get(tkey, tkey), tkey)
        self._type_filter.setMinimumHeight(36)
        search_row.addWidget(self._type_filter)

        self._search_btn = QPushButton("搜索")
        self._search_btn.setMinimumHeight(36)
        self._search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self._search_btn)

        self._rebuild_btn = QPushButton("重建索引")
        self._rebuild_btn.setMinimumHeight(36)
        self._rebuild_btn.clicked.connect(self._on_rebuild_index)
        search_row.addWidget(self._rebuild_btn)

        root.addLayout(search_row)

        # Progress bar (hidden by default)
        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(0)  # indeterminate
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        # Status bar
        status_row = QHBoxLayout()
        status_row.setSpacing(Spacing.LG)

        self._index_status = QLabel("")
        self._index_status.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        status_row.addWidget(self._index_status)

        self._result_count = QLabel("")
        self._result_count.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        status_row.addWidget(self._result_count)

        status_row.addStretch()

        self._context_btn = QPushButton("导出上下文 → AI 写作")
        self._context_btn.setMinimumHeight(32)
        self._context_btn.clicked.connect(self._on_export_context)
        self._context_btn.setVisible(False)
        status_row.addWidget(self._context_btn)

        root.addLayout(status_row)

        # Results area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {L.CANVAS}; }}"
        )

        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(Spacing.SM)
        self._results_layout.addStretch()

        self._scroll.setWidget(self._results_container)
        root.addWidget(self._scroll, 1)

        # Empty state
        self._empty_label = QLabel(
            "尚未建立索引。请点击「重建索引」或先在知识库中添加内容。"
        )
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)

    # ── theme ────────────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        """Re-apply all widget styles using current theme tokens."""
        L = get_theme()
        self._header.apply_theme()
        self._index_status.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._result_count.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {L.CANVAS}; }}"
        )
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        for card in getattr(self, '_result_cards', []):
            card.apply_theme()

    # ── data ──────────────────────────────────────────────────────────────

    def _reload(self) -> None:
        self._refresh_status()

    def _refresh_status(self) -> None:
        size = self._svc.index_size()
        if size > 0:
            self._index_status.setText(f"已索引 {size} 个 chunk")
        else:
            self._index_status.setText("索引为空")

    def _on_rebuild_index(self) -> None:
        item_type = self._type_filter.currentData() or None
        # Only use type filter for rebuild if explicitly selected
        self._progress.setVisible(True)
        self._progress.setMaximum(0)
        QApplication.processEvents()

        count = self._svc.build_index(item_type=None)

        self._progress.setVisible(False)
        self._index_status.setText(f"已索引 {count} 个 chunk（全量）")
        self._result_count.setText("")
        self._context_btn.setVisible(False)
        self._clear_results()

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            return

        # Rebuild index if empty
        if self._svc.index_size() == 0:
            self._svc.build_index()
            self._refresh_status()

        item_type = self._type_filter.currentData() or None
        self._results = self._svc.search(query, top_k=10, item_type=item_type)

        self._result_count.setText(f"找到 {len(self._results)} 条结果")
        self._context_btn.setVisible(len(self._results) > 0)
        self._refresh_results()

    def _on_export_context(self) -> None:
        query = self._search_input.text().strip()
        if not query:
            return
        bundle = self._svc.get_context_bundle(query, top_k=5)
        self.context_ready.emit(bundle)

        # Also copy to clipboard
        QApplication.clipboard().setText(bundle)

    # ── results rendering ─────────────────────────────────────────────────

    def _clear_results(self) -> None:
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _refresh_results(self) -> None:
        self._clear_results()
        self._result_cards = []
        for r in self._results:
            card = _RagResultCard()
            card.set_result(
                title=r.source_title,
                source_id=r.source_id,
                score=r.score,
                item_type=r.item_type,
                snippet=r.text,
            )
            self._result_cards.append(card)
            self._results_layout.insertWidget(
                self._results_layout.count() - 1, card
            )
