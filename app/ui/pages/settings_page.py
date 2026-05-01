"""Settings Center page — API config, theme, connectors."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea, QFrame,
    QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox,
)

from app.ui.design_tokens import Light as L, FontSize, Radius, Spacing
from app.ui.components.base import PageHeader, SettingsSection, ComingSoonBadge, _card_style


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
