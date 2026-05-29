"""Evidence Pack page — Vision 3.4.

Claim-Evidence chain management UI.
- Create Claims from project research question
- Bind evidence items (KnowledgeObjects)
- Gap analysis view
- Export evidence report

PRD: FRONTEND_INTERFACE_MAPPING.md §Evidence Pack
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import _card_style


def _badge_style(color: str) -> str:
    return f"""
        QLabel {{ background-color: {color}; color: white;
                  border-radius: 8px; padding: 2px 8px;
                  font-size: {FontSize.CAPTION}px; font-weight: 600; }}
    """


class _NewClaimDialog(QDialog):
    """Dialog to create a new Claim."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建 Claim")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Claim 文本："))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("描述你的研究论断...")
        self.text_edit.setMaximumHeight(80)
        layout.addWidget(self.text_edit)

        layout.addWidget(QLabel("类型："))
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("fact / finding / method / limitation / assumption")
        layout.addWidget(self.type_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {
            "claim_text": self.text_edit.toPlainText().strip(),
            "claim_type": self.type_edit.text().strip() or "fact",
        }


class _ClaimCard(QFrame):
    """Card showing a Claim and its evidence items."""

    clicked = pyqtSignal(str)  # claim_id

    def __init__(self, claim, evidence_items, parent=None):
        super().__init__(parent)
        self.claim = claim
        self.evidence_items = evidence_items
        self._has_gap = not evidence_items
        self._build_ui()

    def _build_ui(self):
        L = get_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        self.setStyleSheet(_card_style(L))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Claim header
        header = QHBoxLayout()
        self._type_label = QLabel(self.claim.claim_type)
        self._type_label.setStyleSheet(_badge_style(L.PRIMARY))
        header.addWidget(self._type_label)

        if self.evidence_items:
            self._count_label = QLabel(f"{len(self.evidence_items)} 条证据")
            self._count_label.setStyleSheet(f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.CAPTION}px;")
            header.addWidget(self._count_label)
            self._gap_label = None
        else:
            self._gap_label = QLabel("⚠ 无证据 — GAP")
            self._gap_label.setStyleSheet(_badge_style("#e74c3c"))
            header.addWidget(self._gap_label)
            self._count_label = None

        header.addStretch()
        self.setMaximumHeight(120)
        layout.addLayout(header)

        # Claim text
        self._text_label = QLabel(self.claim.claim_text)
        self._text_label.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY};")
        self._text_label.setWordWrap(True)
        layout.addWidget(self._text_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._type_label.setStyleSheet(_badge_style(L.PRIMARY))
        if self._count_label:
            self._count_label.setStyleSheet(f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.CAPTION}px;")
        if self._gap_label:
            self._gap_label.setStyleSheet(_badge_style("#e74c3c"))
        self._text_label.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY};")

    def mousePressEvent(self, event):
        self.clicked.emit(self.claim.id)
        super().mousePressEvent(event)


class EvidencePackPage(QWidget):
    """Evidence Pack page — Vision 3.4.

    Manage Claim-Evidence chains for the active project.
    """

    def __init__(self, project_id: str | None = None):
        super().__init__()
        self._project_id = project_id or ""
        self._claims: list = []
        self._evidence_map: dict[str, list] = {}
        self._cards: list[_ClaimCard] = []
        self._build_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _build_ui(self):
        L = get_theme()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        outer.setSpacing(Spacing.MD)

        # Header
        header = QHBoxLayout()
        self._title_label = QLabel("证据包 / Evidence Pack")
        self._title_label.setStyleSheet(f"font-size: {FontSize.PAGE_TITLE}px; font-weight: 700; color: {L.TEXT_PRIMARY};")
        header.addWidget(self._title_label)
        header.addStretch()

        self._new_btn = QPushButton("+ 新建 Claim")
        self._new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {L.PRIMARY}; color: white;
                border-radius: {Radius.INPUT}px;
                padding: {Spacing.SM} {Spacing.MD}px;
                font-weight: 600;
            }}
        """)
        self._new_btn.clicked.connect(self._on_new_claim)
        header.addWidget(self._new_btn)
        outer.addLayout(header)

        # Gap analysis summary
        self._summary = QLabel("")
        self._summary.setStyleSheet(f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.SECONDARY}px;")
        outer.addWidget(self._summary)

        # Claims scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("border: none; background-color: transparent;")
        content = QWidget()
        self._grid = QGridLayout(content)
        self._grid.setSpacing(Spacing.MD)
        self._scroll.setWidget(content)
        outer.addWidget(self._scroll)

    def _reload(self):
        """Reload claims and evidence from service."""
        from app.core.evidence.service import EvidencePackService

        if not self._project_id:
            self._refresh_empty()
            return

        svc = EvidencePackService(self._project_id)
        self._claims = svc.list_claims()
        self._evidence_map = {c.id: svc.list_evidence(c.id) for c in self._claims}
        self._refresh_cards()

    def _refresh_empty(self):
        L = get_theme()
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        empty = QLabel("请先在研究工作空间选择项目")
        empty.setStyleSheet(f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.SECONDARY}px;")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grid.addWidget(empty, 0, 0)

    def _refresh_cards(self):
        L = get_theme()
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        if not self._claims:
            empty = QLabel("暂无 Claim，点击右上角「新建 Claim」开始")
            empty.setStyleSheet(f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.SECONDARY}px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._grid.addWidget(empty, 0, 0)
        else:
            for i, claim in enumerate(self._claims):
                items = self._evidence_map.get(claim.id, [])
                card = _ClaimCard(claim, items)
                self._cards.append(card)
                row, col = i // 2, i % 2
                self._grid.addWidget(card, row, col)

            # Summary
            gaps = sum(1 for c in self._claims if not self._evidence_map.get(c.id))
            total = len(self._claims)
            self._summary.setText(
                f"共 {total} 个 Claims，{gaps} 个存在证据缺口（gap）"
            )

    def apply_theme(self) -> None:
        L = get_theme()
        self._title_label.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; font-weight: 700; color: {L.TEXT_PRIMARY};"
        )
        self._new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {L.PRIMARY}; color: white;
                border-radius: {Radius.INPUT}px;
                padding: {Spacing.SM} {Spacing.MD}px;
                font-weight: 600;
            }}
        """)
        self._summary.setStyleSheet(
            f"color: {L.TEXT_SECONDARY}; font-size: {FontSize.SECONDARY}px;"
        )
        for card in self._cards:
            card.apply_theme()

    def _on_new_claim(self):
        dlg = _NewClaimDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            vals = dlg.get_values()
            if vals["claim_text"]:
                from app.core.evidence.service import EvidencePackService

                svc = EvidencePackService(self._project_id)
                try:
                    svc.create_claim_from_question(
                        research_question_id="",
                        claim_text=vals["claim_text"],
                        claim_type=vals["claim_type"],
                    )
                except ValueError:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(
                        self, "缺少研究问题",
                        "当前项目没有研究问题，请先在 Research 页面创建研究问题。"
                    )
                    return
                self._reload()
