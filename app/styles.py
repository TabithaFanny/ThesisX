MAIN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

/* ===================== 菜单栏 ===================== */
QMenuBar {
    background-color: #fafafa;
    border-bottom: 1px solid #e0e0e0;
    padding: 2px;
    font-size: 13px;
}

QMenuBar::item {
    padding: 4px 12px;
}

QMenuBar::item:selected {
    background-color: #e3e3e3;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    padding: 4px 0;
}

QMenu::item {
    padding: 6px 32px 6px 24px;
    font-size: 13px;
}

QMenu::item:selected {
    background-color: #e8f0fe;
    color: #1a5fb4;
}

QMenu::item:disabled {
    color: #aaaaaa;
}

QMenu::separator {
    height: 1px;
    background-color: #e8e8e8;
    margin: 4px 12px;
}

QMenu::indicator {
    width: 16px;
    height: 16px;
}

/* ===================== 工具栏 ===================== */
QToolBar {
    background-color: #fafafa;
    border-bottom: 1px solid #e0e0e0;
    padding: 2px 4px;
    spacing: 2px;
}

QToolBar::separator {
    width: 1px;
    background-color: #d8d8d8;
    margin: 4px 6px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
    font-weight: bold;
    color: #444444;
    min-width: 24px;
    min-height: 24px;
}

QToolButton:hover {
    background-color: #e3e8f0;
    border-color: #c0cce0;
}

QToolButton:pressed {
    background-color: #ccd6e8;
    border-color: #99aac8;
}

QToolButton:checked {
    background-color: #dce8f8;
    border-color: #4a90d9;
}

QToolButton::menu-indicator {
    subcontrol-position: right center;
    subcontrol-origin: padding;
    left: -4px;
}

/* ===================== 下拉框 QComboBox ===================== */
QComboBox {
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 3px 24px 3px 8px;
    font-size: 12px;
    background-color: #ffffff;
    color: #333333;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #4a90d9;
}

QComboBox:focus {
    border-color: #4a90d9;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 18px;
    border-left: 1px solid #d0d0d0;
    border-radius: 0 4px 4px 0;
    background-color: #f5f5f5;
}

QComboBox::down-arrow {
    width: 8px;
    height: 8px;
    border-left: 2px solid #666666;
    border-bottom: 2px solid #666666;
    margin-top: -3px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    selection-background-color: #e8f0fe;
    selection-color: #1a5fb4;
    padding: 2px;
}

/* ===================== 分隔器 QSplitter ===================== */
QSplitter::handle {
    background-color: #e0e0e0;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

QSplitter::handle:hover {
    background-color: #4a90d9;
}

/* ===================== 大纲树 QTreeWidget ===================== */
QTreeWidget {
    background-color: #fafafa;
    border: none;
    border-right: 1px solid #e0e0e0;
    font-size: 13px;
    outline: none;
}

QTreeWidget::item {
    padding: 4px 8px;
    height: 24px;
}

QTreeWidget::item:selected {
    background-color: #dce8f8;
    color: #1a5fb4;
}

QTreeWidget::item:hover {
    background-color: #eef3fc;
}

QTreeWidget::branch:selected {
    background-color: #dce8f8;
}

QHeaderView::section {
    background-color: #f0f0f0;
    border: none;
    border-bottom: 1px solid #e0e0e0;
    border-right: 1px solid #e0e0e0;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 13px;
}

/* ===================== 状态栏 ===================== */
QStatusBar {
    background-color: #f5f5f5;
    border-top: 1px solid #e0e0e0;
    font-size: 12px;
    color: #555555;
}

QStatusBar::item {
    border: none;
}

QLabel#statusLabel {
    padding: 0 10px;
    color: #555555;
    font-size: 12px;
}

/* ===================== 滚动条 ===================== */
QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #c8c8c8;
    border-radius: 5px;
    min-height: 30px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a8b8;
}

QScrollBar::handle:vertical:pressed {
    background-color: #8090b0;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background-color: transparent;
}

QScrollBar:horizontal {
    background-color: #f5f5f5;
    height: 10px;
    border: none;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #c8c8c8;
    border-radius: 5px;
    min-width: 30px;
    margin: 1px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a0a8b8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    border: none;
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background-color: transparent;
}

/* ===================== 对话框 ===================== */
QDialog {
    background-color: #ffffff;
}

/* ===================== 按鈕 ===================== */
QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #c8c8c8;
    border-radius: 4px;
    padding: 5px 14px;
    font-size: 13px;
    color: #333333;
    min-width: 64px;
}

QPushButton:hover {
    background-color: #e3e8f0;
    border-color: #9abadc;
}

QPushButton:pressed {
    background-color: #c8d8f0;
    border-color: #4a90d9;
}

QPushButton:disabled {
    color: #aaaaaa;
    background-color: #f5f5f5;
    border-color: #e0e0e0;
}

QPushButton#primaryButton, QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="确定"] {
    background-color: #4a90d9;
    border-color: #3a7bc8;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#primaryButton:hover {
    background-color: #3a7bc8;
}

/* ===================== 输入框 ===================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1px solid #c8c8c8;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
    background-color: #ffffff;
    color: #222222;
    selection-background-color: #b3d4f5;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border-color: #4a90d9;
    background-color: #fafcff;
}

QLineEdit:read-only {
    background-color: #f5f5f5;
    color: #666666;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border-left: 1px solid #c8c8c8;
    background-color: #f5f5f5;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #e0e8f8;
}

/* ===================== 分组框 QGroupBox ===================== */
QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px 8px 8px 8px;
    font-size: 13px;
    font-weight: bold;
    color: #444444;
    background-color: #fafafa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
    background-color: #fafafa;
}

/* ===================== 复选框 QCheckBox ===================== */
QCheckBox {
    font-size: 13px;
    color: #333333;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #b0b0b0;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4a90d9;
    border-color: #3a7bc8;
}

QCheckBox::indicator:hover {
    border-color: #4a90d9;
}

/* ===================== 单选按鈕 QRadioButton ===================== */
QRadioButton {
    font-size: 13px;
    color: #333333;
    spacing: 6px;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #b0b0b0;
    border-radius: 7px;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    background-color: #4a90d9;
    border-color: #3a7bc8;
    border-width: 3px;
}

/* ===================== 标签页 QTabWidget ===================== */
QTabWidget::pane {
    border: 1px solid #d0d0d0;
    border-top: none;
    background-color: #ffffff;
    padding: 8px;
}

QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #d0d0d0;
    border-bottom: none;
    padding: 6px 16px;
    font-size: 13px;
    color: #555555;
    min-width: 60px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1a5fb4;
    border-bottom: 2px solid #4a90d9;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #e8eef8;
}

/* ===================== 表格 QTableWidget ===================== */
QTableWidget {
    border: 1px solid #c8c8c8;
    gridline-color: #e4e4e4;
    background-color: #ffffff;
    font-size: 13px;
    alternate-background-color: #f5f8ff;
    selection-background-color: #dce8f8;
    selection-color: #222222;
}

QTableWidget::item {
    padding: 4px 8px;
}

QTableWidget::item:selected {
    background-color: #dce8f8;
    color: #222222;
}

QTableCornerButton::section {
    background-color: #f0f0f0;
    border: 1px solid #d0d0d0;
}

/* ===================== 进度条 QProgressBar ===================== */
QProgressBar {
    border: 1px solid #c8c8c8;
    border-radius: 4px;
    background-color: #f0f0f0;
    text-align: center;
    font-size: 12px;
    color: #333333;
}

QProgressBar::chunk {
    background-color: #4a90d9;
    border-radius: 3px;
}

/* ===================== 提示框 QToolTip ===================== */
QToolTip {
    background-color: #2d3748;
    color: #ffffff;
    border: 1px solid #1a202c;
    padding: 4px 8px;
    font-size: 12px;
    opacity: 230;
}
"""

DARK_STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}

/* ===================== 菜单栏 ===================== */
QMenuBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px;
    font-size: 13px;
    color: #cdd6f4;
}
QMenuBar::item { padding: 4px 12px; }
QMenuBar::item:selected { background-color: #313244; }
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    padding: 4px 0;
    color: #cdd6f4;
}
QMenu::item { padding: 6px 32px 6px 24px; font-size: 13px; }
QMenu::item:selected { background-color: #313244; color: #89b4fa; }
QMenu::item:disabled { color: #585b70; }
QMenu::separator { height: 1px; background-color: #313244; margin: 4px 12px; }

/* ===================== 工具栏 ===================== */
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px 4px;
    spacing: 2px;
}
QToolBar::separator { width: 1px; background-color: #313244; margin: 4px 6px; }
QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
    font-weight: bold;
    color: #cdd6f4;
    min-width: 24px;
    min-height: 24px;
}
QToolButton:hover { background-color: #313244; border-color: #45475a; }
QToolButton:pressed { background-color: #45475a; }
QToolButton:checked { background-color: #313244; border-color: #89b4fa; }
QToolButton::menu-indicator { subcontrol-position: right center; left: -4px; }

/* ===================== 下拉框 ===================== */
QComboBox {
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 3px 24px 3px 8px;
    font-size: 12px;
    background-color: #1e1e2e;
    color: #cdd6f4;
    min-height: 22px;
}
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { width: 18px; border-left: 1px solid #45475a; background-color: #181825; }
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    selection-background-color: #313244;
    selection-color: #89b4fa;
}

/* ===================== 分隔器 ===================== */
QSplitter::handle { background-color: #313244; }
QSplitter::handle:hover { background-color: #89b4fa; }

/* ===================== 大纲树 ===================== */
QTreeWidget {
    background-color: #181825;
    border: none;
    border-right: 1px solid #313244;
    font-size: 13px;
    color: #cdd6f4;
}
QTreeWidget::item { padding: 4px 8px; height: 24px; }
QTreeWidget::item:selected { background-color: #313244; color: #89b4fa; }
QTreeWidget::item:hover { background-color: #1e1e2e; }
QHeaderView::section {
    background-color: #181825;
    border: none;
    border-bottom: 1px solid #313244;
    padding: 4px 8px;
    font-weight: bold;
    color: #cdd6f4;
}

/* ===================== 状态栏 ===================== */
QStatusBar {
    background-color: #181825;
    border-top: 1px solid #313244;
    font-size: 12px;
    color: #a6adc8;
}
QStatusBar::item { border: none; }
QLabel#statusLabel { padding: 0 10px; color: #a6adc8; }

/* ===================== 滚动条 ===================== */
QScrollBar:vertical { background-color: #1e1e2e; width: 10px; }
QScrollBar::handle:vertical { background-color: #45475a; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background-color: transparent; }
QScrollBar:horizontal { background-color: #1e1e2e; height: 10px; }
QScrollBar::handle:horizontal { background-color: #45475a; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: transparent; }

/* ===================== 对话框 / 按钮 / 输入框 ===================== */
QDialog { background-color: #1e1e2e; color: #cdd6f4; }
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 14px;
    font-size: 13px;
    color: #cdd6f4;
    min-width: 64px;
}
QPushButton:hover { background-color: #45475a; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { color: #585b70; background-color: #1e1e2e; }
QPushButton#primaryButton { background-color: #89b4fa; border-color: #74c7ec; color: #1e1e2e; font-weight: bold; }
QPushButton#primaryButton:hover { background-color: #74c7ec; }

QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
    background-color: #181825;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus { border-color: #89b4fa; }

QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px;
    color: #cdd6f4;
    background-color: #181825;
}
QGroupBox::title { padding: 0 6px; left: 12px; background-color: #181825; }

QCheckBox { color: #cdd6f4; }
QCheckBox::indicator { border: 1px solid #585b70; border-radius: 3px; background-color: #181825; }
QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #74c7ec; }

QTabWidget::pane { border: 1px solid #313244; background-color: #1e1e2e; padding: 8px; }
QTabBar::tab { background-color: #181825; border: 1px solid #313244; padding: 6px 16px; color: #a6adc8; }
QTabBar::tab:selected { background-color: #1e1e2e; color: #89b4fa; border-bottom: 2px solid #89b4fa; }

QTableWidget { border: 1px solid #313244; background-color: #1e1e2e; color: #cdd6f4; }
QTableWidget::item:selected { background-color: #313244; }

QProgressBar { border: 1px solid #45475a; background-color: #181825; color: #cdd6f4; }
QProgressBar::chunk { background-color: #89b4fa; }

QToolTip { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 4px 8px; }

QLabel { color: #cdd6f4; }
"""
