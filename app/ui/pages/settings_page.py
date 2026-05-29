"""Settings Center page — API config, theme, connectors."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QScrollArea, QFrame,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, SettingsSection, ComingSoonBadge, StatusBadge, _card_style


def _load_provider_health():
    try:
        from app.core.providers.detector import generate_provider_health_report
        from app.core.config import Config
        config = Config()
        report = generate_provider_health_report()
        team_config = config.get_agent_team_config()
        return report, team_config
    except Exception as e:
        return None, {}


def _provider_health_section() -> QFrame:
    L = get_theme()
    panel = QFrame()
    panel.setStyleSheet(_card_style())
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
    layout.setSpacing(Spacing.MD)

    header = QLabel("Provider 健康状态")
    header.setStyleSheet(
        f"font-size: {FontSize.CARD_TITLE}px; color: {L.TEXT_PRIMARY}; font-weight: bold;"
    )
    layout.addWidget(header)

    report, team_config = _load_provider_health()

    if report is None:
        err = QLabel("无法加载 Provider 状态")
        err.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED};")
        layout.addWidget(err)
        return panel

    # Overall status
    overall_row = QHBoxLayout()
    overall_row.setSpacing(Spacing.SM)
    icon = "✓" if report.overall_ok else "✗"
    color = L.SUCCESS if report.overall_ok else L.ERROR
    icon_lbl = QLabel(icon)
    icon_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
    overall_row.addWidget(icon_lbl)
    overall_lbl = QLabel("全部正常" if report.overall_ok else "存在问题")
    overall_lbl.setStyleSheet(
        f"font-size: {FontSize.BODY}px; color: {color}; font-weight: 600;"
    )
    overall_row.addWidget(overall_lbl)
    overall_row.addStretch()
    layout.addLayout(overall_row)

    # Agent team path
    agent_path = team_config.get("agent_team_path", "")
    if agent_path:
        path_row = QHBoxLayout()
        path_lbl = QLabel("Agent Team 路径：")
        path_lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};")
        path_lbl.setFixedWidth(130)
        path_row.addWidget(path_lbl)
        path_val = QLabel(agent_path[:60])
        path_val.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-family: monospace;"
        )
        path_row.addWidget(path_val, 1)
        layout.addLayout(path_row)

    # Provider details
    for section_title, items in [
        ("本地 CLI", report.local_clis),
        ("远程 API", report.remote_apis),
        ("Agent Team", report.agent_teams),
    ]:
        section_lbl = QLabel(section_title)
        section_lbl.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: 600; "
            f"margin-top: {Spacing.SM}px;"
        )
        layout.addWidget(section_lbl)

        if not items:
            empty = QLabel("  无")
            empty.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_MUTED};")
            layout.addWidget(empty)
            continue

        for h in items:
            row = QHBoxLayout()
            row.setSpacing(Spacing.SM)

            icon2 = "✓" if h.ok else "✗"
            color2 = L.SUCCESS if h.ok else L.ERROR
            dot = QLabel(icon2)
            dot.setStyleSheet(f"color: {color2}; font-size: 12px; font-weight: bold;")
            row.addWidget(dot)

            name = QLabel(h.provider_name)
            name.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: 600;"
            )
            row.addWidget(name, 1)

            if h.warnings:
                for w in h.warnings:
                    warn = QLabel(f"⚠ {w}")
                    warn.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {L.WARNING};")
                    row.addWidget(warn)

            layout.addLayout(row)

    layout.addStretch()
    return panel


class SettingsCenterPage(QWidget):
    """Settings center with API config, model settings, and connector placeholders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def _init_ui(self):
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

        self._header = PageHeader("设置中心", "配置 API、模型、主题和外部连接器。")
        layout.addWidget(self._header)

        # Provider Health (real data)
        self._health_panel = _provider_health_section()
        layout.addWidget(self._health_panel)

        # API Configuration
        self._api_section = SettingsSection("API 配置", [
            ("OpenAI API Key", "input", "sk-..."),
            ("Base URL", "input", "https://api.openai.com/v1"),
            ("默认模型", "combo", ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]),
        ])
        layout.addWidget(self._api_section)

        # Model Settings
        self._model_section = SettingsSection("模型设置", [
            ("Temperature", "spin", 0.7),
            ("预算上限 (¥)", "spin", 10.0),
            ("自动润色", "check", True),
        ])
        layout.addWidget(self._model_section)

        # Theme
        self._theme_section = SettingsSection("外观", [
            ("主题", "combo", ["浅色", "深色", "跟随系统"]),
            ("字体大小", "combo", ["小", "标准", "大"]),
        ])
        layout.addWidget(self._theme_section)

        # Connectors
        self._connectors_label = QLabel("外部连接器")
        self._connectors_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY}; "
            f"margin-top: {Spacing.MD}px;"
        )
        layout.addWidget(self._connectors_label)

        self._btn_style_str = (
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; "
            f"background-color: {L.PRIMARY_LIGHT}; border: 1px solid {L.PRIMARY_BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_BORDER}; }}"
        )

        # Zotero section
        zotero_row = QHBoxLayout()
        zotero_row.setSpacing(Spacing.MD)
        self._zotero_lbl = QLabel("Zotero 文献库")
        self._zotero_lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        zotero_row.addWidget(self._zotero_lbl)

        self._import_bibtex_btn = QPushButton("导入 BibTeX")
        self._import_bibtex_btn.setStyleSheet(self._btn_style_str)
        self._import_bibtex_btn.clicked.connect(self._on_import_bibtex)
        self._import_bibtex_btn.setToolTip("从 Zotero 导出的 BibTeX 文件导入文献")
        zotero_row.addWidget(self._import_bibtex_btn)

        self._import_ris_btn = QPushButton("导入 RIS")
        self._import_ris_btn.setStyleSheet(self._btn_style_str)
        self._import_ris_btn.clicked.connect(self._on_import_ris)
        self._import_ris_btn.setToolTip("从 Zotero 导出的 RIS 文件导入文献")
        zotero_row.addWidget(self._import_ris_btn)
        zotero_row.addStretch()
        layout.addLayout(zotero_row)

        # Obsidian section
        obsidian_row = QHBoxLayout()
        obsidian_row.setSpacing(Spacing.MD)
        self._obsidian_lbl = QLabel("Obsidian Vault")
        self._obsidian_lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
        obsidian_row.addWidget(self._obsidian_lbl)

        self._scan_vault_btn = QPushButton("扫描 Vault")
        self._scan_vault_btn.setStyleSheet(self._btn_style_str)
        self._scan_vault_btn.clicked.connect(self._on_scan_vault)
        self._scan_vault_btn.setToolTip("选择 Obsidian Vault 目录并扫描所有笔记")
        obsidian_row.addWidget(self._scan_vault_btn)
        obsidian_row.addStretch()
        layout.addLayout(obsidian_row)

        # Future connectors
        self._future_badges: list = []
        future_connectors = [
            ("OpenAlex", "V5 计划"),
            ("CrossRef", "V5 计划"),
            ("Semantic Scholar", "V5 计划"),
            ("OCR 引擎", "V3 计划"),
            ("RAG 知识库", "V4 计划"),
        ]
        for name, badge_text in future_connectors:
            row = QHBoxLayout()
            row.setSpacing(Spacing.MD)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
            row.addWidget(lbl)
            badge = ComingSoonBadge(badge_text)
            self._future_badges.append(badge)
            row.addWidget(badge)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        self._scroll.setWidget(content)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._scroll)

    # ── theme ─────────────────────────────────────────────────────────────

    def apply_theme(self) -> None:
        """Re-apply all widget styles using current theme tokens."""
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}"
        )
        self._header.apply_theme()

        # Rebuild provider health section
        content = self._scroll.widget()
        if content is not None:
            lay = content.layout()
            if lay is not None:
                idx = lay.indexOf(self._health_panel)
                if idx >= 0:
                    new_panel = _provider_health_section()
                    old = lay.replaceWidget(self._health_panel, new_panel)
                    if old is not None:
                        old.deleteLater()
                    self._health_panel = new_panel

        # SettingsSection components have their own apply_theme()
        self._api_section.apply_theme()
        self._model_section.apply_theme()
        self._theme_section.apply_theme()

        # Connectors label
        self._connectors_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY}; "
            f"margin-top: {Spacing.MD}px;"
        )

        # Rebuild btn_style string with current theme
        btn_style = (
            f"QPushButton {{ font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY}; "
            f"background-color: {L.PRIMARY_LIGHT}; border: 1px solid {L.PRIMARY_BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.XS}px {Spacing.SM}px; }} "
            f"QPushButton:hover {{ background-color: {L.PRIMARY_BORDER}; }}"
        )

        self._zotero_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};"
        )
        self._import_bibtex_btn.setStyleSheet(btn_style)
        self._import_ris_btn.setStyleSheet(btn_style)

        self._obsidian_lbl.setStyleSheet(
            f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};"
        )
        self._scan_vault_btn.setStyleSheet(btn_style)

        # Future connector badges
        for badge in self._future_badges:
            badge.apply_theme()

    # ── Connector handlers ──────────────────────────────────────────────

    def _on_import_bibtex(self) -> None:
        """Import Zotero BibTeX file into KnowledgeStore."""
        filepath = QFileDialog.getOpenFileName(
            self, "选择 BibTeX 文件", "", "BibTeX (*.bib);;All Files (*)"
        )[0]
        if not filepath:
            return
        try:
            from app.core.connectors.zotero import ZoteroConnector
            from app.core.knowledge.store import KnowledgeStore
            items = ZoteroConnector.import_bibtex(Path(filepath))
            store = KnowledgeStore()
            count = 0
            for item in items:
                store.add(item)
                count += 1
            QMessageBox.information(self, "导入完成", f"已导入 {count} 条文献。")
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to import BibTeX", exc_info=True)
            QMessageBox.warning(self, "导入失败", "无法解析 BibTeX 文件。")

    def _on_import_ris(self) -> None:
        """Import Zotero RIS file into KnowledgeStore."""
        filepath = QFileDialog.getOpenFileName(
            self, "选择 RIS 文件", "", "RIS (*.ris);;All Files (*)"
        )[0]
        if not filepath:
            return
        try:
            from app.core.connectors.zotero import ZoteroConnector
            from app.core.knowledge.store import KnowledgeStore
            items = ZoteroConnector.import_ris(Path(filepath))
            store = KnowledgeStore()
            count = 0
            for item in items:
                store.add(item)
                count += 1
            QMessageBox.information(self, "导入完成", f"已导入 {count} 条文献。")
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to import RIS", exc_info=True)
            QMessageBox.warning(self, "导入失败", "无法解析 RIS 文件。")

    def _on_scan_vault(self) -> None:
        """Scan Obsidian vault directory into KnowledgeStore."""
        vault_path = QFileDialog.getExistingDirectory(self, "选择 Obsidian Vault 目录")
        if not vault_path:
            return
        try:
            from app.core.connectors.obsidian import ObsidianScanner
            from app.core.knowledge.store import KnowledgeStore
            scanner = ObsidianScanner(Path(vault_path))
            items = scanner.scan()
            store = KnowledgeStore()
            count = 0
            for item in items:
                store.add(item)
                count += 1
            QMessageBox.information(self, "扫描完成", f"已导入 {count} 条笔记。")
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to scan vault", exc_info=True)
            QMessageBox.warning(self, "扫描失败", "无法扫描 Obsidian Vault。")
