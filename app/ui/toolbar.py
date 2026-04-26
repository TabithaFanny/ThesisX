from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QToolButton,
    QWidget,
)

from app.constants import PREVIEW_STYLES
from app.ui.icons import (
    dropdown_arrow_path,
    icon_align_center,
    icon_align_justify,
    icon_align_left,
    icon_align_right,
    icon_bold,
    icon_bullet_list,
    icon_chart,
    icon_chatgpt,
    icon_clear_format,
    icon_code,
    icon_font_color,
    icon_font_size,
    icon_formula,
    icon_gpt_continue,
    icon_gpt_custom,
    icon_gpt_optimize,
    icon_gpt_rewrite,
    icon_heading,
    icon_highlight,
    icon_hr,
    icon_image,
    icon_indent,
    icon_italic,
    icon_link,
    icon_more,
    icon_ordered_list,
    icon_outdent,
    icon_quote,
    icon_strikethrough,
    icon_subscript,
    icon_superscript,
    icon_switch_model,
    icon_table,
    icon_underline,
)


class FormattingToolbar(QToolBar):

    bold_clicked = pyqtSignal()
    italic_clicked = pyqtSignal()
    underline_clicked = pyqtSignal()
    strikethrough_clicked = pyqtSignal()
    heading_clicked = pyqtSignal(int)
    link_clicked = pyqtSignal()
    image_clicked = pyqtSignal()
    code_clicked = pyqtSignal()
    table_clicked = pyqtSignal()
    quote_clicked = pyqtSignal()
    list_clicked = pyqtSignal()
    ordered_list_clicked = pyqtSignal()
    hr_clicked = pyqtSignal()
    font_color_changed = pyqtSignal(str)
    highlight_color_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(str)
    font_family_changed = pyqtSignal(str)
    superscript_clicked = pyqtSignal()
    subscript_clicked = pyqtSignal()
    gpt_optimize_clicked = pyqtSignal()
    gpt_continue_clicked = pyqtSignal()
    gpt_custom_clicked = pyqtSignal()
    gpt_rewrite_clicked = pyqtSignal()
    model_switch_clicked = pyqtSignal()
    skills_clicked = pyqtSignal()
    more_toggled = pyqtSignal(bool)
    align_left_clicked = pyqtSignal()
    align_center_clicked = pyqtSignal()
    align_right_clicked = pyqtSignal()
    align_justify_clicked = pyqtSignal()
    preset_changed = pyqtSignal(str)  # emits preset key

    ICON_SIZE = 20

    def __init__(self, parent=None):
        super().__init__("格式化工具栏", parent)
        self.setMovable(False)
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self._font_color = "#e74c3c"
        self._highlight_color = "#ffc107"
        self._build_toolbar()

    _ACTIVE_STYLE = (
        "QToolButton { background-color: #cde4ff; "
        "border: 1px solid #7aadff; border-radius: 4px; }"
    )

    def _make_btn(self, icon, tooltip, signal=None, click_handler=None):
        btn = QToolButton()
        btn.setIcon(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        if signal is not None:
            btn.clicked.connect(signal.emit)
        elif click_handler is not None:
            btn.clicked.connect(click_handler)
        self.addWidget(btn)
        return btn

    def _combo_style(self):
        """Return a QComboBox stylesheet with custom dropdown arrow."""
        arrow = dropdown_arrow_path().replace("\\", "/")
        return f"""
            QComboBox {{
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 3px 8px;
                padding-right: 22px;
                background: white;
                font-size: 13px;
            }}
            QComboBox:hover {{ border-color: #999; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 22px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url({arrow});
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid #ccc;
                selection-background-color: #E6F7F1;
                selection-color: #333;
            }}
        """

    def _build_toolbar(self):
        s = self.ICON_SIZE

        # Text formatting (store references for active state)
        self.btn_bold = self._make_btn(icon_bold(s), "加粗 (Ctrl+B)", self.bold_clicked)
        self.btn_italic = self._make_btn(icon_italic(s), "斜体", self.italic_clicked)
        self.btn_underline = self._make_btn(
            icon_underline(s), "下划线 (Ctrl+U)", self.underline_clicked
        )
        self.btn_strike = self._make_btn(
            icon_strikethrough(s), "删除线 (Ctrl+D)", self.strikethrough_clicked
        )

        self.addSeparator()

        # Heading dropdown
        heading_btn = QToolButton()
        heading_btn.setIcon(icon_heading(s))
        heading_btn.setToolTip("标题")
        heading_btn.setFixedSize(40, 32)
        heading_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        heading_menu = QMenu(heading_btn)
        for i in range(1, 7):
            action = heading_menu.addAction(f"标题 {i}  (Ctrl+{i})")
            action.triggered.connect(lambda checked, level=i: self.heading_clicked.emit(level))
        heading_btn.setMenu(heading_menu)
        self.addWidget(heading_btn)

        # Font family combo
        self.font_family_combo = QComboBox()
        self.font_family_combo.setToolTip("字体")
        self.font_family_combo.setFixedWidth(110)
        self.font_family_combo.setStyleSheet(self._combo_style())
        fonts = [
            # ── 中文字体 ──
            ("宋体", "SimSun, 宋体"),
            ("黑体", "SimHei, 黑体"),
            ("微软雅黑", "Microsoft YaHei, 微软雅黑"),
            ("楷体", "KaiTi, 楷体"),
            ("仿宋", "FangSong, 仿宋"),
            ("隶书", "LiSu, 隶书"),
            ("幼圆", "YouYuan, 幼圆"),
            ("等线", "DengXian, 等线"),
            ("华文中宋", "STZhongsong"),
            ("华文楷体", "STKaiti"),
            ("华文宋体", "STSong"),
            ("华文仿宋", "STFangsong"),
            ("华文细黑", "STXihei"),
            ("华文新魏", "STXinwei"),
            ("华文行楷", "STXingkai"),
            ("华文彩云", "STCaiyun"),
            ("华文琥珀", "STHupo"),
            ("方正小标宋", "FZXiaoBiaoSong-B05S"),
            ("方正书宋", "FZShuSong-Z01S"),
            ("方正仿宋", "FZFangSong-Z02S"),
            ("方正黑体", "FZHei-B01S"),
            ("方正楷体", "FZKai-Z03S"),
            # ── 英文字体 ──
            ("Arial", "Arial"),
            ("Times New Roman", "Times New Roman"),
            ("Georgia", "Georgia"),
            ("Calibri", "Calibri"),
            ("Cambria", "Cambria"),
            ("Verdana", "Verdana"),
            ("Tahoma", "Tahoma"),
            ("Trebuchet MS", "Trebuchet MS"),
            ("Segoe UI", "Segoe UI"),
            ("Palatino", "Palatino Linotype, Palatino"),
            ("Garamond", "Garamond"),
            ("Book Antiqua", "Book Antiqua"),
            ("Consolas", "Consolas"),
            ("Courier New", "Courier New"),
            ("Lucida Console", "Lucida Console"),
        ]
        for label, family in fonts:
            self.font_family_combo.addItem(label, userData=family)
        self.font_family_combo.setCurrentIndex(2)  # 默认: 微软雅黑
        self.font_family_combo.activated.connect(
            lambda: self.font_family_changed.emit(
                self.font_family_combo.currentData() or "Microsoft YaHei"
            )
        )
        self.addWidget(self.font_family_combo)

        # Font size combo
        self.font_size_combo = QComboBox()
        self.font_size_combo.setToolTip("字号")
        self.font_size_combo.setFixedWidth(62)
        self.font_size_combo.setEditable(True)
        self.font_size_combo.setStyleSheet(self._combo_style())
        sizes = ["10", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48"]
        self.font_size_combo.addItems(sizes)
        self.font_size_combo.setCurrentText("14")
        self.font_size_combo.activated.connect(
            lambda: self.font_size_changed.emit(self.font_size_combo.currentText())
        )
        self.addWidget(self.font_size_combo)

        self.addSeparator()

        # Alignment group
        self.btn_align_left = self._make_btn(icon_align_left(s), "左对齐", self.align_left_clicked)
        self.btn_align_center = self._make_btn(
            icon_align_center(s), "居中对齐", self.align_center_clicked
        )
        self.btn_align_right = self._make_btn(
            icon_align_right(s), "右对齐", self.align_right_clicked
        )
        self.btn_align_justify = self._make_btn(
            icon_align_justify(s), "两端对齐", self.align_justify_clicked
        )

        self.addSeparator()

        # Color group
        self.font_color_btn = QToolButton()
        self.font_color_btn.setIcon(icon_font_color(s, self._font_color))
        self.font_color_btn.setToolTip("字体颜色")
        self.font_color_btn.setFixedSize(32, 32)
        self.font_color_btn.clicked.connect(self._pick_font_color)
        self.addWidget(self.font_color_btn)

        self.highlight_btn = QToolButton()
        self.highlight_btn.setIcon(icon_highlight(s, self._highlight_color))
        self.highlight_btn.setToolTip("背景颜色")
        self.highlight_btn.setFixedSize(32, 32)
        self.highlight_btn.clicked.connect(self._pick_highlight_color)
        self.addWidget(self.highlight_btn)

        self.addSeparator()

        # Insert group
        self._make_btn(icon_link(s), "插入链接 (Ctrl+L)", self.link_clicked)
        self._make_btn(icon_image(s), "插入图片 (Ctrl+Shift+I)", self.image_clicked)
        self.btn_code = self._make_btn(icon_code(s), "代码块 (Ctrl+K)", self.code_clicked)

        self.addSeparator()

        # Structure group
        self._make_btn(icon_table(s), "插入表格 (Ctrl+T)", self.table_clicked)
        self.btn_quote = self._make_btn(icon_quote(s), "引用 (Ctrl+Q)", self.quote_clicked)
        self.btn_list = self._make_btn(
            icon_bullet_list(s), "无序列表 (Ctrl+Shift+L)", self.list_clicked
        )
        self.btn_olist = self._make_btn(icon_ordered_list(s), "有序列表", self.ordered_list_clicked)
        self._make_btn(icon_hr(s), "分隔线", self.hr_clicked)

        self.addSeparator()

        # GPT button — QPushButton 可正确显示 icon+text
        self.btn_gpt = QPushButton()
        self.btn_gpt.setIcon(icon_chatgpt(s, "#FFFFFF"))
        self.btn_gpt.setIconSize(QSize(s, s))
        self.btn_gpt.setText("GPT")
        self.btn_gpt.setToolTip("GPT 写作助手")
        self.btn_gpt.setFixedSize(90, 32)
        self.btn_gpt.setStyleSheet("""
            QPushButton {
                background-color: #10A37F;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 14px 4px 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0D8C6D; }
            QPushButton:pressed { background-color: #0A7A5E; }
        """)
        self._gpt_menu = QMenu(self.btn_gpt)
        self._gpt_menu.setStyleSheet("""
            QMenu {
                background-color: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px 0;
            }
            QMenu::item {
                padding: 8px 16px 8px 8px;
                margin: 1px 6px;
                border-radius: 5px;
                font-size: 13px;
                color: #222;
            }
            QMenu::item:selected {
                background-color: #E6F7F1;
                color: #10A37F;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ebebeb;
                margin: 3px 12px;
            }
        """)
        self._act_optimize = self._gpt_menu.addAction(icon_gpt_optimize(16), "GPT 优化选中内容")
        self._act_optimize.triggered.connect(lambda checked: self.gpt_optimize_clicked.emit())
        self._act_continue = self._gpt_menu.addAction(icon_gpt_continue(16), "GPT 续写论文")
        self._act_continue.triggered.connect(lambda checked: self.gpt_continue_clicked.emit())
        self._gpt_menu.addSeparator()
        self._act_rewrite = self._gpt_menu.addAction(icon_gpt_rewrite(16), "AI 降重改写")
        self._act_rewrite.triggered.connect(lambda checked: self.gpt_rewrite_clicked.emit())
        self._gpt_menu.addSeparator()
        self._act_switch = self._gpt_menu.addAction(icon_switch_model(16), "切换模型...")
        self._act_switch.triggered.connect(lambda checked: self.model_switch_clicked.emit())
        self._act_custom = self._gpt_menu.addAction(icon_gpt_custom(16), "自定义 GPT 指令...")
        self._act_custom.triggered.connect(lambda checked: self.gpt_custom_clicked.emit())
        self._gpt_menu.addSeparator()
        self._act_skills = self._gpt_menu.addAction("📚 Skills 集群记忆...")
        self._act_skills.triggered.connect(lambda checked: self.skills_clicked.emit())
        self.btn_gpt.clicked.connect(self._show_gpt_menu)
        self.addWidget(self.btn_gpt)

        # More button (expand/collapse second toolbar row)
        self.btn_more = QToolButton()
        self.btn_more.setIcon(icon_more(s))
        self.btn_more.setToolTip("更多组件")
        self.btn_more.setFixedSize(32, 32)
        self.btn_more.setCheckable(True)
        self.btn_more.setStyleSheet("""
            QToolButton {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QToolButton:hover {
                background: #e2e2e2;
                border: 1px solid #999;
            }
            QToolButton:checked {
                background-color: #cde4ff;
                border: 1px solid #7aadff;
            }
        """)
        self.btn_more.toggled.connect(self.more_toggled.emit)
        self.addWidget(self.btn_more)

        self.addSeparator()

        # Preset switcher
        self.preset_combo = QComboBox()
        self.preset_combo.setToolTip("预览样式")
        self.preset_combo.setFixedWidth(80)
        self.preset_combo.setStyleSheet(self._combo_style())
        for key, label in PREVIEW_STYLES:
            self.preset_combo.addItem(label, userData=key)
        self.preset_combo.activated.connect(
            lambda: self.preset_changed.emit(self.preset_combo.currentData() or "academic")
        )
        self.addWidget(self.preset_combo)

    def update_ai_button(self, name: str, color: str, hover: str, pressed: str, icon: QIcon):
        """Update GPT button appearance for the active AI model."""
        s = self.ICON_SIZE
        self.btn_gpt.setIcon(icon)
        self.btn_gpt.setIconSize(QSize(s, s))
        self.btn_gpt.setText(name)
        self.btn_gpt.setToolTip(f"{name} 写作助手")
        self.btn_gpt.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 14px 4px 10px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
        """)
        # Update menu item labels
        self._act_optimize.setText(f"{name} 降重优化选中内容")
        self._act_continue.setText(f"{name} 续写论文")
        self._act_rewrite.setText(f"{name} 降重改写")
        self._act_custom.setText(f"自定义 {name} 指令...")
        # Update menu hover color to match brand
        self._gpt_menu.setStyleSheet(f"""
            QMenu {{
                background-color: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px 0;
            }}
            QMenu::item {{
                padding: 8px 16px 8px 8px;
                margin: 1px 6px;
                border-radius: 5px;
                font-size: 13px;
                color: #222;
            }}
            QMenu::item:selected {{
                background-color: {color}18;
                color: {color};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: #ebebeb;
                margin: 3px 12px;
            }}
        """)

    def _show_gpt_menu(self):
        pos = self.btn_gpt.mapToGlobal(self.btn_gpt.rect().bottomLeft())
        self._gpt_menu.exec(pos)

    def _pick_font_color(self):
        color = QColorDialog.getColor(QColor(self._font_color), self, "选择字体颜色")
        if color.isValid():
            self._font_color = color.name()
            self.font_color_btn.setIcon(icon_font_color(self.ICON_SIZE, self._font_color))
            self.font_color_changed.emit(self._font_color)

    def _pick_highlight_color(self):
        color = QColorDialog.getColor(QColor(self._highlight_color), self, "选择背景颜色")
        if color.isValid():
            self._highlight_color = color.name()
            self.highlight_btn.setIcon(icon_highlight(self.ICON_SIZE, self._highlight_color))
            self.highlight_color_changed.emit(self._highlight_color)

    def get_font_color(self):
        return self._font_color

    def get_highlight_color(self):
        return self._highlight_color

    # ------------------------------------------------------------------
    # Active formatting state
    # ------------------------------------------------------------------

    def _set_active(self, btn, active):
        btn.setStyleSheet(self._ACTIVE_STYLE if active else "")

    def update_format_state(self, state: dict):
        """Update toolbar button visuals based on current format state from JS."""
        self._set_active(self.btn_bold, state.get("bold", False))
        self._set_active(self.btn_italic, state.get("italic", False))
        self._set_active(self.btn_underline, state.get("underline", False))
        self._set_active(self.btn_strike, state.get("strikethrough", False))
        self._set_active(self.btn_code, state.get("inCode", False))
        self._set_active(self.btn_quote, state.get("inQuote", False))
        self._set_active(self.btn_list, state.get("inList") == "ul")
        self._set_active(self.btn_olist, state.get("inList") == "ol")
        # Alignment state
        align = state.get("textAlign", "left")
        self._set_active(self.btn_align_left, align == "left")
        self._set_active(self.btn_align_center, align == "center")
        self._set_active(self.btn_align_right, align == "right")
        self._set_active(self.btn_align_justify, align == "justify")


class MoreToolbar(QToolBar):
    """Expandable panel with additional formatting components."""

    superscript_clicked = pyqtSignal()
    subscript_clicked = pyqtSignal()
    clear_format_clicked = pyqtSignal()
    indent_clicked = pyqtSignal()
    outdent_clicked = pyqtSignal()
    chart_clicked = pyqtSignal()
    formula_clicked = pyqtSignal()
    line_height_changed = pyqtSignal(str)  # 行距变更信号

    ICON_SIZE = 20

    _ACTIVE_STYLE = (
        "QToolButton { background-color: #cde4ff; "
        "border: 1px solid #7aadff; border-radius: 4px; }"
    )

    def __init__(self, parent=None):
        super().__init__("更多组件", parent)
        self.setMovable(False)
        self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        self.setVisible(False)
        self.setStyleSheet("QToolBar { border-top: 1px solid #e0e0e0; }")
        self._build()

    def _make_btn(self, icon, tooltip, signal):
        btn = QToolButton()
        btn.setIcon(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        btn.clicked.connect(signal.emit)
        self.addWidget(btn)
        return btn

    def _build(self):
        s = self.ICON_SIZE

        # Super/subscript
        self.btn_super = self._make_btn(
            icon_superscript(s), "上标 (Ctrl+Shift+P)", self.superscript_clicked
        )
        self.btn_sub = self._make_btn(
            icon_subscript(s), "下标 (Ctrl+Shift+B)", self.subscript_clicked
        )

        self.addSeparator()

        # Clear formatting
        self._make_btn(icon_clear_format(s), "清除格式", self.clear_format_clicked)

        self.addSeparator()

        # Indent / Outdent
        self._make_btn(icon_indent(s), "增加缩进", self.indent_clicked)
        self._make_btn(icon_outdent(s), "减少缩进", self.outdent_clicked)

        self.addSeparator()

        # 数据图
        self._make_btn(icon_chart(s), "插入数据图", self.chart_clicked)

        self.addSeparator()

        # 行距选择
        from PyQt6.QtWidgets import QLabel

        lh_label = QLabel("行距:")
        lh_label.setStyleSheet("QLabel { color: #555; font-size: 12px; padding: 0 4px; }")
        self.addWidget(lh_label)
        self.line_height_combo = QComboBox()
        self.line_height_combo.setToolTip("行距设置")
        self.line_height_combo.setFixedWidth(68)
        self.line_height_combo.setStyleSheet(
            "QComboBox { border:1px solid #ccc; border-radius:4px; "
            "padding:2px 6px; font-size:12px; }"
            "QComboBox::drop-down { border:none; }"
        )
        for label, val in [
            ("1.0倍", "1.0"),
            ("1.15倍", "1.15"),
            ("1.5倍", "1.5"),
            ("2.0倍", "2.0"),
            ("2.5倍", "2.5"),
            ("3.0倍", "3.0"),
        ]:
            self.line_height_combo.addItem(label, userData=val)
        self.line_height_combo.setCurrentIndex(2)  # 默认 1.5倍
        self.line_height_combo.activated.connect(
            lambda: self.line_height_changed.emit(self.line_height_combo.currentData() or "1.5")
        )
        self.addWidget(self.line_height_combo)

        self.addSeparator()

        # 公式按钮
        self._make_btn(icon_formula(s), "插入公式", self.formula_clicked)

    def _set_active(self, btn, active):
        btn.setStyleSheet(self._ACTIVE_STYLE if active else "")

    def update_format_state(self, state: dict):
        self._set_active(self.btn_super, state.get("superscript", False))
        self._set_active(self.btn_sub, state.get("subscript", False))
