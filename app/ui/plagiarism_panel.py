"""
plagiarism_panel.py — 论文查重结果侧面板

显示查重统计、风险句列表，提供单条降重和一键降重操作。
"""

import logging

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons.plagiarism_icons import PlagiarismIcons

logger = logging.getLogger(__name__)


_RISK_COLORS = {
    "high": "#fc8181",
    "medium": "#f6ad55",
    "low": "#68d391",
}

_RISK_LABELS = {
    "high": "高风险",
    "medium": "中风险",
    "low": "低风险",
}

_PANEL_STYLE = """
QWidget#PlagiarismPanel {
    background: #fafbfc;
    border-left: 1px solid #e1e4e8;
}
"""

_CARD_HIGH = """
QFrame.risk-card {
    background: #fef0ef;
    border: 1px solid #f5c6cb;
    border-left: 4px solid #e74c3c;
    border-radius: 6px;
    margin: 4px 0;
}
"""

_BTN_PRIMARY = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #10A37F, stop:1 #0D8C6D);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
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
QPushButton:disabled { background: #cccccc; }
"""

_BTN_SECONDARY = """
QPushButton {
    background: white;
    color: #24292e;
    border: 1px solid #e1e4e8;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background: #f6f8fa;
    border-color: #d1d5da;
}
QPushButton:disabled { color: #aaa; }
"""


class _RiskCard(QFrame):
    """单条查重结果卡片。"""

    clicked = pyqtSignal(int)  # 点击时发出 index
    rewrite_clicked = pyqtSignal(int)  # 降重按钮

    def __init__(
        self,
        index: int,
        text: str,
        risk: str,
        dup_type: str,
        suggestion: str,
        sources: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self._index = index
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        color = _RISK_COLORS.get(risk, "#999")
        label = _RISK_LABELS.get(risk, risk)

        self.setStyleSheet(f"""
            QFrame {{
                background: {'#fff5f5' if risk == 'high' else '#fffbeb' if risk == 'medium' else '#f0fdf4'};
                border: 1px solid {color}30;
                border-left: 3px solid {color};
                border-radius: 8px;
                margin: 6px 0;
                padding: 12px;
            }}
            QFrame:hover {{
                background: #ffffff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 标签行
        top_row = QHBoxLayout()
        tag = QLabel(f"  {label}  ")
        tag.setStyleSheet(f"""
            QLabel {{
                background: {color};
                color: white;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
            }}
        """)
        tag.setFixedHeight(20)
        top_row.addWidget(tag)

        if dup_type:
            type_lbl = QLabel(dup_type)
            type_lbl.setStyleSheet("color: #888; font-size: 11px;")
            top_row.addWidget(type_lbl)

        top_row.addStretch()

        if risk in ("high", "medium"):
            btn_rw = QPushButton("降重")
            btn_rw.setFixedSize(52, 24)
            btn_rw.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ opacity: 0.9; }}
            """)
            btn_rw.clicked.connect(lambda: self.rewrite_clicked.emit(self._index))
            top_row.addWidget(btn_rw)

        layout.addLayout(top_row)

        # 原文（截断显示）
        display = text if len(text) <= 80 else text[:77] + "..."
        text_lbl = QLabel(display)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet("font-size: 12px; color: #333; line-height: 1.5;")
        layout.addWidget(text_lbl)

        # 建议（带图标）
        if suggestion:
            sug_row = QHBoxLayout()
            sug_row.setSpacing(4)
            sug_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.SUGGESTION, 14)
            sug_row.addWidget(sug_icon)
            sug_lbl = QLabel(suggestion)
            sug_lbl.setWordWrap(True)
            sug_lbl.setStyleSheet("font-size: 11px; color: #6a737d; font-style: italic;")
            sug_row.addWidget(sug_lbl, 1)
            sug_widget = QWidget()
            sug_widget.setLayout(sug_row)
            layout.addWidget(sug_widget)

        # 真实数据库匹配来源（带图标）
        if sources:
            for src in sources[:3]:
                title = src.get("title", "")
                url = src.get("url", "")
                source_db = src.get("source", "")
                authors = src.get("authors", "")
                year = src.get("year", "")
                # 构建显示文本
                display_parts = []
                if authors:
                    display_parts.append(authors)
                if year:
                    display_parts.append(f"({year})")
                meta = " ".join(display_parts)
                # 截断标题
                short_title = title if len(title) <= 60 else title[:57] + "..."

                src_row = QHBoxLayout()
                src_row.setSpacing(4)
                src_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.SOURCE, 14)
                src_row.addWidget(src_icon)

                if url:
                    src_lbl = QLabel(
                        f'<a href="{url}" style="color:#0366d6;'
                        f'text-decoration:none;">{short_title}</a>'
                        f' <span style="color:#999;font-size:10px;">'
                        f"{meta} · {source_db}</span>"
                    )
                    src_lbl.setOpenExternalLinks(True)
                else:
                    src_lbl = QLabel(
                        f"{short_title}"
                        f' <span style="color:#999;font-size:10px;">'
                        f"{meta} · {source_db}</span>"
                    )
                src_lbl.setTextFormat(Qt.TextFormat.RichText)
                src_lbl.setWordWrap(True)
                src_lbl.setStyleSheet("font-size: 11px; color: #555; padding: 1px 0;")
                src_row.addWidget(src_lbl, 1)
                src_widget = QWidget()
                src_widget.setLayout(src_row)
                layout.addWidget(src_widget)

    def mousePressEvent(self, event):
        self.clicked.emit(self._index)
        super().mousePressEvent(event)


class PlagiarismPanel(QWidget):
    """右侧查重结果面板。"""

    # 信号
    sentence_clicked = pyqtSignal(int)  # 点击某条 → 跳到编辑器
    rewrite_one = pyqtSignal(int)  # 降重单条
    rewrite_all = pyqtSignal()  # 一键降重全部
    smart_rewrite = pyqtSignal()  # 智能降重（迭代）
    recheck = pyqtSignal()  # 重新检测

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlagiarismPanel")
        self.setStyleSheet(_PANEL_STYLE)
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        self._results = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 标题（带图标）
        title_row = QHBoxLayout()
        title_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.CHECK, 20)
        title_row.addWidget(title_icon)
        title = QLabel("论文查重分析")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #24292e; margin-left: 6px;")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        # 提示信息（带图标）
        hint_row = QHBoxLayout()
        info_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.INFO, 14)
        hint_row.addWidget(info_icon)
        self._hint = QLabel("基于 Semantic Scholar / CrossRef 学术数据库 + AI 语义分析")
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #999; font-size: 11px; margin-bottom: 4px; margin-left: 4px;")
        hint_row.addWidget(self._hint)
        hint_row.addStretch()
        layout.addLayout(hint_row)

        # 统计区
        self._stats_widget = QWidget()
        stats_layout = QVBoxLayout(self._stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(6)

        self._rate_label = QLabel("查重率：--")
        self._rate_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #24292e;")
        stats_layout.addWidget(self._rate_label)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(12)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar {
                background: #e1e4e8;
                border: none;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #68d391, stop:0.5 #f6ad55, stop:1 #fc8181);
                border-radius: 6px;
            }
        """)
        stats_layout.addWidget(self._progress)

        # 风险数统计（带图标）
        self._count_row = QHBoxLayout()

        # 高风险
        high_row = QHBoxLayout()
        high_row.setSpacing(4)
        high_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.HIGH_RISK, 16)
        high_row.addWidget(high_icon)
        self._high_label = QLabel("高: 0")
        self._high_label.setStyleSheet("font-size: 13px; color: #fc8181; font-weight: 500;")
        high_row.addWidget(self._high_label)
        high_widget = QWidget()
        high_widget.setLayout(high_row)
        self._count_row.addWidget(high_widget)

        # 中风险
        med_row = QHBoxLayout()
        med_row.setSpacing(4)
        med_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.MEDIUM_RISK, 16)
        med_row.addWidget(med_icon)
        self._med_label = QLabel("中: 0")
        self._med_label.setStyleSheet("font-size: 13px; color: #f6ad55; font-weight: 500;")
        med_row.addWidget(self._med_label)
        med_widget = QWidget()
        med_widget.setLayout(med_row)
        self._count_row.addWidget(med_widget)

        # 低风险
        low_row = QHBoxLayout()
        low_row.setSpacing(4)
        low_icon = PlagiarismIcons.create_icon_label(PlagiarismIcons.LOW_RISK, 16)
        low_row.addWidget(low_icon)
        self._low_label = QLabel("低: 0")
        self._low_label.setStyleSheet("font-size: 13px; color: #68d391; font-weight: 500;")
        low_row.addWidget(self._low_label)
        low_widget = QWidget()
        low_widget.setLayout(low_row)
        self._count_row.addWidget(low_widget)

        self._count_row.addStretch()
        stats_layout.addLayout(self._count_row)

        layout.addWidget(self._stats_widget)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        # 滚动列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, 1)

        # 底部按钮
        btn_row = QHBoxLayout()

        # 智能降重按钮（带图标）
        self._btn_smart_rewrite = QPushButton()
        smart_icon = PlagiarismIcons.get_icon(PlagiarismIcons.SMART_REWRITE)
        self._btn_smart_rewrite.setIcon(smart_icon)
        self._btn_smart_rewrite.setIconSize(smart_icon.actualSize(smart_icon.availableSizes()[0]) if smart_icon.availableSizes() else smart_icon.actualSize(QSize(16, 16)))
        self._btn_smart_rewrite.setText(" 智能降重")
        self._btn_smart_rewrite.setToolTip("自动迭代降重直到达到目标重复率")
        self._btn_smart_rewrite.setStyleSheet(_BTN_PRIMARY)
        self._btn_smart_rewrite.clicked.connect(self.smart_rewrite.emit)
        self._btn_smart_rewrite.setEnabled(False)
        btn_row.addWidget(self._btn_smart_rewrite)

        # 一键降重按钮（带图标）
        self._btn_rewrite_all = QPushButton()
        quick_icon = PlagiarismIcons.get_icon(PlagiarismIcons.QUICK_REWRITE)
        self._btn_rewrite_all.setIcon(quick_icon)
        self._btn_rewrite_all.setIconSize(quick_icon.actualSize(quick_icon.availableSizes()[0]) if quick_icon.availableSizes() else quick_icon.actualSize(QSize(16, 16)))
        self._btn_rewrite_all.setText(" 一键降重")
        self._btn_rewrite_all.setStyleSheet(_BTN_SECONDARY)
        self._btn_rewrite_all.clicked.connect(self.rewrite_all.emit)
        self._btn_rewrite_all.setEnabled(False)
        btn_row.addWidget(self._btn_rewrite_all)
        layout.addLayout(btn_row)

        # 第二行按钮
        btn_row2 = QHBoxLayout()
        self._btn_recheck = QPushButton()
        refresh_icon = PlagiarismIcons.get_icon(PlagiarismIcons.REFRESH)
        self._btn_recheck.setIcon(refresh_icon)
        self._btn_recheck.setIconSize(refresh_icon.actualSize(refresh_icon.availableSizes()[0]) if refresh_icon.availableSizes() else refresh_icon.actualSize(QSize(16, 16)))
        self._btn_recheck.setText(" 重新检测")
        self._btn_recheck.setStyleSheet(_BTN_SECONDARY)
        self._btn_recheck.clicked.connect(self.recheck.emit)
        btn_row2.addWidget(self._btn_recheck)
        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        # 初始提示
        self._empty_label = QLabel("点击工具栏「查重」按钮\n开始检测论文重复率")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #bbb; font-size: 13px; padding: 40px 0;")
        # 插入到列表区之前 (stretch 之前)
        self._list_layout.insertWidget(0, self._empty_label)

    def set_loading(self):
        """显示正在检测状态。"""
        self._clear_cards()
        self._rate_label.setText("查重率：检测中...")
        self._progress.setValue(0)
        self._empty_label.setText("⏳ 正在分析文档...\n请稍候")
        self._empty_label.show()
        self._btn_rewrite_all.setEnabled(False)
        self._btn_smart_rewrite.setEnabled(False)

    def set_loading_status(self, text: str):
        """更新检测中的分阶段状态文字。"""
        self._empty_label.setText(text)
        self._empty_label.show()

    def set_results(self, results: list):
        """接收 CheckResult 列表，更新面板。"""
        self._results = results
        self._clear_cards()
        self._empty_label.hide()

        high = sum(1 for r in results if r.risk == "high")
        med = sum(1 for r in results if r.risk == "medium")
        low = sum(1 for r in results if r.risk == "low")
        total = len(results)

        # 计算模拟重复率
        rate = 0
        if total > 0:
            rate = int((high * 1.0 + med * 0.5) / total * 100)
        self._rate_label.setText(f"查重率：约 {rate}%")
        color = "#fc8181" if rate > 30 else "#f6ad55" if rate > 15 else "#68d391"
        self._rate_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        self._progress.setValue(min(rate, 100))

        self._high_label.setText(f"高: {high}")
        self._med_label.setText(f"中: {med}")
        self._low_label.setText(f"低: {low}")

        # 按风险排序：high > medium > low
        order = {"high": 0, "medium": 1, "low": 2}
        sorted_results = sorted(results, key=lambda r: order.get(r.risk, 3))

        for r in sorted_results:
            if r.risk == "low":
                continue  # 低风险不显示卡片
            card = _RiskCard(
                r.index,
                r.text,
                r.risk,
                r.dup_type,
                r.suggestion,
                sources=getattr(r, "sources", None) or [],
            )
            card.clicked.connect(self.sentence_clicked.emit)
            card.rewrite_clicked.connect(self.rewrite_one.emit)
            # 在 stretch 之前插入
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

        self._btn_rewrite_all.setEnabled(high + med > 0)
        self._btn_smart_rewrite.setEnabled(high + med > 0)

    def set_iterative_progress(self, info: dict):
        """显示迭代降重进度。

        Args:
            info: 进度信息字典，包含 stage, iteration, count 等
        """
        stage = info.get("stage", "")
        iteration = info.get("iteration", 0)

        if stage == "checking":
            self._rate_label.setText(f"第 {iteration} 轮查重中...")
            self._rate_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db;")
        elif stage == "rewriting":
            count = info.get("count", 0)
            self._rate_label.setText(f"第 {iteration} 轮降重中 ({count} 句)...")
            self._rate_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #9b59b6;")
        elif stage == "verifying":
            self._rate_label.setText(f"第 {iteration} 轮验证中...")
            self._rate_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f39c12;")

    def set_iteration_result(self, info: dict):
        """显示单次迭代结果。

        Args:
            info: 迭代结果字典，包含 iteration, rate_before, rate_after, rewritten 等
        """
        iteration = info.get("iteration", 0)
        rate_before = info.get("rate_before", 0)
        rate_after = info.get("rate_after", rate_before)
        rewritten = info.get("rewritten", 0)

        # 更新进度条
        self._progress.setValue(min(int(rate_after * 100), 100))

        # 显示迭代信息
        self._hint.setText(
            f"✅ 第 {iteration} 轮完成：改写 {rewritten} 句，"
            f"重复率 {int(rate_before*100)}% → {int(rate_after*100)}%"
        )
        self._hint.setStyleSheet("color: #68d391; font-size: 11px; margin-bottom: 4px;")

    def set_smart_rewrite_complete(self, success: bool, final_rate: float, iterations: int):
        """显示智能降重完成状态。

        Args:
            success: 是否达到目标
            final_rate: 最终重复率
            iterations: 迭代次数
        """
        rate_pct = int(final_rate * 100)
        if success:
            self._rate_label.setText(f"查重率：约 {rate_pct}% ✅")
            self._rate_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #68d391;")
            self._hint.setText(f"🎉 智能降重完成！经过 {iterations} 轮迭代，已达到目标重复率")
        else:
            color = "#fc8181" if rate_pct > 30 else "#f6ad55" if rate_pct > 15 else "#68d391"
            self._rate_label.setText(f"查重率：约 {rate_pct}%")
            self._rate_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            self._hint.setText(f"⚠️ 经过 {iterations} 轮迭代，未达到目标。建议手动调整或使用激进模式")
        self._hint.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 4px;")
        self._progress.setValue(min(rate_pct, 100))

    def _clear_cards(self):
        """清除所有卡片（保留 stretch 和 empty_label）。"""
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            w = item.widget()
            if w and w is not self._empty_label:
                w.deleteLater()
            elif w is self._empty_label:
                self._list_layout.insertWidget(0, self._empty_label)
                break

    def clear(self):
        """完全重置面板。"""
        self._results = []
        self._clear_cards()
        self._rate_label.setText("查重率：--")
        self._progress.setValue(0)
        self._high_label.setText("高: 0")
        self._med_label.setText("中: 0")
        self._low_label.setText("低: 0")
        self._empty_label.setText("点击工具栏「查重」按钮\n开始检测论文重复率")
        self._empty_label.show()
        self._btn_rewrite_all.setEnabled(False)
        self._btn_smart_rewrite.setEnabled(False)

    def get_results(self) -> list:
        return self._results
