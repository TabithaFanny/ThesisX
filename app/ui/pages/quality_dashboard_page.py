"""Quality Dashboard page — Vision 3.10.

Displays thesis quality metrics: writing progress, claim coverage,
evidence integrity, citation completeness, and an overall score.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, _card_style


def _label(size: int, color: str, weight: str = "normal") -> str:
    return f"QLabel {{ font-size: {size}px; color: {color}; font-weight: {weight}; }}"


class _BigScoreCard(QFrame):
    """Large score display with grade."""

    def __init__(self):
        super().__init__()
        L = get_theme()
        self.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f" stop:0 {L.PRIMARY_LIGHT}, stop:1 {L.SURFACE});"
            f" border: 2px solid {L.PRIMARY_BORDER};"
            f" border-radius: {Radius.PANEL}px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.XS)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._score_label = QLabel("--")
        self._score_label.setStyleSheet(
            f"font-size: {FontSize.HERO + 20}px; color: {L.PRIMARY}; font-weight: 800;"
        )
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._score_label)

        self._max_label = QLabel("/ 100")
        self._max_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._max_label)

        self._grade_label = QLabel("")
        self._grade_label.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )
        self._grade_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._grade_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(
            f"QFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f" stop:0 {L.PRIMARY_LIGHT}, stop:1 {L.SURFACE});"
            f" border: 2px solid {L.PRIMARY_BORDER};"
            f" border-radius: {Radius.PANEL}px; }}"
        )
        self._score_label.setStyleSheet(
            f"font-size: {FontSize.HERO + 20}px; color: {L.PRIMARY}; font-weight: 800;"
        )
        self._max_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        self._grade_label.setStyleSheet(
            f"font-size: {FontSize.PAGE_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: 700;"
        )

    def set_score(self, score: float, grade: str) -> None:
        self._score_label.setText(str(score))
        self._grade_label.setText(grade)


class _MetricCard(QFrame):
    """Single metric card with progress bar and counts."""

    def __init__(self, title: str):
        super().__init__()
        L = get_theme()
        self.setStyleSheet(_card_style(L))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        layout.addWidget(self._title_label)

        self._pct_label = QLabel("--%")
        self._pct_label.setStyleSheet(
            f"font-size: {FontSize.HERO}px; color: {L.PRIMARY}; font-weight: 700;"
        )
        layout.addWidget(self._pct_label)

        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet(
            f"QProgressBar {{ background-color: {L.SURFACE_ALT};"
            f" border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background-color: {L.PRIMARY}; border-radius: 4px; }}"
        )
        layout.addWidget(self._progress)

        self._detail_label = QLabel("")
        self._detail_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))
        layout.addWidget(self._detail_label)

    def apply_theme(self) -> None:
        L = get_theme()
        self.setStyleSheet(_card_style(L))
        self._title_label.setStyleSheet(
            _label(FontSize.CARD_TITLE, L.TEXT_PRIMARY, "bold")
        )
        self._pct_label.setStyleSheet(
            f"font-size: {FontSize.HERO}px; color: {L.PRIMARY}; font-weight: 700;"
        )
        self._progress.setStyleSheet(
            f"QProgressBar {{ background-color: {L.SURFACE_ALT};"
            f" border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background-color: {L.PRIMARY}; border-radius: 4px; }}"
        )
        self._detail_label.setStyleSheet(_label(FontSize.SECONDARY, L.TEXT_SECONDARY))

    def set_value(self, pct: float, detail: str) -> None:
        self._pct_label.setText(f"{pct}%")
        self._progress.setValue(int(pct))
        self._detail_label.setText(detail)


class QualityDashboardPage(QWidget):
    """Thesis quality dashboard with aggregate metrics."""

    def __init__(self):
        super().__init__()
        from app.core.quality.service import QualityService, QualityDashboard
        self._svc = QualityService()
        self._dashboard: QualityDashboard | None = None
        self._built = False
        self._build_ui()
        self._reload()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    # ── UI build ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._built = True
        L = get_theme()
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XXL, Spacing.XL, Spacing.XXL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header with project selector
        header_row = QHBoxLayout()
        header_row.setSpacing(Spacing.MD)

        header_col = QVBoxLayout()
        self._page_header = PageHeader(
            "质量仪表盘",
            "论文质量指标总览。综合评估写作进度、Claim 覆盖、证据完整性和引文完整性。",
        )
        header_col.addWidget(self._page_header)
        header_row.addLayout(header_col, 1)

        from PyQt6.QtWidgets import QComboBox
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(200)
        self._project_combo.setStyleSheet(
            f"QComboBox {{ font-size: {FontSize.BODY}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px; "
            f"background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; }} "
            f"QComboBox::drop-down {{ border: none; }} "
            f"QComboBox QAbstractItemView {{ font-size: {FontSize.BODY}px; }}"
        )
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        header_row.addWidget(self._project_combo)

        root.addLayout(header_row)

        # Scrollable content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {L.CANVAS}; }}")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(Spacing.LG)

        # Big score card
        self._score_card = _BigScoreCard()
        content_layout.addWidget(self._score_card)

        # Metric grid (2×2)
        grid = QGridLayout()
        grid.setSpacing(Spacing.MD)

        self._progress_card = _MetricCard("写作进度")
        grid.addWidget(self._progress_card, 0, 0)

        self._claim_card = _MetricCard("Claim 覆盖")
        grid.addWidget(self._claim_card, 0, 1)

        self._evidence_card = _MetricCard("证据完整性")
        grid.addWidget(self._evidence_card, 1, 0)

        self._citation_card = _MetricCard("引文完整性")
        grid.addWidget(self._citation_card, 1, 1)

        content_layout.addLayout(grid)

        # Suggestions
        self._suggestions_header = QLabel("改进建议")
        self._suggestions_header.setStyleSheet(
            _label(FontSize.PANEL_TITLE, L.TEXT_PRIMARY, "bold")
        )
        content_layout.addWidget(self._suggestions_header)

        self._suggestions_list = QLabel("")
        self._suggestions_list.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._suggestions_list.setWordWrap(True)
        content_layout.addWidget(self._suggestions_list)

        # Empty state
        self._empty_label = QLabel(
            "尚无项目数据。请先创建项目并在研究工作空间定义研究问题，"
            "或将编辑器内容接入质量评估。"
        )
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        content_layout.addWidget(self._empty_label)

        content_layout.addStretch()

        self._scroll.setWidget(content)
        root.addWidget(self._scroll, 1)

    def apply_theme(self) -> None:
        L = get_theme()
        self._page_header.apply_theme()
        self._scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {L.CANVAS}; }}")
        self._project_combo.setStyleSheet(
            f"QComboBox {{ font-size: {FontSize.BODY}px; padding: {Spacing.XS}px {Spacing.SM}px; "
            f"border: 1px solid {L.BORDER}; border-radius: {Radius.INPUT}px; "
            f"background-color: {L.SURFACE}; color: {L.TEXT_PRIMARY}; }} "
            f"QComboBox::drop-down {{ border: none; }} "
            f"QComboBox QAbstractItemView {{ font-size: {FontSize.BODY}px; }}"
        )
        self._score_card.apply_theme()
        self._progress_card.apply_theme()
        self._claim_card.apply_theme()
        self._evidence_card.apply_theme()
        self._citation_card.apply_theme()
        self._suggestions_header.setStyleSheet(
            _label(FontSize.PANEL_TITLE, L.TEXT_PRIMARY, "bold")
        )
        self._suggestions_list.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))
        self._empty_label.setStyleSheet(_label(FontSize.BODY, L.TEXT_SECONDARY))

    # ── data ──────────────────────────────────────────────────────────────

    def _reload(self) -> None:
        self._populate_projects()
        self._feed_real_data()
        self._dashboard = self._svc.get_dashboard()
        self._refresh()

    def _populate_projects(self) -> None:
        """Load project list from ProjectService."""
        try:
            from app.core.project.service import ProjectService
            svc = ProjectService()
            projects = svc.list_projects()
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to load projects for Quality Dashboard", exc_info=True)
            projects = []

        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.addItem("（所有项目）", None)
        for p in projects:
            self._project_combo.addItem(p.get("name", p.get("id", "")), p.get("id"))
        self._project_combo.blockSignals(False)

    def _on_project_changed(self, _: int) -> None:
        self._reload()

    def _feed_real_data(self) -> None:
        """Feed real data from KnowledgeStore and EvidencePackService."""
        project_id = self._project_combo.currentData()

        try:
            from app.core.knowledge.store import KnowledgeStore
            from app.core.quality.models import (
                WritingProgress, ClaimCoverage, EvidenceIntegrity, CitationCompleteness,
            )

            store = KnowledgeStore()

            # Writing progress: count notes with content
            notes = store.list(item_type="note")
            progress_items = [
                WritingProgress.new(
                    section_type=note.title,
                    edit_status="done" if note.content.strip() else "draft",
                )
                for note in notes
            ]
            self._svc.set_progress(progress_items)

            # Claim coverage: try EvidencePackService
            try:
                from app.core.evidence.service import EvidencePackService
                eps = EvidencePackService(project_id or "default")
                claims = eps.list_claims()
                coverages = [
                    ClaimCoverage.new(
                        claim_id=c.id,
                        claim_text=c.claim_text,
                        project_id=project_id or "default",
                    )
                    for c in claims
                ]
                # Set coverage status: check if claim has evidence
                for cov, claim in zip(coverages, claims):
                    evidence_list = eps.list_evidence(claim.id)
                    cov.covered = len(evidence_list) > 0
                    if evidence_list:
                        cov.coverage_score = min(1.0, len(evidence_list) / 3.0)
                self._svc.set_coverages(coverages)

                # Evidence integrity: collect all evidence items across claims
                integrity_items: list[EvidenceIntegrity] = []
                for claim in claims:
                    for ev in eps.list_evidence(claim.id):
                        integrity_items.append(EvidenceIntegrity.new(
                            source_id=ev.evidence_object_id,
                            knowledge_title=ev.evidence_text[:60],
                            verified_status=ev.coverage_status,
                        ))
                self._svc.set_integrity(integrity_items)
            except Exception:
                # Evidence service not available — use KnowledgeStore fallback
                claims = store.list(item_type="evidence")
                coverages = [
                    ClaimCoverage.new(
                        claim_id=c.id,
                        claim_text=c.title,
                        covered=len(c.tags) > 0,
                    )
                    for c in claims
                ]
                self._svc.set_coverages(coverages)
                self._svc.set_integrity([])

            # Citation completeness: count literature items
            literature = store.list(item_type="literature")
            citation_items = [
                CitationCompleteness.new(
                    citation_key=ref.id,
                    is_complete=bool(ref.title and ref.content.strip()),
                )
                for ref in literature
            ]
            self._svc.set_citations(citation_items)

        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to feed quality data", exc_info=True)

    def _refresh(self) -> None:
        d = self._dashboard
        if d.overall_score == 0 and d.total_sections == 0 and d.total_claims == 0 \
                and d.total_evidence_items == 0 and d.total_citations == 0:
            self._empty_label.setVisible(True)
            self._score_card.setVisible(False)
            self._progress_card.setVisible(False)
            self._claim_card.setVisible(False)
            self._evidence_card.setVisible(False)
            self._citation_card.setVisible(False)
            self._suggestions_header.setVisible(False)
            self._suggestions_list.setVisible(False)
            return

        self._empty_label.setVisible(False)
        self._score_card.setVisible(True)
        self._progress_card.setVisible(True)
        self._claim_card.setVisible(True)
        self._evidence_card.setVisible(True)
        self._citation_card.setVisible(True)
        self._suggestions_header.setVisible(True)
        self._suggestions_list.setVisible(True)

        self._score_card.set_score(d.overall_score, d.grade)

        if d.total_sections > 0:
            self._progress_card.set_value(
                d.writing_progress,
                f"已完成 {d.sections_completed}/{d.total_sections} 章节"
            )
        else:
            self._progress_card.set_value(0, "无进度数据")

        if d.total_claims > 0:
            self._claim_card.set_value(
                d.claim_coverage,
                f"已覆盖 {d.claims_covered}/{d.total_claims} 个 Claim"
            )
        else:
            self._claim_card.set_value(0, "无 Claim 数据")

        if d.total_evidence_items > 0:
            self._evidence_card.set_value(
                d.evidence_integrity,
                f"已验证 {d.evidence_verified}/{d.total_evidence_items} 条证据"
            )
        else:
            self._evidence_card.set_value(0, "无证据数据")

        if d.total_citations > 0:
            self._citation_card.set_value(
                d.citation_completeness,
                f"完整 {d.citations_complete}/{d.total_citations} 条引文"
            )
        else:
            self._citation_card.set_value(0, "无引文数据")

        suggestions_html = "<br>".join(f"• {s}" for s in d.suggestions) if d.suggestions else "暂无建议。"
        self._suggestions_list.setText(suggestions_html)
