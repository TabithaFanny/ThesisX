import difflib
import html as _html
import json
import logging
import os
import re
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

from app.constants import (
    APP_NAME,
    EXPORT_DOCX_FILTER,
    EXPORT_HTML_FILTER,
    EXPORT_PDF_FILTER,
    EXPORT_PPTX_FILTER,
    PREVIEW_DEBOUNCE_MS,
    PREVIEW_STYLE_ACADEMIC,
    SUPPORTED_FILE_FILTER,
    WTZ_FILE_FILTER,
)
from app.core.ai_service import (
    MAX_TOKENS_EDIT,
    MAX_TOKENS_OPTIMIZE,
    MAX_TOKENS_REWRITE,
    MAX_TOKENS_SECTION,
    TEMP_CONTINUE,
    TEMP_DEFAULT,
    TEMP_EDIT,
    TEMP_INSERT,
    TEMP_OPTIMIZE,
    TEMP_REWRITE,
    TEMP_SECTION_EDIT,
    AiWorker,
    build_continue_messages,
    build_custom_edit_messages,
    build_custom_insert_messages,
    build_custom_smart_messages,
    build_high_quality_rewrite_messages,
    build_optimize_messages,
    build_optimize_selected_messages,
    build_section_continue_messages,
    build_section_edit_messages,
    build_smart_insert_messages,
)
from app.core.config import Config
from app.core.db_plagiarism_service_optimized import (
    DbPlagiarismWorkerOptimized,
    merge_results,
)
from app.core.document_manager import DocumentManager
from app.core.exporter import Exporter
from app.core.html_to_markdown import html_to_markdown
from app.core.image_service import (
    ImageProcessWorker,
    has_image_placeholders,
)
from app.core.markdown_renderer import MarkdownRenderer
from app.core.outline_parser import OutlineParser
from app.core.plagiarism_service import (
    IterativeRewriteConfig,
    build_anti_aigc_anti_dup_messages,
    build_batch_anti_aigc_anti_dup_messages,
    build_batch_rewrite_messages,
    build_check_messages,
    build_rewrite_messages,
    calculate_duplication_rate,
    create_rewrite_context_from_result,
    fetch_paper_expressions,
    filter_flagged_sentences,
    merge_results,
    parse_check_result,
    parse_rewrite_result,
    split_sentences,
)
from app.core.table_handler import TableHandler
from app.core.wtz_handler import WtzMeta
from app.shortcuts.formatting_actions import FormattingActions
from app.shortcuts.shortcut_manager import ShortcutManager
from app.styles import DARK_STYLE, MAIN_STYLE
from app.ui.ai_dialog import AiDialog
from app.ui.ai_input_bar import AiInputBar
from app.ui.chart_dialog import ChartDialog
from app.ui.docx_export_dialog import DocxExportDialog
from app.ui.find_replace_dialog import FindReplaceDialog
from app.ui.formula_dialog import FormulaDialog
from app.ui.icons import icon_chatgpt, icon_claude, icon_gemini
from app.ui.iterative_rewrite_dialog import IterativeRewriteDialog
from app.ui.model_switch_dialog import ModelSwitchDialog
from app.ui.outline_widget import OutlineWidget
from app.ui.plagiarism_panel import PlagiarismPanel
from app.ui.preview_widget import PreviewWidget
from app.ui.settings_dialog import SettingsDialog
from app.ui.shortcut_settings_dialog import ShortcutSettingsDialog
from app.ui.skills_dialog import SkillsDialog
from app.ui.status_bar import StatusBar
from app.ui.table_dialog import TableDialog
from app.ui.template_dialog import TemplateDialog
from app.ui.toolbar import FormattingToolbar, MoreToolbar


class MainWindow(QMainWindow):
    _LARGE_DOC_SMART_THRESHOLD = 50000  # chars

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(MAIN_STYLE)

        # Load user config first
        self.config = Config()

        self.doc_manager = DocumentManager()
        self.renderer = MarkdownRenderer()
        self.outline_parser = OutlineParser()
        self.exporter = Exporter()

        # Preview CSS for export
        self._preview_css = self._load_preview_css()
        self.exporter.set_css(self._preview_css)

        # Internal Markdown cache (synced from contentEditable)
        self._current_markdown = ""
        self._closing = False  # guard against post-close access

        # AI track-changes state
        self._tc_original_md = None  # original markdown before AI
        self._tc_modified_md = None  # modified markdown from AI
        self._in_track_changes = False  # guard: suppress content sync
        self._ai_batch_running = False
        self._ai_batch_cancelled = False
        self._ai_batch_sections = []
        self._ai_batch_results = []
        self._ai_batch_index = 0
        self._ai_batch_mode = "optimize_low_dup"
        self._ai_batch_instruction = ""

        # Multi-section continue state
        self._multi_continue_running = False
        self._multi_continue_sections = []  # list of section info dicts
        self._multi_continue_index = 0

        # Streaming section diff state (Ctrl+I modify)
        self._tc_stream_running = False
        self._tc_stream_sections = []  # original sections
        self._tc_stream_results = []  # modified sections (None = pending)
        self._tc_stream_index = 0
        self._tc_stream_instruction = ""
        self._tc_stream_target_indices = []  # targeted section indices (empty = all)

        # Plagiarism check state
        self._plag_sentences = []  # list[Sentence]
        self._plag_results = []  # list[CheckResult]

        # Debounce timer for HTML->MD conversion
        self._convert_timer = QTimer()
        self._convert_timer.setSingleShot(True)
        self._convert_timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self._convert_timer.timeout.connect(self._do_convert)
        self._pending_html = ""  # raw HTML from editor, waiting for conversion

        # Autosave timer
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._do_autosave)
        self._autosave_status_timer = QTimer()
        self._autosave_status_timer.setSingleShot(True)
        self._autosave_status_timer.setInterval(3000)
        self._autosave_status_timer.timeout.connect(lambda: self.status_bar.clear_autosave_status())

        self._init_ui()
        self._init_menubar()
        self._init_shortcuts()
        self._connect_signals()
        self._restore_config()

        # Start autosave
        if self.config.get("autosave_enabled"):
            interval_ms = self.config.get("autosave_interval_minutes", 5) * 60 * 1000
            self._autosave_timer.start(interval_ms)

        # Restore model key FIRST so _apply_ai_config uses the correct per-model API key
        self._restore_model_appearance()

        # Apply custom AI configuration (model, URL, key) from user config
        self._apply_ai_config()

        # Apply saved theme
        if self.config.get("theme") == "dark":
            self.setStyleSheet(DARK_STYLE)

        # Check for unsaved auto-recovery on startup
        self._check_auto_recovery()

        # Enable drag & drop
        self.setAcceptDrops(True)

    def _load_preview_css(self) -> str:
        css_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "preview.css"
        )
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css = f.read()
            pygments_css = MarkdownRenderer.get_pygments_css()
            return css + "\n" + pygments_css
        except FileNotFoundError:
            return ""

    def _init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        self.toolbar = FormattingToolbar()
        self.addToolBar(self.toolbar)

        self.addToolBarBreak()
        self.more_toolbar = MoreToolbar()
        self.addToolBar(self.more_toolbar)

        self._content_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.outline = OutlineWidget()
        self._content_splitter.addWidget(self.outline)

        # Single editable panel — no more left/right split
        self.preview = PreviewWidget()
        self._content_splitter.addWidget(self.preview)

        # Plagiarism panel (right side, hidden by default)
        self.plagiarism_panel = PlagiarismPanel()
        self.plagiarism_panel.setVisible(False)
        self._content_splitter.addWidget(self.plagiarism_panel)

        self._content_splitter.setSizes([180, 820, 0])
        self._content_splitter.setHandleWidth(1)

        main_layout.addWidget(self._content_splitter)

        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        self.formatting = FormattingActions(self.preview)

    def _init_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        open_action = QAction("打开(&O)", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_document)
        file_menu.addAction(open_action)

        self.recent_menu = file_menu.addMenu("最近文件")
        self._update_recent_menu()

        file_menu.addSeparator()

        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_document_as)
        file_menu.addAction(save_as_action)

        save_wtz_action = QAction("保存为 ThesisX 文档 (.wtz)...", self)
        save_wtz_action.triggered.connect(self.save_as_wtz)
        file_menu.addAction(save_wtz_action)

        file_menu.addSeparator()

        export_html_action = QAction("导出 HTML", self)
        export_html_action.triggered.connect(self.export_html)
        file_menu.addAction(export_html_action)

        export_pdf_action = QAction("导出 PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_action)

        export_docx_action = QAction("导出 Word (DOCX)", self)
        export_docx_action.setShortcut(QKeySequence("Ctrl+E"))
        export_docx_action.triggered.connect(self.export_docx)
        file_menu.addAction(export_docx_action)

        export_docx_enhanced_action = QAction("导出 Word 强化版...", self)
        export_docx_enhanced_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_docx_enhanced_action.triggered.connect(self.export_docx_enhanced)
        file_menu.addAction(export_docx_enhanced_action)

        export_pptx_action = QAction("导出 PPT (PPTX)", self)
        export_pptx_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        export_pptx_action.triggered.connect(self.export_pptx)
        file_menu.addAction(export_pptx_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence("Ctrl+W"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("编辑(&E)")

        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.preview.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.preview.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Cut/Copy/Paste are handled natively by contentEditable,
        # but we add menu entries for discoverability
        cut_action = QAction("剪切", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        edit_menu.addAction(cut_action)

        copy_action = QAction("复制", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        edit_menu.addAction(copy_action)

        paste_action = QAction("粘贴", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("全选", self)
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self.preview.select_all)
        edit_menu.addAction(select_all_action)

        edit_menu.addSeparator()

        find_action = QAction("查找...", self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(lambda: self._find_dialog.show_and_focus("find"))
        edit_menu.addAction(find_action)

        replace_action = QAction("替换...", self)
        replace_action.setShortcut(QKeySequence("Ctrl+H"))
        replace_action.triggered.connect(lambda: self._find_dialog.show_and_focus("replace"))
        edit_menu.addAction(replace_action)

        # Format menu
        format_menu = menubar.addMenu("格式(&O)")

        bold_action = QAction("加粗", self)
        bold_action.setShortcut(QKeySequence("Ctrl+B"))
        bold_action.triggered.connect(self.formatting.toggle_bold)
        format_menu.addAction(bold_action)

        italic_action = QAction("斜体", self)
        italic_action.triggered.connect(self.formatting.toggle_italic)
        format_menu.addAction(italic_action)

        underline_action = QAction("下划线", self)
        underline_action.setShortcut(QKeySequence("Ctrl+U"))
        underline_action.triggered.connect(self.formatting.toggle_underline)
        format_menu.addAction(underline_action)

        strike_action = QAction("删除线", self)
        strike_action.setShortcut(QKeySequence("Ctrl+D"))
        strike_action.triggered.connect(self.formatting.toggle_strikethrough)
        format_menu.addAction(strike_action)

        format_menu.addSeparator()

        for i in range(1, 7):
            h_action = QAction(f"标题 {i}", self)
            h_action.setShortcut(QKeySequence(f"Ctrl+{i}"))
            h_action.triggered.connect(
                lambda checked, level=i: self.formatting.insert_heading(level)
            )
            format_menu.addAction(h_action)

        format_menu.addSeparator()

        code_action = QAction("代码块", self)
        code_action.setShortcut(QKeySequence("Ctrl+K"))
        code_action.triggered.connect(self.formatting.insert_code_block)
        format_menu.addAction(code_action)

        quote_action = QAction("引用", self)
        quote_action.setShortcut(QKeySequence("Ctrl+Q"))
        quote_action.triggered.connect(self.formatting.insert_quote)
        format_menu.addAction(quote_action)

        format_menu.addSeparator()

        sup_action = QAction("上标", self)
        sup_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        sup_action.triggered.connect(self.formatting.insert_superscript)
        format_menu.addAction(sup_action)

        sub_action = QAction("下标", self)
        sub_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        sub_action.triggered.connect(self.formatting.insert_subscript)
        format_menu.addAction(sub_action)

        # Insert menu
        insert_menu = menubar.addMenu("插入(&I)")

        link_action = QAction("链接", self)
        link_action.setShortcut(QKeySequence("Ctrl+L"))
        link_action.triggered.connect(self.formatting.insert_link)
        insert_menu.addAction(link_action)

        image_action = QAction("图片", self)
        image_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        image_action.triggered.connect(self.formatting.insert_image)
        insert_menu.addAction(image_action)

        insert_menu.addSeparator()

        table_action = QAction("表格...", self)
        table_action.setShortcut(QKeySequence("Ctrl+T"))
        table_action.triggered.connect(self.insert_table)
        insert_menu.addAction(table_action)

        clipboard_table_action = QAction("从剪贴板导入表格", self)
        clipboard_table_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        clipboard_table_action.triggered.connect(self.import_table_from_clipboard)
        insert_menu.addAction(clipboard_table_action)

        insert_menu.addSeparator()

        list_action = QAction("无序列表", self)
        list_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        list_action.triggered.connect(self.formatting.insert_list)
        insert_menu.addAction(list_action)

        olist_action = QAction("有序列表", self)
        olist_action.triggered.connect(self.formatting.insert_ordered_list)
        insert_menu.addAction(olist_action)

        insert_menu.addSeparator()

        hr_action = QAction("分隔线", self)
        hr_action.triggered.connect(self.formatting.insert_horizontal_rule)
        insert_menu.addAction(hr_action)

        # Tools menu
        tools_menu = menubar.addMenu("工具(&T)")

        plagiarism_action = QAction("🛡 论文查重", self)
        plagiarism_action.triggered.connect(self._plagiarism_check)
        tools_menu.addAction(plagiarism_action)

        rewrite_all_action = QAction("⚡ 一键降重", self)
        rewrite_all_action.triggered.connect(self._plagiarism_rewrite_all)
        tools_menu.addAction(rewrite_all_action)

        tools_menu.addSeparator()

        settings_action = QAction("⚙ 设置...", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        shortcut_action = QAction("⌨ 快捷键设置...", self)
        shortcut_action.triggered.connect(self._show_shortcut_settings)
        tools_menu.addAction(shortcut_action)

        # View menu
        view_menu = menubar.addMenu("视图(&V)")

        toggle_outline = QAction("显示/隐藏大纲", self)
        toggle_outline.triggered.connect(self._toggle_outline)
        view_menu.addAction(toggle_outline)

        toggle_plag = QAction("显示/隐藏查重面板", self)
        toggle_plag.triggered.connect(self._toggle_plagiarism_panel)
        view_menu.addAction(toggle_plag)

        view_menu.addSeparator()

        self._dark_mode_action = QAction("深色模式", self)
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.setChecked(self.config.get("theme") == "dark")
        self._dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self._dark_mode_action)

        # Help menu
        help_menu = menubar.addMenu("帮助(&H)")

        template_action = QAction("从模板新建...", self)
        template_action.triggered.connect(self.new_from_template)
        help_menu.addAction(template_action)

        help_menu.addSeparator()

        about_action = QAction(f"关于 {APP_NAME}", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_shortcuts(self):
        self.shortcut_manager = ShortcutManager(self)
        self._find_dialog = FindReplaceDialog(self.preview, self)

    def _connect_signals(self):
        # Content changes from the editable preview
        self.preview.content_changed.connect(self._on_content_changed)
        # Stats updates from JS
        self.preview.cursor_info_updated.connect(self._on_stats_updated)
        # Cursor position updates from JS
        self.preview.cursor_position_updated.connect(
            lambda line, col: self.status_bar.update_position(line, col)
        )
        # Outline heading clicks
        self.outline.heading_clicked.connect(self._jump_to_heading)

        # Preset switcher
        self.toolbar.preset_changed.connect(self._on_preset_changed)

        # Toolbar signals
        self.toolbar.bold_clicked.connect(self.formatting.toggle_bold)
        self.toolbar.italic_clicked.connect(self.formatting.toggle_italic)
        self.toolbar.underline_clicked.connect(self.formatting.toggle_underline)
        self.toolbar.strikethrough_clicked.connect(self.formatting.toggle_strikethrough)
        self.toolbar.heading_clicked.connect(self.formatting.insert_heading)
        self.toolbar.link_clicked.connect(self.formatting.insert_link)
        self.toolbar.image_clicked.connect(self.formatting.insert_image)
        self.toolbar.code_clicked.connect(self.formatting.insert_code_block)
        self.toolbar.table_clicked.connect(self.insert_table)
        self.toolbar.quote_clicked.connect(self.formatting.insert_quote)
        self.toolbar.list_clicked.connect(self.formatting.insert_list)
        self.toolbar.ordered_list_clicked.connect(self.formatting.insert_ordered_list)
        self.toolbar.hr_clicked.connect(self.formatting.insert_horizontal_rule)
        # GPT actions (from toolbar)
        self.toolbar.gpt_optimize_clicked.connect(self._ai_optimize)
        self.toolbar.gpt_continue_clicked.connect(self._ai_continue)
        self.toolbar.gpt_custom_clicked.connect(self._ai_custom)
        self.toolbar.gpt_rewrite_clicked.connect(self._ai_rewrite_selected)
        self.toolbar.model_switch_clicked.connect(self._show_model_switch)
        self.toolbar.skills_clicked.connect(self._show_skills_dialog)
        # Plagiarism panel signals
        self.plagiarism_panel.sentence_clicked.connect(self._plag_jump_to)
        self.plagiarism_panel.rewrite_one.connect(self._plag_rewrite_one)
        self.plagiarism_panel.rewrite_all.connect(self._plagiarism_rewrite_all)
        self.plagiarism_panel.smart_rewrite.connect(self._smart_iterative_rewrite)
        self.plagiarism_panel.recheck.connect(self._plagiarism_check)

        # More panel toggle
        self.toolbar.more_toggled.connect(self.more_toolbar.setVisible)

        # More toolbar buttons
        self.more_toolbar.superscript_clicked.connect(self.formatting.insert_superscript)
        self.more_toolbar.subscript_clicked.connect(self.formatting.insert_subscript)
        self.more_toolbar.clear_format_clicked.connect(self.formatting.clear_formatting)
        self.more_toolbar.indent_clicked.connect(self.formatting.indent)
        self.more_toolbar.outdent_clicked.connect(self.formatting.outdent)
        self.more_toolbar.line_height_changed.connect(self.formatting.set_line_height)
        self.more_toolbar.chart_clicked.connect(self.insert_chart)
        self.more_toolbar.formula_clicked.connect(self.insert_formula)

        self.toolbar.font_color_changed.connect(self.formatting.set_font_color)
        self.toolbar.highlight_color_changed.connect(self.formatting.set_highlight_color)
        self.toolbar.font_size_changed.connect(self.formatting.set_font_size)
        self.toolbar.font_family_changed.connect(self.formatting.set_font_family)

        self.toolbar.align_left_clicked.connect(lambda: self.formatting.set_text_align("left"))
        self.toolbar.align_center_clicked.connect(lambda: self.formatting.set_text_align("center"))
        self.toolbar.align_right_clicked.connect(lambda: self.formatting.set_text_align("right"))
        self.toolbar.align_justify_clicked.connect(
            lambda: self.formatting.set_text_align("justify")
        )

        # AI dialog shortcut (Ctrl+I) — lightweight input bar
        self._ai_input_bar = AiInputBar()
        self._ai_input_bar.instruction_submitted.connect(self._ai_inline_custom)
        self.preview.ai_dialog_requested.connect(self._show_ai_input_bar)

        # AI smart modify accept / reject
        self.preview.smart_modify_accepted.connect(self._on_smart_modify_accepted)
        self.preview.smart_modify_rejected.connect(self._on_smart_modify_rejected)

        # Ctrl+F / Ctrl+H from WebEngine
        self.preview.find_replace_requested.connect(
            lambda mode: self._find_dialog.show_and_focus(mode)
        )

        # Format state (active formatting indicators)
        self.preview.format_state_changed.connect(self._on_format_state_changed)

    def _on_format_state_changed(self, state_json: str):
        """Update toolbar active indicators based on current cursor format."""
        try:
            state = json.loads(state_json)
            self.toolbar.update_format_state(state)
            self.more_toolbar.update_format_state(state)
        except (json.JSONDecodeError, Exception):
            pass

    def _on_preset_changed(self, preset: str):
        self.preview.set_preset(preset)
        # If working with .wtz, persist preset in metadata
        if self.doc_manager.current_wtz_meta:
            self.doc_manager.current_wtz_meta.style_preset = preset

    def _on_content_changed(self, html: str):
        """Called when user edits in the contentEditable area."""
        if self._closing:
            return
        self._pending_html = html
        # Adaptive debounce: longer interval for larger documents
        doc_len = len(self._current_markdown)
        if doc_len > 100_000:
            self._convert_timer.setInterval(800)
        elif doc_len > 30_000:
            self._convert_timer.setInterval(500)
        else:
            self._convert_timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self._convert_timer.start()

    def _do_convert(self):
        """Convert pending HTML to Markdown and update internal state."""
        if self._closing or self._in_track_changes:
            return
        try:
            html = self._pending_html
            if not html:
                self._current_markdown = ""
            else:
                self._current_markdown = html_to_markdown(html)

            self.doc_manager.current_document.update_content(self._current_markdown)
            self._update_title()
            self._update_status_file_info()

            # Update outline from current markdown
            headings = self.outline_parser.parse(self._current_markdown)
            self.outline.update_outline(headings)
        except Exception as e:
            logger.warning("内容转换/更新失败: %s", e)

    def _on_stats_updated(self, words: int, chars: int):
        """Receive word/char counts from JS."""
        self.status_bar.update_stats(words, chars)

    def _update_title(self):
        doc = self.doc_manager.current_document
        title = APP_NAME
        if doc.file_path:
            title = f"{APP_NAME} - {doc.filename}"
        if doc.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def _update_status_file_info(self):
        doc = self.doc_manager.current_document
        self.status_bar.update_file_info(doc.file_path or "", doc.is_modified)

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------

    def _restore_config(self):
        w = self.config.get("window_width", 1280)
        h = self.config.get("window_height", 800)
        self.resize(w, h)
        x = self.config.get("window_x", -1)
        y = self.config.get("window_y", -1)
        if x >= 0 and y >= 0:
            self.move(x, y)

        outline_w = self.config.get("outline_width", 180)
        preview_w = self.config.get("preview_width", 820)
        # 防止大纲宽度被保存为 0 导致不可见
        if outline_w < 80:
            outline_w = 220
        if hasattr(self, "_content_splitter"):
            self._content_splitter.setSizes([outline_w, preview_w, 0])

    def _save_config(self):
        geom = self.geometry()
        self.config.set("window_width", geom.width())
        self.config.set("window_height", geom.height())
        self.config.set("window_x", geom.x())
        self.config.set("window_y", geom.y())
        if hasattr(self, "_content_splitter"):
            sizes = self._content_splitter.sizes()
            if len(sizes) >= 2:
                # 只在大纲可见且宽度合理时才保存，避免保存 0
                self.config.set("outline_width", max(sizes[0], 80))
                self.config.set("preview_width", sizes[1])
        self.config.save()
        logger.info("配置已保存")

    # ------------------------------------------------------------------
    # Autosave
    # ------------------------------------------------------------------

    def _do_autosave(self):
        if self._closing:
            return
        doc = self.doc_manager.current_document
        if not doc.is_modified:
            return
        if doc.file_path:
            doc.update_content(self._current_markdown)
            if self.doc_manager.save_document():
                self._update_title()
                self._update_status_file_info()
                self.status_bar.show_autosave_status("已自动保存")
                self._autosave_status_timer.start()
                logger.info("自动保存: %s", doc.file_path)
        else:
            # Save to backup location
            backup_dir = os.path.join(os.path.expanduser("~"), ".wenbiao", "autosave")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, "autosave.md")
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(self._current_markdown)
                self.status_bar.show_autosave_status("备份已保存")
                self._autosave_status_timer.start()
                logger.info("自动备份保存到: %s", backup_path)
            except OSError as e:
                logger.warning("自动备份失败: %s", e)

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                if path.lower().endswith((".md", ".txt", ".markdown", ".wtz")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".md", ".txt", ".markdown", ".wtz")):
                if self._check_save():
                    doc = self.doc_manager.open_document(path)
                    self._current_markdown = doc.content
                    self.preview.set_content_from_markdown(doc.content)
                    self._update_title()
                    self._update_status_file_info()
                    self._update_recent_menu()
                    logger.info("拖拽打开: %s", path)
                break
        event.acceptProposedAction()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def new_document(self):
        if not self._check_save():
            return
        self.doc_manager.new_document()
        self._current_markdown = ""
        self.preview.set_content_from_markdown("")
        self._update_title()
        self._update_status_file_info()

    def open_document(self):
        if not self._check_save():
            return
        last_dir = self.config.get("last_open_dir", "")
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", last_dir, SUPPORTED_FILE_FILTER)
        if path:
            doc = self.doc_manager.open_document(path)
            self._current_markdown = doc.content
            self.preview.set_content_from_markdown(doc.content)
            self._update_title()
            self._update_status_file_info()
            self._update_recent_menu()
            self.config.set("last_open_dir", os.path.dirname(path))
            # Restore preset from .wtz metadata
            if self.doc_manager.current_wtz_meta:
                preset = self.doc_manager.current_wtz_meta.style_preset
                self.preview.set_preset(preset)
                self._sync_preset_combo(preset)
            logger.info("打开文件: %s", path)

    def save_document(self):
        if self.doc_manager.current_document.file_path:
            self.doc_manager.current_document.update_content(self._current_markdown)
            self.doc_manager.save_document()
            self._update_title()
            self._update_status_file_info()
            logger.info("保存: %s", self.doc_manager.current_document.file_path)
        else:
            self.save_document_as()

    def save_document_as(self):
        last_dir = self.config.get("last_open_dir", "")
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", last_dir, SUPPORTED_FILE_FILTER)
        if path:
            self.doc_manager.current_document.update_content(self._current_markdown)
            self.doc_manager.save_document(path)
            self._update_title()
            self._update_status_file_info()
            self._update_recent_menu()
            self.config.set("last_open_dir", os.path.dirname(path))
            logger.info("另存为: %s", path)

    def save_as_wtz(self):
        """Save current document as .wtz."""
        last_dir = self.config.get("last_open_dir", "")
        path, _ = QFileDialog.getSaveFileName(
            self, "保存为 ThesisX 文档", last_dir, WTZ_FILE_FILTER
        )
        if not path:
            return
        self.doc_manager.current_document.update_content(self._current_markdown)
        meta = self.doc_manager.current_wtz_meta or WtzMeta()
        meta.style_preset = self.preview.get_preset()
        self.doc_manager.current_wtz_meta = meta
        if self.doc_manager.save_document(path):
            self._update_title()
            self._update_status_file_info()
            self._update_recent_menu()
            self.config.set("last_open_dir", os.path.dirname(path))
            logger.info("保存 .wtz: %s", path)
        else:
            QMessageBox.warning(self, "保存失败", "无法保存 .wtz 文档。")

    def _sync_preset_combo(self, preset: str):
        """Sync the toolbar preset combo to the given preset key."""
        for i in range(self.toolbar.preset_combo.count()):
            if self.toolbar.preset_combo.itemData(i) == preset:
                self.toolbar.preset_combo.setCurrentIndex(i)
                break

    def _check_save(self) -> bool:
        doc = self.doc_manager.current_document
        doc.update_content(self._current_markdown)
        if not doc.is_modified:
            return True
        reply = QMessageBox.question(
            self,
            "保存更改",
            f'文档 "{doc.filename}" 已修改，是否保存？',
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            self.save_document()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _update_recent_menu(self):
        self.recent_menu.clear()
        for path in self.doc_manager.get_recent_files():
            action = QAction(os.path.basename(path), self)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self._open_recent(p))
            self.recent_menu.addAction(action)
        if not self.doc_manager.get_recent_files():
            empty = QAction("(空)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)

    def _open_recent(self, path):
        if not self._check_save():
            return
        if os.path.exists(path):
            doc = self.doc_manager.open_document(path)
            self._current_markdown = doc.content
            self.preview.set_content_from_markdown(doc.content)
            self._update_title()
            self._update_status_file_info()
            logger.info("打开最近文件: %s", path)

    # Export

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 HTML", "", EXPORT_HTML_FILTER)
        if path:
            self.exporter.export_html(self._current_markdown, path)
            QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")

    def export_pdf(self):
        from PyQt6.QtWidgets import QProgressDialog

        path, _ = QFileDialog.getSaveFileName(self, "导出 PDF", "", EXPORT_PDF_FILTER)
        if path:
            progress = QProgressDialog("正在导出 PDF...", None, 0, 0, self)
            progress.setWindowTitle("导出")
            progress.setMinimumDuration(0)
            progress.show()
            QApplication.processEvents()
            try:
                self.exporter.export_pdf(self._current_markdown, path)
                QMessageBox.information(self, "导出成功", f"已导出到：\n{path}")
            finally:
                progress.close()

    def export_docx(self):
        from PyQt6.QtWidgets import QProgressDialog

        path, _ = QFileDialog.getSaveFileName(self, "导出 Word", "", EXPORT_DOCX_FILTER)
        if path:
            progress = QProgressDialog("正在导出 Word...", None, 0, 0, self)
            progress.setWindowTitle("导出")
            progress.setMinimumDuration(0)
            progress.show()
            QApplication.processEvents()
            try:
                self.exporter.export_docx(self._current_markdown, path)
                QMessageBox.information(self, "导出成功", f"已导出到：\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出 DOCX 失败：\n{str(e)}")
            finally:
                progress.close()

    def export_docx_enhanced(self):
        """导出 Word 强化版，先弹出选项对话框。"""
        doc = self.doc_manager.current_document
        default_title = os.path.splitext(doc.filename or "")[0]
        dlg = DocxExportDialog(self, default_title=default_title)
        if dlg.exec() != DocxExportDialog.DialogCode.Accepted:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 Word 强化版", "", EXPORT_DOCX_FILTER)
        if not path:
            return
        file_dir = ""
        if doc.file_path:
            file_dir = os.path.dirname(doc.file_path)
        try:
            self.exporter.export_docx_enhanced(
                self._current_markdown,
                path,
                style=dlg.style,
                title=dlg.title,
                author=dlg.author,
                add_cover=dlg.add_cover,
                add_toc=dlg.add_toc,
                add_page_numbers=dlg.add_page_numbers,
                table_style=dlg.table_style,
                file_dir=file_dir,
            )
            QMessageBox.information(
                self,
                "导出成功",
                f"已导出到:\n{path}\n\n" f"提示：目录字段需在 Word 中按 Ctrl+A 后 F9 更新。",
            )
        except Exception as e:
            logger.exception("导出 Word 强化版失败")
            QMessageBox.warning(self, "导出失败", f"导出 DOCX 失败:\n{str(e)}")

    def export_pptx(self):
        """导出 PowerPoint 演示文稿，使用当前预设主题。"""
        doc = self.doc_manager.current_document
        default_title = os.path.splitext(doc.filename or "")[0]
        path, _ = QFileDialog.getSaveFileName(self, "导出 PPT", default_title, EXPORT_PPTX_FILTER)
        if not path:
            return
        try:
            style = self.preview.get_preset()
            self.exporter.export_pptx(
                self._current_markdown,
                path,
                style=style,
                title=default_title,
            )
            QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
        except Exception as e:
            logger.exception("导出 PPT 失败")
            QMessageBox.warning(self, "导出失败", f"导出 PPTX 失败:\n{str(e)}")

    # Table operations

    def insert_table(self):
        dialog = TableDialog(self)
        if dialog.exec():
            table_html = dialog.get_table_html()
            if table_html:
                self.preview.insert_table_html(table_html)

    def insert_chart(self):
        """Open chart selection dialog and insert the selected chart."""
        dialog = ChartDialog(self)
        if dialog.exec():
            chart_html = dialog.get_chart_html()
            if chart_html:
                self.preview.insert_chart_html(chart_html)

    def insert_formula(self):
        """Open formula selection dialog and insert the selected formula."""
        dialog = FormulaDialog(self)
        if dialog.exec():
            latex = dialog.get_formula()
            if latex:
                # Extract raw LaTeX and determine block vs inline
                stripped = latex.strip()
                is_block = stripped.startswith("$$") and stripped.endswith("$$")
                if is_block:
                    raw = stripped[2:-2].strip()
                else:
                    raw = stripped.lstrip("$").rstrip("$").strip()
                import json as _json

                safe_latex = _json.dumps(raw)
                is_block_js = "true" if is_block else "false"
                self.preview.exec_js(f"insertFormula({safe_latex}, {is_block_js});")

    def import_table_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text.strip():
            QMessageBox.warning(self, "导入失败", "剪贴板中没有文本数据。")
            return
        md = TableHandler.from_clipboard_text(text)
        if md:
            # Convert markdown table to HTML via renderer
            table_html = self.renderer.render(md)
            self.preview.insert_table_html(table_html)
        else:
            QMessageBox.warning(self, "导入失败", "无法解析剪贴板中的表格数据。")

    # Template

    def new_from_template(self):
        if not self._check_save():
            return
        dialog = TemplateDialog(self)
        if dialog.exec():
            content = dialog.get_content()
            if content:
                self.doc_manager.new_document()
                self._current_markdown = content
                self.preview.set_content_from_markdown(content)
                self._update_title()

    # View toggles

    def _toggle_outline(self):
        self.outline.setVisible(not self.outline.isVisible())

    def _toggle_plagiarism_panel(self):
        vis = not self.plagiarism_panel.isVisible()
        self.plagiarism_panel.setVisible(vis)
        if vis:
            sizes = self._content_splitter.sizes()
            if len(sizes) == 3 and sizes[2] == 0:
                total = sum(sizes)
                self._content_splitter.setSizes([sizes[0], total - sizes[0] - 300, 300])

    def _jump_to_heading(self, line_num: int):
        """Jump to a heading via outline click.
        We use the heading text to scroll in the WebEngine editor."""
        # Find the heading text at this line number from the outline
        headings = self.outline_parser.parse(self._current_markdown)
        for level, title, ln in headings:
            if ln == line_num:
                self.preview.scroll_to_heading(title)
                return

    def _show_about(self):
        QMessageBox.about(
            self,
            f"关于 {APP_NAME}",
            f"{APP_NAME} v2.0.0\n\n"
            "学术论文撰写与表格处理工具\n\n"
            "基于 Python + PyQt6 开发\n"
            "支持导出 PDF / HTML / DOCX / PPTX",
        )

    def _toggle_dark_mode(self, checked: bool):
        """Toggle between light and dark theme."""
        if checked:
            self.setStyleSheet(DARK_STYLE)
            self.config.set("theme", "dark")
        else:
            self.setStyleSheet(MAIN_STYLE)
            self.config.set("theme", "light")
        self.config.save()

    def _show_settings(self):
        """Open the settings dialog."""
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            # Re-apply AI config after settings change
            self._apply_ai_config()
            # Update autosave timer
            if self.config.get("autosave_enabled"):
                interval_ms = self.config.get("autosave_interval_minutes", 5) * 60 * 1000
                self._autosave_timer.start(interval_ms)
            else:
                self._autosave_timer.stop()

    def _show_shortcut_settings(self):
        """Open the keyboard shortcut settings dialog."""
        dlg = ShortcutSettingsDialog(self.config, self)
        dlg.exec()

    def _get_api_key_for_model(self, model_key: str) -> str:
        """根据模型 key 返回对应的 API Key。"""
        if model_key in ("claude", "gemini"):
            return self.config.get("ai_api_key_claude_gemini", "")
        return self.config.get("custom_ai_api_key", "")

    def _apply_ai_config(self):
        """Apply custom AI model/URL/key from user config at runtime."""
        from app.core.ai_service import configure_ai

        model_key = self._current_model_key
        api_key = self._get_api_key_for_model(model_key)
        configure_ai(
            api_url=self.config.get("custom_ai_api_url", ""),
            model=self.config.get("custom_ai_model", ""),
            api_key=api_key,
        )

    # Track current model key for the switch dialog
    _current_model_key = "gpt"

    def _restore_model_appearance(self):
        """On startup, derive model key from saved config and update button appearance."""
        saved = (self.config.get("custom_ai_model", "") or "").lower()
        if not saved:
            return
        if "claude" in saved:
            self._current_model_key = "claude"
        elif "gemini" in saved:
            self._current_model_key = "gemini"
        else:
            self._current_model_key = "gpt"
        self._update_ai_button_appearance(self._current_model_key)

    def _show_model_switch(self):
        """Open the model switch dialog."""
        dlg = ModelSwitchDialog(self._current_model_key, self)
        dlg.model_selected.connect(self._on_model_switched)
        dlg.exec()

    def _show_skills_dialog(self):
        """打开 Skills 集群记忆对话框"""
        dlg = SkillsDialog(self)
        dlg.exec()

    def _on_model_switched(self, model_key: str, model_id: str):
        """Handle model selection from the switch dialog."""
        self._current_model_key = model_key
        from app.core.ai_service import configure_ai

        api_key = self._get_api_key_for_model(model_key)
        # Always pass api_key (even "") so configure_ai can clear the
        # env-var when switching to a model without an explicit key,
        # allowing the config.ini fallback to work correctly.
        configure_ai(
            model=model_id,
            api_key=api_key if api_key else "",
        )
        # Persist to config
        self.config.set("custom_ai_model", model_id)
        self.config.save()
        self._update_ai_button_appearance(model_key)
        self.status_bar.showMessage(f"已切换模型: {model_id}", 4000)

    def _update_ai_button_appearance(self, model_key: str):
        """Update the toolbar AI button icon, text, and color for the active model."""
        brand = self._MODEL_BRANDS.get(model_key, self._MODEL_BRANDS["gpt"])
        self.toolbar.update_ai_button(
            name=brand["name"],
            color=brand["color"],
            hover=brand["hover"],
            pressed=brand["pressed"],
            icon=brand["icon_func"](self.toolbar.ICON_SIZE, "#FFFFFF"),
        )

    def _check_auto_recovery(self):
        """On startup, check for auto-saved backup and offer to recover."""
        backup_dir = os.path.join(os.path.expanduser("~"), ".wenbiao", "autosave")
        backup_path = os.path.join(backup_dir, "autosave.md")
        if not os.path.isfile(backup_path):
            return
        try:
            mtime = os.path.getmtime(backup_path)
            import datetime

            dt = datetime.datetime.fromtimestamp(mtime)
            age = datetime.datetime.now() - dt
            # Only offer recovery if backup is less than 24 hours old
            if age.total_seconds() > 86400:
                return
            with open(backup_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                return
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            reply = QMessageBox.question(
                self,
                "自动恢复",
                f"发现未保存的自动备份（{time_str}），是否恢复？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._current_markdown = content
                self.preview.set_content_from_markdown(content)
                self._update_title()
                self.status_bar.showMessage("已恢复自动备份内容", 5000)
                # Rotate backup
                self._rotate_backup(backup_path)
            else:
                # User declined — rotate old backup so it won't prompt again
                self._rotate_backup(backup_path)
        except Exception as e:
            logger.warning("自动恢复检查失败: %s", e)

    def _rotate_backup(self, backup_path: str):
        """Rotate autosave backup files, keeping up to max_backup_versions."""
        try:
            max_versions = self.config.get("max_backup_versions", 5)
            backup_dir = os.path.dirname(backup_path)
            base = os.path.basename(backup_path)
            name, ext = os.path.splitext(base)
            # Shift existing backups
            for i in range(max_versions - 1, 0, -1):
                src = os.path.join(backup_dir, f"{name}.{i}{ext}")
                dst = os.path.join(backup_dir, f"{name}.{i + 1}{ext}")
                if os.path.isfile(src):
                    if i + 1 >= max_versions:
                        os.remove(src)
                    else:
                        os.replace(src, dst)
            # Move current backup to .1
            if os.path.isfile(backup_path):
                dst = os.path.join(backup_dir, f"{name}.1{ext}")
                os.replace(backup_path, dst)
        except Exception as e:
            logger.warning("备份轮转失败: %s", e)

    # ------------------------------------------------------------------
    # AI assistant
    # ------------------------------------------------------------------

    # Brand info for each AI model
    _MODEL_BRANDS = {
        "gpt": {
            "name": "GPT",
            "color": "#10A37F",
            "hover": "#0D8C6D",
            "pressed": "#0A7A5E",
            "icon_func": lambda s, c: icon_chatgpt(s, c),
        },
        "claude": {
            "name": "Claude",
            "color": "#D97757",
            "hover": "#C06545",
            "pressed": "#A85535",
            "icon_func": lambda s, c: icon_claude(s, c),
        },
        "gemini": {
            "name": "Gemini",
            "color": "#4285F4",
            "hover": "#3574D4",
            "pressed": "#2A63B4",
            "icon_func": lambda s, c: icon_gemini(s, c),
        },
    }

    def _cancel_ai_worker(self):
        """Cancel any running AI worker and wait for it to stop."""
        if hasattr(self, "_ai_worker") and self._ai_worker and self._ai_worker.isRunning():
            self._ai_worker.cancel()
            self._ai_worker.wait(2000)

    def _ai_optimize(self):
        """AI 降重优化选中内容 — 基于全文上下文，结果用 Track Changes 展示。"""

        def _on_ctx(ctx_json):
            try:
                ctx = json.loads(ctx_json) if ctx_json else {}
            except Exception:
                ctx = {}
            selected = ctx.get("selectedText", "")
            if not selected.strip():
                QMessageBox.information(
                    self, "AI 提示", "请先选中需要降重优化的文本，然后再点击「GPT 降重优化」"
                )
                return
            # Convert selected HTML to Markdown so it matches _current_markdown.
            # sel.toString() returns plain text (no formatting markers), which
            # won't match the Markdown source that contains **bold**, ## etc.
            selected_html = ctx.get("selectedHTML", "")
            if selected_html:
                selected_md = html_to_markdown(selected_html).strip()
            else:
                selected_md = selected
            full_doc = self._current_markdown
            # Verify the Markdown selection can be found in the full document
            if selected_md not in full_doc:
                # Fallback: try plain text match
                selected_md = selected
            self._optimize_selected_text = selected_md
            self.status_bar.showMessage("🔄 AI 正在基于全文上下文降重并优化选中内容...")
            msgs = build_optimize_selected_messages(full_doc, selected)
            self._run_ai_optimize_selected(msgs)

        self.preview.get_ai_context(_on_ctx)

    def _run_ai_optimize_selected(self, messages: list):
        """Run AI to optimize selected text, then show track changes."""
        self._cancel_ai_worker()

        worker = AiWorker(messages, max_tokens=MAX_TOKENS_OPTIMIZE, temperature=TEMP_OPTIMIZE)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        def _on_finished(response):
            optimized = response.strip()
            # Strip markdown code fence wrapper if AI added one
            if optimized.startswith("```"):
                lines = optimized.split("\n")
                optimized = "\n".join(lines[1:])
                if optimized.endswith("```"):
                    optimized = optimized[:-3].strip()
            original_selected = self._optimize_selected_text
            full_doc = self._current_markdown
            # Replace the selected text in the full document
            modified_doc = full_doc.replace(original_selected, optimized, 1)
            # Use existing track changes mechanism to show the diff
            self._apply_ai_smart_result(modified_doc)

        worker.finished_ok.connect(_on_finished)
        worker.error_occurred.connect(
            lambda err: self.status_bar.showMessage(f"❌ AI 错误：{err}", 8000)
        )
        worker.start()

    @staticmethod
    def _find_sections_needing_content(
        markdown: str,
        min_content_chars: int = 100,
    ) -> list:
        """分析文档，找出需要续写内容的章节（标题下内容不足 min_content_chars 字）。

        Returns list of dicts:
            heading: str          # 完整标题行，如 '## 1.2 研究背景'
            heading_text: str     # 去掉 # 后的文本
            level: int
            heading_line: int     # 行号
            content: str          # 该章节下的内容文本
        """
        lines = markdown.split("\n")
        sections = []
        current_heading = None
        current_heading_line = -1
        current_content_lines = []

        for i, line in enumerate(lines):
            m = re.match(r"^(#{1,6})\s+(.+)$", line)
            if m:
                # Save previous section
                if current_heading is not None:
                    content_text = "\n".join(current_content_lines).strip()
                    level = len(re.match(r"^(#+)", current_heading).group(1))
                    sections.append(
                        {
                            "heading": current_heading,
                            "heading_text": current_heading.lstrip("#").strip(),
                            "level": level,
                            "heading_line": current_heading_line,
                            "content": content_text,
                        }
                    )
                current_heading = line
                current_heading_line = i
                current_content_lines = []
            elif current_heading is not None:
                current_content_lines.append(line)

        # Last section
        if current_heading is not None:
            content_text = "\n".join(current_content_lines).strip()
            level = len(re.match(r"^(#+)", current_heading).group(1))
            sections.append(
                {
                    "heading": current_heading,
                    "heading_text": current_heading.lstrip("#").strip(),
                    "level": level,
                    "heading_line": current_heading_line,
                    "content": content_text,
                }
            )

        # Filter sections that need content
        needs_content = []
        for sec in sections:
            stripped = sec["content"].strip()
            if len(stripped) < min_content_chars:
                needs_content.append(sec)

        return needs_content

    def _ai_continue(self):
        """智能AI续写：先分析文档找出需要续写的章节，多个则逐段续写，否则光标处续写。"""
        text = self._current_markdown
        sections = self._find_sections_needing_content(text)

        if len(sections) >= 2:
            # 多个章节需要内容 → 自动多段续写模式
            self._ai_continue_multi(sections)
        else:
            # 0 或1 个章节需要内容 → 按原逻辑在光标处续写
            self._ai_continue_at_cursor()

    def _ai_continue_at_cursor(self):
        """原有的光标处续写逻辑。"""

        def _on_ctx(ctx_json):
            try:
                ctx = json.loads(ctx_json) if ctx_json else {}
            except Exception:
                ctx = {}
            text_before = ctx.get("textBefore", "") or self._current_markdown
            text_after = ctx.get("textAfter", "")
            ai_id = f"ai_{int(time.time() * 1000)}"
            self.preview.ai_start_block(ai_id, "continue")
            msgs = build_continue_messages(text_before, after_context=text_after)
            self._run_ai_inline(ai_id, msgs, temperature=TEMP_CONTINUE)

        self.preview.get_ai_context(_on_ctx)

    def _ai_continue_multi(self, sections: list):
        """多章节智能续写：自动到每个需要内容的章节位置逐段生成内容。"""
        if self._multi_continue_running:
            self._cancel_ai_worker()
            self._multi_continue_running = False

        self._multi_continue_running = True
        self._multi_continue_sections = sections
        self._multi_continue_index = 0

        names = "、".join(s["heading_text"][:15] for s in sections[:5])
        if len(sections) > 5:
            names += "..."
        self.status_bar.showMessage(
            f"✨ 发现 {len(sections)} 个章节需要续写（{names}），开始逐段生成..."
        )
        self._run_next_multi_continue()

    def _run_next_multi_continue(self):
        """处理下一个需要续写的章节。"""
        if not self._multi_continue_running:
            return

        idx = self._multi_continue_index
        total = len(self._multi_continue_sections)

        if idx >= total:
            # 全部完成
            self._multi_continue_running = False
            self.status_bar.showMessage(
                f"✅ 全部 {total} 个章节续写完成，请逐个查看并决定是否采纳", 8000
            )
            return

        section = self._multi_continue_sections[idx]
        heading_text = section["heading_text"]

        self.status_bar.showMessage(
            f"✨ 正在续写第 {idx + 1}/{total} 个章节：{heading_text[:20]}..."
        )

        # Build context from current markdown
        md = self._current_markdown
        lines = md.split("\n")
        heading_line = section["heading_line"]

        # Text before: everything up to and including this heading
        text_before = "\n".join(lines[: heading_line + 1])

        # Text after: find next heading and take content from there
        text_after = ""
        for i in range(heading_line + 1, len(lines)):
            if re.match(r"^#{1,6}\s+", lines[i]):
                text_after = "\n".join(lines[i : i + 20])
                break

        ai_id = f"ai_{int(time.time() * 1000)}_{idx}"

        # Insert AI block at the heading position
        self.preview.ai_start_block_at_heading(ai_id, "continue", heading_text)

        # Build messages
        msgs = build_section_continue_messages(
            heading=section["heading"],
            text_before=text_before,
            text_after=text_after,
        )

        # Run AI inline with chaining callback
        self._run_ai_inline_multi(ai_id, msgs, idx)

    def _run_ai_inline_multi(self, ai_id: str, messages: list, section_index: int):
        """运行 AI 并将结果流式输出到 inline block，完成后自动处理下一个章节。"""
        self._cancel_ai_worker()

        worker = AiWorker(messages, temperature=TEMP_CONTINUE)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        worker.chunk_received.connect(
            lambda text, _id=ai_id: self.preview.ai_append_chunk(_id, text)
        )
        worker.reasoning_received.connect(
            lambda text, _id=ai_id: self.preview.ai_update_thinking(_id, text)
        )

        def _on_finished(full_text, _id=ai_id, _idx=section_index):
            # Render final content
            rendered = self.renderer.render(full_text)
            self.preview.ai_render_block(_id, rendered)
            self.preview.ai_finish_block(_id)

            # Chain to next section
            self._multi_continue_index = _idx + 1
            # Small delay for UI to update before starting next
            QTimer.singleShot(500, self._run_next_multi_continue)

        def _on_error(err, _id=ai_id, _idx=section_index):
            self.preview.ai_error_block(_id, err)
            logger.warning("多章节续写第 %d 段失败: %s", _idx + 1, err)
            # Continue to next section even on error
            self._multi_continue_index = _idx + 1
            QTimer.singleShot(500, self._run_next_multi_continue)

        worker.finished_ok.connect(_on_finished)
        worker.error_occurred.connect(_on_error)
        worker.start()

    @staticmethod
    def _split_markdown_sections(text: str, max_section_chars: int = 9000) -> list:
        """按标题分段，并限制单段长度，适合大文档批处理。"""
        if not text.strip():
            return []

        lines = text.split("\n")
        sections = []
        start = 0

        def _is_heading(line: str) -> bool:
            return bool(re.match(r"^\s{0,3}#{1,3}\s+\S", line))

        for i in range(1, len(lines)):
            if _is_heading(lines[i]):
                chunk = "\n".join(lines[start:i]).strip()
                if chunk:
                    sections.append(chunk)
                start = i
        last = "\n".join(lines[start:]).strip()
        if last:
            sections.append(last)

        if not sections:
            sections = [text]

        # 再按长度细分
        refined = []
        for sec in sections:
            if len(sec) <= max_section_chars:
                refined.append(sec)
                continue
            paras = re.split(r"(\n{2,})", sec)
            cur = ""
            for part in paras:
                if len(cur) + len(part) > max_section_chars and cur.strip():
                    refined.append(cur.strip())
                    cur = part
                else:
                    cur += part
            if cur.strip():
                refined.append(cur.strip())
        return refined

    def _ai_batch_optimize_document(self):
        """超长文档章节批处理：逐段调用 AI，最后合并并展示修订。"""
        self._start_ai_batch_processing(
            mode="optimize_low_dup",
            instruction="",
            title="章节批处理确认",
            description="将逐段优化并合并回全文（更省 token，适合超长文档）。",
        )

    def _start_ai_batch_processing(self, mode: str, instruction: str, title: str, description: str):
        """启动章节批处理（统一入口）。"""
        if self._ai_batch_running:
            reply = QMessageBox.question(
                self,
                "批处理进行中",
                "当前批处理仍在执行，是否取消？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._ai_batch_cancelled = True
                self._cancel_ai_worker()
                self.status_bar.showMessage("批处理已取消", 5000)
            return

        text = self._current_markdown
        if not text.strip():
            QMessageBox.information(self, "AI 提示", "文档内容为空，请先写一些内容。")
            return

        sections = self._split_markdown_sections(text)
        if not sections:
            QMessageBox.information(self, "AI 提示", "未识别到可处理的章节内容。")
            return

        reply = QMessageBox.question(
            self,
            title,
            f"检测到 {len(sections)} 个章节片段。\n" f"{description}\n\n" "是否开始？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._ai_batch_running = True
        self._ai_batch_cancelled = False
        self._ai_batch_sections = sections
        self._ai_batch_results = []
        self._ai_batch_index = 0
        self._ai_batch_mode = mode
        self._ai_batch_instruction = instruction or ""
        self.status_bar.showMessage(f"📚 章节批处理中：0/{len(self._ai_batch_sections)}", 3000)
        self._run_next_batch_section()

    def _run_next_batch_section(self):
        if self._ai_batch_cancelled:
            self._finish_batch_processing(cancelled=True)
            return

        idx = self._ai_batch_index
        total = len(self._ai_batch_sections)
        if idx >= total:
            self._finish_batch_processing(cancelled=False)
            return

        section = self._ai_batch_sections[idx]
        # 短片段不改，降低无效 token
        if len(section.strip()) < 120:
            self._ai_batch_results.append(section)
            self._ai_batch_index += 1
            self._run_next_batch_section()
            return

        self.status_bar.showMessage(f"📚 章节批处理中：{idx + 1}/{total}（第 {idx + 1} 段）")
        if self._ai_batch_mode == "custom":
            focused_instruction = (
                f"{self._ai_batch_instruction}\n\n"
                "【重要】只修改我提供的这一个章节片段并返回修改后的完整片段；"
                "不要解释，不要省略。"
            )
            msgs = build_custom_edit_messages(section, focused_instruction)
        elif self._ai_batch_mode == "optimize":
            msgs = build_optimize_messages(section, low_dup=False)
        else:
            msgs = build_optimize_messages(section, low_dup=True)

        self._cancel_ai_worker()
        _batch_max = MAX_TOKENS_EDIT if self._ai_batch_mode == "custom" else MAX_TOKENS_OPTIMIZE

        _batch_temp = TEMP_EDIT if self._ai_batch_mode == "custom" else TEMP_OPTIMIZE
        worker = AiWorker(msgs, max_tokens=_batch_max, temperature=_batch_temp)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        def _on_done(response):
            rewritten = (response or "").strip()
            if rewritten.startswith("```"):
                lines = rewritten.split("\n")
                rewritten = "\n".join(lines[1:])
                if rewritten.endswith("```"):
                    rewritten = rewritten[:-3].strip()
            self._ai_batch_results.append(rewritten if rewritten else section)
            self._ai_batch_index += 1
            self._run_next_batch_section()

        def _on_err(err):
            logger.warning("章节批处理第 %d 段失败: %s", idx + 1, err)
            self._ai_batch_results.append(section)
            self._ai_batch_index += 1
            self._run_next_batch_section()

        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(_on_err)
        worker.start()

    def _finish_batch_processing(self, cancelled: bool):
        total = len(self._ai_batch_sections)
        done = len(self._ai_batch_results)
        self._ai_batch_running = False

        if cancelled:
            self.status_bar.showMessage(f"批处理已取消：完成 {done}/{total}", 6000)
            return

        merged = "\n\n".join(self._ai_batch_results).strip()
        if not merged:
            self.status_bar.showMessage("批处理未产出有效结果", 6000)
            return

        self._apply_ai_smart_result(merged)
        self.status_bar.showMessage(f"✅ 章节批处理完成：{done}/{total}", 8000)

    def _ai_batch_custom_document(self, instruction: str):
        """全文自定义指令统一走章节批处理。"""
        self._start_ai_batch_processing(
            mode="custom",
            instruction=instruction,
            title="全文自定义批处理确认",
            description="将按章节逐段执行该自定义指令并合并回全文（更省 token）。",
        )

    # ------------------------------------------------------------------
    # Streaming section-by-section diff (Ctrl+I modify)
    # ------------------------------------------------------------------

    def _ai_streaming_section_modify(self, instruction: str):
        """Ctrl+I 修改类指令：逐章节流式 Diff 展示（红删绿增）。"""
        # Cancel if already running
        if self._tc_stream_running:
            self._cancel_ai_worker()
            self._tc_stream_running = False

        text = self._current_markdown
        if not text.strip():
            QMessageBox.information(self, "AI 提示", "文档内容为空，请先写一些内容。")
            return

        sections = self._split_markdown_sections(text)
        if not sections:
            QMessageBox.information(self, "AI 提示", "未识别到可处理的章节内容。")
            return

        # Detect targeted sections from instruction
        target_indices = self._find_target_section_indices(instruction, sections)
        self._tc_stream_target_indices = target_indices  # empty = all

        # Store state
        self._tc_original_md = text
        self._tc_stream_sections = sections
        self._tc_stream_results = [None] * len(sections)
        self._tc_stream_index = 0
        self._tc_stream_instruction = instruction
        self._tc_stream_running = True
        self._in_track_changes = True

        # Show initial state
        self._render_streaming_diff()
        self.preview.show_track_changes_bar(0, 0)
        if target_indices:
            names = ", ".join(f"第{i+1}节" for i in target_indices)
            self.status_bar.showMessage(f"🔄 定向处理 {names}（共 {len(sections)} 个章节）...")
        else:
            self.status_bar.showMessage(f"🔄 开始逐章节处理（共 {len(sections)} 个章节）...")

        # Start processing first section
        self._run_next_stream_section()

    def _run_next_stream_section(self):
        """处理下一个章节。"""
        if not self._tc_stream_running:
            return

        idx = self._tc_stream_index
        total = len(self._tc_stream_sections)

        if idx >= total:
            self._finish_streaming_sections()
            return

        section = self._tc_stream_sections[idx]
        targets = self._tc_stream_target_indices

        # Skip non-target sections (when specific targets detected)
        if targets and idx not in targets:
            self._tc_stream_results[idx] = section
            self._tc_stream_index += 1
            self._render_streaming_diff()
            QTimer.singleShot(20, self._run_next_stream_section)
            return

        # Short sections: skip (keep unchanged) — unless explicitly targeted
        if not targets and len(section.strip()) < 120:
            self._tc_stream_results[idx] = section
            self._tc_stream_index += 1
            self._render_streaming_diff()
            QTimer.singleShot(50, self._run_next_stream_section)
            return

        self.status_bar.showMessage(f"🔄 正在处理第 {idx + 1}/{total} 个章节...")
        # Re-render to show "processing" indicator for this section
        self._render_streaming_diff()

        # Cancel previous worker if any
        self._cancel_ai_worker()

        msgs = build_section_edit_messages(section, self._tc_stream_instruction, idx, total)
        worker = AiWorker(msgs, max_tokens=MAX_TOKENS_SECTION, temperature=TEMP_SECTION_EDIT)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        def _on_done(response, _idx=idx, _section=section):
            if not self._tc_stream_running:
                return
            result = (response or "").strip()
            # Strip markdown code fence wrapper
            if result.startswith("```"):
                lines = result.split("\n")
                result = "\n".join(lines[1:])
                if result.endswith("```"):
                    result = result[:-3].strip()
            self._tc_stream_results[_idx] = result if result else _section
            self._tc_stream_index = _idx + 1
            # Immediately render this section's diff
            self._render_streaming_diff(scroll_to_section=_idx)
            # Process next section
            QTimer.singleShot(100, self._run_next_stream_section)

        def _on_err(err, _idx=idx, _section=section):
            if not self._tc_stream_running:
                return
            logger.warning("流式章节处理第 %d 段失败: %s", _idx + 1, err)
            self._tc_stream_results[_idx] = _section  # keep original on error
            self._tc_stream_index = _idx + 1
            self._render_streaming_diff(scroll_to_section=_idx)
            QTimer.singleShot(100, self._run_next_stream_section)

        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(_on_err)
        worker.start()

    def _render_streaming_diff(self, scroll_to_section: int = -1):
        """Build and display the progressive section diff.

        For completed sections: show word-level diff (red del / green ins).
        For the current section: show processing animation.
        For pending sections: show dimmed original text.
        """
        parts: list[str] = []
        del_count = 0
        ins_count = 0
        total = len(self._tc_stream_sections)

        for i, section in enumerate(self._tc_stream_sections):
            # Extract section heading for label
            first_line = section.split("\n", 1)[0].strip()
            heading_label = first_line if first_line.startswith("#") else f"片段 {i + 1}"

            if self._tc_stream_results[i] is not None:
                # Completed section
                original = section
                modified = self._tc_stream_results[i]
                if original.strip() != modified.strip():
                    diff_md = self._build_tracked_changes_md(original, modified)
                    sec_del = diff_md.count('<del class="ai-del">')
                    sec_ins = diff_md.count('<ins class="ai-ins">')
                    del_count += sec_del
                    ins_count += sec_ins
                    label = f"✓ {sec_del} 处删除，{sec_ins} 处新增"
                    parts.append(
                        f'<div class="tc-section-done" id="tc-sec-{i}">'
                        f"第 {i+1}/{total} 节 — {label}</div>\n\n" + diff_md
                    )
                else:
                    parts.append(
                        f'<div class="tc-section-unchanged" id="tc-sec-{i}">'
                        f"第 {i+1}/{total} 节 — 无变更</div>\n\n" + section
                    )
            elif i == self._tc_stream_index:
                # Currently processing
                parts.append(
                    f'<div class="tc-section-processing" id="tc-sec-{i}">'
                    f"⏳ 正在处理第 {i+1}/{total} 节...</div>\n\n" + section
                )
            else:
                # Pending
                parts.append(
                    f'<div class="tc-section-pending" id="tc-sec-{i}">'
                    f"⌛ 第 {i+1}/{total} 节 — 等待处理</div>\n\n" + section
                )

        annotated_md = "\n\n".join(parts)
        tracked_html = self.renderer.render(annotated_md)
        escaped = tracked_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        self.preview._safe_run_js(f"_savedRange = null; setEditorContent(`{escaped}`);")
        # Make editor read-only
        self.preview._safe_run_js("if(editorEl) editorEl.setAttribute('contenteditable','false');")

        # Update track changes bar stats
        self.preview.show_track_changes_bar(del_count, ins_count)

        # Scroll to the just-completed section
        if scroll_to_section >= 0:
            self.preview._safe_run_js(
                f"setTimeout(function(){{ "
                f"var el=document.getElementById('tc-sec-{scroll_to_section}'); "
                f"if(el) el.scrollIntoView({{behavior:'smooth',block:'center'}}); "
                f"}}, 100);"
            )

    def _finish_streaming_sections(self):
        """All sections processed — build final modified document."""
        self._tc_stream_running = False

        # Join all results to form the modified document
        modified_parts = []
        for i, section in enumerate(self._tc_stream_sections):
            result = self._tc_stream_results[i]
            modified_parts.append(result if result is not None else section)
        self._tc_modified_md = "\n\n".join(modified_parts).strip()

        self.status_bar.showMessage("✅ 所有章节处理完成，请查看修订内容并决定是否采纳", 8000)

    def _ai_custom(self):
        """AI 自定义指令 — 仍用对话框模式。"""

        def _on_selection(text):
            text = text or ""
            dlg = AiDialog(self)
            dlg.accepted_result.connect(self._on_ai_custom_result)
            dlg.show()
            dlg.start_custom(text if text.strip() else self._current_markdown)

        self.preview.exec_js(
            "(function(){ var s = window.getSelection(); return s.toString(); })();", _on_selection
        )

    def _show_ai_input_bar(self):
        """Ctrl+I — 在光标下方显示轻量输入条。"""

        def _on_pos(pos_json):
            try:
                pos = json.loads(pos_json) if pos_json else {}
            except Exception:
                pos = {}
            # JS 返回的是相对于 WebView viewport 的坐标，需要转为屏幕坐标
            js_x = int(pos.get("x", 0))
            js_y = int(pos.get("y", 0))
            view = self.preview._view
            screen_pos = view.mapToGlobal(view.rect().topLeft())
            screen_x = screen_pos.x() + js_x
            screen_y = screen_pos.y() + js_y
            self._ai_input_bar.position_at_cursor(screen_x, screen_y, self.preview)
            self._ai_input_bar.show_and_focus()

        self.preview.get_cursor_screen_pos(_on_pos)

    # 插入/续写类关键词 — 表示用户想在光标处生成新内容
    _INSERT_KEYWORDS = (
        "续写",
        "继续写",
        "继续",
        "接着写",
        "往下写",
        "补充",
        "补写",
        "添加",
        "插入",
        "新增",
        "增加",
        "写一段",
        "写一下",
        "帮我写",
        "帮写",
        "生成",
        "撰写",
        "扩展",
        "扩写",
        "丰富",
        "起草",
        "拟",
        "写个",
        "写出",
        "给我写",
        "开始写",
        "写关于",
        "展开",
        "详细写",
        "详写",
        "多写",
        "加一段",
    )

    # 修改/编辑类关键词 — 表示用户想修改现有内容
    _MODIFY_KEYWORDS = (
        "修改",
        "改写",
        "改一下",
        "改下",
        "改改",
        "修订",
        "修正",
        "纠正",
        "优化",
        "改进",
        "改善",
        "润色",
        "精简",
        "缩写",
        "重写",
        "改成",
        "换成",
        "替换",
        "删除",
        "删掉",
        "去掉",
        "移除",
        "调整",
        "更改",
        "变更",
        "校正",
        "修复",
        "改动",
        "编辑",
        "降重",
        "减少重复",
        "压缩",
        "精炼",
        "提炼",
        "简化",
        "美化",
        "改论文",
        "修改论文",
        "改文章",
        "修改文章",
        "语法",
        "错别字",
        "纠错",
        "校对",
    )

    @staticmethod
    def _is_insert_instruction(instruction: str) -> bool:
        """判断指令是否表示需要在光标位置插入/续写/补充新内容。"""
        for kw in MainWindow._INSERT_KEYWORDS:
            if kw in instruction:
                return True
        return False

    @staticmethod
    def _is_modify_instruction(instruction: str) -> bool:
        """判断指令是否明确表示修改/编辑现有内容（优先级高于插入）。"""
        for kw in MainWindow._MODIFY_KEYWORDS:
            if kw in instruction:
                return True
        return False

    @staticmethod
    def _has_location_reference(instruction: str) -> bool:
        """判断指令是否包含对特定章节/位置的引用。"""
        import re

        # 第X章, 第X节
        if re.search(r"第[一二三四五六七八九十百\d]+[章节]", instruction):
            return True
        # 学术论文常见章节名
        for kw in (
            "引言",
            "摘要",
            "结论",
            "绪论",
            "参考文献",
            "致谢",
            "附录",
            "目录",
            "前言",
            "导论",
        ):
            if kw in instruction:
                return True
        return False

    def _find_target_section_indices(self, instruction: str, sections: list) -> list:
        """根据指令中的位置引用，找到目标章节索引。空列表=全部处理。"""
        import re

        targets = set()

        # 提取章/节编号引用
        ch_matches = re.findall(r"第([一二三四五六七八九十百\d]+)[章节]", instruction)
        # 提取命名章节引用
        named_kws = [
            kw
            for kw in (
                "引言",
                "摘要",
                "结论",
                "绪论",
                "参考文献",
                "致谢",
                "附录",
                "目录",
                "前言",
                "导论",
            )
            if kw in instruction
        ]

        if not ch_matches and not named_kws:
            return []  # 无位置引用 → 处理全部

        for i, section in enumerate(sections):
            first_line = section.split("\n", 1)[0].strip()
            for ch in ch_matches:
                if f"第{ch}章" in first_line or f"第{ch}节" in first_line:
                    targets.add(i)
            for kw in named_kws:
                if kw in first_line:
                    targets.add(i)

        return sorted(targets)

    def _ai_inline_custom(self, instruction: str):
        """用户在输入条提交指令后，智能判断是修改现有内容还是插入新内容。"""

        def _on_ctx(ctx_json):
            try:
                ctx = json.loads(ctx_json) if ctx_json else {}
            except Exception:
                ctx = {}
            selected = ctx.get("selectedText", "")

            if selected.strip():
                # ① 有选中文本 → 只修改选中部分（保持原有逻辑）
                ai_id = f"ai_{int(time.time() * 1000)}"
                self.preview.ai_start_block(ai_id, "optimize")
                msgs = build_custom_edit_messages(selected, instruction)
                self._run_ai_inline(ai_id, msgs, temperature=TEMP_EDIT)
            else:
                text_before = ctx.get("textBefore", "")
                text_after = ctx.get("textAfter", "")
                full_doc = self._current_markdown
                is_large_doc = len(full_doc) >= self._LARGE_DOC_SMART_THRESHOLD

                if not full_doc.strip():
                    # ② 文档为空 → 用 inline block 直接生成
                    ai_id = f"ai_{int(time.time() * 1000)}"
                    self.preview.ai_start_block(ai_id, "continue")
                    msgs = build_custom_insert_messages(instruction, text_before, text_after)
                    self._run_ai_inline(ai_id, msgs, temperature=TEMP_INSERT)
                elif self._is_modify_instruction(instruction):
                    # ③ 明确修改类 → 流式章节 Diff
                    self._ai_streaming_section_modify(instruction)
                elif self._is_insert_instruction(instruction):
                    if self._has_location_reference(instruction):
                        # ④a 插入+指定章节 → 流式 Diff 定向处理
                        self._ai_streaming_section_modify(instruction)
                    else:
                        # ④b 插入+无位置 → inline block 光标处生成
                        ai_id = f"ai_{int(time.time() * 1000)}"
                        self.preview.ai_start_block(ai_id, "continue")
                        msgs = build_custom_insert_messages(instruction, text_before, text_after)
                        self._run_ai_inline(ai_id, msgs, temperature=TEMP_INSERT)
                else:
                    # ⑤ 无法明确分类 → 默认走修改
                    self._ai_streaming_section_modify(instruction)

        self.preview.get_ai_context(_on_ctx)

    @staticmethod
    def _build_focus_segment(text_before: str, text_after: str) -> str:
        """构造光标附近局部片段，用于大文档省 token 修改。"""
        before_tail = (text_before or "")[-5000:]
        after_head = (text_after or "")[:5000]
        return before_tail + after_head

    def _run_ai_focus_modify(
        self, full_doc: str, text_before: str, text_after: str, instruction: str
    ):
        """大文档修改类指令：仅对光标附近片段进行 AI 修订，再合并回全文。"""
        segment = self._build_focus_segment(text_before, text_after)
        if not segment.strip():
            self.status_bar.showMessage("⚠ 光标附近没有可修改内容，请先选中段落再执行修改。", 6000)
            return

        self._cancel_ai_worker()

        self.status_bar.showMessage("📦 大文档模式：正在修改光标附近片段（省 token）...")
        focused_instruction = (
            f"{instruction}\n\n"
            "【重要】只修改我提供的片段并返回修改后的完整片段；"
            "不要解释，不要省略。"
        )
        msgs = build_custom_edit_messages(segment, focused_instruction)

        worker = AiWorker(msgs, temperature=TEMP_EDIT)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))
        worker.finished_ok.connect(
            lambda resp, _doc=full_doc, _seg=segment: self._apply_ai_focus_modify_result(
                _doc, _seg, resp
            )
        )
        worker.error_occurred.connect(
            lambda err: self.status_bar.showMessage(f"❌ AI 错误：{err}", 8000)
        )
        worker.start()

    def _apply_ai_focus_modify_result(self, full_doc: str, segment: str, response: str):
        """将大文档局部修订结果合并回全文，并展示 Track Changes。"""
        modified_segment = (response or "").strip()
        if modified_segment.startswith("```"):
            lines = modified_segment.split("\n")
            modified_segment = "\n".join(lines[1:])
            if modified_segment.endswith("```"):
                modified_segment = modified_segment[:-3].strip()

        if not modified_segment:
            self.status_bar.showMessage("⚠ AI 未返回有效修改结果", 6000)
            return

        if segment not in full_doc:
            self.status_bar.showMessage("⚠ 无法精确定位原片段，请改为选中具体段落后再修改。", 7000)
            return

        merged = full_doc.replace(segment, modified_segment, 1)
        self._finish_smart_result(merged)

    def _run_ai_inline(
        self,
        ai_id: str,
        messages: list,
        enforce_high_quality: bool = False,
        quality_task_hint: str = "",
        temperature: float = TEMP_DEFAULT,
    ):
        """Run AI worker and stream results into an inline block."""
        self._cancel_ai_worker()

        worker = AiWorker(messages, temperature=temperature)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        worker.chunk_received.connect(
            lambda text, _id=ai_id: self.preview.ai_append_chunk(_id, text)
        )
        worker.reasoning_received.connect(
            lambda text, _id=ai_id: self.preview.ai_update_thinking(_id, text)
        )

        def _render_inline_result(final_text: str, _id=ai_id):
            # 检查是否包含图片占位符，如有则后台搜图后再渲染
            if has_image_placeholders(final_text):
                self.status_bar.showMessage("🖼️ 正在搜索并插入图片/图表...")
                pixabay_key = self.config.get("pixabay_api_key", "")
                img_worker = ImageProcessWorker(final_text, pixabay_key=pixabay_key)
                self._img_worker = img_worker

                def _on_images_done(processed_md, _id2=_id):
                    rendered = self.renderer.render(processed_md)
                    self.preview.ai_render_block(_id2, rendered)
                    self.preview.ai_finish_block(_id2)
                    self.status_bar.showMessage("✓ 图片插入完成", 3000)

                def _on_images_error(err, _id2=_id):
                    # 图片失败时仍然渲染原始文本
                    rendered = self.renderer.render(final_text)
                    self.preview.ai_render_block(_id2, rendered)
                    self.preview.ai_finish_block(_id2)
                    self.status_bar.showMessage(f"⚠ 图片搜索失败，已使用原始内容: {err}", 5000)

                img_worker.finished.connect(_on_images_done)
                img_worker.error.connect(_on_images_error)
                img_worker.start()
            else:
                # 无图片占位符，直接渲染
                rendered = self.renderer.render(final_text)
                self.preview.ai_render_block(_id, rendered)
                self.preview.ai_finish_block(_id)

        def _on_ai_finished(full_text, _id=ai_id):
            if not enforce_high_quality:
                _render_inline_result(full_text, _id)
                return

            # 第二轮：强制学术提质
            self.status_bar.showMessage("🧠 正在进行高质量学术提质...")
            self.preview.ai_update_block_status(_id, "🧠 正在提质...")
            polish_msgs = build_high_quality_rewrite_messages(
                full_text, task_hint=quality_task_hint
            )
            polish_worker = AiWorker(
                polish_msgs, max_tokens=MAX_TOKENS_REWRITE, temperature=TEMP_REWRITE
            )
            self._ai_polish_worker = polish_worker

            def _on_polish_done(polished_text):
                final_text = (polished_text or "").strip() or full_text
                _render_inline_result(final_text, _id)
                self.status_bar.showMessage("✓ 已完成高质量提质", 3000)

            def _on_polish_error(err):
                self.status_bar.showMessage(f"⚠ 提质失败，已使用首轮结果: {err}", 5000)
                _render_inline_result(full_text, _id)

            polish_worker.finished_ok.connect(_on_polish_done)
            polish_worker.error_occurred.connect(_on_polish_error)
            polish_worker.start()

        worker.finished_ok.connect(_on_ai_finished)
        worker.error_occurred.connect(lambda err, _id=ai_id: self.preview.ai_error_block(_id, err))
        worker.start()

    def _run_ai_smart(self, messages: list):
        """Run AI in smart mode: collect full response, then show track changes."""
        self._cancel_ai_worker()

        worker = AiWorker(messages)
        self._ai_worker = worker
        worker.status_update.connect(lambda msg: self.status_bar.showMessage(msg))

        worker.finished_ok.connect(self._apply_ai_smart_result)
        worker.error_occurred.connect(
            lambda err: self.status_bar.showMessage(f"❌ AI 错误：{err}", 8000)
        )
        worker.start()

    def _apply_ai_smart_result(self, response: str):
        """Compute word-level diff and show inline track-changes view.

        If the response contains image placeholders, process them first."""
        modified = response.strip()
        # Strip markdown code fence wrapper if AI added one
        if modified.startswith("```"):
            lines = modified.split("\n")
            modified = "\n".join(lines[1:])
            if modified.endswith("```"):
                modified = modified[:-3].strip()

        # 处理图片占位符
        if has_image_placeholders(modified):
            self.status_bar.showMessage("🖼️ 正在搜索并插入图片/图表...")
            pixabay_key = self.config.get("pixabay_api_key", "")
            img_worker = ImageProcessWorker(modified, pixabay_key=pixabay_key)
            self._img_worker = img_worker

            def _on_images_done(processed_md):
                self._finish_smart_result(processed_md)

            def _on_images_error(err):
                self.status_bar.showMessage(f"⚠ 图片搜索失败，使用原始内容: {err}", 5000)
                self._finish_smart_result(modified)

            img_worker.finished.connect(_on_images_done)
            img_worker.error.connect(_on_images_error)
            img_worker.start()
            return

        self._finish_smart_result(modified)

    def _finish_smart_result(self, modified: str):
        """After optional image processing, show track-changes diff."""
        original = self._current_markdown

        if original.strip() == modified.strip():
            self.status_bar.showMessage("AI 未发现需要修改的内容", 5000)
            return

        # Store for accept / reject
        self._tc_original_md = original
        self._tc_modified_md = modified
        self._in_track_changes = True

        # Build annotated markdown with inline <del>/<ins>
        annotated_md = self._build_tracked_changes_md(original, modified)

        # Render and replace the entire editor content
        tracked_html = self.renderer.render(annotated_md)
        escaped = tracked_html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        self.preview._safe_run_js(f"_savedRange = null; setEditorContent(`{escaped}`);")

        # Count changes for stats display
        del_count = annotated_md.count('<del class="ai-del">')
        ins_count = annotated_md.count('<ins class="ai-ins">')

        self.preview.show_track_changes_bar(del_count, ins_count)
        self.status_bar.showMessage("AI 修改完成，请查看修订内容并决定是否采纳", 5000)

    # ------------------------------------------------------------------
    # Word-level diff engine
    # ------------------------------------------------------------------

    # Precompiled regex: CJK chars individually, alpha words, digit runs,
    # whitespace runs, or any other single character.
    _DIFF_TOKEN_RE = re.compile(
        r"[\u4e00-\u9fff\u3400-\u4dbf]" r"|[A-Za-z]+" r"|\d+" r"|[ \t]+" r"|.",
        re.DOTALL,
    )

    @staticmethod
    def _tokenize_for_diff(text: str) -> list:
        """Tokenize text for word-level diffing (regex fast-path)."""
        return MainWindow._DIFF_TOKEN_RE.findall(text)

    def _build_tracked_changes_md(self, original: str, modified: str) -> str:
        """Build markdown with inline <del>/<ins> HTML showing changes.

        The annotated markdown is then rendered normally; the markdown
        renderer preserves inline HTML so <del>/<ins> tags survive.
        """
        orig_tokens = self._tokenize_for_diff(original)
        mod_tokens = self._tokenize_for_diff(modified)

        sm = difflib.SequenceMatcher(None, orig_tokens, mod_tokens, autojunk=False)
        parts: list[str] = []

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                parts.append("".join(orig_tokens[i1:i2]))
            elif tag == "delete":
                text = "".join(orig_tokens[i1:i2])
                parts.append(f'<del class="ai-del">{text}</del>')
            elif tag == "insert":
                text = "".join(mod_tokens[j1:j2])
                parts.append(f'<ins class="ai-ins">{text}</ins>')
            elif tag == "replace":
                old = "".join(orig_tokens[i1:i2])
                new = "".join(mod_tokens[j1:j2])
                parts.append(f'<del class="ai-del">{old}</del>')
                parts.append(f'<ins class="ai-ins">{new}</ins>')

        return "".join(parts)

    # ------------------------------------------------------------------
    # Track-changes accept / reject
    # ------------------------------------------------------------------

    def _on_smart_modify_accepted(self, ai_id: str):
        """User accepted tracked changes — apply the modified document."""
        if self._tc_modified_md is None:
            return
        modified_md = self._tc_modified_md
        self._current_markdown = modified_md
        self.doc_manager.current_document.update_content(modified_md)
        self._in_track_changes = False
        self.preview.hide_track_changes_bar()
        self.preview.set_content_from_markdown(modified_md)
        self._tc_original_md = None
        self._tc_modified_md = None
        # Reset streaming section state
        self._tc_stream_running = False
        self._tc_stream_sections = []
        self._tc_stream_results = []
        self._tc_stream_index = 0
        self._tc_stream_instruction = ""
        self._tc_stream_target_indices = []
        self._update_title()
        self.status_bar.showMessage("✓ AI 修改已采纳", 5000)

    def _on_smart_modify_rejected(self, ai_id: str):
        """User rejected tracked changes — restore original document."""
        if self._tc_original_md is None:
            return
        # Cancel any in-progress streaming section worker
        if self._tc_stream_running:
            self._cancel_ai_worker()
        original_md = self._tc_original_md
        self._in_track_changes = False
        self.preview.hide_track_changes_bar()
        self.preview.set_content_from_markdown(original_md)
        self._tc_original_md = None
        self._tc_modified_md = None
        # Reset streaming section state
        self._tc_stream_running = False
        self._tc_stream_sections = []
        self._tc_stream_results = []
        self._tc_stream_index = 0
        self._tc_stream_instruction = ""
        self._tc_stream_target_indices = []
        self.status_bar.showMessage("AI 修改已撤回", 5000)

    # ------------------------------------------------------------------
    # AI low-dup continue / rewrite selected
    # ------------------------------------------------------------------

    def _ai_continue_low_dup(self):
        """AI 低重复模式续写。"""

        def _on_ctx(ctx_json):
            try:
                ctx = json.loads(ctx_json) if ctx_json else {}
            except Exception:
                ctx = {}
            text_before = ctx.get("textBefore", "") or self._current_markdown
            text_after = ctx.get("textAfter", "")
            ai_id = f"ai_{int(time.time() * 1000)}"
            self.preview.ai_start_block(ai_id, "continue")
            msgs = build_continue_messages(text_before, after_context=text_after, low_dup=True)
            self._run_ai_inline(
                ai_id,
                msgs,
                enforce_high_quality=True,
                quality_task_hint="低重复续写",
            )

        self.preview.get_ai_context(_on_ctx)

    def _ai_rewrite_selected(self):
        """AI 降重改写 — 全文降重，结果用 Track Changes 展示。"""
        text = self._current_markdown
        if not text.strip():
            QMessageBox.information(self, "AI 提示", "文档内容为空，请先写一些内容。")
            return
        self._ai_batch_optimize_document()

    # ------------------------------------------------------------------
    # Plagiarism check & rewrite
    # ------------------------------------------------------------------

    def _plagiarism_check(self):
        """启动混合查重：AI 语义分析 + 真实学术数据库搜索，并行执行。"""
        text = self._current_markdown
        if not text.strip():
            QMessageBox.information(self, "查重提示", "文档内容为空，请先写一些内容。")
            return

        # 显示查重面板
        self.plagiarism_panel.setVisible(True)
        sizes = self._content_splitter.sizes()
        if len(sizes) == 3 and sizes[2] == 0:
            total = sum(sizes)
            self._content_splitter.setSizes([sizes[0], total - sizes[0] - 300, 300])
        self.plagiarism_panel.set_loading()
        self.status_bar.showMessage("🛡 正在分析文档重复率 (AI + 学术数据库)...")

        # 拆句
        sentences = split_sentences(text)
        if not sentences:
            self.plagiarism_panel.clear()
            self.status_bar.showMessage("文档内容太短，无法分析", 5000)
            return
        self._plag_sentences = sentences

        # 并行状态追踪
        self._plag_ai_done = False
        self._plag_db_done = False
        self._plag_ai_results = []  # list[CheckResult]
        self._plag_db_results = []  # list[SentenceDbResult]

        # ── 1) 启动 AI 查重 ──
        self._run_ai_plagiarism_check(sentences)

        # ── 2) 启动数据库查重 ──
        self._run_db_plagiarism_check(sentences)

    def _run_ai_plagiarism_check(self, sentences: list):
        """运行 AI 查重分析（并行路径之一）。"""
        if (
            hasattr(self, "_ai_plag_worker")
            and self._ai_plag_worker
            and self._ai_plag_worker.isRunning()
        ):
            self._ai_plag_worker.cancel()
            self._ai_plag_worker.wait(2000)

        msgs = build_check_messages(sentences)
        worker = AiWorker(msgs)
        self._ai_plag_worker = worker

        def _on_done(response):
            results = parse_check_result(response, sentences)
            self._plag_ai_results = results
            self._plag_ai_done = True
            self.plagiarism_panel.set_loading_status("⏳ 正在分析...\nAI 分析 ✅ / 数据库搜索中...")
            self.status_bar.showMessage("AI 分析完成，等待数据库搜索...")
            self._try_merge_plagiarism_results()

        def _on_err(err):
            logger.warning("AI 查重失败: %s", err)
            self._plag_ai_results = []
            self._plag_ai_done = True
            self.plagiarism_panel.set_loading_status("⏳ AI 分析失败，等待数据库结果...")
            self._try_merge_plagiarism_results()

        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(_on_err)
        worker.start()

    def _run_db_plagiarism_check(self, sentences: list):
        """运行数据库查重（并行路径之二）。"""
        if (
            hasattr(self, "_db_plag_worker")
            and self._db_plag_worker
            and self._db_plag_worker.isRunning()
        ):
            self._db_plag_worker.cancel()
            self._db_plag_worker.wait(2000)

        # 使用优化版 Worker（并发 API + 缓存）
        worker = DbPlagiarismWorkerOptimized(sentences, max_workers=5)
        self._db_plag_worker = worker

        def _on_progress(done, total):
            self.plagiarism_panel.set_loading_status(
                f"⏳ 正在分析...\n"
                f"{'AI 分析 ✅' if self._plag_ai_done else 'AI 分析中...'}"
                f" / 数据库搜索 {done}/{total}"
            )

        def _on_done(db_results):
            self._plag_db_results = db_results
            self._plag_db_done = True
            self.plagiarism_panel.set_loading_status(
                "⏳ 正在分析...\n"
                f"{'AI 分析 ✅' if self._plag_ai_done else 'AI 分析中...'}"
                " / 数据库搜索 ✅"
            )
            self.status_bar.showMessage("数据库搜索完成，正在合并结果...")
            self._try_merge_plagiarism_results()

        def _on_err(err):
            logger.warning("数据库查重失败: %s", err)
            self._plag_db_results = []
            self._plag_db_done = True
            self._try_merge_plagiarism_results()

        worker.progress.connect(_on_progress)
        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(_on_err)
        worker.start()

    def _try_merge_plagiarism_results(self):
        """两路都完成后合并结果并展示。"""
        if not self._plag_ai_done or not self._plag_db_done:
            return

        ai_results = self._plag_ai_results
        db_results = self._plag_db_results

        if ai_results and db_results:
            merged = merge_results(ai_results, db_results)
        elif ai_results:
            merged = ai_results
        else:
            # 仅数据库结果 → 构造 CheckResult
            from app.core.plagiarism_service import CheckResult

            merged = []
            sent_map = {s.index: s for s in self._plag_sentences}
            for db_r in db_results:
                sent = sent_map.get(db_r.sentence_index)
                if not sent:
                    continue
                sources = []
                for m in db_r.matches[:3]:
                    sources.append(
                        {
                            "title": m.title,
                            "url": m.url,
                            "source": m.source,
                            "authors": m.authors,
                            "year": m.year,
                            "score": m.score,
                        }
                    )
                merged.append(
                    CheckResult(
                        index=db_r.sentence_index,
                        text=sent.text,
                        risk=db_r.risk,
                        dup_type="数据库匹配" if db_r.matches else "",
                        sources=sources,
                    )
                )

        self._plag_results = merged
        self.plagiarism_panel.set_results(merged)

        # 在编辑器中高亮
        results_json = json.dumps(
            [{"index": r.index, "text": r.text, "risk": r.risk} for r in merged], ensure_ascii=False
        )
        self.preview.highlight_plagiarism(results_json)

        high = sum(1 for r in merged if r.risk == "high")
        med = sum(1 for r in merged if r.risk == "medium")
        db_tag = "(含数据库比对)" if db_results else "(仅 AI 分析)"
        self.status_bar.showMessage(
            f"查重完成 {db_tag}：发现 {high} 处高风险、{med} 处中风险", 8000
        )

    def _plag_jump_to(self, index: int):
        """点击查重面板某条 → 编辑器滚动并高亮。"""
        self.preview.scroll_to_plag_sentence(index)

    def _plag_rewrite_one(self, index: int):
        """单条降重 — 感知查重结果，用 Track Changes 展示。"""
        result = None
        for r in self._plag_results:
            if r.index == index:
                result = r
                break
        if not result:
            return

        self.status_bar.showMessage(f"AI 正在降重改写第 {index + 1} 句...")

        # 获取论文表达参考
        paper_expressions = fetch_paper_expressions(result.text, limit=5)

        # 使用感知查重结果的 prompt
        msgs = build_anti_aigc_anti_dup_messages(
            result.text,
            check_result=result,
            paper_expressions=paper_expressions,
            aggressive=False
        )

        if (
            hasattr(self, "_ai_plag_worker")
            and self._ai_plag_worker
            and self._ai_plag_worker.isRunning()
        ):
            self._ai_plag_worker.cancel()
            self._ai_plag_worker.wait(2000)

        worker = AiWorker(msgs, max_tokens=MAX_TOKENS_REWRITE)
        self._ai_plag_worker = worker

        def _on_done(response):
            rewritten = response.strip()
            if not rewritten:
                self.status_bar.showMessage("❌ 降重结果为空", 5000)
                return
            modified = self._current_markdown.replace(result.text, rewritten, 1)
            self._apply_ai_smart_result(modified)
            self.status_bar.showMessage("降重完成，请查看修订内容", 8000)

        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(
            lambda err: self.status_bar.showMessage(f"❌ 降重失败：{err}", 8000)
        )
        worker.start()

    def _plagiarism_rewrite_all(self):
        """一键降重所有高风险句子。"""
        flagged = [r for r in self._plag_results if r.risk in ("high", "medium")]
        if not flagged:
            QMessageBox.information(
                self, "降重提示", "没有发现需要降重的句子。\n请先进行查重分析。"
            )
            return

        self.status_bar.showMessage(f"🔄 AI 正在批量降重 {len(flagged)} 句...")
        msgs = build_batch_rewrite_messages(flagged)
        self._run_ai_batch_rewrite(msgs, flagged)

    def _run_ai_batch_rewrite(self, messages: list, flagged: list):
        """运行批量降重 AI，完成后用 Track Changes 显示。"""
        if (
            hasattr(self, "_ai_plag_worker")
            and self._ai_plag_worker
            and self._ai_plag_worker.isRunning()
        ):
            self._ai_plag_worker.cancel()
            self._ai_plag_worker.wait(2000)

        worker = AiWorker(messages)
        self._ai_plag_worker = worker

        def _on_done(response):
            rewrites = parse_rewrite_result(response)
            if not rewrites:
                self.status_bar.showMessage("❌ 降重结果解析失败", 5000)
                return
            # 在原文中替换，用 Track Changes 显示
            modified = self._current_markdown
            for r in flagged:
                if r.index in rewrites:
                    modified = modified.replace(r.text, rewrites[r.index], 1)
            self._apply_ai_smart_result(modified)
            self.status_bar.showMessage(
                f"降重完成：已改写 {len(rewrites)} 处，请查看修订内容", 8000
            )

        def _on_err(err):
            self.status_bar.showMessage(f"❌ 降重失败：{err}", 8000)

        worker.finished_ok.connect(_on_done)
        worker.error_occurred.connect(_on_err)
        worker.start()

    # ── 智能迭代降重 ──

    def _smart_iterative_rewrite(self):
        """智能迭代降重：查重 → 降重 → 验证 → 循环，直到达到目标重复率。"""
        if not self._plag_results:
            QMessageBox.information(
                self, "提示", "请先进行查重分析，再使用智能降重功能。"
            )
            return

        # 计算当前重复率
        current_rate = calculate_duplication_rate(self._plag_results)
        high_count = sum(1 for r in self._plag_results if r.risk == "high")
        med_count = sum(1 for r in self._plag_results if r.risk == "medium")

        if high_count + med_count == 0:
            QMessageBox.information(
                self, "提示", "当前文档没有高风险或中风险句子，无需降重。"
            )
            return

        # 显示设置对话框
        dialog = IterativeRewriteDialog(current_rate, high_count, med_count, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        config = dialog.get_config()

        # 如果是保守模式，使用原有的一键降重
        if dialog.is_conservative_mode():
            self._plagiarism_rewrite_all()
            return

        # 启动迭代降重
        self._start_iterative_rewrite(config)

    def _start_iterative_rewrite(self, config: IterativeRewriteConfig):
        """启动迭代降重流程。"""
        self._iterative_config = config
        self._iterative_iteration = 0
        self._iterative_original_rate = calculate_duplication_rate(self._plag_results)
        self._iterative_text = self._current_markdown

        self.status_bar.showMessage("🎯 智能降重启动...")
        self.plagiarism_panel.set_iterative_progress({
            "stage": "checking",
            "iteration": 1
        })

        # 开始第一轮
        self._run_iterative_round()

    def _run_iterative_round(self):
        """执行一轮迭代降重。"""
        self._iterative_iteration += 1
        config = self._iterative_config

        # 检查是否超过最大迭代次数
        if self._iterative_iteration > config.max_iterations:
            self._finish_iterative_rewrite(False)
            return

        # 更新进度
        self.plagiarism_panel.set_iterative_progress({
            "stage": "rewriting",
            "iteration": self._iterative_iteration,
            "count": len(filter_flagged_sentences(self._plag_results, config.rewrite_threshold))
        })

        # 筛选需要降重的句子
        flagged = filter_flagged_sentences(self._plag_results, config.rewrite_threshold)
        if not flagged:
            self._finish_iterative_rewrite(True)
            return

        # 获取论文表达参考
        paper_expressions = None
        if config.use_paper_db:
            sample_text = " ".join(r.text for r in flagged[:3])
            paper_expressions = fetch_paper_expressions(sample_text, limit=8)

        # 构建降重消息
        msgs = build_batch_anti_aigc_anti_dup_messages(
            flagged,
            paper_expressions=paper_expressions,
            aggressive=config.aggressive_mode
        )

        self.status_bar.showMessage(
            f"🔄 第 {self._iterative_iteration} 轮降重中 ({len(flagged)} 句)..."
        )

        # 运行 AI 降重
        self._run_iterative_ai_rewrite(msgs, flagged)

    def _run_iterative_ai_rewrite(self, messages: list, flagged: list):
        """运行迭代降重的 AI 调用。"""
        if (
            hasattr(self, "_ai_iterative_worker")
            and self._ai_iterative_worker
            and self._ai_iterative_worker.isRunning()
        ):
            self._ai_iterative_worker.cancel()
            self._ai_iterative_worker.wait(2000)

        worker = AiWorker(messages)
        self._ai_iterative_worker = worker
        self._iterative_flagged = flagged

        worker.finished_ok.connect(self._on_iterative_rewrite_done)
        worker.error_occurred.connect(self._on_iterative_rewrite_error)
        worker.start()

    def _on_iterative_rewrite_done(self, response: str):
        """迭代降重 AI 完成回调。"""
        rewrites = parse_rewrite_result(response)
        if not rewrites:
            self.status_bar.showMessage(
                f"⚠️ 第 {self._iterative_iteration} 轮降重结果解析失败，跳过", 5000
            )
            # 继续下一轮
            self._verify_and_continue()
            return

        # 应用改写
        flagged = self._iterative_flagged
        modified = self._iterative_text
        rewritten_count = 0
        for r in flagged:
            if r.index in rewrites:
                modified = modified.replace(r.text, rewrites[r.index], 1)
                rewritten_count += 1

        self._iterative_text = modified
        self.status_bar.showMessage(
            f"✅ 第 {self._iterative_iteration} 轮完成：改写 {rewritten_count} 句"
        )

        # 验证并继续
        self._verify_and_continue()

    def _on_iterative_rewrite_error(self, error: str):
        """迭代降重 AI 错误回调。"""
        self.status_bar.showMessage(f"❌ 第 {self._iterative_iteration} 轮降重失败：{error}", 8000)
        # 尝试继续下一轮
        self._verify_and_continue()

    def _verify_and_continue(self):
        """验证降重效果并决定是否继续。"""
        config = self._iterative_config

        if not config.verify_after_rewrite:
            # 不验证，直接继续下一轮
            self._run_iterative_round()
            return

        # 更新进度
        self.plagiarism_panel.set_iterative_progress({
            "stage": "verifying",
            "iteration": self._iterative_iteration
        })

        # 重新查重验证
        self._run_iterative_check()

    def _run_iterative_check(self):
        """运行迭代查重验证。"""
        sentences = split_sentences(self._iterative_text)
        if not sentences:
            self._finish_iterative_rewrite(True)
            return

        msgs = build_check_messages(sentences)

        if (
            hasattr(self, "_ai_iterative_check_worker")
            and self._ai_iterative_check_worker
            and self._ai_iterative_check_worker.isRunning()
        ):
            self._ai_iterative_check_worker.cancel()
            self._ai_iterative_check_worker.wait(2000)

        worker = AiWorker(msgs)
        self._ai_iterative_check_worker = worker
        self._iterative_sentences = sentences

        worker.finished_ok.connect(self._on_iterative_check_done)
        worker.error_occurred.connect(self._on_iterative_check_error)
        worker.start()

    def _on_iterative_check_done(self, response: str):
        """迭代查重完成回调。"""
        sentences = self._iterative_sentences
        results = parse_check_result(response, sentences)

        if not results:
            # 解析失败，假设已完成
            self._finish_iterative_rewrite(True)
            return

        # 更新查重结果
        self._plag_results = results
        current_rate = calculate_duplication_rate(results)
        config = self._iterative_config

        # 显示迭代结果
        self.plagiarism_panel.set_iteration_result({
            "iteration": self._iterative_iteration,
            "rate_before": self._iterative_original_rate,
            "rate_after": current_rate,
            "rewritten": len(self._iterative_flagged) if hasattr(self, "_iterative_flagged") else 0
        })

        # 检查是否达到目标
        if current_rate <= config.target_rate:
            self._finish_iterative_rewrite(True)
            return

        # 检查是否还有需要降重的句子
        flagged = filter_flagged_sentences(results, config.rewrite_threshold)
        if not flagged:
            self._finish_iterative_rewrite(True)
            return

        # 继续下一轮
        self._run_iterative_round()

    def _on_iterative_check_error(self, error: str):
        """迭代查重错误回调。"""
        self.status_bar.showMessage(f"⚠️ 验证查重失败：{error}，继续下一轮", 5000)
        # 继续下一轮
        self._run_iterative_round()

    def _finish_iterative_rewrite(self, success: bool):
        """完成迭代降重。"""
        final_rate = calculate_duplication_rate(self._plag_results) if self._plag_results else 0
        iterations = self._iterative_iteration

        # 应用最终结果
        self._apply_ai_smart_result(self._iterative_text)

        # 更新面板
        self.plagiarism_panel.set_smart_rewrite_complete(success, final_rate, iterations)
        self.plagiarism_panel.set_results(self._plag_results)

        if success:
            QMessageBox.information(
                self, "智能降重完成",
                f"经过 {iterations} 轮迭代，重复率已降至约 {int(final_rate*100)}%\n"
                f"请查看修订内容并确认。"
            )
        else:
            QMessageBox.warning(
                self, "智能降重未达标",
                f"经过 {iterations} 轮迭代，重复率为约 {int(final_rate*100)}%\n"
                f"建议手动调整部分句子或使用激进模式重试。"
            )

        self.status_bar.showMessage(
            f"智能降重完成：{iterations} 轮迭代，最终重复率约 {int(final_rate*100)}%", 10000
        )

    def _on_ai_custom_result(self, text: str, mode: str):
        """Handle result from AI custom dialog."""
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        js = f"""
        (function() {{
            var sel = window.getSelection();
            if (sel.rangeCount > 0 && !sel.isCollapsed) {{
                document.execCommand('insertText', false, `{escaped}`);
            }} else {{
                var range = document.createRange();
                range.selectNodeContents(editorEl);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
                document.execCommand('insertText', false, `{escaped}`);
            }}
            scheduleContentReport();
        }})();
        """
        self.preview.exec_js(js)

    def closeEvent(self, event):
        if self._check_save():
            self._closing = True
            # Stop all timers to prevent post-destruction access
            self._convert_timer.stop()
            self._autosave_timer.stop()
            self._autosave_status_timer.stop()
            self._save_config()
            event.accept()
        else:
            event.ignore()
