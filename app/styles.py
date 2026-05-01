"""ThesisX global stylesheet — SVG-derived design system.

Uses design tokens from app.ui.design_tokens for consistent theming.
"""

from app.ui.design_tokens import FONT_FAMILY, Light as L, Dark as D, Radius, FontSize

# ---------------------------------------------------------------------------
# Light theme
# ---------------------------------------------------------------------------

MAIN_STYLE = """
QMainWindow {
    background-color: %(canvas)s;
    font-family: %(font)s;
}

/* ===================== Menu Bar ===================== */
QMenuBar {
    background-color: %(surface)s;
    border-bottom: 1px solid %(border)s;
    padding: 2px;
    font-size: %(body)dpx;
    font-family: %(font)s;
    color: %(text)s;
}
QMenuBar::item { padding: 4px 12px; }
QMenuBar::item:selected { background-color: %(primary_light)s; color: %(primary)s; }

QMenu {
    background-color: %(surface)s;
    border: 1px solid %(border)s;
    padding: 4px 0;
    font-family: %(font)s;
}
QMenu::item {
    padding: 6px 32px 6px 24px;
    font-size: %(body)dpx;
    font-family: %(font)s;
    color: %(text)s;
}
QMenu::item:selected { background-color: %(primary_light)s; color: %(primary)s; }
QMenu::item:disabled { color: %(muted)s; }
QMenu::separator { height: 1px; background-color: %(border_subtle)s; margin: 4px 12px; }
QMenu::indicator { width: 16px; height: 16px; }

/* ===================== Toolbar ===================== */
QToolBar {
    background-color: %(surface)s;
    border-bottom: 1px solid %(border)s;
    padding: 2px 4px;
    spacing: 2px;
}
QToolBar::separator { width: 1px; background-color: %(border)s; margin: 4px 6px; }

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: %(r_btn)dpx;
    padding: 4px 8px;
    font-size: %(body)dpx;
    font-weight: bold;
    color: %(text)s;
    min-width: 24px;
    min-height: 24px;
}
QToolButton:hover { background-color: %(primary_light)s; border-color: %(primary_border)s; }
QToolButton:pressed { background-color: #DBEAFE; border-color: %(primary)s; }
QToolButton:checked { background-color: %(primary_light)s; border-color: %(primary)s; }
QToolButton::menu-indicator {
    subcontrol-position: right center;
    subcontrol-origin: padding;
    left: -4px;
}

/* ===================== ComboBox ===================== */
QComboBox {
    border: 1px solid %(border)s;
    border-radius: %(r_input)dpx;
    padding: 3px 24px 3px 8px;
    font-size: %(secondary)dpx;
    background-color: %(surface)s;
    color: %(text)s;
    min-height: 22px;
}
QComboBox:hover { border-color: %(primary)s; }
QComboBox:focus { border-color: %(primary)s; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 18px;
    border-left: 1px solid %(border)s;
    border-radius: 0 %(r_input)dpx %(r_input)dpx 0;
    background-color: %(surface_alt)s;
}
QComboBox::down-arrow {
    width: 8px; height: 8px;
    border-left: 2px solid %(text_secondary)s;
    border-bottom: 2px solid %(text_secondary)s;
    margin-top: -3px;
}
QComboBox QAbstractItemView {
    background-color: %(surface)s;
    border: 1px solid %(border)s;
    selection-background-color: %(primary_light)s;
    selection-color: %(primary)s;
    padding: 2px;
}

/* ===================== Splitter ===================== */
QSplitter::handle { background-color: %(border)s; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:hover { background-color: %(primary)s; }

/* ===================== Tree Widget ===================== */
QTreeWidget {
    background-color: %(surface)s;
    border: none;
    border-right: 1px solid %(border)s;
    font-size: %(body)dpx;
    color: %(text)s;
    outline: none;
}
QTreeWidget::item { padding: 4px 8px; height: 24px; }
QTreeWidget::item:selected { background-color: %(primary_light)s; color: %(primary)s; }
QTreeWidget::item:hover { background-color: #F0F6FF; }
QTreeWidget::branch:selected { background-color: %(primary_light)s; }

QHeaderView::section {
    background-color: %(surface_alt)s;
    border: none;
    border-bottom: 1px solid %(border)s;
    border-right: 1px solid %(border)s;
    padding: 4px 8px;
    font-weight: bold;
    font-size: %(body)dpx;
    color: %(text)s;
}

/* ===================== Status Bar ===================== */
QStatusBar {
    background-color: %(surface)s;
    border-top: 1px solid %(border)s;
    font-size: %(secondary)dpx;
    color: %(text_secondary)s;
}
QStatusBar::item { border: none; }
QLabel#statusLabel { padding: 0 10px; color: %(text_secondary)s; font-size: %(secondary)dpx; }

/* ===================== Scrollbar ===================== */
QScrollBar:vertical {
    background-color: %(canvas)s;
    width: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: %(scrollbar)s;
    border-radius: 5px;
    min-height: 30px;
    margin: 1px;
}
QScrollBar::handle:vertical:hover { background-color: %(scrollbar_hover)s; }
QScrollBar::handle:vertical:pressed { background-color: %(text_secondary)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background-color: transparent; }

QScrollBar:horizontal {
    background-color: %(canvas)s;
    height: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: %(scrollbar)s;
    border-radius: 5px;
    min-width: 30px;
    margin: 1px;
}
QScrollBar::handle:horizontal:hover { background-color: %(scrollbar_hover)s; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: transparent; }

/* ===================== Dialog ===================== */
QDialog { background-color: %(surface)s; }

/* ===================== Button ===================== */
QPushButton {
    background-color: %(surface_alt)s;
    border: 1px solid %(border)s;
    border-radius: %(r_btn)dpx;
    padding: 5px 14px;
    font-size: %(body)dpx;
    color: %(text)s;
    min-width: 64px;
}
QPushButton:hover { background-color: %(primary_light)s; border-color: %(primary_border)s; }
QPushButton:pressed { background-color: #DBEAFE; border-color: %(primary)s; }
QPushButton:disabled { color: %(muted)s; background-color: %(surface_alt)s; border-color: %(border_subtle)s; }

QPushButton#primaryButton,
QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="确定"] {
    background-color: %(primary)s;
    border-color: %(primary)s;
    color: %(text_on_primary)s;
    font-weight: bold;
}
QPushButton#primaryButton:hover { background-color: %(primary_hover)s; }

/* ===================== Input ===================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1px solid %(border)s;
    border-radius: %(r_input)dpx;
    padding: 5px 8px;
    font-size: %(body)dpx;
    background-color: %(surface)s;
    color: %(text)s;
    selection-background-color: %(primary_light)s;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border-color: %(primary)s;
    background-color: #FAFCFF;
}
QLineEdit:read-only { background-color: %(surface_alt)s; color: %(text_secondary)s; }

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border-left: 1px solid %(border)s;
    background-color: %(surface_alt)s;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: %(primary_light)s; }

/* ===================== Group Box ===================== */
QGroupBox {
    border: 1px solid %(border)s;
    border-radius: %(r_panel)dpx;
    margin-top: 12px;
    padding: 8px;
    font-size: %(body)dpx;
    font-weight: bold;
    color: %(text)s;
    background-color: %(surface)s;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
    background-color: %(surface)s;
}

/* ===================== Checkbox ===================== */
QCheckBox { font-size: %(body)dpx; color: %(text)s; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid %(border)s;
    border-radius: 3px;
    background-color: %(surface)s;
}
QCheckBox::indicator:checked { background-color: %(primary)s; border-color: %(primary)s; }
QCheckBox::indicator:hover { border-color: %(primary)s; }

/* ===================== Radio Button ===================== */
QRadioButton { font-size: %(body)dpx; color: %(text)s; spacing: 6px; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border: 1px solid %(border)s;
    border-radius: 7px;
    background-color: %(surface)s;
}
QRadioButton::indicator:checked {
    background-color: %(primary)s;
    border-color: %(primary)s;
    border-width: 3px;
}

/* ===================== Tab Widget ===================== */
QTabWidget::pane {
    border: 1px solid %(border)s;
    border-top: none;
    background-color: %(surface)s;
    padding: 8px;
}
QTabBar::tab {
    background-color: %(surface_alt)s;
    border: 1px solid %(border)s;
    border-bottom: none;
    padding: 6px 16px;
    font-size: %(body)dpx;
    color: %(text_secondary)s;
    min-width: 60px;
}
QTabBar::tab:selected {
    background-color: %(surface)s;
    color: %(primary)s;
    border-bottom: 2px solid %(primary)s;
    font-weight: bold;
}
QTabBar::tab:hover:!selected { background-color: %(primary_light)s; }

/* ===================== Table ===================== */
QTableWidget {
    border: 1px solid %(border)s;
    gridline-color: %(border_subtle)s;
    background-color: %(surface)s;
    font-size: %(body)dpx;
    alternate-background-color: #FAFCFF;
    selection-background-color: %(primary_light)s;
    selection-color: %(text)s;
}
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background-color: %(primary_light)s; color: %(text)s; }
QTableCornerButton::section { background-color: %(surface_alt)s; border: 1px solid %(border)s; }

/* ===================== Progress Bar ===================== */
QProgressBar {
    border: 1px solid %(border)s;
    border-radius: %(r_btn)dpx;
    background-color: %(surface_alt)s;
    text-align: center;
    font-size: %(secondary)dpx;
    color: %(text)s;
}
QProgressBar::chunk { background-color: %(primary)s; border-radius: 3px; }

/* ===================== Tooltip ===================== */
QToolTip {
    background-color: %(text)s;
    color: %(surface)s;
    border: 1px solid %(text)s;
    padding: 4px 8px;
    font-size: %(secondary)dpx;
    opacity: 230;
}
""" % {
    "font": FONT_FAMILY,
    "canvas": L.CANVAS,
    "surface": L.SURFACE,
    "surface_alt": L.SURFACE_ALT,
    "primary": L.PRIMARY,
    "primary_hover": L.PRIMARY_HOVER,
    "primary_light": L.PRIMARY_LIGHT,
    "primary_border": L.PRIMARY_BORDER,
    "text": L.TEXT_PRIMARY,
    "text_secondary": L.TEXT_SECONDARY,
    "text_on_primary": L.TEXT_ON_PRIMARY,
    "muted": L.TEXT_MUTED,
    "border": L.BORDER,
    "border_subtle": L.BORDER_SUBTLE,
    "scrollbar": L.SCROLLBAR,
    "scrollbar_hover": L.SCROLLBAR_HOVER,
    "body": FontSize.BODY,
    "secondary": FontSize.SECONDARY,
    "r_btn": Radius.BUTTON,
    "r_input": Radius.INPUT,
    "r_panel": Radius.PANEL,
}


# ---------------------------------------------------------------------------
# Dark theme
# ---------------------------------------------------------------------------

DARK_STYLE = """
QMainWindow {
    background-color: %(canvas)s;
    font-family: %(font)s;
}

/* ===================== Menu Bar ===================== */
QMenuBar {
    background-color: %(surface)s;
    border-bottom: 1px solid %(border)s;
    padding: 2px;
    font-size: %(body)dpx;
    font-family: %(font)s;
    color: %(text)s;
}
QMenuBar::item { padding: 4px 12px; }
QMenuBar::item:selected { background-color: %(border)s; color: %(primary)s; }

QMenu {
    background-color: %(surface)s;
    border: 1px solid %(border)s;
    padding: 4px 0;
    color: %(text)s;
    font-family: %(font)s;
}
QMenu::item { padding: 6px 32px 6px 24px; font-size: %(body)dpx; font-family: %(font)s; color: %(text)s; }
QMenu::item:selected { background-color: %(border)s; color: %(primary)s; }
QMenu::item:disabled { color: %(muted)s; }
QMenu::separator { height: 1px; background-color: %(border)s; margin: 4px 12px; }

/* ===================== Toolbar ===================== */
QToolBar {
    background-color: %(surface)s;
    border-bottom: 1px solid %(border)s;
    padding: 2px 4px;
    spacing: 2px;
}
QToolBar::separator { width: 1px; background-color: %(border)s; margin: 4px 6px; }
QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: %(r_btn)dpx;
    padding: 4px 8px;
    font-size: %(body)dpx;
    font-weight: bold;
    color: %(text)s;
    min-width: 24px;
    min-height: 24px;
}
QToolButton:hover { background-color: %(border)s; border-color: %(border_subtle)s; }
QToolButton:pressed { background-color: %(border_subtle)s; }
QToolButton:checked { background-color: %(border)s; border-color: %(primary)s; }
QToolButton::menu-indicator { subcontrol-position: right center; left: -4px; }

/* ===================== ComboBox ===================== */
QComboBox {
    border: 1px solid %(border_subtle)s;
    border-radius: %(r_input)dpx;
    padding: 3px 24px 3px 8px;
    font-size: %(secondary)dpx;
    background-color: %(surface)s;
    color: %(text)s;
    min-height: 22px;
}
QComboBox:hover { border-color: %(primary)s; }
QComboBox::drop-down { width: 18px; border-left: 1px solid %(border_subtle)s; background-color: %(surface_alt)s; }
QComboBox QAbstractItemView {
    background-color: %(surface)s;
    border: 1px solid %(border_subtle)s;
    selection-background-color: %(border)s;
    selection-color: %(primary)s;
}

/* ===================== Splitter ===================== */
QSplitter::handle { background-color: %(border)s; }
QSplitter::handle:hover { background-color: %(primary)s; }

/* ===================== Tree Widget ===================== */
QTreeWidget {
    background-color: %(surface_alt)s;
    border: none;
    border-right: 1px solid %(border)s;
    font-size: %(body)dpx;
    color: %(text)s;
}
QTreeWidget::item { padding: 4px 8px; height: 24px; }
QTreeWidget::item:selected { background-color: %(border)s; color: %(primary)s; }
QTreeWidget::item:hover { background-color: %(surface)s; }
QHeaderView::section {
    background-color: %(surface_alt)s;
    border: none;
    border-bottom: 1px solid %(border)s;
    border-right: 1px solid %(border)s;
    padding: 4px 8px;
    font-weight: bold;
    font-size: %(body)dpx;
    color: %(text)s;
}

/* ===================== Status Bar ===================== */
QStatusBar {
    background-color: %(surface_alt)s;
    border-top: 1px solid %(border)s;
    font-size: %(secondary)dpx;
    color: %(text_secondary)s;
}
QStatusBar::item { border: none; }
QLabel#statusLabel { padding: 0 10px; color: %(text_secondary)s; font-size: %(secondary)dpx; }

/* ===================== Scrollbar ===================== */
QScrollBar:vertical { background-color: %(canvas)s; width: 10px; border: none; margin: 0; }
QScrollBar::handle:vertical { background-color: %(scrollbar)s; border-radius: 5px; min-height: 30px; margin: 1px; }
QScrollBar::handle:vertical:hover { background-color: %(scrollbar_hover)s; }
QScrollBar::handle:vertical:pressed { background-color: %(text_secondary)s; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background-color: transparent; }
QScrollBar:horizontal { background-color: %(canvas)s; height: 10px; border: none; margin: 0; }
QScrollBar::handle:horizontal { background-color: %(scrollbar)s; border-radius: 5px; min-width: 30px; margin: 1px; }
QScrollBar::handle:horizontal:hover { background-color: %(scrollbar_hover)s; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: transparent; }

/* ===================== Dialog ===================== */
QDialog { background-color: %(surface)s; }

/* ===================== Button ===================== */
QPushButton {
    background-color: %(border)s;
    border: 1px solid %(border_subtle)s;
    border-radius: %(r_btn)dpx;
    padding: 5px 14px;
    font-size: %(body)dpx;
    color: %(text)s;
    min-width: 64px;
}
QPushButton:hover { background-color: %(border_subtle)s; border-color: %(muted)s; }
QPushButton:pressed { background-color: %(muted)s; }
QPushButton:disabled { color: %(muted)s; background-color: %(surface)s; border-color: %(border)s; }
QPushButton#primaryButton,
QDialogButtonBox QPushButton[text="OK"],
QDialogButtonBox QPushButton[text="确定"] {
    background-color: %(primary)s;
    border-color: %(primary)s;
    color: %(text_on_primary)s;
    font-weight: bold;
}
QPushButton#primaryButton:hover { background-color: %(primary_hover)s; }

/* ===================== Input ===================== */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    border: 1px solid %(border_subtle)s;
    border-radius: %(r_input)dpx;
    padding: 5px 8px;
    font-size: %(body)dpx;
    background-color: %(surface_alt)s;
    color: %(text)s;
    selection-background-color: %(border)s;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border-color: %(primary)s;
    background-color: %(surface)s;
}
QLineEdit:read-only { background-color: %(surface)s; color: %(muted)s; }
QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border-left: 1px solid %(border_subtle)s;
    background-color: %(surface_alt)s;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: %(border)s; }

/* ===================== Group Box ===================== */
QGroupBox {
    border: 1px solid %(border_subtle)s;
    border-radius: %(r_panel)dpx;
    margin-top: 12px;
    padding: 8px;
    font-size: %(body)dpx;
    font-weight: bold;
    color: %(text)s;
    background-color: %(surface_alt)s;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
    background-color: %(surface_alt)s;
}

/* ===================== Checkbox ===================== */
QCheckBox { font-size: %(body)dpx; color: %(text)s; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid %(muted)s;
    border-radius: 3px;
    background-color: %(surface_alt)s;
}
QCheckBox::indicator:checked { background-color: %(primary)s; border-color: %(primary)s; }
QCheckBox::indicator:hover { border-color: %(primary)s; }

/* ===================== Radio Button ===================== */
QRadioButton { font-size: %(body)dpx; color: %(text)s; spacing: 6px; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border: 1px solid %(muted)s;
    border-radius: 7px;
    background-color: %(surface_alt)s;
}
QRadioButton::indicator:checked { background-color: %(primary)s; border-color: %(primary)s; border-width: 3px; }

/* ===================== Tab Widget ===================== */
QTabWidget::pane {
    border: 1px solid %(border)s;
    border-top: none;
    background-color: %(surface)s;
    padding: 8px;
}
QTabBar::tab {
    background-color: %(surface_alt)s;
    border: 1px solid %(border)s;
    border-bottom: none;
    padding: 6px 16px;
    font-size: %(body)dpx;
    color: %(text_secondary)s;
    min-width: 60px;
}
QTabBar::tab:selected {
    background-color: %(surface)s;
    color: %(primary)s;
    border-bottom: 2px solid %(primary)s;
    font-weight: bold;
}
QTabBar::tab:hover:!selected { background-color: %(border)s; }

/* ===================== Table ===================== */
QTableWidget {
    border: 1px solid %(border)s;
    gridline-color: %(border)s;
    background-color: %(surface)s;
    font-size: %(body)dpx;
    alternate-background-color: %(surface_alt)s;
    selection-background-color: %(border)s;
    selection-color: %(text)s;
}
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:selected { background-color: %(border)s; color: %(text)s; }
QTableCornerButton::section { background-color: %(surface_alt)s; border: 1px solid %(border)s; }

/* ===================== Progress Bar ===================== */
QProgressBar {
    border: 1px solid %(border)s;
    border-radius: %(r_btn)dpx;
    background-color: %(surface_alt)s;
    text-align: center;
    font-size: %(secondary)dpx;
    color: %(text)s;
}
QProgressBar::chunk { background-color: %(primary)s; border-radius: 3px; }

/* ===================== Tooltip ===================== */
QToolTip {
    background-color: %(border)s;
    color: %(text)s;
    border: 1px solid %(border_subtle)s;
    padding: 4px 8px;
    font-size: %(secondary)dpx;
}
""" % {
    "font": FONT_FAMILY,
    "canvas": D.CANVAS,
    "surface": D.SURFACE,
    "surface_alt": D.SURFACE_ALT,
    "primary": D.PRIMARY,
    "primary_hover": D.PRIMARY_HOVER,
    "primary_light": D.PRIMARY_LIGHT,
    "primary_border": D.PRIMARY_BORDER,
    "text": D.TEXT_PRIMARY,
    "text_secondary": D.TEXT_SECONDARY,
    "text_on_primary": D.TEXT_ON_PRIMARY,
    "muted": D.TEXT_MUTED,
    "border": D.BORDER,
    "border_subtle": D.BORDER_SUBTLE,
    "scrollbar": D.SCROLLBAR,
    "scrollbar_hover": D.SCROLLBAR_HOVER,
    "body": FontSize.BODY,
    "secondary": FontSize.SECONDARY,
    "r_btn": Radius.BUTTON,
    "r_input": Radius.INPUT,
    "r_panel": Radius.PANEL,
}
