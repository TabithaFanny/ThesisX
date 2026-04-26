"""
iterative_rewrite_dialog.py — 迭代降重设置对话框

提供智能降重的配置界面：目标重复率、迭代次数、降重模式等。
"""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from app.core.plagiarism_service import IterativeRewriteConfig
from app.ui.icons.plagiarism_icons import PlagiarismIcons


_BTN_PRIMARY = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #10A37F, stop:1 #0D8C6D);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0D8C6D, stop:1 #0A7A5E);
}
QPushButton:pressed {
    background: #0A7A5E;
}
"""

_BTN_SECONDARY = """
QPushButton {
    background: white;
    color: #24292e;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background: #f6f8fa;
    border-color: #d1d5da;
}
"""

_GROUP_STYLE = """
QGroupBox {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    font-size: 14px;
    font-weight: 600;
    color: #24292e;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background: #fafbfc;
}
"""

_SPIN_STYLE = """
QSpinBox {
    background: white;
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #24292e;
}
QSpinBox:focus {
    border-color: #0366d6;
}
"""

_RADIO_STYLE = """
QRadioButton {
    font-size: 13px;
    color: #24292e;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
}
QRadioButton::indicator:unchecked {
    border: 2px solid #d1d5da;
    border-radius: 9px;
    background: white;
}
QRadioButton::indicator:checked {
    border: 2px solid #10A37F;
    border-radius: 9px;
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
        fx:0.5, fy:0.5, stop:0 #10A37F, stop:0.5 #10A37F, stop:0.6 white);
}
"""

_CHECKBOX_STYLE = """
QCheckBox {
    font-size: 13px;
    color: #24292e;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}
QCheckBox::indicator:unchecked {
    border: 2px solid #d1d5da;
    border-radius: 4px;
    background: white;
}
QCheckBox::indicator:checked {
    border: 2px solid #10A37F;
    border-radius: 4px;
    background: #10A37F;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMiA2bDMgMyA1LTUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
}
"""


class IterativeRewriteDialog(QDialog):
    """迭代降重设置对话框。"""

    def __init__(self, current_rate: float, high_count: int, med_count: int, parent=None):
        """初始化对话框。

        Args:
            current_rate: 当前重复率 (0.0 - 1.0)
            high_count: 高风险句子数
            med_count: 中风险句子数
            parent: 父窗口
        """
        super().__init__(parent)
        self._current_rate = current_rate
        self._high_count = high_count
        self._med_count = med_count
        self.setWindowTitle("智能降重设置")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # 当前状态
        status_group = QGroupBox("当前状态")
        status_group.setStyleSheet(_GROUP_STYLE)
        status_layout = QVBoxLayout(status_group)

        rate_pct = int(self._current_rate * 100)
        color = "#fc8181" if rate_pct > 30 else "#f6ad55" if rate_pct > 15 else "#68d391"
        rate_label = QLabel(f"当前重复率：��� {rate_pct}%")
        rate_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        status_layout.addWidget(rate_label)

        count_label = QLabel(f"高风险: {self._high_count} 句　中风险: {self._med_count} 句")
        count_label.setStyleSheet("font-size: 13px; color: #666;")

        # 添加风险图标
        count_row = QHBoxLayout()
        high_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.HIGH_RISK, 14)
        count_row.addWidget(high_icon)
        high_label = QLabel(f"高风险: {self._high_count} 句")
        high_label.setStyleSheet("font-size: 13px; color: #fc8181; margin-left: 4px;")
        count_row.addWidget(high_label)
        count_row.addSpacing(16)
        med_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.MEDIUM_RISK, 14)
        count_row.addWidget(med_icon)
        med_label = QLabel(f"中风险: {self._med_count} 句")
        med_label.setStyleSheet("font-size: 13px; color: #f6ad55; margin-left: 4px;")
        count_row.addWidget(med_label)
        count_row.addStretch()
        status_layout.addLayout(count_row)

        layout.addWidget(status_group)

        # 目标设置
        target_group = QGroupBox("目标设置")
        target_group.setStyleSheet(_GROUP_STYLE)
        target_layout = QFormLayout(target_group)
        target_layout.setSpacing(12)

        self._target_spin = QSpinBox()
        self._target_spin.setRange(5, 30)
        self._target_spin.setValue(15)
        self._target_spin.setSuffix("%")
        self._target_spin.setFixedWidth(100)
        self._target_spin.setStyleSheet(_SPIN_STYLE)
        target_layout.addRow("目标重复率:", self._target_spin)

        self._max_iter_spin = QSpinBox()
        self._max_iter_spin.setRange(1, 5)
        self._max_iter_spin.setValue(3)
        self._max_iter_spin.setSuffix(" 轮")
        self._max_iter_spin.setFixedWidth(100)
        self._max_iter_spin.setStyleSheet(_SPIN_STYLE)
        target_layout.addRow("最大迭代次数:", self._max_iter_spin)

        layout.addWidget(target_group)

        # 降重模式（带图标）
        mode_group = QGroupBox("降重模式")
        mode_group.setStyleSheet(_GROUP_STYLE)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(8)

        # 标准模式
        normal_row = QHBoxLayout()
        normal_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.MODE_STANDARD, 18)
        normal_row.addWidget(normal_icon)
        self._mode_normal = QRadioButton("标准模式 — 平衡改写幅度和原意保持")
        self._mode_normal.setChecked(True)
        self._mode_normal.setStyleSheet(_RADIO_STYLE)
        normal_row.addWidget(self._mode_normal)
        normal_row.addStretch()
        mode_layout.addLayout(normal_row)

        # 激进模式
        aggressive_row = QHBoxLayout()
        aggressive_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.MODE_AGGRESSIVE, 18)
        aggressive_row.addWidget(aggressive_icon)
        self._mode_aggressive = QRadioButton("激进模式 — 更大幅度改写，降重效果更好")
        self._mode_aggressive.setStyleSheet(_RADIO_STYLE)
        aggressive_row.addWidget(self._mode_aggressive)
        aggressive_row.addStretch()
        mode_layout.addLayout(aggressive_row)

        # 保守模式
        conservative_row = QHBoxLayout()
        conservative_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.MODE_CONSERVATIVE, 18)
        conservative_row.addWidget(conservative_icon)
        self._mode_conservative = QRadioButton("保守模式 — 最小改动，优先保持原意")
        self._mode_conservative.setStyleSheet(_RADIO_STYLE)
        conservative_row.addWidget(self._mode_conservative)
        conservative_row.addStretch()
        mode_layout.addLayout(conservative_row)

        layout.addWidget(mode_group)

        # 高级选项
        options_group = QGroupBox("高级选项")
        options_group.setStyleSheet(_GROUP_STYLE)
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(8)

        self._verify_check = QCheckBox("每次降重后自动验证效果")
        self._verify_check.setChecked(True)
        self._verify_check.setStyleSheet(_CHECKBOX_STYLE)
        options_layout.addWidget(self._verify_check)

        self._use_paper_db = QCheckBox("使用论文数据库增强（推荐，参考真实论文表达）")
        self._use_paper_db.setChecked(True)
        self._use_paper_db.setStyleSheet(_CHECKBOX_STYLE)
        options_layout.addWidget(self._use_paper_db)

        self._include_medium = QCheckBox("同时处理中风险句子（默认只处理高风险）")
        self._include_medium.setChecked(True)
        self._include_medium.setStyleSheet(_CHECKBOX_STYLE)
        options_layout.addWidget(self._include_medium)

        layout.addWidget(options_group)

        # 说明（带图标）
        hint_row = QHBoxLayout()
        info_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.INFO, 16)
        hint_row.addWidget(info_icon)
        hint = QLabel(
            "智能降重会自动迭代：查重 → 降重 → 验证 → 循环，直到达到目标重复率或达到最大迭代次数。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 12px; color: #888; padding: 8px 0; margin-left: 4px;")
        hint_row.addWidget(hint, 1)
        layout.addLayout(hint_row)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.setStyleSheet(_BTN_SECONDARY)
        self._btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_cancel)

        btn_layout.addStretch()

        self._btn_start = QPushButton()
        start_icon = PlagiarismIcons.get_icon(PlagiarismIcons.SMART_REWRITE)
        self._btn_start.setIcon(start_icon)
        self._btn_start.setIconSize(start_icon.actualSize(start_icon.availableSizes()[0]) if start_icon.availableSizes() else start_icon.actualSize(QSize(16, 16)))
        self._btn_start.setText(" 开始智能降重")
        self._btn_start.setStyleSheet(_BTN_PRIMARY)
        self._btn_start.clicked.connect(self.accept)
        btn_layout.addWidget(self._btn_start)

        layout.addLayout(btn_layout)

    def get_config(self) -> IterativeRewriteConfig:
        """获取用户配置。

        Returns:
            IterativeRewriteConfig 对象
        """
        # 确定降重阈值
        threshold = "medium" if self._include_medium.isChecked() else "high"

        return IterativeRewriteConfig(
            target_rate=self._target_spin.value() / 100,
            max_iterations=self._max_iter_spin.value(),
            rewrite_threshold=threshold,
            verify_after_rewrite=self._verify_check.isChecked(),
            aggressive_mode=self._mode_aggressive.isChecked(),
            use_paper_db=self._use_paper_db.isChecked(),
        )

    def is_conservative_mode(self) -> bool:
        """是否为保守模式。"""
        return self._mode_conservative.isChecked()
