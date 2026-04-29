"""AgentTeamDialog — three-stage UI for the AI paper draft assistant.

Stage 0: Configuration (topic, journal, mode, budget, agent team path)
Stage 1: Progress (6-agent progress, cost, log)
Stage 2: Result (preview, quality check, compliance, import)

Also contains AgentTeamWorker (QThread) that drives the async pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.config import Config
from app.core.pipeline.events import (
    AGENT_LABELS,
    STAGE_PROGRESS,
    PaperEvent,
    make_error_event,
)
from app.core.pipeline.models import PaperRequest, RunMode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AgentTeamWorker — QThread that runs the async pipeline
# ---------------------------------------------------------------------------


class AgentTeamWorker(QThread):
    """Background thread that drives the AgentTeamRunner async pipeline."""

    event_received = pyqtSignal(object)  # PaperEvent
    error_occurred = pyqtSignal(str)
    paper_ready = pyqtSignal(str, str, float)  # markdown, session_id, cost

    def __init__(self, request: PaperRequest, parent: QWidget | None = None):
        super().__init__(parent)
        self._request = request
        self._runner: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[None] | None = None

    def run(self) -> None:
        """Thread entry — create event loop and run pipeline."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._task = self._loop.create_task(self._run_pipeline())
            self._loop.run_until_complete(self._task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            # Cancel any remaining tasks
            for task in asyncio.all_tasks(self._loop):
                task.cancel()
            self._loop.close()

    async def _run_pipeline(self) -> None:
        """Create runner and consume the event stream."""
        # Lazy import — avoid importing Agent Team at module level
        from app.core.pipeline.agent_team_runner import AgentTeamRunner

        self._runner = AgentTeamRunner()
        markdown = ""
        session_id = ""
        total_cost = 0.0

        try:
            async for event in self._runner.run(self._request):
                self.event_received.emit(event)

                # Track completion data
                if event.type == "completion":
                    markdown = event.payload.get("markdown", "")
                    session_id = event.payload.get("session_id", "")
                    total_cost = event.payload.get("total_cost_cny", 0.0)
        except asyncio.CancelledError:
            return
        except Exception as e:
            self.error_occurred.emit(str(e))
            return

        if markdown:
            self.paper_ready.emit(markdown, session_id, total_cost)

    def cancel(self) -> None:
        """Request cancellation."""
        if self._runner:
            self._runner.cancel()
        if self._task and not self._task.done():
            # Schedule task cancellation on the event loop
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._task.cancel)


# ---------------------------------------------------------------------------
# Compliance text
# ---------------------------------------------------------------------------

_COMPLIANCE_TEXT = (
    "本功能用于论文初稿与学术写作辅助。请用户自行核查文献真实性、数据来源、"
    "引用格式与学术规范，不建议将 AI 生成内容直接提交。"
)

_MOCK_EXTRA_TEXT = (
    "当前为 Mock 演示模式，内容与文献仅用于流程预览，不可作为正式论文依据。"
)

_LITERATURE_TEXT = (
    "当前版本不会自动验证参考文献真实性，请在正式使用前手动核查作者、标题、"
    "期刊、年份、DOI 与引用格式。"
)


# ---------------------------------------------------------------------------
# AgentTeamDialog
# ---------------------------------------------------------------------------


class AgentTeamDialog(QWidget):
    """Three-stage dialog for AI paper draft generation.

    Signals:
        paper_import_requested: emitted when user clicks "导入编辑器"
    """

    paper_import_requested = pyqtSignal(str, str)  # markdown, import_mode

    def __init__(self, config: Config, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self._worker: AgentTeamWorker | None = None
        self._result_markdown: str = ""
        self._result_session_id: str = ""
        self._result_cost: float = 0.0
        self._log_line_count = 0
        self._max_log_lines = 500

        self.setWindowTitle("AI 论文初稿助手")
        self.setMinimumSize(800, 600)
        self._init_ui()
        self._load_saved_config()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_config_page())
        self._stack.addWidget(self._create_progress_page())
        self._stack.addWidget(self._create_result_page())
        layout.addWidget(self._stack)

    def _create_config_page(self) -> QWidget:
        """Stage 0: Configuration page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Topic
        topic_group = QGroupBox("研究课题")
        topic_layout = QVBoxLayout(topic_group)
        self._topic_edit = QTextEdit()
        self._topic_edit.setPlaceholderText("请输入研究课题，例如：数字政府背景下基层治理能力提升路径研究")
        self._topic_edit.setMaximumHeight(100)
        topic_layout.addWidget(self._topic_edit)
        layout.addWidget(topic_group)

        # Settings grid
        settings_group = QGroupBox("生成设置")
        settings_layout = QVBoxLayout(settings_group)

        # Row 1: Generation type + Journal
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("生成类型:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["论文初稿", "文献综述（开发中）", "开题报告（开发中）", "研究计划（开发中）"])
        self._type_combo.model().item(1).setEnabled(False)
        self._type_combo.model().item(2).setEnabled(False)
        self._type_combo.model().item(3).setEnabled(False)
        row1.addWidget(self._type_combo)

        row1.addWidget(QLabel("目标风格:"))
        self._journal_combo = QComboBox()
        self._journal_combo.addItems(["中文核心", "CSSCI", "本科课程论文", "硕士论文风", "英文APA"])
        row1.addWidget(self._journal_combo)
        settings_layout.addLayout(row1)

        # Row 2: Run mode + Literature mode
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("运行模式:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Mock 演示", "Real 模式"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        row2.addWidget(self._mode_combo)

        row2.addWidget(QLabel("文献模式:"))
        self._lit_combo = QComboBox()
        self._lit_combo.addItems(["示例文献结构", "真实文献检索（V5）", "用户文献库（V3）"])
        self._lit_combo.model().item(1).setEnabled(False)
        self._lit_combo.model().item(2).setEnabled(False)
        row2.addWidget(self._lit_combo)
        settings_layout.addLayout(row2)

        # Row 3: Budget + Auto polish
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("预算上限 (¥):"))
        self._budget_spin = QDoubleSpinBox()
        self._budget_spin.setRange(0.0, 1000.0)
        self._budget_spin.setValue(
            self._config.get("agent_team_default_budget_cny", 10.0)
        )
        self._budget_spin.setPrefix("¥ ")
        row3.addWidget(self._budget_spin)

        self._polish_check = QCheckBox("自动润色")
        row3.addWidget(self._polish_check)
        row3.addStretch()
        settings_layout.addLayout(row3)

        layout.addWidget(settings_group)

        # Agent Team path
        path_group = QGroupBox("Agent Team 路径")
        path_layout = QHBoxLayout(path_group)
        self._path_label = QLabel("未选择")
        self._path_label.setWordWrap(True)
        path_layout.addWidget(self._path_label, 1)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_agent_path)
        path_layout.addWidget(browse_btn)
        layout.addWidget(path_group)

        # Info labels
        self._mode_info = QLabel()
        self._mode_info.setWordWrap(True)
        self._mode_info.setStyleSheet("color: #666; font-size: 12px;")
        self._update_mode_info()
        layout.addWidget(self._mode_info)

        # Compliance
        compliance = QLabel(_COMPLIANCE_TEXT)
        compliance.setWordWrap(True)
        compliance.setStyleSheet("color: #999; font-size: 11px; padding: 8px;")
        layout.addWidget(compliance)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._start_btn = QPushButton("开始生成")
        self._start_btn.setDefault(True)
        self._start_btn.clicked.connect(self._start_generation)
        btn_layout.addWidget(self._start_btn)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        return page

    def _create_progress_page(self) -> QWidget:
        """Stage 1: Progress page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # 6-agent status rows
        stages_group = QGroupBox("流水线进度")
        stages_layout = QVBoxLayout(stages_group)
        self._stage_labels: dict[str, QLabel] = {}
        for agent_key in ["architect", "advisor", "researcher", "writer", "reviewer", "polisher"]:
            row = QHBoxLayout()
            label = QLabel(AGENT_LABELS.get(agent_key, agent_key))
            label.setMinimumWidth(120)
            row.addWidget(label)
            status = QLabel("等待中...")
            status.setStyleSheet("color: #999;")
            row.addWidget(status, 1)
            self._stage_labels[agent_key] = status
            stages_layout.addLayout(row)
        layout.addWidget(stages_group)

        # Cost display
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("累计费用:"))
        self._cost_label = QLabel("¥ 0.00")
        cost_layout.addWidget(self._cost_label)
        cost_layout.addWidget(QLabel("/"))
        self._budget_label = QLabel("¥ 0.00")
        cost_layout.addWidget(self._budget_label)
        cost_layout.addStretch()
        layout.addLayout(cost_layout)

        # Log area
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setFont(QFont("Consolas", 10))
        self._log_text.setMaximumHeight(200)
        log_layout.addWidget(self._log_text)
        layout.addWidget(log_group)

        # Cancel button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._cancel_btn = QPushButton("取消任务")
        self._cancel_btn.clicked.connect(self._cancel_generation)
        btn_layout.addWidget(self._cancel_btn)
        layout.addLayout(btn_layout)

        return page

    def _create_result_page(self) -> QWidget:
        """Stage 2: Result page."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Header
        self._result_title = QLabel("生成完成")
        self._result_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self._result_title)

        # Stats
        self._stats_label = QLabel()
        self._stats_label.setWordWrap(True)
        layout.addWidget(self._stats_label)

        # Paper preview
        preview_group = QGroupBox("论文预览（前 5000 字）")
        preview_layout = QVBoxLayout(preview_group)
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setFont(QFont("Microsoft YaHei", 11))
        preview_layout.addWidget(self._preview_text)
        layout.addWidget(preview_group)

        # Quality check
        quality_group = QGroupBox("质量检查")
        quality_layout = QVBoxLayout(quality_group)
        self._quality_text = QTextEdit()
        self._quality_text.setReadOnly(True)
        self._quality_text.setMaximumHeight(120)
        quality_layout.addWidget(self._quality_text)
        layout.addWidget(quality_group)

        # Compliance
        self._compliance_label = QLabel()
        self._compliance_label.setWordWrap(True)
        self._compliance_label.setStyleSheet("color: #c00; font-size: 11px; padding: 8px;")
        layout.addWidget(self._compliance_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self._import_new_btn = QPushButton("导入编辑器（新建）")
        self._import_new_btn.clicked.connect(lambda: self._emit_import("new"))
        btn_layout.addWidget(self._import_new_btn)

        self._import_replace_btn = QPushButton("导入编辑器（替换）")
        self._import_replace_btn.clicked.connect(lambda: self._emit_import("replace"))
        btn_layout.addWidget(self._import_replace_btn)

        self._import_append_btn = QPushButton("导入编辑器（追加）")
        self._import_append_btn.clicked.connect(lambda: self._emit_import("append"))
        btn_layout.addWidget(self._import_append_btn)

        btn_layout.addStretch()

        self._regen_btn = QPushButton("重新生成")
        self._regen_btn.clicked.connect(self._restart)
        btn_layout.addWidget(self._regen_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        return page

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------

    def _load_saved_config(self) -> None:
        saved_path = self._config.get("agent_team_path", "")
        if saved_path:
            self._path_label.setText(saved_path)
        saved_journal = self._config.get("agent_team_default_journal", "中文核心")
        idx = self._journal_combo.findText(saved_journal)
        if idx >= 0:
            self._journal_combo.setCurrentIndex(idx)
        saved_mode = self._config.get("agent_team_default_mode", "mock")
        if saved_mode == "real":
            self._mode_combo.setCurrentIndex(1)
        saved_budget = self._config.get("agent_team_default_budget_cny", 10.0)
        self._budget_spin.setValue(saved_budget)

    def _save_config(self) -> None:
        self._config.set("agent_team_path", self._path_label.text())
        self._config.set("agent_team_default_journal", self._journal_combo.currentText())
        mode = "real" if self._mode_combo.currentIndex() == 1 else "mock"
        self._config.set("agent_team_default_mode", mode)
        self._config.set("agent_team_default_budget_cny", self._budget_spin.value())
        self._config.save()

    # ------------------------------------------------------------------
    # Config page callbacks
    # ------------------------------------------------------------------

    def _browse_agent_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择 Agent Team 目录")
        if path:
            self._path_label.setText(path)
            self._save_config()

    def _on_mode_changed(self, index: int) -> None:
        self._update_mode_info()

    def _update_mode_info(self) -> None:
        if self._mode_combo.currentIndex() == 0:
            self._mode_info.setText(
                "Mock 演示模式：使用模拟数据，无需 API Key，"
                "生成的论文仅用于流程预览，不可用于正式用途。"
            )
        else:
            self._mode_info.setText(
                "Real 模式：调用真实 LLM API 生成论文，"
                "会产生费用（受预算上限控制）。请确保已设置 OPENAI_API_KEY 环境变量。"
            )

    # ------------------------------------------------------------------
    # Validation & start
    # ------------------------------------------------------------------

    def _validate(self) -> str | None:
        """Validate inputs. Returns error message or None if OK."""
        topic = self._topic_edit.toPlainText().strip()
        if not topic:
            return "请输入研究课题。"

        agent_path = self._path_label.text()
        if agent_path == "未选择" or not agent_path.strip():
            return "请选择 Agent Team 路径。"

        if self._mode_combo.currentIndex() == 1:
            # Real mode — check for API key
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "") or os.environ.get("AI_API_KEY", "")
            if not api_key:
                return (
                    "Real 模式需要 API Key。\n"
                    "请设置环境变量 OPENAI_API_KEY 或 AI_API_KEY 后重试。"
                )

        return None

    def _start_generation(self) -> None:
        """Validate inputs and start the pipeline."""
        error = self._validate()
        if error:
            QMessageBox.warning(self, "无法启动", error)
            return

        self._save_config()
        self._reset_progress()

        request = self._build_request()
        self._worker = AgentTeamWorker(request, parent=self)
        self._worker.event_received.connect(self._on_event)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.paper_ready.connect(self._on_paper_ready)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self._stack.setCurrentIndex(1)

    def _build_request(self) -> PaperRequest:
        topic = self._topic_edit.toPlainText().strip()
        agent_path = self._path_label.text()
        if agent_path == "未选择":
            agent_path = ""

        run_mode: RunMode = "real" if self._mode_combo.currentIndex() == 1 else "mock"

        import os
        api_key = os.environ.get("OPENAI_API_KEY", "") or os.environ.get("AI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "")
        model = os.environ.get("OPENAI_MODEL", "")

        return PaperRequest(
            topic=topic,
            journal=self._journal_combo.currentText(),
            run_mode=run_mode,
            budget_cap_cny=self._budget_spin.value(),
            auto_polish=self._polish_check.isChecked(),
            agent_team_path=agent_path,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    def _reset_progress(self) -> None:
        self._progress_bar.setValue(0)
        self._log_text.clear()
        self._log_line_count = 0
        for label in self._stage_labels.values():
            label.setText("等待中...")
            label.setStyleSheet("color: #999;")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setText("取消任务")

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def _on_event(self, event: PaperEvent) -> None:
        """Handle a PaperEvent from the worker thread."""
        if event.type == "state":
            self._handle_state_event(event)
        elif event.type == "token":
            self._handle_token_event(event)
        elif event.type == "cost":
            self._handle_cost_event(event)
        elif event.type == "error":
            self._handle_error_event(event)
        elif event.type == "message":
            self._handle_message_event(event)
        elif event.type == "artifact":
            self._append_log(f"[产物] {event.agent}: {event.payload.get('path', '')}")
        elif event.type == "completion":
            self._append_log("[完成] 论文生成完毕")

    def _handle_state_event(self, event: PaperEvent) -> None:
        stage = event.stage
        progress = STAGE_PROGRESS.get(stage, -1)
        if progress >= 0:
            self._progress_bar.setValue(progress)

        # Update agent status labels
        agent = event.agent
        if agent in self._stage_labels:
            if stage.endswith("_running"):
                self._stage_labels[agent].setText("执行中...")
                self._stage_labels[agent].setStyleSheet("color: #0066cc; font-weight: bold;")
            elif stage.endswith("_done"):
                self._stage_labels[agent].setText("✅ 完成")
                self._stage_labels[agent].setStyleSheet("color: #090;")

        if stage == "cancelled":
            self._append_log("[取消] 任务已取消")
        elif stage == "failed":
            self._append_log("[失败] 任务失败")

        self._append_log(f"[状态] {stage}")

    def _handle_token_event(self, event: PaperEvent) -> None:
        content = event.payload.get("content", "")
        if content:
            # Don't flood the log with token chunks — just show agent stage changes
            agent = event.agent
            label = AGENT_LABELS.get(agent, agent)
            # Only log first few tokens per agent to show activity
            pass  # Token stream is too verbose for log; state events show progress

    def _handle_cost_event(self, event: PaperEvent) -> None:
        cumulative = event.payload.get("cumulative_cny", 0.0)
        budget = event.payload.get("budget_cap_cny", 0.0)
        self._cost_label.setText(f"¥ {cumulative:.2f}")
        self._budget_label.setText(f"¥ {budget:.2f}")

        pct = event.payload.get("budget_pct", 0.0)
        if pct >= 100:
            self._cost_label.setStyleSheet("color: #c00; font-weight: bold;")
        elif pct >= 80:
            self._cost_label.setStyleSheet("color: #c60; font-weight: bold;")
        else:
            self._cost_label.setStyleSheet("")

    def _handle_error_event(self, event: PaperEvent) -> None:
        code = event.payload.get("code", "")
        self._append_log(f"[错误] {event.message} (code={code})")

    def _handle_message_event(self, event: PaperEvent) -> None:
        agent = event.agent or "system"
        label = AGENT_LABELS.get(agent, agent)
        msg = event.message[:200] if event.message else ""
        if msg:
            self._append_log(f"[{label}] {msg}")

    def _append_log(self, text: str) -> None:
        self._log_text.append(text)
        self._log_line_count += 1
        # Enforce max log lines
        if self._log_line_count > self._max_log_lines:
            cursor = self._log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                self._log_line_count - self._max_log_lines,
            )
            cursor.removeSelectedText()
            self._log_line_count = self._max_log_lines

    # ------------------------------------------------------------------
    # Completion & errors
    # ------------------------------------------------------------------

    @pyqtSlot(str, str, float)
    def _on_paper_ready(self, markdown: str, session_id: str, cost: float) -> None:
        self._result_markdown = markdown
        self._result_session_id = session_id
        self._result_cost = cost
        self._show_result()

    @pyqtSlot(str)
    def _on_error(self, error_msg: str) -> None:
        self._append_log(f"[错误] {error_msg}")
        QMessageBox.critical(self, "生成失败", f"论文生成过程中发生错误:\n\n{error_msg}")
        self._stack.setCurrentIndex(0)

    def _on_worker_finished(self) -> None:
        """Called when the worker thread exits (may be after paper_ready or error)."""
        pass

    # ------------------------------------------------------------------
    # Result page
    # ------------------------------------------------------------------

    def _show_result(self) -> None:
        self._stack.setCurrentIndex(2)

        mode_str = "Mock 演示" if self._mode_combo.currentIndex() == 0 else "Real 模式"
        self._result_title.setText(f"生成完成 — {self._result_session_id}")
        self._stats_label.setText(
            f"字数: {len(self._result_markdown)} 字 | "
            f"费用: ¥{self._result_cost:.2f} | "
            f"模式: {mode_str}"
        )

        # Preview (first 5000 chars)
        preview = self._result_markdown[:5000]
        if len(self._result_markdown) > 5000:
            preview += "\n\n... (内容截断，完整内容请导入编辑器查看)"
        self._preview_text.setPlainText(preview)

        # Quality check
        try:
            from app.core.pipeline.quality_checks import build_quality_report

            quality = build_quality_report(self._result_markdown)
            quality_lines = [
                f"字数: {quality.word_count}",
                f"摘要: {'✅' if quality.has_abstract else '❌'}",
                f"关键词: {'✅' if quality.has_keywords else '❌'}",
                f"引言: {'✅' if quality.has_introduction else '❌'}",
                f"结论: {'✅' if quality.has_conclusion else '❌'}",
                f"参考文献: {'✅' if quality.has_references else '❌'}",
                f"引用待核查: {quality.citation_warning_count} 处",
                f"数据待补充: {quality.data_missing_count} 处",
            ]
            if quality.warnings:
                quality_lines.append("")
                quality_lines.extend(f"⚠ {w}" for w in quality.warnings)
            self._quality_text.setPlainText("\n".join(quality_lines))
        except Exception as e:
            self._quality_text.setPlainText(f"质量检查失败: {e}")

        # Compliance text
        compliance_parts = [_COMPLIANCE_TEXT, _LITERATURE_TEXT]
        if self._mode_combo.currentIndex() == 0:
            compliance_parts.append(_MOCK_EXTRA_TEXT)
        self._compliance_label.setText("\n\n".join(compliance_parts))

    # ------------------------------------------------------------------
    # Import to editor
    # ------------------------------------------------------------------

    def _emit_import(self, mode: str) -> None:
        if not self._result_markdown:
            QMessageBox.warning(self, "无内容", "没有可导入的论文内容。")
            return
        self.paper_import_requested.emit(self._result_markdown, mode)
        QMessageBox.information(self, "导入成功", f"论文已{mode}导入编辑器。")

    # ------------------------------------------------------------------
    # Cancel & restart
    # ------------------------------------------------------------------

    def _cancel_generation(self) -> None:
        if self._worker and self._worker.isRunning():
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.setText("正在取消...")
            self._worker.cancel()

    def _restart(self) -> None:
        """Go back to config page."""
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event: Any) -> None:
        """Clean up worker thread on close."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            if not self._worker.wait(3000):
                logger.warning("Worker thread did not finish in 3s, terminating")
                self._worker.terminate()
                self._worker.wait(1000)
        event.accept()
