"""Theory Matcher page — recommend theories based on research questions.

PRD Section 8: Theory Matcher Panel
- Research question input
- Keyword extraction display
- Theory candidate list with match scores
- Theory detail (concepts, applicable topics, explanation)
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, _card_style


def _truncate(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


class TheoryMatcherPage(QWidget):
    """Theory Matcher — find the right theory for your research question."""

    # Emitted when user selects theories to use in a paper run
    theories_selected = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._candidates: list = []  # list of TheoryCandidate dicts
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet(f"background-color: {L.CANVAS};")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        root = QVBoxLayout(content)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header
        header = PageHeader(
            "理论匹配",
            "输入研究问题，系统推荐适合的理论框架，帮助你构建扎实的理论基础。",
        )
        root.addWidget(header)

        # Input card
        input_card = QFrame()
        input_card.setStyleSheet(_card_style())
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        input_layout.setSpacing(Spacing.MD)

        lbl = QLabel("研究问题")
        lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold;"
        )
        input_layout.addWidget(lbl)

        self._question_input = QTextEdit()
        self._question_input.setPlaceholderText(
            "例如：AI工具对大学生学习方式的影响研究\n短视频对大学生注意力影响的研究\n社区治理数字化转型效果研究"
        )
        self._question_input.setFixedHeight(100)
        self._question_input.setStyleSheet(
            f"QTextEdit {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; "
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; "
            f"font-family: 'PingFang SC', sans-serif; }} "
            f"QTextEdit:focus {{ border-color: {L.PRIMARY}; }} "
            f"QTextEdit::placeholder {{ color: {L.TEXT_MUTED}; }}"
        )
        input_layout.addWidget(self._question_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.MD)
        btn_row.addStretch()

        match_btn = QPushButton("匹配理论")
        match_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.LG}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        match_btn.clicked.connect(self._on_match)
        btn_row.addWidget(match_btn)

        self._send_btn = QPushButton("发送给 AI 使用")
        self._send_btn.setEnabled(False)
        self._send_btn.setStyleSheet(
            f"QPushButton {{ background-color: {L.SURFACE_ALT}; color: {L.TEXT_SECONDARY}; "
            f"border: 1px solid {L.BORDER}; border-radius: {Radius.BUTTON}px; "
            f"padding: {Spacing.XS}px {Spacing.LG}px; "
            f"font-size: {FontSize.SECONDARY}px; font-weight: bold; }} "
            f"QPushButton:enabled {{ background-color: {L.PRIMARY}; color: {L.TEXT_ON_PRIMARY}; "
            f"border: none; }} "
            f"QPushButton:enabled:hover {{ background-color: {L.PRIMARY_HOVER}; }}"
        )
        self._send_btn.clicked.connect(self._on_send_to_ai)
        btn_row.addWidget(self._send_btn)
        input_layout.addLayout(btn_row)

        # Keywords display
        self._keywords_lbl = QLabel("")
        self._keywords_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY};"
        )
        input_layout.addWidget(self._keywords_lbl)

        root.addWidget(input_card)

        # Results area
        self._results_area = QVBoxLayout()
        self._results_area.setSpacing(Spacing.MD)
        root.addLayout(self._results_area, 1)

        root.addStretch()
        scroll.setWidget(content)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

    def _on_match(self) -> None:
        question = self._question_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "请输入", "请先输入研究问题。")
            return

        try:
            from app.core.theory import TheoryMatcher

            matcher = TheoryMatcher()
            keywords = matcher.extract_keywords(question)
            self._keywords_lbl.setText(
                "关键词：" + " · ".join(keywords[:12]) if keywords else "（未提取到关键词）"
            )
            raw_candidates = matcher.match(question, top_k=5)
            self._candidates = []
            for c in raw_candidates:
                self._candidates.append({
                    "id": c.id,
                    "name_zh": c.name_zh,
                    "name_en": c.name_en,
                    "discipline": c.discipline,
                    "core_concepts": c.core_concepts,
                    "applicable_topics": c.applicable_topics,
                    "explanation": c.explanation,
                    "limitations": c.limitations,
                    "match_score": c.match_score,
                })
            self._refresh_results()
        except Exception as e:
            QMessageBox.warning(self, "匹配失败", f"理论匹配出错：{e}")

    def _refresh_results(self) -> None:
        # Clear old results
        while self._results_area.count():
            child = self._results_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._candidates:
            empty = QLabel("未找到匹配的理论。尝试换一种研究问题表述。")
            empty.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; padding: {Spacing.MD}px;"
            )
            self._results_area.addWidget(empty)
            return

        title = QLabel(f"推荐理论（{len(self._candidates)} 个）")
        title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: bold;"
        )
        self._results_area.addWidget(title)

        for i, cand in enumerate(self._candidates):
            card = self._create_candidate_card(cand, i)
            self._results_area.addWidget(card)

        self._send_btn.setEnabled(bool(self._candidates))

    def _on_send_to_ai(self) -> None:
        """Emit theories_selected signal with top candidates for paper generation."""
        if not self._candidates:
            return
        self.theories_selected.emit(self._candidates[:3])
        QMessageBox.information(
            self,
            "已选择",
            "理论已选中，将在下次论文生成时注入上下文。\n"
            "你也可以在 AI 论文助手中进一步调整。",
        )

    def _create_candidate_card(self, cand: dict, index: int) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_card_style())
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        # Header: name + score
        header = QHBoxLayout()
        header.setSpacing(Spacing.MD)

        rank_lbl = QLabel(f"#{index + 1}")
        rank_lbl.setFixedWidth(24)
        rank_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.PRIMARY}; font-weight: 800;"
        )
        header.addWidget(rank_lbl)

        name_lbl = QLabel(f"{cand['name_zh']} ({cand['name_en']})")
        name_lbl.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        header.addWidget(name_lbl, 1)

        score_lbl = QLabel(f"匹配度 {cand['match_score']:.0%}")
        score_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; font-weight: bold;"
        )
        header.addWidget(score_lbl)
        layout.addLayout(header)

        # Discipline tags
        tags_row = QHBoxLayout()
        tags_row.setSpacing(Spacing.XS)
        for disc in cand["discipline"][:3]:
            tag = QLabel(disc)
            tag.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED}; "
                f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
                f"border-radius: {Radius.BAR}px; padding: 1px 6px;"
            )
            tags_row.addWidget(tag)
        tags_row.addStretch()
        layout.addLayout(tags_row)

        # Core concepts
        concepts_lbl = QLabel(
            "核心理论概念：" + " · ".join(cand["core_concepts"][:4])
        )
        concepts_lbl.setWordWrap(True)
        concepts_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};"
        )
        layout.addWidget(concepts_lbl)

        # Explanation
        exp_lbl = QLabel(cand["explanation"])
        exp_lbl.setWordWrap(True)
        exp_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; "
            f"background-color: {L.SURFACE_ALT}; border: 1px solid {L.BORDER_SUBTLE}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px;"
        )
        layout.addWidget(exp_lbl)

        # Applicable topics
        topics_lbl = QLabel(
            "适用话题：" + " · ".join(cand["applicable_topics"][:3])
        )
        topics_lbl.setWordWrap(True)
        topics_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};"
        )
        layout.addWidget(topics_lbl)

        # Limitations
        limits_lbl = QLabel(
            "局限：" + "；".join(cand["limitations"])
        )
        limits_lbl.setWordWrap(True)
        limits_lbl.setStyleSheet(
            f"font-size: {FontSize.SMALL}px; color: {L.WARNING};"
        )
        layout.addWidget(limits_lbl)

        return card
