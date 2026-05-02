"""Settings Center page — API config, theme, connectors."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea, QFrame,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
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
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {L.CANVAS}; border: none; }}")

        content = QWidget()
        content.setStyleSheet(f"background-color: {L.CANVAS};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)

        layout.addWidget(PageHeader("设置中心", "配置 API、模型、主题和外部连接器。"))

        # Provider Health (real data)
        layout.addWidget(_provider_health_section())

        # API Configuration
        api_section = SettingsSection("API 配置", [
            ("OpenAI API Key", "input", "sk-..."),
            ("Base URL", "input", "https://api.openai.com/v1"),
            ("默认模型", "combo", ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"]),
        ])
        layout.addWidget(api_section)

        # Model Settings
        model_section = SettingsSection("模型设置", [
            ("Temperature", "spin", 0.7),
            ("预算上限 (¥)", "spin", 10.0),
            ("自动润色", "check", True),
        ])
        layout.addWidget(model_section)

        # Theme
        theme_section = SettingsSection("外观", [
            ("主题", "combo", ["浅色", "深色", "跟随系统"]),
            ("字体大小", "combo", ["小", "标准", "大"]),
        ])
        layout.addWidget(theme_section)

        # Connectors (coming soon)
        connectors_label = QLabel("外部连接器")
        connectors_label.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY}; "
            f"margin-top: {Spacing.MD}px;"
        )
        layout.addWidget(connectors_label)

        connectors = [
            ("Zotero 文献库", "V3 计划"),
            ("本地文件夹", "V3 计划"),
            ("OpenAlex", "V5 计划"),
            ("CrossRef", "V5 计划"),
            ("Semantic Scholar", "V5 计划"),
            ("OCR 引擎", "V3 计划"),
            ("RAG 知识库", "V4 计划"),
        ]
        for name, badge_text in connectors:
            row = QHBoxLayout()
            row.setSpacing(Spacing.MD)
            lbl = QLabel(name)
            lbl.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY};")
            row.addWidget(lbl)
            row.addWidget(ComingSoonBadge(badge_text))
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        scroll.setWidget(content)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
