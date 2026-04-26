"""
ai_dialog.py — AI 写作助手对话框

提供三种模式：
  · 优化选中内容
  · 续写论文
  · 自定义 AI 指令
支持流式输出、一键采纳结果。
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.ai_service import (
    AiWorker,
    build_continue_messages,
    build_custom_edit_messages,
    build_optimize_messages,
)

logger = logging.getLogger(__name__)


class AiDialog(QDialog):
    """AI 写作助手浮动对话框。"""

    # 当用户点击"采纳"时发出，携带最终文本和模式
    accepted_result = pyqtSignal(str, str)  # (text, mode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 写作助手")
        self.setMinimumSize(600, 500)
        self.resize(680, 560)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self._worker: AiWorker | None = None
        self._mode = ""  # "optimize" | "continue" | "custom"
        self._source_text = ""  # 原始文本（用于对比）
        self._full_response = ""

        self._init_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── 标题 ──
        title = QLabel("✦ AI 写作助手")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #6C5CE7;")
        layout.addWidget(title)

        # ── 自定义指令输入 ──
        self._instruction_row = QWidget()
        row_layout = QHBoxLayout(self._instruction_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(QLabel("AI 指令:"))
        self._instruction_input = QLineEdit()
        self._instruction_input.setPlaceholderText(
            "例如：将这段文字改写为更正式的学术语言 / 添加过渡句 / 精简为 200 字..."
        )
        self._instruction_input.returnPressed.connect(self._on_custom_send)
        row_layout.addWidget(self._instruction_input)
        self._send_btn = QPushButton("发送")
        self._send_btn.setFixedWidth(60)
        self._send_btn.clicked.connect(self._on_custom_send)
        row_layout.addWidget(self._send_btn)
        layout.addWidget(self._instruction_row)
        self._instruction_row.hide()

        # ── 状态提示 ──
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self._status_label)

        # ── AI 输出区域 ──
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("Microsoft YaHei", 12))
        self._output.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
                color: #333333;
            }
        """)
        self._output.setPlaceholderText("AI 输出将显示在这里...")
        layout.addWidget(self._output)

        # ── 按钮栏 ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._accept_btn = QPushButton("✓ 采纳结果")
        self._accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5A4BD1; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self._accept_btn.clicked.connect(self._on_accept)
        self._accept_btn.setEnabled(False)

        self._copy_btn = QPushButton("复制")
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self._copy_btn.clicked.connect(self._on_copy)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)

        self._close_btn = QPushButton("关闭")
        self._close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
        """)
        self._close_btn.clicked.connect(self.close)

        btn_layout.addWidget(self._accept_btn)
        btn_layout.addWidget(self._copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Public API — 启动不同模式
    # ------------------------------------------------------------------

    def start_optimize(self, selected_text: str):
        """优化选中内容。"""
        if not selected_text.strip():
            self._status_label.setText("⚠ 请先选中需要优化的文本")
            return
        self._mode = "optimize"
        self._source_text = selected_text
        self._instruction_row.hide()
        self._status_label.setText("🔄 正在优化选中内容...")
        self._output.clear()
        self._run(build_optimize_messages(selected_text))

    def start_continue(self, context_text: str):
        """续写论文内容。"""
        self._mode = "continue"
        self._source_text = context_text
        self._instruction_row.hide()
        self._status_label.setText("🔄 正在续写论文内容...")
        self._output.clear()
        self._run(build_continue_messages(context_text))

    def start_custom(self, selected_text: str):
        """自定义 AI 指令模式。"""
        self._mode = "custom"
        self._source_text = selected_text
        self._instruction_row.show()
        self._instruction_input.clear()
        self._instruction_input.setFocus()
        self._status_label.setText("请输入 AI 指令，然后点击发送")
        self._output.clear()
        self._accept_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_custom_send(self):
        instruction = self._instruction_input.text().strip()
        if not instruction:
            self._status_label.setText("⚠ 请输入 AI 指令")
            return
        self._status_label.setText("🔄 正在处理...")
        self._output.clear()
        self._run(build_custom_edit_messages(self._source_text, instruction))

    def _run(self, messages: list):
        # 取消之前的任务
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

        self._full_response = ""
        self._accept_btn.setEnabled(False)

        self._worker = AiWorker(messages, parent=self)
        self._worker.chunk_received.connect(self._on_chunk)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.status_update.connect(self._status_label.setText)
        self._worker.start()

    def _on_chunk(self, text: str):
        self._full_response += text
        # 追加文本到输出区域
        cursor = self._output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _on_finished(self, full_text: str):
        self._full_response = full_text
        self._accept_btn.setEnabled(True)
        mode_name = {
            "optimize": "优化",
            "continue": "续写",
            "custom": "处理",
        }.get(self._mode, "处理")
        self._status_label.setText(f"✓ {mode_name}完成！点击「采纳结果」应用到文档")

    def _on_error(self, error_msg: str):
        self._status_label.setText(f"✗ 错误: {error_msg}")
        self._accept_btn.setEnabled(False)
        logger.warning("AI 服务错误: %s", error_msg)

    def _on_accept(self):
        if self._full_response:
            self.accepted_result.emit(self._full_response, self._mode)
            self.close()

    def _on_copy(self):
        if self._full_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._full_response)
            self._status_label.setText("✓ 已复制到剪贴板")

    def _on_cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._status_label.setText("已取消")
            self._accept_btn.setEnabled(False)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)
