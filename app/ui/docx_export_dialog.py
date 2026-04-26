"""
docx_export_dialog.py — 强化版 DOCX 导出选项对话框
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
)

from app.core.docx_exporter_v2 import (
    PRESETS,
    TABLE_STYLE_FULL,
    TABLE_STYLE_THREELINE,
)


class DocxExportDialog(QDialog):
    """
    导出选项对话框。

    属性（accept() 后读取）：
        style           str   — 样式预设键 ("academic"/"modern"/"classic")
        title           str   — 文档标题
        author          str   — 作者
        add_cover       bool  — 是否生成封面
        add_toc         bool  — 是否插入目录
        add_page_numbers bool — 是否加页码
        table_style     str   — 表格样式 ("threeline"/"full")
    """

    def __init__(self, parent=None, default_title: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("导出 Word 强化版")
        self.setMinimumWidth(400)
        self.setModal(True)

        # ── 输出属性（用于外部读取） ───────────────────────────────────
        self.style = "academic"
        self.title = default_title
        self.author = ""
        self.add_cover = False
        self.add_toc = False
        self.add_page_numbers = True
        self.table_style = TABLE_STYLE_THREELINE

        self._build_ui(default_title)

    # ------------------------------------------------------------------

    def _build_ui(self, default_title: str) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # ── 样式预设 ──────────────────────────────────────────────────
        grp_style = QGroupBox("样式预设")
        fl_style = QFormLayout(grp_style)
        self._combo_style = QComboBox()
        for key, info in PRESETS.items():
            self._combo_style.addItem(info["label"], userData=key)
        fl_style.addRow("文档风格：", self._combo_style)
        root.addWidget(grp_style)

        # ── 文档信息 ──────────────────────────────────────────────────
        grp_info = QGroupBox("文档信息")
        fl_info = QFormLayout(grp_info)
        self._edit_title = QLineEdit(default_title)
        self._edit_author = QLineEdit()
        self._edit_title.setPlaceholderText("可留空")
        self._edit_author.setPlaceholderText("可留空")
        fl_info.addRow("标题：", self._edit_title)
        fl_info.addRow("作者：", self._edit_author)
        root.addWidget(grp_info)

        # ── 页面选项 ──────────────────────────────────────────────────
        grp_page = QGroupBox("页面选项")
        vl_page = QVBoxLayout(grp_page)
        self._chk_cover = QCheckBox("生成封面页（标题 + 作者 + 日期）")
        self._chk_toc = QCheckBox("插入目录（需在 Word 中按 F9 更新）")
        self._chk_pagenum = QCheckBox("页脚显示页码")
        self._chk_pagenum.setChecked(True)
        vl_page.addWidget(self._chk_cover)
        vl_page.addWidget(self._chk_toc)
        vl_page.addWidget(self._chk_pagenum)
        root.addWidget(grp_page)

        # ── 表格样式 ──────────────────────────────────────────────────
        grp_tbl = QGroupBox("表格样式")
        vl_tbl = QVBoxLayout(grp_tbl)
        self._btn_grp = QButtonGroup(self)
        self._radio_3ln = QRadioButton("三线表（学术风格，顶底粗线 + 标题底细线）")
        self._radio_full = QRadioButton("全边框表（每格均有边框）")
        self._radio_3ln.setChecked(True)
        self._btn_grp.addButton(self._radio_3ln, 0)
        self._btn_grp.addButton(self._radio_full, 1)
        vl_tbl.addWidget(self._radio_3ln)
        vl_tbl.addWidget(self._radio_full)
        root.addWidget(grp_tbl)

        # ── 提示 ──────────────────────────────────────────────────────
        hint = QLabel(
            "<small>提示：导出后用 Microsoft Word 打开可获得最佳效果。"
            "目录字段需在 Word 中按 <b>Ctrl+A → F9</b> 刷新。</small>"
        )
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(hint)

        # ── 按钮 ──────────────────────────────────────────────────────
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText("导出")
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        root.addWidget(btn_box)

    # ------------------------------------------------------------------

    def _on_accept(self) -> None:
        """Collect widget values into public attributes, then accept."""
        self.style = self._combo_style.currentData() or "academic"
        self.title = self._edit_title.text().strip()
        self.author = self._edit_author.text().strip()
        self.add_cover = self._chk_cover.isChecked()
        self.add_toc = self._chk_toc.isChecked()
        self.add_page_numbers = self._chk_pagenum.isChecked()
        self.table_style = (
            TABLE_STYLE_THREELINE if self._radio_3ln.isChecked() else TABLE_STYLE_FULL
        )
        self.accept()
