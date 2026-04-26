import json
import logging
import os

logger = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".wenbiao")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")

_DEFAULTS = {
    "window_width": 1280,
    "window_height": 800,
    "window_x": -1,
    "window_y": -1,
    "outline_width": 180,
    "editor_width": 500,
    "preview_width": 500,
    "last_open_dir": "",
    "autosave_enabled": True,
    "autosave_interval_minutes": 5,
    "editor_font_size": 12,
    "pixabay_api_key": "",
    # Theme: "light" or "dark"
    "theme": "light",
    # Custom AI model settings (empty = use built-in defaults)
    "custom_ai_api_url": "",
    "custom_ai_model": "",
    "custom_ai_api_key": "",
    # Keyboard shortcut overrides: {"action_id": "key_sequence"}
    "shortcut_overrides": {},
    # Auto-recovery: max backup versions
    "max_backup_versions": 5,
}


class Config:
    """User preference manager. Reads/writes ~/.wenbiao/config.json."""

    def __init__(self):
        self._data: dict = dict(_DEFAULTS)
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value):
        self._data[key] = value

    def save(self):
        try:
            os.makedirs(_CONFIG_DIR, exist_ok=True)
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning("配置保存失败: %s", e)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self):
        try:
            if os.path.exists(_CONFIG_FILE):
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge stored values over defaults
                self._data.update(stored)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("配置加载失败，使用默认值: %s", e)
