"""Submission & Rebuttal page — real SubmissionService + RebuttalService integration."""

from __future__ import annotations

import uuid
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.base import ComingSoonBadge, PageHeader, PreviewBadge, StatusBadge, _card_style
from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing


class SubmissionPage(QWidget):
    """Submission tracking page with real SubmissionService + RebuttalService."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._svc_path = str(Path.home() / ".wenbiao" / "runs" / "_submission_context")
        self._current_sub_id: str | None = None
        self._init_ui()
        self._load_records()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _init_ui(self) -> None:
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        self._header_widget = PageHeader(
            "投稿与回复",
            "管理投稿记录，跟踪审稿状态，规划 rebuttal 回复计划。",
        )
        header_row = QHBoxLayout()
        header_row.addWidget(self._header_widget)
        header_row.addStretch()
        layout.addLayout(header_row)

        layout.addLayout(self._create_stats_row())

        main_row = QHBoxLayout()
        main_row.setSpacing(Spacing.MD)
        self._submission_table = self._create_submission_table()
        main_row.addWidget(self._submission_table, 2)
        self._rebuttal_panel = self._create_rebuttal_panel()
        main_row.addWidget(self._rebuttal_panel)
        layout.addLayout(main_row, 1)

        layout.addStretch()
        self._scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._scroll)

    def _create_stats_row(self) -> QHBoxLayout:
        L = get_theme()
        row = QHBoxLayout()
        row.setSpacing(Spacing.MD)

        self._stat_cards: list[tuple[QLabel, QLabel, str]] = []  # (count_lbl, name_lbl, key)
        self._stat_card_frames: list[QFrame] = []

        for label_str in ["草稿", "已投稿", "审稿中", "修改中", "已接受", "已拒绝"]:
            card = QFrame()
            card.setStyleSheet(_card_style())
            card.setMinimumWidth(80)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
            card_layout.setSpacing(Spacing.XS)

            count_lbl = QLabel("0")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_lbl.setStyleSheet(
                f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
            )
            card_layout.addWidget(count_lbl)

            name_lbl = QLabel(label_str)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
            )
            card_layout.addWidget(name_lbl)

            row.addWidget(card)
            self._stat_card_frames.append(card)
            self._stat_cards.append((count_lbl, name_lbl, label_str.lower()))

        row.addStretch()
        return row

    def _create_submission_table(self) -> QFrame:
        L = get_theme()
        self._submission_panel = QFrame()
        self._submission_panel.setStyleSheet(_card_style())
        layout = QVBoxLayout(self._submission_panel)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        top_row = QHBoxLayout()
        self._submission_title = QLabel("投稿记录")
        self._submission_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        top_row.addWidget(self._submission_title)
        top_row.addStretch()

        self._add_btn = QPushButton("新增投稿")
        self._add_btn.setFixedHeight(28)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: 0 {Spacing.MD}px; font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._add_btn.clicked.connect(self._on_add_submission)
        top_row.addWidget(self._add_btn)

        layout.addLayout(top_row)

        self._record_list = QListWidget()
        self._record_list.setStyleSheet(
            f"QListWidget {{ border: none; background-color: transparent; }}"
        )
        self._record_list.itemClicked.connect(self._on_record_selected)
        layout.addWidget(self._record_list)

        return self._submission_panel

    def _create_rebuttal_panel(self) -> QFrame:
        L = get_theme()
        self._rebuttal_panel_frame = QFrame()
        self._rebuttal_panel_frame.setFixedWidth(280)
        self._rebuttal_panel_frame.setStyleSheet(_card_style())
        layout = QVBoxLayout(self._rebuttal_panel_frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        self._rebuttal_header = QLabel("审稿意见 / Rebuttal")
        self._rebuttal_header.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._rebuttal_header)

        self._rebuttal_title = QLabel("选择一条投稿查看审稿意见")
        self._rebuttal_title.setWordWrap(True)
        self._rebuttal_title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(self._rebuttal_title)

        self._rebuttal_concerns = QTextEdit()
        self._rebuttal_concerns.setPlaceholderText("粘贴审稿人意见文本...")
        self._rebuttal_concerns.setFixedHeight(120)
        self._rebuttal_concerns.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        layout.addWidget(self._rebuttal_concerns)

        self._rebuttal_plan = QTextEdit()
        self._rebuttal_plan.setReadOnly(True)
        self._rebuttal_plan.setPlaceholderText("点击「生成回复计划」查看 AI 生成的回复提纲")
        self._rebuttal_plan.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        layout.addWidget(self._rebuttal_plan, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.SM)

        self._gen_btn = QPushButton("生成回复计划")
        self._gen_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._gen_btn.clicked.connect(self._on_generate_rebuttal)
        btn_row.addWidget(self._gen_btn)

        self._export_btn = QPushButton("导出 Markdown")
        self._export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_PRIMARY}; "
            f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.SURFACE}; }}"
        )
        self._export_btn.clicked.connect(self._on_export_rebuttal)
        btn_row.addWidget(self._export_btn)

        layout.addLayout(btn_row)
        layout.addStretch()
        return self._rebuttal_panel_frame

    def _load_records(self) -> None:
        try:
            from app.core.submission import SubmissionService
            svc = SubmissionService()
            records = svc.list_all()
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to load submission records", exc_info=True)
            records = []

        self._record_list.clear()
        for rec in records:
            item = QListWidgetItem(
                f"{rec.venue}  |  {rec.paper_title[:30]}  |  {rec.status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, rec.id)
            self._record_list.addItem(item)

        self._update_stats(records)

    def _update_stats(self, records: list) -> None:
        counts: dict[str, int] = {
            "草稿": 0, "已投稿": 0, "审稿中": 0,
            "修改中": 0, "已接受": 0, "已拒绝": 0,
        }
        status_map = {
            "draft": "草稿", "submitted": "已投稿", "under_review": "审稿中",
            "revision": "修改中", "accepted": "已接受", "rejected": "已拒绝",
        }
        for rec in records:
            key = status_map.get(rec.status, "草稿")
            counts[key] = counts.get(key, 0) + 1

        for lbl, _name_lbl, key in self._stat_cards:
            lbl.setText(str(counts.get(key, 0)))

    def _on_add_submission(self) -> None:
        title, ok1 = QInputDialog.getText(self, "新增投稿", "论文标题：")
        if not ok1 or not title.strip():
            return
        venue, ok2 = QInputDialog.getText(self, "新增投稿", "期刊/会议：")
        if not ok2 or not venue.strip():
            return

        try:
            from app.core.submission import SubmissionService
            svc = SubmissionService()
            rec = svc.add(title.strip(), venue.strip())
            self._load_records()
            QMessageBox.information(self, "已添加", f"已创建投稿记录：{rec.id}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"添加失败：{e}")

    def _on_record_selected(self, item: QListWidgetItem) -> None:
        self._current_sub_id = item.data(Qt.ItemDataRole.UserRole)
        self._rebuttal_title.setText(
            item.text().split("|")[1].strip() if "|" in item.text() else "已选择投稿"
        )
        self._rebuttal_concerns.clear()
        self._rebuttal_plan.clear()

    def _on_generate_rebuttal(self) -> None:
        if not self._current_sub_id:
            QMessageBox.warning(self, "请选择", "请先在左侧列表选择一条投稿。")
            return

        reviewer_text = self._rebuttal_concerns.toPlainText().strip()
        if not reviewer_text:
            QMessageBox.warning(self, "请输入", "请先粘贴审稿人意见文本。")
            return

        try:
            from app.core.submission import RebuttalService
            svc = RebuttalService()
            plan = svc.build_plan(self._current_sub_id, [reviewer_text])
            self._rebuttal_plan.clear()
            for i, (concern, response) in enumerate(zip(plan.concerns, plan.plans), 1):
                self._rebuttal_plan.append(
                    f"### {i}. {concern}\n\n{response}\n"
                )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成回复计划失败：{e}")

    def _on_export_rebuttal(self) -> None:
        plan_text = self._rebuttal_plan.toPlainText().strip()
        if not plan_text:
            QMessageBox.warning(self, "无可导出内容", "请先生成回复计划。")
            return

        sub_id = self._current_sub_id or "unknown"
        out_dir = Path.home() / ".wenbiao" / "runs" / "_rebuttals"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"rebuttal_{sub_id}.md"
        out_path.write_text(
            f"# Rebuttal Plan — {sub_id}\n\n{plan_text}\n\n"
            "---\n*由 ThesisX 自动生成*",
            encoding="utf-8",
        )
        QMessageBox.information(self, "已导出", f"回复计划已保存至：\n{out_path}")

    # ── theme ─────────────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        """Re-apply all widget styles using current theme tokens."""
        L = get_theme()
        self._header_widget.apply_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )
        self._submission_panel.setStyleSheet(_card_style())
        self._rebuttal_panel_frame.setStyleSheet(_card_style())
        # Stats row cards
        for card in self._stat_card_frames:
            card.setStyleSheet(_card_style())
        for count_lbl, name_lbl, _key in self._stat_cards:
            count_lbl.setStyleSheet(
                f"font-size: {FontSize.PANEL_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
            )
            name_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
            )
        # Submission table
        self._submission_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: 0 {Spacing.MD}px; font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        # Rebuttal panel
        self._rebuttal_header.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._rebuttal_title.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_MUTED};"
        )
        self._rebuttal_concerns.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        self._rebuttal_plan.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; "
            f"font-size: {FontSize.SMALL}px; color: {L.TEXT_PRIMARY}; "
            f"font-family: 'PingFang SC', sans-serif; }}"
        )
        self._gen_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_PRIMARY}; "
            f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.SM}px; "
            f"font-size: {FontSize.SECONDARY}px; }} "
            f"QPushButton:hover {{ background-color: {L.SURFACE}; }}"
        )
