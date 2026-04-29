"""
preview_widget.py — 可编辑 A4 文档面板 (QWebEngineView + contentEditable)

特性:
  · 用户直接在 A4 纸张上打字，所见即所得
  · 工具栏格式化通过 JS execCommand 执行
  · 内容变更通过 WebChannel 通知 Python 端
  · 内部存储仍为 Markdown（HTML ↔ Markdown 双向转换）
"""

import logging
import os

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.constants import PREVIEW_STYLE_ACADEMIC
from app.core.html_to_markdown import html_to_markdown
from app.core.markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)


# ======================================================================
# JS Bridge — for content editing communication
# ======================================================================


class _ContentBridge(QObject):
    """Exposed to JS as 'bridge'. Receives content changes and cursor info."""

    content_changed = pyqtSignal(str)  # emits inner HTML
    cursor_info_updated = pyqtSignal(int, int)  # word_count, char_count
    cursor_position_updated = pyqtSignal(int, int)  # line, column
    page_ready = pyqtSignal()  # emitted when page is fully loaded
    format_state_changed = pyqtSignal(str)  # JSON format state
    ai_dialog_requested = pyqtSignal()  # Ctrl+I AI shortcut
    smart_modify_accepted = pyqtSignal(str)  # AI smart modify accepted (ai_id)
    smart_modify_rejected = pyqtSignal(str)  # AI smart modify rejected (ai_id)
    find_replace_requested = pyqtSignal(str)  # Ctrl+F/H from JS

    @pyqtSlot(str)
    def reportContentChanged(self, html: str):
        self.content_changed.emit(html)

    @pyqtSlot(int, int)
    def reportCursorInfo(self, words: int, chars: int):
        self.cursor_info_updated.emit(words, chars)

    @pyqtSlot(int, int)
    def reportCursorPosition(self, line: int, col: int):
        self.cursor_position_updated.emit(line, col)

    @pyqtSlot()
    def reportPageReady(self):
        self.page_ready.emit()

    @pyqtSlot(str)
    def reportFormatState(self, state: str):
        self.format_state_changed.emit(state)

    @pyqtSlot()
    def requestAiDialog(self):
        self.ai_dialog_requested.emit()

    @pyqtSlot(str)
    def acceptSmartModify(self, ai_id: str):
        self.smart_modify_accepted.emit(ai_id)

    @pyqtSlot(str)
    def rejectSmartModify(self, ai_id: str):
        self.smart_modify_rejected.emit(ai_id)

    @pyqtSlot(str)
    def requestFindReplace(self, mode: str):
        self.find_replace_requested.emit(mode)


# ======================================================================
# CSS Loader
# ======================================================================

_CSS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resources",
)


def _load_css(filename: str) -> str:
    path = os.path.join(_CSS_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("CSS 文件缺失: %s", path)
        return ""


def _load_js(filename: str) -> str:
    path = os.path.join(_CSS_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("JS 文件缺失: %s", path)
        return ""


# ======================================================================
# Editable Preview Widget
# ======================================================================


class PreviewWidget(QWidget):
    """Editable A4 document panel powered by QWebEngineView + contentEditable."""

    # Signals for MainWindow
    content_changed = pyqtSignal(str)  # emits inner HTML when user edits
    cursor_info_updated = pyqtSignal(int, int)  # word_count, char_count
    cursor_position_updated = pyqtSignal(int, int)  # line, column
    format_state_changed = pyqtSignal(str)  # JSON format state
    ai_dialog_requested = pyqtSignal()  # Ctrl+I AI shortcut
    smart_modify_accepted = pyqtSignal(str)  # AI smart modify accepted (ai_id)
    smart_modify_rejected = pyqtSignal(str)  # AI smart modify rejected (ai_id)
    find_replace_requested = pyqtSignal(str)  # Ctrl+F/H find dialog

    def __init__(self, parent=None):
        super().__init__(parent)
        self._preset = PREVIEW_STYLE_ACADEMIC
        self._doc_css = _load_css("document_preview.css")
        self._pygments_css = MarkdownRenderer.get_pygments_css()
        self._chart_edit_js = _load_js("chart_edit.js")
        self._renderer = MarkdownRenderer()
        self._page_loaded = False
        self._pending_content = None  # markdown to set after page loads
        self._renderer_crashed = False  # track renderer process state

        self._init_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QWebEngineView()
        settings = self._view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        # 允许本地页面加载远程图片 URL（AI 插图功能必需）
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        # ── Performance: enable hardware acceleration & compositing ──
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        layout.addWidget(self._view)

        # WebChannel for content bridge
        self._bridge = _ContentBridge()
        self._bridge.content_changed.connect(lambda html: self.content_changed.emit(html))
        self._bridge.cursor_info_updated.connect(lambda w, c: self.cursor_info_updated.emit(w, c))
        self._bridge.cursor_position_updated.connect(
            lambda line, col: self.cursor_position_updated.emit(line, col)
        )
        self._bridge.page_ready.connect(self._on_page_ready)
        self._bridge.format_state_changed.connect(lambda s: self.format_state_changed.emit(s))
        self._bridge.ai_dialog_requested.connect(lambda: self.ai_dialog_requested.emit())
        self._bridge.smart_modify_accepted.connect(
            lambda ai_id: self.smart_modify_accepted.emit(ai_id)
        )
        self._bridge.smart_modify_rejected.connect(
            lambda ai_id: self.smart_modify_rejected.emit(ai_id)
        )
        self._bridge.find_replace_requested.connect(
            lambda mode: self.find_replace_requested.emit(mode)
        )

        self._channel = QWebChannel()
        self._channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(self._channel)

        # Handle renderer process crashes
        self._view.page().renderProcessTerminated.connect(self._on_renderer_crash)

        # Load the editable page — base URL points to resources/ so
        # relative paths (e.g. katex/katex.min.css) resolve correctly.
        self._base_url = QUrl.fromLocalFile(_CSS_DIR + os.sep)
        full_html = self._build_html("")
        self._view.setHtml(full_html, self._base_url)

    # ------------------------------------------------------------------
    # JavaScript for the editable document
    # ------------------------------------------------------------------

    _JS_EDITOR = r"""
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
    var bridge = null;
    var _contentChangeTimer = null;
    var _statsTimer = null;
    var _formatTimer = null;
    var _savedRange = null;
    var _imgOverlay = null;
    var _selectedImg = null;
    var _imgResizing = false;
    var _imgHandle = '';
    var _imgStartX = 0, _imgStartY = 0, _imgStartW = 0, _imgStartH = 0;
    var _paginationTimer = null;
    var _suppressContentChange = false;
    var _lastPageCount = 1;

    // ── AI auto-scroll state ──
    var _aiAutoScroll = true;
    var _aiScrollUpCount = 0;
    var _aiStreaming = false;

    // ── Cached selection context (survives focus loss to toolbar) ──
    var _cachedSelectionCtx = null;

    new QWebChannel(qt.webChannelTransport, function(channel) {
        bridge = channel.objects.bridge;
        bridge.reportPageReady();
    });

    // ── Content change detection ──
    var editorEl = null;

    function initEditor() {
        editorEl = document.getElementById('editor-content');
        if (!editorEl) return;

        editorEl.addEventListener('input', function() {
            scheduleContentReport();
            scheduleStatsReport();
        });

        // Paste handler: clean HTML on paste, support image paste
        editorEl.addEventListener('paste', function(e) {
            if (e.clipboardData) {
                // Check for pasted image files (e.g. Ctrl+V screenshot)
                var items = e.clipboardData.items;
                for (var i = 0; i < items.length; i++) {
                    if (items[i].type.indexOf('image') !== -1) {
                        e.preventDefault();
                        var blob = items[i].getAsFile();
                        if (!blob) continue;
                        var reader = new FileReader();
                        reader.onload = function(evt) {
                            var dataUri = evt.target.result;
                            var imgHtml = '<img src="' + dataUri + '" alt="\u7c98\u8d34\u56fe\u7247" style="max-width:100%">';
                            document.execCommand('insertHTML', false, imgHtml);
                            scheduleContentReport();
                            scheduleStatsReport();
                        };
                        reader.readAsDataURL(blob);
                        return;
                    }
                }
            }
            e.preventDefault();
            var text = '';
            if (e.clipboardData) {
                // Prefer HTML, but clean it
                var html = e.clipboardData.getData('text/html');
                if (html) {
                    // Strip scripts, styles, and class/id attributes
                    var temp = document.createElement('div');
                    temp.innerHTML = html;
                    // Remove script/style tags
                    var scripts = temp.querySelectorAll('script, style, meta, link');
                    scripts.forEach(function(s) { s.remove(); });
                    // Remove class/id/data attributes
                    var allEls = temp.querySelectorAll('*');
                    allEls.forEach(function(el) {
                        var attrs = Array.from(el.attributes);
                        attrs.forEach(function(attr) {
                            if (attr.name !== 'style' && attr.name !== 'href' &&
                                attr.name !== 'src' && attr.name !== 'alt') {
                                el.removeAttribute(attr.name);
                            }
                        });
                    });
                    document.execCommand('insertHTML', false, temp.innerHTML);
                } else {
                    text = e.clipboardData.getData('text/plain');
                    document.execCommand('insertText', false, text);
                }
            }
            scheduleContentReport();
            scheduleStatsReport();
        });

        // Keyboard shortcuts for undo/redo handled natively by contentEditable

        // ── Keyboard shortcuts: Ctrl+I (AI), Ctrl+F (Find), Ctrl+H (Replace) ──
        editorEl.addEventListener('keydown', function(e) {
            if (e.ctrlKey && !e.shiftKey && !e.altKey) {
                if (e.key === 'i' || e.key === 'I') {
                    e.preventDefault();
                    e.stopPropagation();
                    if (bridge) bridge.requestAiDialog();
                    return;
                }
                if (e.key === 'f' || e.key === 'F') {
                    e.preventDefault();
                    e.stopPropagation();
                    if (bridge) bridge.requestFindReplace('find');
                    return;
                }
                if (e.key === 'h' || e.key === 'H') {
                    e.preventDefault();
                    e.stopPropagation();
                    if (bridge) bridge.requestFindReplace('replace');
                    return;
                }
            }
        });

        // ── Keyboard handler: exit block elements ──
        editorEl.addEventListener('keydown', function(e) {
            if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey) return;
            var sel = window.getSelection();
            if (!sel.rangeCount) return;
            var node = sel.anchorNode;

            // --- PRE (code block) ---
            var pre = _closestTag(node, 'PRE');
            if (pre && editorEl.contains(pre)) {
                e.preventDefault();
                var fullText = pre.textContent || '';
                // Empty code block -> remove and exit
                if (!fullText.trim()) {
                    _exitBlock(pre, true);
                    scheduleContentReport();
                    return;
                }
                // Get text before cursor
                var r = sel.getRangeAt(0);
                var preRange = document.createRange();
                preRange.selectNodeContents(pre);
                preRange.setEnd(r.startContainer, r.startOffset);
                var before = preRange.toString();
                var afterCursor = fullText.substring(before.length);
                // At end with empty last line -> exit
                if (before.endsWith('\n') && !afterCursor.trim()) {
                    pre.textContent = fullText.replace(/\n+$/, '');
                    if (!pre.textContent.trim()) _exitBlock(pre, true);
                    else _exitBlock(pre, false);
                    scheduleContentReport();
                    return;
                }
                // Normal newline inside pre
                document.execCommand('insertText', false, '\n');
                scheduleContentReport();
                return;
            }

            // --- BLOCKQUOTE ---
            var bq = _closestTag(node, 'BLOCKQUOTE');
            if (bq && editorEl.contains(bq)) {
                // Find current block-level child inside blockquote
                var current = node;
                while (current.parentNode && current.parentNode !== bq && current.parentNode !== editorEl) {
                    current = current.parentNode;
                }
                var lineText = (current.textContent || '').trim();
                if (!lineText) {
                    e.preventDefault();
                    if (current !== bq) current.remove();
                    if (!bq.textContent.trim()) _exitBlock(bq, true);
                    else _exitBlock(bq, false);
                    scheduleContentReport();
                    return;
                }
            }
        });

        // ── Image interaction ──
        editorEl.addEventListener('click', function(e) {
            var t = e.target;
            if (t.tagName === 'IMG' && editorEl.contains(t)) {
                e.preventDefault();
                e.stopPropagation();
                _selectImg(t);
                return;
            }
            // Click on TD/TH: enter cell editing, deselect any selected table
            if ((t.tagName === 'TD' || t.tagName === 'TH') && editorEl.contains(t)) {
                if (_selectedTable) _deselectTableEl();
                return;
            }
            // Click directly on TABLE / TBODY / THEAD / TFOOT / TR: select whole table
            if ((t.tagName === 'TABLE' || t.tagName === 'TBODY' || t.tagName === 'THEAD' ||
                 t.tagName === 'TFOOT' || t.tagName === 'TR') && editorEl.contains(t)) {
                var tbl = _findTableFromNode(t);
                if (tbl) {
                    e.preventDefault();
                    _deselectImg();
                    _selectTableEl(tbl);
                    return;
                }
            }
            // Click elsewhere: deselect table
            if (_selectedTable) _deselectTableEl();
        });
        document.addEventListener('mousedown', function(e) {
            var t = e.target;
            if (_selectedImg) {
                if (t !== _selectedImg && !(t.nodeType === 1 &&
                    (t.classList.contains('img-handle') || t.classList.contains('img-mover')))) {
                    _deselectImg();
                    editorEl.focus();
                }
            }
            if (_selectedTable) {
                if (!_selectedTable.contains(t)) {
                    _deselectTableEl();
                }
            }
            // Hide context menu when clicking outside it
            if (_ctxMenu && _ctxMenu.style.display === 'block' && !_ctxMenu.contains(t)) {
                _hideContextMenu();
            }
        });
        editorEl.addEventListener('keydown', function(e) {
            if (_selectedImg && (e.key === 'Delete' || e.key === 'Backspace')) {
                e.preventDefault();
                var img = _selectedImg;
                _deselectImg();
                img.remove();
                editorEl.focus();
                scheduleContentReport();
            } else if (!_selectedTable && !_selectedImg && e.key === 'Escape' && _activeTable) {
                // Escape while cursor is inside a table: select the whole table
                e.preventDefault();
                _selectTableEl(_activeTable);
            }
        });

        // ── Tab key in table cells: prevent browser default new-row creation ──
        editorEl.addEventListener('keydown', function(e) {
            if (e.key !== 'Tab' || e.ctrlKey || e.altKey || e.metaKey) return;
            var sel = window.getSelection();
            if (!sel.rangeCount) return;
            var node = sel.anchorNode;
            var td = _closestTag(node, 'TD') || _closestTag(node, 'TH');
            if (!td || !editorEl.contains(td)) return;
            e.preventDefault();
            var table = _findTableFromNode(td);
            if (!table) return;
            var allCells = Array.from(table.querySelectorAll('th, td'));
            var idx = allCells.indexOf(td);
            if (e.shiftKey) {
                if (idx > 0) {
                    var prev = allCells[idx - 1];
                    var r = document.createRange();
                    r.selectNodeContents(prev); r.collapse(false);
                    sel.removeAllRanges(); sel.addRange(r);
                }
            } else {
                if (idx < allCells.length - 1) {
                    var next = allCells[idx + 1];
                    var r = document.createRange();
                    r.selectNodeContents(next); r.collapse(false);
                    sel.removeAllRanges(); sel.addRange(r);
                } else {
                    // Last cell: move cursor to paragraph after table
                    var after = table.nextElementSibling;
                    if (!after || !editorEl.contains(after)) {
                        after = document.createElement('p');
                        after.innerHTML = '<br>';
                        editorEl.appendChild(after);
                        scheduleContentReport();
                    }
                    var r = document.createRange();
                    r.setStart(after, 0); r.collapse(true);
                    sel.removeAllRanges(); sel.addRange(r);
                }
            }
        });
        document.addEventListener('mousemove', function(e) {
            if (!_imgResizing || !_selectedImg) return;
            e.preventDefault();
            var dx = e.clientX - _imgStartX;
            var ratio = _imgStartH / _imgStartW;
            var newW;
            if (_imgHandle === 'se' || _imgHandle === 'ne') {
                newW = Math.max(30, _imgStartW + dx);
            } else {
                newW = Math.max(30, _imgStartW - dx);
            }
            var newH = Math.round(newW * ratio);
            _selectedImg.style.width = newW + 'px';
            _selectedImg.style.height = newH + 'px';
            _selectedImg.removeAttribute('width');
            _selectedImg.removeAttribute('height');
            _positionImgOverlay();
        });
        document.addEventListener('mouseup', function() {
            if (_imgResizing) {
                _imgResizing = false;
                scheduleContentReport();
            }
        });
        window.addEventListener('scroll', function() {
            if (_selectedImg) _positionImgOverlay();
        }, true);
        editorEl.addEventListener('dragover', function(e) {
            if (_selectedImg) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            }
        });
        editorEl.addEventListener('drop', function(e) {
            if (_selectedImg && e.dataTransfer.getData('text/plain') === 'img-move') {
                e.preventDefault();
                var range = null;
                if (document.caretRangeFromPoint) {
                    range = document.caretRangeFromPoint(e.clientX, e.clientY);
                }
                if (range) {
                    var img = _selectedImg;
                    var oldParent = img.parentNode;
                    _deselectImg();
                    // Remove from old position before inserting at new
                    if (oldParent) oldParent.removeChild(img);
                    range.insertNode(img);
                    _selectImg(img);
                }
                scheduleContentReport();
            }
        });

        // ── AI auto-scroll: wheel listener ──
        window.addEventListener('wheel', function(e) {
            if (!_aiStreaming) return;
            if (e.deltaY < 0) {
                // User scrolled UP
                _aiScrollUpCount++;
                if (_aiScrollUpCount >= 2) {
                    _aiAutoScroll = false;
                }
            } else if (e.deltaY > 0) {
                // User scrolled DOWN — check if near bottom, resume
                var scrollBottom = window.innerHeight + window.pageYOffset;
                var docHeight = document.documentElement.scrollHeight;
                if (docHeight - scrollBottom < 80) {
                    _aiAutoScroll = true;
                    _aiScrollUpCount = 0;
                }
            }
        }, {passive: true});

        // ── Chart interaction (click-to-select + delete) ──
        var _selectedChart = null;

        function _findChartFromNode(node) {
            while (node && node !== editorEl) {
                if (node.nodeType === 1 && node.classList &&
                    node.classList.contains('chart-container')) return node;
                node = node.parentNode;
            }
            return null;
        }

        function _selectChart(chart) {
            _deselectChart();
            _selectedChart = chart;
            chart.style.outline = '2px solid #4A90D9';
            chart.style.outlineOffset = '3px';
            chart.style.borderRadius = '6px';
        }

        function _deselectChart() {
            if (_selectedChart) {
                _selectedChart.style.outline = '';
                _selectedChart.style.outlineOffset = '';
                _selectedChart = null;
            }
        }

        function _deleteChart(chart) {
            var next = chart.nextElementSibling;
            if (!chart.previousElementSibling && !chart.nextElementSibling) {
                var p = document.createElement('p');
                p.innerHTML = '<br>';
                chart.parentNode.insertBefore(p, chart);
                next = p;
            }
            chart.remove();
            _selectedChart = null;
            if (next && editorEl.contains(next)) {
                var sel = window.getSelection();
                var r = document.createRange();
                r.selectNodeContents(next); r.collapse(true);
                sel.removeAllRanges(); sel.addRange(r);
            }
            editorEl.focus();
            scheduleContentReport();
        }

        editorEl.addEventListener('click', function(e) {
            var chart = _findChartFromNode(e.target);
            if (chart) {
                e.preventDefault();
                e.stopPropagation();
                _deselectImg();
                if (_selectedTable) _deselectTableEl();
                _selectChart(chart);
                // Inline edit: find data-ce element under cursor
                if (chart.getAttribute('data-chart-type')) {
                    var ceEl = e.target;
                    while (ceEl && ceEl !== chart) {
                        if (ceEl.getAttribute && ceEl.getAttribute('data-ce')) break;
                        ceEl = ceEl.parentNode;
                    }
                    if (ceEl && ceEl !== chart && ceEl.getAttribute && ceEl.getAttribute('data-ce')) {
                        if (typeof window._openInlineEdit === 'function') {
                            window._openInlineEdit(chart, ceEl);
                        }
                    }
                }
                return;
            }
            // Click elsewhere deselect chart
            if (_selectedChart && !_selectedChart.contains(e.target)) {
                _deselectChart();
            }
        }, true);

        // ── Chart double-click to edit ──
        editorEl.addEventListener('dblclick', function(e) {
            var chart = _findChartFromNode(e.target);
            if (chart && chart.getAttribute('data-chart-type') && typeof window._openChartEditor === 'function') {
                e.preventDefault();
                e.stopPropagation();
                window._openChartEditor(chart);
            }
        }, true);

        editorEl.addEventListener('keydown', function(e) {
            if (_selectedChart && (e.key === 'Delete' || e.key === 'Backspace')) {
                e.preventDefault();
                var chart = _selectedChart;
                _deleteChart(chart);
            }
        });

        document.addEventListener('mousedown', function(e) {
            if (_selectedChart && !_selectedChart.contains(e.target)) {
                // Don't deselect if clicking context menu
                if (_ctxMenu && _ctxMenu.contains(e.target)) return;
                _deselectChart();
            }
        });

        // ── Table interaction ──
        var _activeTable = null;
        var _selectedTable = null;

        function _deleteActiveTable() {
            if (!_activeTable) return;
            var tbl = _activeTable;
            var next = tbl.nextElementSibling;
            _hideTableToolbar();
            // Insert empty paragraph if table is the only content
            if (!tbl.previousElementSibling && !tbl.nextElementSibling) {
                var p = document.createElement('p');
                p.innerHTML = '<br>';
                tbl.parentNode.insertBefore(p, tbl);
                next = p;
            }
            tbl.remove();
            // Move cursor
            if (next && editorEl.contains(next)) {
                var sel = window.getSelection();
                var r = document.createRange();
                r.selectNodeContents(next);
                r.collapse(true);
                sel.removeAllRanges();
                sel.addRange(r);
            }
            editorEl.focus();
            scheduleContentReport();
        }

        function _tableAddRow() {
            if (!_activeTable) return;
            var tbody = _activeTable.querySelector('tbody') || _activeTable;
            var lastRow = tbody.rows[tbody.rows.length - 1];
            var cols = lastRow ? lastRow.cells.length : 1;
            var tr = document.createElement('tr');
            for (var i = 0; i < cols; i++) {
                var td = document.createElement('td');
                td.innerHTML = '<br>';
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
            scheduleContentReport();
        }

        function _tableAddCol() {
            if (!_activeTable) return;
            var rows = _activeTable.rows;
            for (var i = 0; i < rows.length; i++) {
                var cell = (i === 0 && rows[i].parentNode.tagName === 'THEAD')
                    ? document.createElement('th')
                    : document.createElement('td');
                cell.innerHTML = (i === 0) ? ('\u5217' + (rows[i].cells.length + 1)) : '<br>';
                rows[i].appendChild(cell);
            }
            scheduleContentReport();
        }

        function _showTableToolbar(table) {
            _activeTable = table;
        }

        function _hideTableToolbar() {
            _activeTable = null;
        }

        function _selectTableEl(table) {
            if (_selectedTable === table) return;
            _deselectTableEl();
            _selectedTable = table;
            table.classList.add('table-selected');
            _activeTable = table;
            // Clear cursor — document-level keydown handles Delete
            var sel = window.getSelection();
            sel.removeAllRanges();
        }

        function _deselectTableEl() {
            if (_selectedTable) {
                _selectedTable.classList.remove('table-selected');
                _selectedTable = null;
            }
            _hideTableToolbar();
        }

        function _findTableFromNode(node) {
            while (node && node !== editorEl) {
                if (node.nodeType === 1 && node.tagName === 'TABLE') return node;
                node = node.parentNode;
            }
            return null;
        }

        // ── Table context menu (right-click) ──
        var _ctxMenu = null;
        var _ctxTable = null;

        function _initContextMenu() {
            _ctxMenu = document.createElement('div');
            _ctxMenu.id = 'table-ctx-menu';
            _ctxMenu.contentEditable = 'false';
            _ctxMenu.addEventListener('mousedown', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var item = e.target;
                while (item && item !== _ctxMenu && !item.getAttribute('data-action')) {
                    item = item.parentNode;
                }
                var action = item ? item.getAttribute('data-action') : null;
                var tbl = _ctxTable;
                var cht = _ctxChart;
                _hideContextMenu();
                if (action === 'del-chart' && cht) {
                    _deleteChart(cht);
                    return;
                }
                if (action === 'edit-chart' && cht) {
                    if (typeof window._openChartEditor === 'function') window._openChartEditor(cht);
                    return;
                }
                if (!tbl || !action) return;
                _activeTable = tbl;
                if (action === 'add-row') {
                    _tableAddRow();
                } else if (action === 'add-col') {
                    _tableAddCol();
                } else if (action === 'del-tbl') {
                    if (_selectedTable === tbl) {
                        _selectedTable = null;
                        tbl.classList.remove('table-selected');
                    }
                    _deleteActiveTable();
                }
            });
            document.body.appendChild(_ctxMenu);
        }
        var _ctxChart = null;

        function _showContextMenu(x, y, table, chart) {
            if (!_ctxMenu) _initContextMenu();
            _ctxTable = table || null;
            _ctxChart = chart || null;
            // Build menu items dynamically based on target
            if (chart) {
                var hasConfig = chart.getAttribute('data-chart-type');
                _ctxMenu.innerHTML =
                    (hasConfig ? '<div class="ctx-item" data-action="edit-chart">\u270f\ufe0f \u7f16\u8f91\u6570\u636e</div>' : '') +
                    '<div class="ctx-item ctx-danger" data-action="del-chart">\ud83d\uddd1 \u5220\u9664\u6570\u636e\u56fe</div>';
            } else {
                _ctxMenu.innerHTML =
                    '<div class="ctx-item" data-action="add-row">\u2795 \u6dfb\u52a0\u884c</div>' +
                    '<div class="ctx-item" data-action="add-col">\u2795 \u6dfb\u52a0\u5217</div>' +
                    '<div class="ctx-sep"></div>' +
                    '<div class="ctx-item ctx-danger" data-action="del-tbl">\u5220\u9664\u8868\u683c</div>';
            }
            _ctxMenu.style.left = x + 'px';
            _ctxMenu.style.top = y + 'px';
            _ctxMenu.style.display = 'block';
            // Clamp to viewport
            setTimeout(function() {
                if (!_ctxMenu) return;
                if (x + _ctxMenu.offsetWidth > window.innerWidth)
                    _ctxMenu.style.left = (x - _ctxMenu.offsetWidth) + 'px';
                if (y + _ctxMenu.offsetHeight > window.innerHeight)
                    _ctxMenu.style.top = (y - _ctxMenu.offsetHeight) + 'px';
            }, 0);
        }

        function _hideContextMenu() {
            _ctxTable = null;
            _ctxChart = null;
            if (_ctxMenu) _ctxMenu.style.display = 'none';
        }

        // contextmenu event on table or chart elements
        editorEl.addEventListener('contextmenu', function(e) {
            // Check chart first
            var chart = _findChartFromNode(e.target);
            if (chart) {
                e.preventDefault();
                e.stopPropagation();
                _selectChart(chart);
                _showContextMenu(e.pageX, e.pageY, null, chart);
                return;
            }
            var tbl = _findTableFromNode(e.target);
            if (!tbl) return;
            e.preventDefault();
            e.stopPropagation();
            _selectTableEl(tbl);
            _showContextMenu(e.pageX, e.pageY, tbl, null);
        });

        // ── Table: document-level keydown (fires even without a cursor in editorEl) ──
        document.addEventListener('keydown', function(e) {
            if (!_selectedTable) return;
            if (e.key === 'Delete' || e.key === 'Backspace') {
                e.preventDefault();
                var tbl = _selectedTable;
                _selectedTable = null;
                tbl.classList.remove('table-selected');
                _activeTable = tbl;
                _deleteActiveTable();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                _deselectTableEl();
                editorEl.focus();
            }
        });

        // ── Clear cached selection when user clicks inside editor ──
        // (clicking toolbar/GPT button does NOT trigger this, so cache survives)
        editorEl.addEventListener('mousedown', function() {
            _cachedSelectionCtx = null;
        });

        // Helper: get HTML string from a Range
        function _rangeToHTML(range) {
            try {
                var frag = range.cloneContents();
                var tmp = document.createElement('div');
                tmp.appendChild(frag);
                return tmp.innerHTML;
            } catch(e) { return ''; }
        }

        // ── Format state tracking & selection persistence ──
        document.addEventListener('selectionchange', function() {
            _scheduleFormatReport();
            _reportCursorPosition();
            var sel = window.getSelection();
            if (sel.rangeCount > 0 && editorEl.contains(sel.anchorNode)) {
                _savedRange = sel.getRangeAt(0).cloneRange();

                // Cache full context as plain strings whenever there's a
                // non-collapsed selection. Plain strings survive focus loss
                // (unlike live Range objects which can become invalid).
                if (!_savedRange.collapsed) {
                    var selText = sel.toString() || '';
                    if (selText) {
                        var ctx = {
                            selectedText: selText,
                            selectedHTML: _rangeToHTML(_savedRange),
                            hasSelection: true,
                            textBefore: '',
                            textAfter: ''
                        };
                        try {
                            var preR = document.createRange();
                            preR.selectNodeContents(editorEl);
                            preR.setEnd(_savedRange.startContainer, _savedRange.startOffset);
                            ctx.textBefore = preR.toString().slice(-1000);
                        } catch(e) {}
                        try {
                            var postR = document.createRange();
                            postR.selectNodeContents(editorEl);
                            postR.setStart(_savedRange.endContainer, _savedRange.endOffset);
                            ctx.textAfter = postR.toString().slice(0, 400);
                        } catch(e) {}
                        _cachedSelectionCtx = ctx;
                    }
                }

                // Table toolbar: show/hide
                var tbl = _findTableFromNode(sel.anchorNode);
                if (tbl) {
                    _showTableToolbar(tbl);
                } else {
                    _hideTableToolbar();
                    // Cursor moved outside any table: clear table selection
                    if (_selectedTable) {
                        _selectedTable.classList.remove('table-selected');
                        _selectedTable = null;
                    }
                }
            }
        });

        scheduleStatsReport();
    }

    function scheduleContentReport() {
        if (_suppressContentChange) return;
        if (_contentChangeTimer) clearTimeout(_contentChangeTimer);
        _contentChangeTimer = setTimeout(function() {
            try {
            if (bridge && editorEl) {
                bridge.reportContentChanged(_getCleanHTML());
            }
            } catch(e) { console.error('content report error', e); }
        }, 300);
        _schedulePagination();
    }

    function scheduleStatsReport() {
        if (_statsTimer) clearTimeout(_statsTimer);
        _statsTimer = setTimeout(function() {
            try {
            if (bridge && editorEl) {
                var text = editorEl.innerText || '';
                // Count Chinese chars + English words
                var cjkRe = /[\u4e00-\u9fff\u3400-\u4dbf]/g;
                var chineseChars = (text.match(cjkRe) || []).length;
                var englishWords = text.replace(cjkRe, ' ')
                    .split(/\s+/).filter(function(w) { return w.length > 0; }).length;
                var wordCount = chineseChars + englishWords;
                var charCount = text.replace(/\s/g, '').length;
                bridge.reportCursorInfo(wordCount, charCount);
                // Report cursor line/column
                _reportCursorPosition();
            }
            } catch(e) { console.error('stats error', e); }
        }, 500);
    }

    function _reportCursorPosition() {
        try {
            if (!bridge || !editorEl) return;
            var sel = window.getSelection();
            if (!sel.rangeCount || !editorEl.contains(sel.anchorNode)) return;
            var range = document.createRange();
            range.selectNodeContents(editorEl);
            range.setEnd(sel.anchorNode, sel.anchorOffset);
            var before = range.toString();
            var lines = before.split('\n');
            var line = lines.length;
            var col = lines[lines.length - 1].length + 1;
            bridge.reportCursorPosition(line, col);
        } catch(e) {}
    }

    // ── Restore selection ──
    function _restoreSelection() {
        editorEl.focus();
        // Always restore from saved range — toolbar clicks lose the real cursor
        if (_savedRange) {
            try {
                if (editorEl.contains(_savedRange.startContainer)) {
                    var sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(_savedRange);
                    return;
                }
            } catch(e) {}
        }
        // Fallback: ensure a cursor exists somewhere in the editor
        var sel = window.getSelection();
        if (!sel.rangeCount || !editorEl.contains(sel.anchorNode)) {
            try {
                var range = document.createRange();
                range.selectNodeContents(editorEl);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            } catch(e) {}
        }
    }

    // ── Format commands ──
    function execFormat(command, value) {
        editorEl.focus();
        _restoreSelection();
        document.execCommand(command, false, value || null);
        scheduleContentReport();
    }

    function applyHeading(level) {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('formatBlock', false, '<h' + level + '>');
        scheduleContentReport();
    }

    function applyParagraph() {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('formatBlock', false, '<p>');
        scheduleContentReport();
    }

    function insertCodeBlock() {
        editorEl.focus();
        _restoreSelection();
        var sel = window.getSelection();
        var text = sel.toString() || '';
        var pre = document.createElement('pre');
        var code = document.createElement('code');
        code.textContent = text || '\n';
        pre.appendChild(code);
        // Delete selected content first
        if (sel.rangeCount > 0) {
            var range = sel.getRangeAt(0);
            range.deleteContents();
            range.insertNode(pre);
            // Move cursor after the pre
            range.setStartAfter(pre);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
        }
        scheduleContentReport();
    }

    function insertQuote() {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('formatBlock', false, '<blockquote>');
        scheduleContentReport();
    }

    function insertLink(url, displayText) {
        editorEl.focus();
        _restoreSelection();
        var sel = window.getSelection();
        var selText = sel.toString();
        if (selText.length > 0) {
            // 有选中文字：用选中文字作链接文字
            document.execCommand('createLink', false, url);
        } else {
            // 无选中：插入传入的显示文字
            var label = displayText || url || '链接';
            document.execCommand('insertHTML', false,
                '<a href="' + url + '">' + label + '</a>');
        }
        scheduleContentReport();
    }

    function insertImage(src, alt) {
        editorEl.focus();
        _restoreSelection();
        var html = '<img src="' + src + '" alt="' + (alt || '') + '" style="max-width:100%;" />';
        document.execCommand('insertHTML', false, html);
        scheduleContentReport();
        // Ensure cursor is visible after insert
        setTimeout(function() { editorEl.focus(); }, 50);
    }

    function insertTableHTML(tableHTML) {
        editorEl.focus();
        _restoreSelection();

        // Parse the table element from the HTML string
        var tmp = document.createElement('div');
        tmp.innerHTML = tableHTML;
        var tableEl = tmp.querySelector('table');

        if (!tableEl) {
            // No <table> found — fall back to execCommand
            document.execCommand('insertHTML', false, tableHTML);
            scheduleContentReport();
            setTimeout(function() { editorEl.focus(); }, 50);
            return;
        }

        // Find the block-level ancestor of the cursor that is a direct
        // child of editorEl, so we can insert after it cleanly.
        var sel = window.getSelection();
        var anchor = null;
        if (sel.rangeCount > 0) {
            var node = sel.getRangeAt(0).startContainer;
            while (node && node !== editorEl && node.parentNode !== editorEl) {
                node = node.parentNode;
            }
            if (node && node !== editorEl) anchor = node;
        }

        // Ensure every empty cell has a <br> so it has height and is clickable
        var cells = tableEl.querySelectorAll('td, th');
        for (var i = 0; i < cells.length; i++) {
            if (!cells[i].innerHTML.trim()) {
                cells[i].innerHTML = '<br>';
            }
        }

        // Insert table after anchor (or append if no anchor)
        if (anchor && anchor.nextSibling) {
            editorEl.insertBefore(tableEl, anchor.nextSibling);
        } else {
            editorEl.appendChild(tableEl);
        }

        // Insert an empty paragraph after the table for cursor placement
        var p = document.createElement('p');
        p.innerHTML = '<br>';
        if (tableEl.nextSibling) {
            editorEl.insertBefore(p, tableEl.nextSibling);
        } else {
            editorEl.appendChild(p);
        }

        // Move cursor into the paragraph after the table
        try {
            var r = document.createRange();
            r.setStart(p, 0);
            r.collapse(true);
            sel.removeAllRanges();
            sel.addRange(r);
            _savedRange = r.cloneRange();
        } catch(e) {}

        scheduleContentReport();
        setTimeout(function() { editorEl.focus(); }, 50);
    }

    function _initAllCharts() {
        if (typeof window._rerenderAllCharts === 'function') {
            window._rerenderAllCharts();
        }
    }

    // ── KaTeX auto-rendering for math formulas ──
    function _renderAllKatex(root) {
        if (typeof katex === 'undefined') return;
        var container = root || editorEl;
        if (!container) return;
        var elems = container.querySelectorAll('[data-latex]');
        for (var i = 0; i < elems.length; i++) {
            var el = elems[i];
            // Skip already rendered (has .katex child)
            if (el.querySelector('.katex')) continue;
            var latex = el.getAttribute('data-latex');
            if (!latex) continue;
            var isBlock = el.classList.contains('math-formula-block');
            try {
                katex.render(latex, el, {
                    throwOnError: false,
                    displayMode: isBlock
                });
            } catch(e) {
                console.warn('KaTeX render failed:', latex, e);
            }
        }
    }

    function insertChartHTML(chartHTML) {
        editorEl.focus();
        _restoreSelection();

        var tmp = document.createElement('div');
        tmp.innerHTML = chartHTML;

        // The HTML already contains a chart-container div; use it directly
        var chartEl = tmp.querySelector('.chart-container') || tmp.firstElementChild || tmp;
        if (chartEl.parentNode) chartEl.parentNode.removeChild(chartEl);
        chartEl.contentEditable = 'false';

        // Find the block-level ancestor of the cursor
        var sel = window.getSelection();
        var anchor = null;
        if (sel.rangeCount > 0) {
            var node = sel.getRangeAt(0).startContainer;
            while (node && node !== editorEl && node.parentNode !== editorEl) {
                node = node.parentNode;
            }
            if (node && node !== editorEl) anchor = node;
        }

        // Insert after anchor
        if (anchor && anchor.nextSibling) {
            editorEl.insertBefore(chartEl, anchor.nextSibling);
        } else {
            editorEl.appendChild(chartEl);
        }

        // Insert an empty paragraph after for cursor placement
        var p = document.createElement('p');
        p.innerHTML = '<br>';
        if (chartEl.nextSibling) {
            editorEl.insertBefore(p, chartEl.nextSibling);
        } else {
            editorEl.appendChild(p);
        }

        // Move cursor into the paragraph
        try {
            var r = document.createRange();
            r.setStart(p, 0);
            r.collapse(true);
            sel.removeAllRanges();
            sel.addRange(r);
            _savedRange = r.cloneRange();
        } catch(e) {}

        scheduleContentReport();
        setTimeout(function() {
            editorEl.focus();
            _initAllCharts();
        }, 50);
    }

    function insertHR() {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('insertHorizontalRule', false, null);
        scheduleContentReport();
    }

    function setFontColor(color) {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('foreColor', false, color);
        scheduleContentReport();
    }

    function setHighlightColor(color) {
        editorEl.focus();
        _restoreSelection();
        document.execCommand('hiliteColor', false, color);
        scheduleContentReport();
    }

    function setFontSizePx(px) {
        editorEl.focus();
        _restoreSelection();
        // execCommand fontSize uses 1-7 scale, not px.
        // Workaround: apply fontSize 7 then replace generated <font> with styled span.
        var sel = window.getSelection();
        if (!sel.rangeCount) return;
        var range = sel.getRangeAt(0);
        if (range.collapsed) {
            // No selection: insert a zero-width space with the size so next typing uses it
            var span = document.createElement('span');
            span.style.fontSize = px + 'px';
            span.innerHTML = '\u200B';
            range.insertNode(span);
            range.setStartAfter(span.firstChild);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
            scheduleContentReport();
            return;
        }
        document.execCommand('fontSize', false, '7');
        // Replace generated <font size="7"> with <span style="font-size: ...">
        var fonts = editorEl.querySelectorAll('font[size="7"]');
        fonts.forEach(function(f) {
            var span = document.createElement('span');
            span.style.fontSize = px + 'px';
            while (f.firstChild) span.appendChild(f.firstChild);
            f.parentNode.replaceChild(span, f);
        });
        scheduleContentReport();
    }

    function setTextAlign(align) {
        editorEl.focus();
        _restoreSelection();
        var cmd = 'justifyLeft';
        if (align === 'center') cmd = 'justifyCenter';
        else if (align === 'right') cmd = 'justifyRight';
        else if (align === 'justify') cmd = 'justifyFull';
        document.execCommand(cmd, false, null);
        scheduleContentReport();
    }

    function setLineHeight(value) {
        // 对当前光标所在块级元素设置行距
        editorEl.focus();
        _restoreSelection();
        var sel = window.getSelection();
        if (!sel.rangeCount) return;
        // 获取选中范围内所有块级元素
        var range = sel.getRangeAt(0);
        // 找所有包含选中区域的块级元素
        var blocks = [];
        var node = range.startContainer;
        while (node && node.nodeType !== 1) node = node.parentNode;
        var startBlock = node;
        node = range.endContainer;
        while (node && node.nodeType !== 1) node = node.parentNode;
        var endBlock = node;
        // 遍历全部块元素
        var allBlocks = editorEl.querySelectorAll('p,h1,h2,h3,h4,h5,h6,li,blockquote,pre,div');
        var inRange = false;
        for (var i = 0; i < allBlocks.length; i++) {
            if (allBlocks[i] === startBlock || allBlocks[i].contains(startBlock)) inRange = true;
            if (inRange) blocks.push(allBlocks[i]);
            if (allBlocks[i] === endBlock || allBlocks[i].contains(endBlock)) break;
        }
        // 如果未找到，至少应用到 startBlock
        if (blocks.length === 0 && startBlock && editorEl.contains(startBlock)) {
            blocks.push(startBlock);
        }
        for (var j = 0; j < blocks.length; j++) {
            if (editorEl.contains(blocks[j])) {
                blocks[j].style.lineHeight = value;
            }
        }
        scheduleContentReport();
    }

    function setFontFamily(family) {
        editorEl.focus();
        _restoreSelection();
        var sel = window.getSelection();
        if (!sel.rangeCount) return;
        var range = sel.getRangeAt(0);
        if (range.collapsed) {
            // No selection: insert zero-width space so next typing uses this font
            var span = document.createElement('span');
            span.style.fontFamily = family;
            span.innerHTML = '\u200B';
            range.insertNode(span);
            range.setStartAfter(span.firstChild);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
            scheduleContentReport();
            return;
        }
        document.execCommand('fontName', false, family);
        scheduleContentReport();
    }

    // ── Find & Replace ──
    function findInContent(needle, caseSensitive, backward) {
        if (!needle) return false;
        // window.find(string, caseSensitive, backwards, wrapAround)
        return window.find(needle, caseSensitive, backward, true);
    }

    function replaceSelection(replacement) {
        var sel = window.getSelection();
        if (sel.rangeCount > 0 && !sel.isCollapsed) {
            document.execCommand('insertText', false, replacement);
            scheduleContentReport();
            return true;
        }
        return false;
    }

    function replaceAll(needle, replacement, caseSensitive) {
        if (!needle || !editorEl) return 0;
        // Move cursor to start
        var sel = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(editorEl);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);

        var count = 0;
        while (window.find(needle, caseSensitive, false, false)) {
            document.execCommand('insertText', false, replacement);
            count++;
            if (count > 10000) break; // safety
        }
        if (count > 0) scheduleContentReport();
        return count;
    }

    // ── Scroll to heading ──
    function scrollToHeading(headingId) {
        var el = document.getElementById(headingId);
        if (!el) {
            // Try matching by text content
            var headings = editorEl.querySelectorAll('h1,h2,h3,h4,h5,h6');
            for (var i = 0; i < headings.length; i++) {
                if (headings[i].textContent.trim() === headingId) {
                    el = headings[i];
                    break;
                }
            }
        }
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // ── Get clean content (strip pagination spacers & AI toolbars) ──
    // Use regex on innerHTML instead of cloning the entire DOM (much faster)
    function _getCleanHTML() {
        if (!editorEl) return '';
        var html = editorEl.innerHTML;
        // Strip page-break spacers
        html = html.replace(/<div[^>]*class="[^"]*page-break-spacer[^"]*"[^>]*>[\s\S]*?<\/div>/gi, '');
        // Strip AI block toolbars
        html = html.replace(/<div[^>]*class="[^"]*ai-block-toolbar[^"]*"[^>]*>[\s\S]*?<\/div>/gi, '');
        return html;
    }

    function getEditorHTML() {
        return _getCleanHTML();
    }

    // ── Set content (used when loading files) ──
    function setEditorContent(html) {
        if (editorEl) {
            editorEl.innerHTML = html;
            scheduleStatsReport();
            setTimeout(function() {
                _initAllCharts();
                _renderAllKatex();
            }, 50);
        }
    }

    // ── Undo / Redo ──
    function editorUndo() {
        editorEl.focus();
        document.execCommand('undo', false, null);
        scheduleContentReport();
    }

    function editorRedo() {
        editorEl.focus();
        document.execCommand('redo', false, null);
        scheduleContentReport();
    }

    function editorSelectAll() {
        editorEl.focus();
        document.execCommand('selectAll', false, null);
    }

    // ── Helper: find closest ancestor with given tag ──
    function _closestTag(node, tagName) {
        while (node && node !== editorEl) {
            if (node.nodeType === 1 && node.tagName === tagName) return node;
            node = node.parentNode;
        }
        return null;
    }

    // ── Helper: exit a block element ──
    function _exitBlock(block, removeBlock) {
        var p = document.createElement('p');
        p.innerHTML = '<br>';
        if (block.nextSibling) {
            block.parentNode.insertBefore(p, block.nextSibling);
        } else {
            block.parentNode.appendChild(p);
        }
        if (removeBlock) block.remove();
        var sel = window.getSelection();
        var range = document.createRange();
        range.setStart(p, 0);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
    }

    // ── Format state detection ──
    function _getFormatState() {
        var state = {};
        try {
            state.bold = document.queryCommandState('bold');
            state.italic = document.queryCommandState('italic');
            state.underline = document.queryCommandState('underline');
            state.strikethrough = document.queryCommandState('strikeThrough');
            state.superscript = document.queryCommandState('superscript');
            state.subscript = document.queryCommandState('subscript');
            state.blockType = '';
            state.inList = '';
            state.inCode = false;
            state.inQuote = false;
            state.textAlign = 'left';
            var bv = document.queryCommandValue('formatBlock');
            if (bv) state.blockType = bv.toLowerCase().replace(/[<>]/g, '');
            // Detect alignment
            try {
                if (document.queryCommandValue('justifyCenter') === 'true' ||
                    document.queryCommandState('justifyCenter')) state.textAlign = 'center';
                else if (document.queryCommandValue('justifyRight') === 'true' ||
                    document.queryCommandState('justifyRight')) state.textAlign = 'right';
                else if (document.queryCommandValue('justifyFull') === 'true' ||
                    document.queryCommandState('justifyFull')) state.textAlign = 'justify';
                else {
                    // Fallback: check computed style on the block element
                    var sel2 = window.getSelection();
                    if (sel2.rangeCount > 0) {
                        var block = sel2.anchorNode;
                        while (block && block.nodeType !== 1) block = block.parentNode;
                        if (block && editorEl.contains(block)) {
                            var cs = window.getComputedStyle(block).textAlign;
                            if (cs === 'center') state.textAlign = 'center';
                            else if (cs === 'right' || cs === 'end') state.textAlign = 'right';
                            else if (cs === 'justify') state.textAlign = 'justify';
                        }
                    }
                }
            } catch(e2) {}
            var sel = window.getSelection();
            if (sel.rangeCount > 0) {
                var n = sel.anchorNode;
                while (n && n !== editorEl) {
                    if (n.nodeType === 1) {
                        var t = n.tagName;
                        if (t === 'PRE') state.inCode = true;
                        if (t === 'BLOCKQUOTE') state.inQuote = true;
                        if (t === 'UL') state.inList = 'ul';
                        if (t === 'OL') state.inList = 'ol';
                    }
                    n = n.parentNode;
                }
            }
        } catch(e) {}
        return state;
    }

    function _scheduleFormatReport() {
        if (_formatTimer) clearTimeout(_formatTimer);
        _formatTimer = setTimeout(function() {
            try {
                if (bridge) {
                    bridge.reportFormatState(JSON.stringify(_getFormatState()));
                }
            } catch(e) {}
        }, 100);
    }

    // ── Image resize helpers ──
    function _initImgOverlay() {
        _imgOverlay = document.createElement('div');
        _imgOverlay.id = 'img-resize-overlay';
        // Mover area (drag to reposition)
        var mover = document.createElement('div');
        mover.className = 'img-mover';
        mover.draggable = true;
        mover.addEventListener('dragstart', function(ev) {
            if (!_selectedImg) return;
            ev.dataTransfer.setDragImage(_selectedImg, _selectedImg.offsetWidth / 2, _selectedImg.offsetHeight / 2);
            ev.dataTransfer.setData('text/plain', 'img-move');
            ev.dataTransfer.effectAllowed = 'move';
        });
        _imgOverlay.appendChild(mover);
        // Corner resize handles
        ['nw', 'ne', 'sw', 'se'].forEach(function(pos) {
            var h = document.createElement('div');
            h.className = 'img-handle img-handle-' + pos;
            h.addEventListener('mousedown', function(ev) {
                ev.preventDefault();
                ev.stopPropagation();
                if (!_selectedImg) return;
                _imgResizing = true;
                _imgHandle = pos;
                _imgStartX = ev.clientX;
                _imgStartY = ev.clientY;
                _imgStartW = _selectedImg.offsetWidth;
                _imgStartH = _selectedImg.offsetHeight;
            });
            _imgOverlay.appendChild(h);
        });
        document.body.appendChild(_imgOverlay);
    }

    function _selectImg(img) {
        _deselectImg();
        _selectedImg = img;
        img.classList.add('img-selected');
        if (!_imgOverlay) _initImgOverlay();
        _positionImgOverlay();
        _imgOverlay.style.display = 'block';
    }

    function _deselectImg() {
        if (_selectedImg) {
            _selectedImg.classList.remove('img-selected');
            _selectedImg = null;
        }
        if (_imgOverlay) {
            _imgOverlay.style.display = 'none';
        }
    }

    function _positionImgOverlay() {
        if (!_selectedImg || !_imgOverlay) return;
        var rect = _selectedImg.getBoundingClientRect();
        var sx = window.pageXOffset || document.documentElement.scrollLeft;
        var sy = window.pageYOffset || document.documentElement.scrollTop;
        _imgOverlay.style.left = (rect.left + sx) + 'px';
        _imgOverlay.style.top = (rect.top + sy) + 'px';
        _imgOverlay.style.width = rect.width + 'px';
        _imgOverlay.style.height = rect.height + 'px';
    }

    // ── Pagination ──
    function _schedulePagination() {
        if (_paginationTimer) clearTimeout(_paginationTimer);
        _paginationTimer = setTimeout(_updatePagination, 600);
    }

    function _updatePagination() {
        if (!editorEl) return;
        var container = editorEl.parentNode; // .page-container

        _suppressContentChange = true;

        // Save cursor
        var savedAnchor = null, savedAnchorOff = 0;
        var savedFocus = null, savedFocusOff = 0;
        try {
            var sel = window.getSelection();
            if (sel.rangeCount > 0 && editorEl.contains(sel.anchorNode)) {
                savedAnchor = sel.anchorNode;
                savedAnchorOff = sel.anchorOffset;
                savedFocus = sel.focusNode;
                savedFocusOff = sel.focusOffset;
            }
        } catch(e) {}

        // Remove existing spacers
        var oldSpacers = editorEl.querySelectorAll('.page-break-spacer');
        for (var i = 0; i < oldSpacers.length; i++) oldSpacers[i].remove();

        // Calculate metrics from computed style
        var cs = window.getComputedStyle(container);
        var padTop = parseFloat(cs.paddingTop);
        var padBottom = parseFloat(cs.paddingBottom);
        var padLeft = parseFloat(cs.paddingLeft);
        var padRight = parseFloat(cs.paddingRight);

        var pageH = 297 * 96 / 25.4;  // A4 height in px
        var contentH = pageH - padTop - padBottom;
        var gapH = 40; // px — gray gap between pages

        var editorH = editorEl.scrollHeight;
        var numPages = Math.max(1, Math.ceil(editorH / contentH));

        // Update page counter
        var counter = document.getElementById('page-counter');
        if (counter) {
            counter.textContent = '\u7B2C 1 \u9875 / \u5171 ' + numPages + ' \u9875';
            counter.style.display = (numPages > 1) ? 'block' : 'none';
        }

        if (numPages <= 1) {
            container.style.minHeight = pageH + 'px';
            _lastPageCount = 1;
            _suppressContentChange = false;
            return;
        }

        // Insert spacers at each page boundary (work backwards to keep positions stable)
        var editorRect = editorEl.getBoundingClientRect();

        for (var pg = numPages - 1; pg >= 1; pg--) {
            var breakY = pg * contentH; // offset from editor-content top

            // Find the first block child that starts at or after breakY
            var children = editorEl.children;
            var insertBefore = null;
            for (var j = 0; j < children.length; j++) {
                var child = children[j];
                if (child.classList && child.classList.contains('page-break-spacer')) continue;
                var childRect = child.getBoundingClientRect();
                var childTop = childRect.top - editorRect.top;
                if (childTop >= breakY - 4) {
                    insertBefore = child;
                    break;
                }
            }

            var spacer = document.createElement('div');
            spacer.className = 'page-break-spacer';
            spacer.contentEditable = 'false';
            spacer.style.marginLeft = '-' + padLeft + 'px';
            spacer.style.marginRight = '-' + padRight + 'px';
            spacer.style.width = 'calc(100% + ' + (padLeft + padRight) + 'px)';

            var endDiv = document.createElement('div');
            endDiv.className = 'spacer-page-end';
            endDiv.style.height = padBottom + 'px';
            spacer.appendChild(endDiv);

            var gapDiv = document.createElement('div');
            gapDiv.className = 'spacer-gap';
            gapDiv.style.height = gapH + 'px';
            gapDiv.innerHTML = '<span class="page-break-spacer-label">\u2014 \u7B2C ' + pg + ' \u9875 / \u7B2C ' + (pg + 1) + ' \u9875 \u2014</span>';
            spacer.appendChild(gapDiv);

            var startDiv = document.createElement('div');
            startDiv.className = 'spacer-page-start';
            startDiv.style.height = padTop + 'px';
            spacer.appendChild(startDiv);

            if (insertBefore) {
                editorEl.insertBefore(spacer, insertBefore);
            } else {
                editorEl.appendChild(spacer);
            }
        }

        // Update container min-height
        var totalH = numPages * pageH + (numPages - 1) * gapH;
        container.style.minHeight = totalH + 'px';
        _lastPageCount = numPages;

        // Restore cursor
        try {
            if (savedAnchor && editorEl.contains(savedAnchor)) {
                var sel = window.getSelection();
                sel.removeAllRanges();
                var range = document.createRange();
                range.setStart(savedAnchor, savedAnchorOff);
                if (savedFocus && editorEl.contains(savedFocus)) {
                    range.setEnd(savedFocus, savedFocusOff);
                } else {
                    range.collapse(true);
                }
                sel.addRange(range);
            }
        } catch(e) {}

        _suppressContentChange = false;
    }

    // ── AI Inline Editing ──
    var _aiBlocks = {};

    function aiGetContext() {
        if (!editorEl) return '{}';
        var sel = window.getSelection();
        var r = {selectedText:'', hasSelection:false, textBefore:'', textAfter:''};
        try {
            // Use live selection if available; otherwise fall back to _savedRange;
            // final fallback: _cachedSelectionCtx (plain-string snapshot that
            // survives focus loss when user clicks the toolbar GPT button).
            var range = null;
            if (sel.rangeCount > 0 && !sel.isCollapsed && editorEl.contains(sel.anchorNode)) {
                range = sel.getRangeAt(0);
                r.selectedText = sel.toString() || '';
                r.selectedHTML = _rangeToHTML(range);
                r.hasSelection = true;
            } else if (_savedRange && !_savedRange.collapsed && editorEl.contains(_savedRange.startContainer)) {
                range = _savedRange;
                r.selectedText = _savedRange.toString() || '';
                r.selectedHTML = _rangeToHTML(_savedRange);
                r.hasSelection = true;
            }

            // If both live selection and _savedRange failed, use cached context
            if (!r.hasSelection && _cachedSelectionCtx && _cachedSelectionCtx.selectedText) {
                return JSON.stringify(_cachedSelectionCtx);
            }

            // Also try collapsed cursor (no selection but cursor at a position)
            // so that textBefore/textAfter reflect the actual cursor location
            if (!range) {
                if (sel.rangeCount > 0 && editorEl.contains(sel.anchorNode)) {
                    range = sel.getRangeAt(0);
                } else if (_savedRange && editorEl.contains(_savedRange.startContainer)) {
                    range = _savedRange;
                }
            }

            if (range) {
                try {
                    var pre = document.createRange();
                    pre.selectNodeContents(editorEl);
                    pre.setEnd(range.startContainer, range.startOffset);
                    r.textBefore = pre.toString().slice(-2000);
                } catch(e2) {}
                try {
                    var post = document.createRange();
                    post.selectNodeContents(editorEl);
                    post.setStart(range.endContainer, range.endOffset);
                    r.textAfter = post.toString().slice(0, 800);
                } catch(e3) {}
            } else {
                r.textBefore = (editorEl.innerText || '').slice(-2000);
            }
        } catch(e) {}
        return JSON.stringify(r);
    }

    function aiStartBlock(aiId, mode) {
        // Reset auto-scroll for new AI generation
        _aiAutoScroll = true;
        _aiScrollUpCount = 0;
        _aiStreaming = true;

        editorEl.focus();
        _restoreSelection();
        var sel = window.getSelection();

        var block = document.createElement('div');
        block.className = 'ai-block ' + (mode === 'continue' ? 'ai-block-new' : 'ai-block-modified');
        block.setAttribute('data-ai-id', aiId);
        block.setAttribute('contenteditable', 'false');

        _aiBlocks[aiId] = {mode: mode, originalHTML: ''};

        var content = document.createElement('div');
        content.className = 'ai-block-content';
        // ── Thinking animation (removed on first content chunk) ──
        content.innerHTML = '<div class="ai-thinking">' +
            '<svg width="56" height="56" viewBox="0 0 56 56" fill="none">' +
              '<defs>' +
                '<linearGradient id="ag1_' + aiId + '" x1="0" y1="0" x2="56" y2="56" gradientUnits="userSpaceOnUse">' +
                  '<stop stop-color="#10A37F"/><stop offset="1" stop-color="#1a73e8"/>' +
                '</linearGradient>' +
                '<linearGradient id="ag2_' + aiId + '" x1="56" y1="0" x2="0" y2="56" gradientUnits="userSpaceOnUse">' +
                  '<stop stop-color="#10A37F" stop-opacity="0.3"/><stop offset="1" stop-color="#6C5CE7" stop-opacity="0.5"/>' +
                '</linearGradient>' +
              '</defs>' +
              '<circle cx="28" cy="28" r="24" stroke="url(#ag1_' + aiId + ')" stroke-width="2.5" stroke-dasharray="38 113" stroke-linecap="round">' +
                '<animateTransform attributeName="transform" type="rotate" from="0 28 28" to="360 28 28" dur="1.1s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="16" stroke="url(#ag2_' + aiId + ')" stroke-width="1.8" stroke-dasharray="20 80" stroke-linecap="round">' +
                '<animateTransform attributeName="transform" type="rotate" from="360 28 28" to="0 28 28" dur="1.6s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="6" fill="#10A37F" opacity="0.15">' +
                '<animate attributeName="r" values="6;9;6" dur="2s" repeatCount="indefinite"/>' +
                '<animate attributeName="opacity" values="0.15;0.05;0.15" dur="2s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="4" fill="#10A37F">' +
                '<animate attributeName="r" values="3.5;4.5;3.5" dur="1.5s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle r="2" fill="#10A37F" opacity="0.6">' +
                '<animateMotion dur="3s" repeatCount="indefinite" path="M28,4 A24,24 0 1,1 27.99,4"/>' +
                '<animate attributeName="opacity" values="0.6;0.15;0.6" dur="3s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle r="1.5" fill="#1a73e8" opacity="0.4">' +
                '<animateMotion dur="4s" repeatCount="indefinite" path="M28,4 A24,24 0 1,1 27.99,4" begin="1.5s"/>' +
                '<animate attributeName="opacity" values="0.4;0.1;0.4" dur="4s" repeatCount="indefinite" begin="1.5s"/>' +
              '</circle>' +
            '</svg>' +
            '<div class="ai-thinking-text">AI \u6b63\u5728\u601d\u8003' +
              '<span class="ai-dot"></span><span class="ai-dot"></span><span class="ai-dot"></span>' +
            '</div>' +
          '</div>';
        block.appendChild(content);

        var tb = document.createElement('div');
        tb.className = 'ai-block-toolbar';
        var lbl = mode === 'continue' ? '\u2726 AI \u7eed\u5199' : '\u2726 AI \u4fee\u6539';
        tb.innerHTML = '<span class="ai-block-label">' + lbl + '</span>' +
            '<span class="ai-block-loading">\u6b63\u5728\u751f\u6210...</span>' +
            '<button class="ai-btn-accept" onclick="aiAcceptBlock(\'' + aiId + '\')" disabled>\u2713 \u91c7\u7eb3</button>' +
            '<button class="ai-btn-reject" onclick="aiRejectBlock(\'' + aiId + '\')">&times; \u64a4\u56de</button>';
        block.insertBefore(tb, content);

        if (mode === 'optimize' && sel.rangeCount > 0 && !sel.isCollapsed) {
            var range = sel.getRangeAt(0);
            var frag = range.cloneContents();
            var tmp = document.createElement('div');
            tmp.appendChild(frag);
            _aiBlocks[aiId].originalHTML = tmp.innerHTML;
            range.deleteContents();
            range.insertNode(block);
        } else {
            if (sel.rangeCount > 0) {
                var range = sel.getRangeAt(0);
                range.collapse(false);
                var node = range.startContainer;
                while (node && node !== editorEl && node.parentNode !== editorEl) {
                    node = node.parentNode;
                }
                if (node && node !== editorEl && node.nextSibling) {
                    editorEl.insertBefore(block, node.nextSibling);
                } else {
                    editorEl.appendChild(block);
                }
            } else {
                editorEl.appendChild(block);
            }
        }
        block.scrollIntoView({behavior:'smooth', block:'center'});
    }

    function aiStartBlockAtHeading(aiId, mode, headingText) {
        // Reset auto-scroll for new AI generation
        _aiAutoScroll = true;
        _aiScrollUpCount = 0;
        _aiStreaming = true;

        // Find the heading element by text content
        var target = null;
        var headings = editorEl.querySelectorAll('h1,h2,h3,h4,h5,h6');
        for (var i = 0; i < headings.length; i++) {
            if (headings[i].textContent.trim() === headingText.trim()) {
                target = headings[i];
                break;
            }
        }
        if (!target) {
            // Fallback: append at end
            aiStartBlock(aiId, mode);
            return;
        }

        var block = document.createElement('div');
        block.className = 'ai-block ' + (mode === 'continue' ? 'ai-block-new' : 'ai-block-modified');
        block.setAttribute('data-ai-id', aiId);
        block.setAttribute('contenteditable', 'false');

        _aiBlocks[aiId] = {mode: mode, originalHTML: ''};

        var content = document.createElement('div');
        content.className = 'ai-block-content';
        content.innerHTML = '<div class="ai-thinking">' +
            '<svg width="56" height="56" viewBox="0 0 56 56" fill="none">' +
              '<defs>' +
                '<linearGradient id="ag1_' + aiId + '" x1="0" y1="0" x2="56" y2="56" gradientUnits="userSpaceOnUse">' +
                  '<stop stop-color="#10A37F"/><stop offset="1" stop-color="#1a73e8"/>' +
                '</linearGradient>' +
                '<linearGradient id="ag2_' + aiId + '" x1="56" y1="0" x2="0" y2="56" gradientUnits="userSpaceOnUse">' +
                  '<stop stop-color="#10A37F" stop-opacity="0.3"/><stop offset="1" stop-color="#6C5CE7" stop-opacity="0.5"/>' +
                '</linearGradient>' +
              '</defs>' +
              '<circle cx="28" cy="28" r="24" stroke="url(#ag1_' + aiId + ')" stroke-width="2.5" stroke-dasharray="38 113" stroke-linecap="round">' +
                '<animateTransform attributeName="transform" type="rotate" from="0 28 28" to="360 28 28" dur="1.1s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="16" stroke="url(#ag2_' + aiId + ')" stroke-width="1.8" stroke-dasharray="20 80" stroke-linecap="round">' +
                '<animateTransform attributeName="transform" type="rotate" from="360 28 28" to="0 28 28" dur="1.6s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="6" fill="#10A37F" opacity="0.15">' +
                '<animate attributeName="r" values="6;9;6" dur="2s" repeatCount="indefinite"/>' +
                '<animate attributeName="opacity" values="0.15;0.05;0.15" dur="2s" repeatCount="indefinite"/>' +
              '</circle>' +
              '<circle cx="28" cy="28" r="4" fill="#10A37F">' +
                '<animate attributeName="r" values="3.5;4.5;3.5" dur="1.5s" repeatCount="indefinite"/>' +
              '</circle>' +
            '</svg>' +
            '<div class="ai-thinking-text">AI \u6b63\u5728\u601d\u8003' +
              '<span class="ai-dot"></span><span class="ai-dot"></span><span class="ai-dot"></span>' +
            '</div>' +
          '</div>';
        block.appendChild(content);

        var tb = document.createElement('div');
        tb.className = 'ai-block-toolbar';
        var lbl = '\u2726 AI \u7eed\u5199';
        tb.innerHTML = '<span class="ai-block-label">' + lbl + '</span>' +
            '<span class="ai-block-loading">\u6b63\u5728\u751f\u6210...</span>' +
            '<button class="ai-btn-accept" onclick="aiAcceptBlock(\'' + aiId + '\')" disabled>\u2713 \u91c7\u7eb3</button>' +
            '<button class="ai-btn-reject" onclick="aiRejectBlock(\'' + aiId + '\')">&times; \u64a4\u56de</button>';
        block.insertBefore(tb, content);

        // Insert block right after the heading, skipping empty paragraphs
        var insertPoint = target.nextSibling;
        while (insertPoint && insertPoint.nodeType === 1 &&
               insertPoint.tagName === 'P' &&
               !insertPoint.textContent.trim()) {
            insertPoint = insertPoint.nextSibling;
        }
        if (insertPoint) {
            editorEl.insertBefore(block, insertPoint);
        } else {
            editorEl.appendChild(block);
        }
        block.scrollIntoView({behavior:'smooth', block:'center'});
    }

    function aiUpdateThinking(aiId, text) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var content = block.querySelector('.ai-block-content');
        if (!content) return;
        var thinkDiv = content.querySelector('.ai-thinking');
        if (!thinkDiv) return;
        // On first reasoning chunk, replace spinner with streaming text
        var textEl = thinkDiv.querySelector('.ai-thinking-stream');
        if (!textEl) {
            thinkDiv.innerHTML = '<div class="ai-thinking-header">' +
                '<span class="ai-thinking-icon">\ud83d\udca1</span>' +
                '<span>AI \u601d\u8003\u4e2d</span>' +
                '<span class="ai-dot"></span><span class="ai-dot"></span><span class="ai-dot"></span>' +
            '</div>' +
            '<div class="ai-thinking-stream"></div>';
            textEl = thinkDiv.querySelector('.ai-thinking-stream');
        }
        textEl.insertAdjacentHTML('beforeend', text.replace(/\n/g, '<br>'));
        // Keep only last ~600 chars visible to avoid huge DOM
        if (textEl.textContent.length > 800) {
            var full = textEl.innerHTML;
            textEl.innerHTML = '\u2026' + full.slice(full.length - 600);
        }
        if (_aiAutoScroll) {
            thinkDiv.scrollIntoView({behavior:'smooth', block:'end'});
        }
    }

    function aiAppendChunk(aiId, text) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var content = block.querySelector('.ai-block-content');
        if (!content) return;
        // Remove thinking animation on first content chunk
        var thinking = content.querySelector('.ai-thinking');
        if (thinking) thinking.remove();
        content.insertAdjacentHTML('beforeend', text.replace(/\n/g, '<br>'));
        // Auto-scroll: follow AI output unless user scrolled up
        if (_aiAutoScroll) {
            block.scrollIntoView({behavior:'smooth', block:'end'});
        }
    }

    function aiRenderBlock(aiId, renderedHTML) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var content = block.querySelector('.ai-block-content');
        if (content) {
            content.innerHTML = renderedHTML;
            // Render KaTeX formulas inside the AI block
            setTimeout(function() { _renderAllKatex(content); }, 30);
        }
    }

    function aiFinishBlock(aiId) {
        _aiStreaming = false;
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        block.classList.add('ai-block-done');
        var ld = block.querySelector('.ai-block-loading');
        if (ld) ld.style.display = 'none';
        var ab = block.querySelector('.ai-btn-accept');
        if (ab) { ab.disabled = false; ab.style.display = ''; }
        scheduleContentReport();
    }

    function aiAcceptBlock(aiId) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        // Smart modify blocks: delegate to Python for find/replace
        if (block.getAttribute('data-ai-smart') === 'true') {
            if (bridge) bridge.acceptSmartModify(aiId);
            block.remove();
            delete _aiBlocks[aiId];
            scheduleContentReport();
            return;
        }
        var content = block.querySelector('.ai-block-content');
        if (content) {
            while (content.firstChild) {
                block.parentNode.insertBefore(content.firstChild, block);
            }
        }
        block.remove();
        delete _aiBlocks[aiId];
        scheduleContentReport();
    }

    function aiRejectBlock(aiId) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var info = _aiBlocks[aiId];
        if (info && info.mode === 'optimize' && info.originalHTML) {
            var tmp = document.createElement('span');
            tmp.innerHTML = info.originalHTML;
            while (tmp.firstChild) {
                block.parentNode.insertBefore(tmp.firstChild, block);
            }
        }
        block.remove();
        delete _aiBlocks[aiId];
        scheduleContentReport();
    }

    function aiUpdateBlockStatus(aiId, text) {
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var ld = block.querySelector('.ai-block-loading');
        if (ld) { ld.style.display = ''; ld.textContent = text; }
    }

    function aiErrorBlock(aiId, msg) {
        _aiStreaming = false;
        var block = editorEl.querySelector('[data-ai-id="' + aiId + '"]');
        if (!block) return;
        var ld = block.querySelector('.ai-block-loading');
        if (ld) { ld.textContent = '\u2717 ' + msg; ld.style.color = '#e74c3c'; }
        block.classList.add('ai-block-error');
        var ab = block.querySelector('.ai-btn-accept');
        if (ab) { ab.style.display = 'none'; }
    }

    // ── Plagiarism Highlighting ──
    function highlightPlagiarism(resultsJson) {
        clearPlagiarismHighlights();
        if (!editorEl) return;
        var results;
        try { results = JSON.parse(resultsJson); } catch(e) { return; }
        var text = editorEl.innerText || '';
        // Build a map of sentence text -> risk
        var marks = [];
        for (var i = 0; i < results.length; i++) {
            var r = results[i];
            if (r.risk === 'low') continue;
            marks.push({text: r.text, risk: r.risk, index: r.index});
        }
        if (marks.length === 0) return;
        // Walk text nodes and wrap matching sentences
        var walker = document.createTreeWalker(
            editorEl, NodeFilter.SHOW_TEXT, null, false);
        var textNodes = [];
        while (walker.nextNode()) textNodes.push(walker.currentNode);
        var fullText = '';
        var nodeMap = []; // {node, startInFull, endInFull}
        for (var i = 0; i < textNodes.length; i++) {
            var start = fullText.length;
            fullText += textNodes[i].textContent;
            nodeMap.push({node: textNodes[i], start: start, end: fullText.length});
        }
        // For each mark, find its position in fullText
        for (var m = 0; m < marks.length; m++) {
            var needle = marks[m].text.trim();
            if (!needle) continue;
            var pos = fullText.indexOf(needle);
            if (pos < 0) continue;
            var endPos = pos + needle.length;
            // Find overlapping text nodes
            for (var n = 0; n < nodeMap.length; n++) {
                var nm = nodeMap[n];
                if (nm.end <= pos || nm.start >= endPos) continue;
                var localStart = Math.max(0, pos - nm.start);
                var localEnd = Math.min(nm.node.textContent.length, endPos - nm.start);
                try {
                    var range = document.createRange();
                    range.setStart(nm.node, localStart);
                    range.setEnd(nm.node, localEnd);
                    var span = document.createElement('span');
                    span.className = 'plag-mark plag-' + marks[m].risk;
                    span.setAttribute('data-plag-index', marks[m].index);
                    range.surroundContents(span);
                    // After surroundContents, the nodeMap is stale but
                    // we break to next mark since each sentence appears once
                    break;
                } catch(e) { /* cross-boundary, skip */ }
            }
        }
    }

    function clearPlagiarismHighlights() {
        if (!editorEl) return;
        var marks = editorEl.querySelectorAll('.plag-mark');
        for (var i = 0; i < marks.length; i++) {
            var parent = marks[i].parentNode;
            while (marks[i].firstChild) {
                parent.insertBefore(marks[i].firstChild, marks[i]);
            }
            parent.removeChild(marks[i]);
        }
    }

    function scrollToPlagSentence(index) {
        if (!editorEl) return;
        var el = editorEl.querySelector('[data-plag-index="' + index + '"]');
        if (el) {
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
            // Flash effect
            el.style.transition = 'outline 0.2s';
            el.style.outline = '2px solid #6C5CE7';
            setTimeout(function() { el.style.outline = 'none'; }, 1500);
        }
    }

    // ── Track Changes Bar ──
    function showTrackChangesBar(delCount, insCount) {
        var bar = document.getElementById('track-changes-bar');
        if (bar) {
            bar.style.display = 'flex';
            var stats = document.getElementById('tc-stats');
            if (stats) {
                var parts = [];
                if (delCount > 0) parts.push(delCount + ' \u5904\u5220\u9664');
                if (insCount > 0) parts.push(insCount + ' \u5904\u65b0\u589e/\u4fee\u6539');
                stats.textContent = parts.join('\uff0c');
            }
        }
        // Make editor read-only during review
        if (editorEl) editorEl.setAttribute('contenteditable', 'false');
        // Add top padding so toolbar doesn't cover content
        document.body.style.paddingTop = '50px';
        // Scroll to first change
        setTimeout(function() {
            var first = editorEl ? editorEl.querySelector('del.ai-del, ins.ai-ins') : null;
            if (first) first.scrollIntoView({behavior: 'smooth', block: 'center'});
        }, 200);
    }

    function hideTrackChangesBar() {
        var bar = document.getElementById('track-changes-bar');
        if (bar) bar.style.display = 'none';
        if (editorEl) editorEl.setAttribute('contenteditable', 'true');
        document.body.style.paddingTop = '0';
    }

    function tcAccept() {
        if (bridge) bridge.acceptSmartModify('__track_changes__');
    }

    function tcReject() {
        if (bridge) bridge.rejectSmartModify('__track_changes__');
    }

    // ── JSON Viewer: fold/unfold ──
    function jvToggle(el) {
        var collapsible = el.parentNode.querySelector('.jv-collapsible');
        if (!collapsible) {
            // For cases where collapsible is a sibling
            var next = el.nextElementSibling;
            while (next) {
                if (next.classList && next.classList.contains('jv-collapsible')) {
                    collapsible = next; break;
                }
                next = next.nextElementSibling;
            }
        }
        if (!collapsible) return;
        var isCollapsed = collapsible.classList.contains('collapsed');
        if (isCollapsed) {
            collapsible.classList.remove('collapsed');
            el.classList.remove('collapsed');
            el.textContent = '\u25BC';
            // Remove hint
            var hint = el.parentNode.querySelector('.jv-collapsed-hint');
            if (hint) hint.remove();
        } else {
            collapsible.classList.add('collapsed');
            el.classList.add('collapsed');
            el.textContent = '\u25BC';
            // Add count hint
            var text = collapsible.textContent || '';
            var lines = text.split('\n').filter(function(l) { return l.trim(); });
            var hint = document.createElement('span');
            hint.className = 'jv-collapsed-hint';
            hint.textContent = ' ...' + lines.length + ' items ';
            // Insert hint after the opening brace/bracket
            var brace = el.nextElementSibling;
            if (brace) brace.parentNode.insertBefore(hint, collapsible);
        }
    }

    // ── Copy code block content ──
    function copyCodeBlock(btn) {
        var container = btn.closest('.json-viewer, .xml-viewer, .terminal-ui');
        if (!container) return;
        var codeEl = container.querySelector('pre code');
        if (!codeEl) return;
        var text = codeEl.textContent || '';
        // Clean up: remove line numbers for JSON/XML viewers
        if (container.classList.contains('json-viewer') ||
            container.classList.contains('xml-viewer')) {
            // Line numbers are in .jv-ln / .xv-ln spans, already excluded from textContent
            // but let's clean leading numbers just in case
        }
        try {
            navigator.clipboard.writeText(text).then(function() {
                var orig = btn.textContent;
                btn.textContent = '\u2713 \u5df2\u590d\u5236';
                setTimeout(function() { btn.textContent = orig; }, 1500);
            });
        } catch(e) {
            // Fallback for older browsers
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            var orig = btn.textContent;
            btn.textContent = '\u2713 \u5df2\u590d\u5236';
            setTimeout(function() { btn.textContent = orig; }, 1500);
        }
    }

    // ── Formula: delete with Backspace / Delete ──
    function _initFormulaDelete() {
        if (!editorEl) return;
        editorEl.addEventListener('keydown', function(e) {
            if (e.key !== 'Backspace' && e.key !== 'Delete') return;
            var sel = window.getSelection();
            if (!sel.rangeCount) return;

            // Case 1: selection covers formula(s) — let browser handle,
            // but also remove any .math-formula nodes inside
            if (!sel.isCollapsed) {
                var range = sel.getRangeAt(0);
                var formulas = editorEl.querySelectorAll('.math-formula');
                for (var i = 0; i < formulas.length; i++) {
                    if (range.intersectsNode(formulas[i])) {
                        formulas[i].remove();
                    }
                }
                scheduleContentReport();
                return; // let browser clean up remaining selection
            }

            // Case 2: collapsed cursor adjacent to a formula
            var range = sel.getRangeAt(0);
            var node = range.startContainer;
            var offset = range.startOffset;

            if (e.key === 'Backspace') {
                // Check node before cursor
                var prev = null;
                if (node.nodeType === 3) {
                    // In a text node: if at start (or only zero-width spaces before),
                    // check previous sibling
                    var textBefore = node.textContent.substring(0, offset);
                    if (textBefore.replace(/[\u200B]/g, '').length === 0 && node.previousSibling) {
                        prev = node.previousSibling;
                    }
                } else if (node.nodeType === 1 && offset > 0) {
                    prev = node.childNodes[offset - 1];
                }
                if (prev && prev.nodeType === 1 && prev.classList &&
                    prev.classList.contains('math-formula')) {
                    e.preventDefault();
                    prev.remove();
                    scheduleContentReport();
                    return;
                }
            }
            if (e.key === 'Delete') {
                // Check node after cursor
                var next = null;
                if (node.nodeType === 3) {
                    var textAfter = node.textContent.substring(offset);
                    if (textAfter.replace(/[\u200B]/g, '').length === 0 && node.nextSibling) {
                        next = node.nextSibling;
                    }
                } else if (node.nodeType === 1 && offset < node.childNodes.length) {
                    next = node.childNodes[offset];
                }
                if (next && next.nodeType === 1 && next.classList &&
                    next.classList.contains('math-formula')) {
                    e.preventDefault();
                    next.remove();
                    scheduleContentReport();
                    return;
                }
            }
        });
    }

    // ── Formula insertion via KaTeX ──
    function insertFormula(latex, isBlock) {
        editorEl.focus();
        _restoreSelection();
        var span = document.createElement('span');
        span.className = isBlock ? 'math-formula math-formula-block' : 'math-formula';
        span.contentEditable = 'false';
        span.setAttribute('data-latex', latex);
        try {
            if (typeof katex !== 'undefined') {
                katex.render(latex, span, {
                    throwOnError: false,
                    displayMode: isBlock
                });
            } else {
                // KaTeX not loaded — show raw LaTeX as fallback
                span.textContent = (isBlock ? '$$' : '$') + latex + (isBlock ? '$$' : '$');
                span.style.fontFamily = 'monospace';
                span.style.color = '#666';
            }
        } catch(e) {
            span.textContent = latex;
        }
        var sel = window.getSelection();
        if (sel.rangeCount > 0) {
            var range = sel.getRangeAt(0);
            range.deleteContents();
            range.insertNode(span);
            // Move cursor after the formula
            range.setStartAfter(span);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);
            _savedRange = range.cloneRange();
        } else {
            editorEl.appendChild(span);
        }
        // Always ensure there is an editable paragraph after the formula
        // so the cursor can be placed below it
        var nextEl = span.nextSibling;
        // Skip zero-width space text nodes
        while (nextEl && nextEl.nodeType === 3 && nextEl.textContent.replace(/[\u200B\s]/g, '').length === 0) {
            nextEl = nextEl.nextSibling;
        }
        if (!nextEl || (nextEl.nodeType === 1 && nextEl.classList && nextEl.classList.contains('math-formula'))) {
            // No editable element after formula — insert an empty paragraph
            var p = document.createElement('p');
            p.innerHTML = '<br>';
            span.parentNode.insertBefore(p, span.nextSibling);
            // Place cursor in the new paragraph
            var newRange = document.createRange();
            newRange.setStart(p, 0);
            newRange.collapse(true);
            var s = window.getSelection();
            s.removeAllRanges();
            s.addRange(newRange);
            _savedRange = newRange.cloneRange();
        }
        // Add a zero-width space after inline formula so user can type after it
        if (!isBlock) {
            var zws = document.createTextNode('\u200B');
            span.parentNode.insertBefore(zws, span.nextSibling);
        }
        scheduleContentReport();
    }

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initEditor();
        _initFormulaDelete();
        setTimeout(function() { _updatePagination(); _initAllCharts(); _renderAllKatex(); }, 300);
    });
    // Fallback
    window.addEventListener('load', function() {
        if (!editorEl) initEditor();
        _initFormulaDelete();
        setTimeout(function() { _updatePagination(); _initAllCharts(); _renderAllKatex(); }, 500);
    });
    </script>
    """

    # ------------------------------------------------------------------
    # Build full HTML page
    # ------------------------------------------------------------------

    def _build_html(self, body_html: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="katex/katex.min.css"
      integrity="sha384-n8MVd4RsNIU0tAv4ct0nTaAbDJwPJzDEaqSD1odI+WdtXRGWt2kTvGFasHpSy3SV"
      crossorigin="anonymous">
<script src="katex/katex.min.js"
        integrity="sha384-XjKyOOlGwcjNTAIQHIpgOno0Hl1YQqzUOEleOLALmuqehneUG+vnGctmUb0ZY0l8"
        crossorigin="anonymous"></script>
<style>
{self._doc_css}
{self._pygments_css}

/* Editor-specific styles */
#editor-content {{
    outline: none;
    min-height: 200mm;
    cursor: text;
}}
#editor-content:empty:before {{
    content: '开始写作...';
    color: #bbbbbb;
    font-style: italic;
    pointer-events: none;
}}
/* ── Table editing styles (override preset border:none) ── */
#editor-content table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    table-layout: auto;
}}
#editor-content th,
#editor-content td {{
    border: 1px solid #c0c0c0 !important;
    padding: 6px 12px;
    min-width: 60px;
    min-height: 28px;
    height: 28px;
    line-height: 1.5;
    vertical-align: middle;
    word-wrap: break-word;
    text-indent: 0;
}}
#editor-content th {{
    background-color: #f2f3f5 !important;
    font-weight: bold;
    text-align: center;
    color: #333;
}}
#editor-content td:empty::after {{
    content: '\00a0';
}}
#editor-content table:hover {{
    box-shadow: 0 0 0 1px #a0c4ff;
}}
#editor-content table.table-selected {{
    outline: 2px solid #1a73e8 !important;
    outline-offset: 2px;
    box-shadow: 0 0 0 3px rgba(26,115,232,0.15);
}}

/* ── Table context menu ── */
#table-ctx-menu {{
    position: absolute;
    display: none;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 4px 0;
    box-shadow: 0 4px 16px rgba(0,0,0,0.14);
    z-index: 9999;
    min-width: 130px;
    font-size: 13px;
    font-family: 'Microsoft YaHei', sans-serif;
    user-select: none;
}}
.ctx-item {{
    padding: 7px 16px;
    cursor: pointer;
    color: #333;
}}
.ctx-item:hover {{
    background: #f0f4ff;
    color: #1a73e8;
}}
.ctx-sep {{
    height: 1px;
    background: #eee;
    margin: 3px 0;
}}
.ctx-danger {{
    color: #d9534f;
}}
.ctx-danger:hover {{
    background: #fdecea !important;
    color: #c9302c !important;
}}

/* ── Math formula ── */
.math-formula {{
    display: inline-block;
    vertical-align: middle;
    cursor: default;
    padding: 0 2px;
}}
.math-formula-block {{
    display: block;
    text-align: center;
    margin: 0.8em 0;
    padding: 8px 0;
}}
.math-formula:hover {{
    background: rgba(74, 144, 217, 0.08);
    border-radius: 3px;
}}
.math-formula .katex {{
    font-size: 1.1em;
}}
.math-formula-block .katex {{
    font-size: 1.3em;
}}

/* Image interaction */
#editor-content img {{
    cursor: pointer;
    max-width: 100%;
}}
#editor-content img.img-selected {{
    outline: 2px solid #1a73e8;
    outline-offset: 2px;
}}
#img-resize-overlay {{
    position: absolute;
    pointer-events: none;
    box-sizing: border-box;
    z-index: 10000;
    display: none;
}}
.img-mover {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    cursor: move;
    pointer-events: all;
    z-index: 1;
}}
.img-handle {{
    position: absolute;
    width: 10px;
    height: 10px;
    background: #1a73e8;
    border: 1px solid #fff;
    border-radius: 2px;
    pointer-events: all;
    z-index: 2;
}}
.img-handle-se {{ bottom: -5px; right: -5px; cursor: se-resize; }}
.img-handle-sw {{ bottom: -5px; left: -5px; cursor: sw-resize; }}
.img-handle-ne {{ top: -5px; right: -5px; cursor: ne-resize; }}
.img-handle-nw {{ top: -5px; left: -5px; cursor: nw-resize; }}

/* ── AI Inline Editing ── */
.ai-block {{
    position: relative;
    margin: 8px 0;
    border-radius: 6px;
    overflow: hidden;
}}
.ai-block-new {{
    background-color: #E8F5E9;
    border-left: 4px solid #10A37F;
}}
.ai-block-modified {{
    background-color: #FFF8E1;
    border-left: 4px solid #FF9800;
}}
.ai-block-error {{
    border-left-color: #e74c3c;
}}
.ai-block-toolbar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 12px;
    background: rgba(0,0,0,0.03);
    border-bottom: 1px solid rgba(0,0,0,0.06);
    font-size: 12px;
    user-select: none;
}}
.ai-block-label {{
    color: #10A37F;
    font-weight: bold;
}}
.ai-block-modified .ai-block-label {{
    color: #FF9800;
}}
.ai-block-loading {{
    color: #999;
    font-style: italic;
}}
.ai-block-content {{
    padding: 10px 14px;
    line-height: 1.8;
    min-height: 20px;
}}
.ai-btn-accept {{
    background: #10A37F;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 3px 12px;
    font-size: 12px;
    cursor: pointer;
    font-weight: bold;
    margin-left: auto;
}}
.ai-btn-accept:disabled {{
    background: #a0d4c4;
    cursor: not-allowed;
    opacity: 0.6;
}}
.ai-btn-accept:hover:not(:disabled) {{ background: #0D8C6D; }}
.ai-btn-reject {{
    background: transparent;
    color: #999;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 3px 12px;
    font-size: 12px;
    cursor: pointer;
}}
.ai-btn-reject:hover {{ background: #f5f5f5; color: #666; }}

/* ── AI Thinking Animation ── */
.ai-thinking {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 28px 0 20px;
    gap: 14px;
    animation: aiThinkIn 0.5s ease-out;
}}
@keyframes aiThinkIn {{
    from {{ opacity: 0; transform: scale(0.85) translateY(10px); }}
    to {{ opacity: 1; transform: scale(1) translateY(0); }}
}}
.ai-thinking-text {{
    font-size: 13px;
    color: #10A37F;
    font-family: 'Microsoft YaHei', sans-serif;
    letter-spacing: 0.5px;
    display: flex;
    align-items: baseline;
    gap: 1px;
}}
.ai-thinking-header {{
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #10A37F;
    font-weight: bold;
    margin-bottom: 6px;
    font-family: 'Microsoft YaHei', sans-serif;
}}
.ai-thinking-icon {{
    font-size: 16px;
}}
.ai-thinking-stream {{
    font-size: 12px;
    color: #888;
    line-height: 1.5;
    max-height: 120px;
    overflow-y: auto;
    padding: 6px 10px;
    background: rgba(16, 163, 127, 0.04);
    border-radius: 4px;
    border-left: 2px solid rgba(16, 163, 127, 0.2);
    font-family: 'Microsoft YaHei', sans-serif;
    word-break: break-all;
}}
.ai-dot {{
    display: inline-block;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #10A37F;
    animation: aiDotWave 1.4s ease-in-out infinite;
    margin-left: 2px;
}}
.ai-dot:nth-child(2) {{ animation-delay: 0.15s; }}
.ai-dot:nth-child(3) {{ animation-delay: 0.3s; }}
@keyframes aiDotWave {{
    0%, 80%, 100% {{ transform: translateY(0); opacity: 0.3; }}
    40% {{ transform: translateY(-5px); opacity: 1; }}
}}

/* ── Plagiarism Highlights ── */
.plag-mark {{
    border-radius: 2px;
    padding: 0 1px;
    cursor: pointer;
    position: relative;
}}
.plag-high {{
    text-decoration: underline wavy #e74c3c;
    text-underline-offset: 3px;
    background-color: rgba(231, 76, 60, 0.08);
}}
.plag-medium {{
    text-decoration: underline dashed #f39c12;
    text-underline-offset: 3px;
    background-color: rgba(243, 156, 18, 0.06);
}}

/* ── Track Changes (inline diff) ── */
del.ai-del {{
    color: #c0392b;
    text-decoration: line-through;
    background-color: rgba(231, 76, 60, 0.12);
    border-radius: 2px;
    padding: 1px 2px;
    text-decoration-thickness: 2px;
}}
ins.ai-ins {{
    color: #1e8449;
    text-decoration: none;
    background-color: rgba(39, 174, 96, 0.15);
    border-radius: 2px;
    padding: 1px 2px;
    font-weight: 500;
}}

/* ── Streaming Section Diff Indicators ── */
.tc-section-header {{
    font-size: 12px;
    color: #999;
    padding: 6px 14px;
    margin: 16px 0 4px;
    font-family: 'Microsoft YaHei', sans-serif;
    text-indent: 0;
    border-top: 1px solid #e8e8e8;
    user-select: none;
}}
.tc-section-processing {{
    font-size: 12px;
    color: #1a73e8;
    padding: 8px 14px;
    background: linear-gradient(90deg, rgba(26,115,232,0.08) 0%, rgba(26,115,232,0.02) 100%);
    border-left: 3px solid #1a73e8;
    border-radius: 0 6px 6px 0;
    margin: 6px 0;
    font-family: 'Microsoft YaHei', sans-serif;
    text-indent: 0;
    animation: tcPulse 1.8s ease-in-out infinite;
}}
@keyframes tcPulse {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}
.tc-section-pending {{
    font-size: 11px;
    color: #ccc;
    padding: 4px 14px;
    margin: 4px 0;
    font-family: 'Microsoft YaHei', sans-serif;
    text-indent: 0;
}}
.tc-section-done {{
    font-size: 12px;
    color: #27ae60;
    padding: 4px 14px;
    margin: 4px 0;
    font-family: 'Microsoft YaHei', sans-serif;
    text-indent: 0;
}}
.tc-section-unchanged {{
    font-size: 11px;
    color: #bbb;
    padding: 4px 14px;
    margin: 4px 0;
    font-family: 'Microsoft YaHei', sans-serif;
    text-indent: 0;
    font-style: italic;
}}
#track-changes-bar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: linear-gradient(135deg, #ffffff 0%, #f8fffe 100%);
    border-bottom: 2px solid #10A37F;
    padding: 10px 24px;
    display: none;
    align-items: center;
    gap: 14px;
    font-size: 13px;
    font-family: 'Microsoft YaHei', sans-serif;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}}
#track-changes-bar .tc-label {{
    color: #10A37F;
    font-weight: bold;
    font-size: 14px;
}}
#track-changes-bar .tc-stats {{
    color: #888;
    font-size: 12px;
}}
#track-changes-bar .tc-btn-accept {{
    margin-left: auto;
    background: #10A37F;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 20px;
    font-size: 13px;
    cursor: pointer;
    font-weight: bold;
}}
#track-changes-bar .tc-btn-accept:hover {{
    background: #0D8C6D;
}}
#track-changes-bar .tc-btn-reject {{
    background: transparent;
    color: #666;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
}}
#track-changes-bar .tc-btn-reject:hover {{
    background: #f5f5f5;
    color: #333;
}}
</style>
{self._JS_EDITOR}
<script>
{self._chart_edit_js}
</script>
</head>
<body class="preset-{self._preset}">
<div id="track-changes-bar">
    <span style="font-size:16px">✦</span>
    <span class="tc-label">AI 修订预览</span>
    <span class="tc-stats" id="tc-stats"></span>
    <button class="tc-btn-accept" onclick="tcAccept()">✓ 采纳修改</button>
    <button class="tc-btn-reject" onclick="tcReject()">✕ 撤回</button>
</div>
<div class="pages-wrapper">
<div class="page-container">
<div id="editor-content" contenteditable="true">
{body_html}
</div>
</div>
</div>
<div id="page-counter" class="page-counter" style="display:none;"></div>
</body>
</html>"""

    # ------------------------------------------------------------------
    # Page lifecycle
    # ------------------------------------------------------------------

    def _on_renderer_crash(self, status, exit_code):
        """Handle WebEngine renderer process crash — reload the page."""
        logger.warning(
            "WebEngine 渲染进程崩溃 (status=%s, code=%d)，正在重载...",
            status,
            exit_code,
        )
        self._renderer_crashed = True
        self._page_loaded = False
        # Schedule reload on next event loop iteration to avoid re-entry
        QTimer.singleShot(100, self._reload_after_crash)

    def _reload_after_crash(self):
        """Reload the editor page after a renderer crash."""
        try:
            md = self._pending_content or ""
            full_html = self._build_html(self._renderer.render(md) if md else "")
            self._view.setHtml(full_html, self._base_url)
            self._renderer_crashed = False
            logger.info("WebEngine 页面已重新加载")
        except Exception as e:
            logger.error("WebEngine 重载失败: %s", e)

    def _on_page_ready(self):
        """Called when WebChannel is connected and editor is initialized."""
        self._page_loaded = True
        self._renderer_crashed = False
        if self._pending_content is not None:
            self.set_content_from_markdown(self._pending_content)
            self._pending_content = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _safe_run_js(self, js: str, callback=None):
        """Run JavaScript only if the page is loaded and renderer is alive."""
        if not self._page_loaded or self._renderer_crashed:
            return
        try:
            if callback:
                self._view.page().runJavaScript(js, callback)
            else:
                self._view.page().runJavaScript(js)
        except RuntimeError as e:
            logger.warning("JS 执行失败 (page 已销毁?): %s", e)

    def set_content_from_markdown(self, markdown_text: str):
        """Render markdown and load into the editable area."""
        if not self._page_loaded:
            self._pending_content = markdown_text
            return
        html_body = self._renderer.render(markdown_text)
        # Escape backticks and backslashes for JS string
        escaped = html_body.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        # Invalidate saved selection range before replacing content
        js = f"_savedRange = null; setEditorContent(`{escaped}`);"
        self._safe_run_js(js)

    def get_html(self, callback):
        """Asynchronously get current HTML from the editor."""
        self._safe_run_js("getEditorHTML();", callback)

    def get_markdown(self, callback):
        """Asynchronously get current content as Markdown."""

        def _on_html(html):
            md = html_to_markdown(html) if html else ""
            callback(md)

        self.get_html(_on_html)

    def exec_format_command(self, command: str, value: str = ""):
        """Execute a formatting command via JavaScript."""
        if value:
            escaped_value = value.replace("'", "\\'")
            js = f"execFormat('{command}', '{escaped_value}');"
        else:
            js = f"execFormat('{command}');"
        self._safe_run_js(js)

    def exec_js(self, js_code: str, callback=None):
        """Execute arbitrary JavaScript in the editor page."""
        self._safe_run_js(js_code, callback)

    def insert_table_html(self, html: str):
        """Insert a table at the current cursor position via safe JSON encoding."""
        import json as _json

        safe = _json.dumps(html)
        self._safe_run_js(f"insertTableHTML({safe});")

    def insert_chart_html(self, html: str):
        """Insert a chart (inline SVG) at the current cursor position."""
        import json as _json

        safe = _json.dumps(html)
        self._safe_run_js(f"insertChartHTML({safe});")

    def set_preset(self, preset: str):
        """Switch document style preset (academic/modern/classic)."""
        if preset != self._preset:
            self._preset = preset
            js = f'document.body.className = "preset-{preset}";'
            self._safe_run_js(js)

    def get_preset(self) -> str:
        return self._preset

    # Editor actions exposed as methods
    def undo(self):
        self._safe_run_js("editorUndo();")

    def redo(self):
        self._safe_run_js("editorRedo();")

    def select_all(self):
        self._safe_run_js("editorSelectAll();")

    def focus_editor(self):
        self._safe_run_js("if(editorEl) editorEl.focus();")

    # Find & Replace
    def find_text(
        self, needle: str, case_sensitive: bool = False, backward: bool = False, callback=None
    ):
        cs = "true" if case_sensitive else "false"
        bw = "true" if backward else "false"
        escaped = needle.replace("'", "\\'").replace("\\", "\\\\")
        js = f"findInContent('{escaped}', {cs}, {bw});"
        self._safe_run_js(js, callback)

    def replace_selection(self, replacement: str, callback=None):
        escaped = replacement.replace("'", "\\'").replace("\\", "\\\\")
        js = f"replaceSelection('{escaped}');"
        self._safe_run_js(js, callback)

    def replace_all(
        self, needle: str, replacement: str, case_sensitive: bool = False, callback=None
    ):
        en = needle.replace("'", "\\'").replace("\\", "\\\\")
        er = replacement.replace("'", "\\'").replace("\\", "\\\\")
        cs = "true" if case_sensitive else "false"
        js = f"replaceAll('{en}', '{er}', {cs});"
        self._safe_run_js(js, callback)

    def scroll_to_heading(self, heading_text: str):
        escaped = heading_text.replace("'", "\\'")
        self._safe_run_js(f"scrollToHeading('{escaped}');")

    # Compatibility shim
    def set_css(self, css: str):
        """Ignored — CSS is managed internally."""
        pass

    # ------------------------------------------------------------------
    # AI inline editing
    # ------------------------------------------------------------------

    def get_cursor_screen_pos(self, callback):
        """Get cursor screen position (x, y) from the editor via JS.
        Uses a temporary marker element for reliable coordinates."""
        js = """
        (function() {
            var sel = window.getSelection();
            if (!sel.rangeCount) return JSON.stringify({x:0, y:0});
            var range = sel.getRangeAt(0).cloneRange();
            range.collapse(false);
            var marker = document.createElement('span');
            marker.textContent = '\u200b';
            range.insertNode(marker);
            var rect = marker.getBoundingClientRect();
            var result = {x: Math.round(rect.left), y: Math.round(rect.bottom)};
            marker.parentNode.removeChild(marker);
            sel.removeAllRanges();
            try { sel.addRange(range); } catch(e) {}
            return JSON.stringify(result);
        })();
        """
        self._safe_run_js(js, callback)

    def get_ai_context(self, callback):
        """Get document context at cursor position for AI."""
        self._safe_run_js("aiGetContext();", callback)

    def ai_start_block(self, ai_id: str, mode: str):
        """Create an inline AI block at cursor position."""
        self._safe_run_js(f"aiStartBlock('{ai_id}', '{mode}');")

    def ai_start_block_at_heading(self, ai_id: str, mode: str, heading_text: str):
        """Create an inline AI block right after a specific heading."""
        import json as _json

        safe = _json.dumps(heading_text)
        self._safe_run_js(f"aiStartBlockAtHeading('{ai_id}', '{mode}', {safe});")

    def ai_update_thinking(self, ai_id: str, text: str):
        """Stream reasoning/thinking text into the AI block's thinking area."""
        import json as _json

        safe = _json.dumps(text)
        self._safe_run_js(f"aiUpdateThinking('{ai_id}', {safe});")

    def ai_append_chunk(self, ai_id: str, text: str):
        """Append a streamed text chunk to an active AI block."""
        import json as _json

        safe = _json.dumps(text)
        self._safe_run_js(f"aiAppendChunk('{ai_id}', {safe});")

    def ai_render_block(self, ai_id: str, html: str):
        """Replace AI block content with rendered HTML."""
        import json as _json

        safe = _json.dumps(html)
        self._safe_run_js(f"aiRenderBlock('{ai_id}', {safe});")

    def ai_finish_block(self, ai_id: str):
        """Mark an AI block as complete, show accept button."""
        self._safe_run_js(f"aiFinishBlock('{ai_id}');")

    def ai_update_block_status(self, ai_id: str, text: str):
        """Update the loading status text inside an AI block."""
        import json as _json

        safe = _json.dumps(text)
        self._safe_run_js(f"aiUpdateBlockStatus('{ai_id}', {safe});")

    def ai_error_block(self, ai_id: str, msg: str):
        """Show error state on an AI block."""
        import json as _json

        safe = _json.dumps(msg)
        self._safe_run_js(f"aiErrorBlock('{ai_id}', {safe});")

    def ai_mark_smart_block(self, ai_id: str):
        """Mark an AI block as a smart-modify block (accept goes to Python)."""
        self._safe_run_js(
            f"var b=editorEl.querySelector('[data-ai-id=\"{ai_id}\"]');"
            f"if(b)b.setAttribute('data-ai-smart','true');"
        )

    def show_track_changes_bar(self, del_count: int = 0, ins_count: int = 0):
        """Show the track-changes accept/reject toolbar."""
        self._safe_run_js(f"showTrackChangesBar({del_count}, {ins_count});")

    def hide_track_changes_bar(self):
        """Hide the track-changes toolbar and restore editing."""
        self._safe_run_js("hideTrackChangesBar();")

    # ------------------------------------------------------------------
    # Plagiarism highlighting
    # ------------------------------------------------------------------

    def highlight_plagiarism(self, results_json: str):
        """Highlight plagiarism results in the editor."""
        import json as _json

        safe = _json.dumps(results_json)
        self._safe_run_js(f"highlightPlagiarism({safe});")

    def clear_plagiarism_highlights(self):
        """Remove all plagiarism highlights."""
        self._safe_run_js("clearPlagiarismHighlights();")

    def scroll_to_plag_sentence(self, index: int):
        """Scroll to a specific plagiarism-highlighted sentence."""
        self._safe_run_js(f"scrollToPlagSentence({index});")
