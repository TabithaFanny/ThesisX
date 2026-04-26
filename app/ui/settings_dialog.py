"""
settings_dialog.py — 设置对话框

提供 AI 模型、API 地址、API Key 等配置的可视化编辑界面。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """General settings dialog with tabs."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(520)
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # ── AI Tab ──
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)

        ai_group = QGroupBox("AI 模型配置")
        form = QFormLayout()

        self._api_url = QLineEdit()
        self._api_url.setPlaceholderText("留空使用内置地址")
        form.addRow("API 地址:", self._api_url)

        self._model = QLineEdit()
        self._model.setPlaceholderText("留空使用内置模型")
        form.addRow("模型名称:", self._model)

        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key.setPlaceholderText("留空使用环境变量或 config.ini")
        form.addRow("API Key:", self._api_key)

        self._pixabay_key = QLineEdit()
        self._pixabay_key.setPlaceholderText("用于图片搜索（可选）")
        form.addRow("Pixabay Key:", self._pixabay_key)

        ai_group.setLayout(form)
        ai_layout.addWidget(ai_group)

        hint = QLabel(
            "提示：自定义 API 地址需兼容 OpenAI Chat Completions 接口格式。\n"
            "支持本地模型（如 Ollama、LM Studio）：填入本地地址即可。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 12px; margin-top: 4px;")
        ai_layout.addWidget(hint)
        ai_layout.addStretch()

        tabs.addTab(ai_tab, "AI 模型")

        # ── General Tab ──
        gen_tab = QWidget()
        gen_layout = QVBoxLayout(gen_tab)

        save_group = QGroupBox("自动保存")
        save_form = QFormLayout()
        self._autosave_enabled = QCheckBox("启用自动保存")
        save_form.addRow(self._autosave_enabled)
        self._autosave_interval = QSpinBox()
        self._autosave_interval.setRange(1, 60)
        self._autosave_interval.setSuffix(" 分钟")
        save_form.addRow("保存间隔:", self._autosave_interval)
        self._max_backups = QSpinBox()
        self._max_backups.setRange(1, 20)
        save_form.addRow("最大备份版本:", self._max_backups)
        save_group.setLayout(save_form)
        gen_layout.addWidget(save_group)
        gen_layout.addStretch()

        tabs.addTab(gen_tab, "常规")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_values(self):
        self._api_url.setText(self._config.get("custom_ai_api_url", ""))
        self._model.setText(self._config.get("custom_ai_model", ""))
        self._api_key.setText(self._config.get("custom_ai_api_key", ""))
        self._pixabay_key.setText(self._config.get("pixabay_api_key", ""))
        self._autosave_enabled.setChecked(self._config.get("autosave_enabled", True))
        self._autosave_interval.setValue(self._config.get("autosave_interval_minutes", 5))
        self._max_backups.setValue(self._config.get("max_backup_versions", 5))

    def _save(self):
        self._config.set("custom_ai_api_url", self._api_url.text().strip())
        self._config.set("custom_ai_model", self._model.text().strip())
        self._config.set("custom_ai_api_key", self._api_key.text().strip())
        self._config.set("pixabay_api_key", self._pixabay_key.text().strip())
        self._config.set("autosave_enabled", self._autosave_enabled.isChecked())
        self._config.set("autosave_interval_minutes", self._autosave_interval.value())
        self._config.set("max_backup_versions", self._max_backups.value())
        self._config.save()

        # Apply AI config at runtime
        from app.core.ai_service import configure_ai

        configure_ai(
            api_url=self._api_url.text().strip(),
            model=self._model.text().strip(),
            api_key=self._api_key.text().strip(),
        )

        QMessageBox.information(self, "设置", "设置已保存。部分更改在重启后生效。")
        self.accept()
