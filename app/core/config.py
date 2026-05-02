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
    # Agent Team (AI 论文初稿助手)
    "agent_team_path": "",
    "agent_team_default_journal": "中文核心",
    "agent_team_default_mode": "mock",
    "agent_team_default_budget_cny": 10.0,
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
    # Providers.json read/write
    # ------------------------------------------------------------------

    def load_providers(self) -> dict:
        """Load ~/.wenbiao/providers.json. Returns empty dict if missing."""
        providers_path = os.path.join(_CONFIG_DIR, "providers.json")
        try:
            if os.path.exists(providers_path):
                with open(providers_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("providers.json 加载失败: %s", e)
        return {}

    def save_providers(self, data: dict) -> None:
        """Atomic write to ~/.wenbiao/providers.json."""
        providers_path = os.path.join(_CONFIG_DIR, "providers.json")
        try:
            os.makedirs(_CONFIG_DIR, exist_ok=True)
            tmp_path = providers_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, providers_path)
        except OSError as e:
            logger.warning("providers.json 保存失败: %s", e)

    def get_agent_team_config(self) -> dict:
        """Return unified Agent Team configuration, merged from all sources.

        Priority: environment variables > config.json > built-in defaults.

        Returns a dict with:
            agent_team_path, api_key, base_url, model,
            default_journal, default_mode, default_budget_cny
        """
        # API key: env DEEPSEEK_API_KEY > OPENAI_API_KEY > AI_API_KEY > config
        api_key = (
            os.environ.get("DEEPSEEK_API_KEY", "")
            or os.environ.get("OPENAI_API_KEY", "")
            or os.environ.get("AI_API_KEY", "")
            or self.get("custom_ai_api_key", "")
        )

        # Base URL: env OPENAI_BASE_URL > config custom_ai_api_url > default
        base_url = (
            os.environ.get("OPENAI_BASE_URL", "")
            or self.get("custom_ai_api_url", "")
            or "https://api.openai.com/v1"
        )

        # Model: env OPENAI_MODEL > config custom_ai_model > default
        model = (
            os.environ.get("OPENAI_MODEL", "")
            or self.get("custom_ai_model", "")
            or "gpt-4o-mini"
        )

        agent_team_path = self.get("agent_team_path", "")

        return {
            "agent_team_path": agent_team_path,
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "default_journal": self.get("agent_team_default_journal", "中文核心"),
            "default_mode": self.get("agent_team_default_mode", "mock"),
            "default_budget_cny": self.get("agent_team_default_budget_cny", 10.0),
        }

    def get_agent_team_config_health(self) -> dict:
        """Check the health of Agent Team configuration without making API calls.

        Returns:
            dict with 'ok' (bool), 'issues' (list[str]), 'warnings' (list[str]).
        """
        cfg = self.get_agent_team_config()
        issues: list[str] = []
        warnings: list[str] = []

        # Check agent_team_path
        path = (cfg.get("agent_team_path") or "").strip()
        if not path or path == "未选择":
            issues.append("Agent Team 路径未设置（当前为'未选择'），请在设置中配置路径。")
        elif not os.path.isdir(path):
            issues.append(f"Agent Team 路径不存在: {path}")
        else:
            pkg_dir = os.path.join(path, "academic_agent_team")
            if not os.path.isdir(pkg_dir):
                issues.append(f"路径中未找到 academic_agent_team 包: {path}")
            else:
                # Run contract detection
                from .pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter
                check = AgentTeamCompatAdapter.validate_agent_team_contract(path)
                if not check.supported:
                    issues.append(f"Agent Team 契约不支持: {check.reason}")
                else:
                    if check.contract_type != "tui_runner":
                        warnings.append(
                            f"Agent Team 契约类型为 {check.contract_type}，"
                            "当前只有 tui_runner 支持真实执行，其他契约走 dry-run 适配。"
                        )

        # Check API key
        api_key = cfg.get("api_key", "")
        if not api_key:
            warnings.append(
                "API Key 未设置。Mock 模式不需要 API Key；"
                "Real 模式需要设置 OPENAI_API_KEY 环境变量或在 config.json 中配置 custom_ai_api_key。"
            )
        else:
            masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            warnings.append(f"API Key 已配置 ({masked})。确认余额充足后再使用 Real 模式。")

        # Check base_url — always has a sensible default; warn if not explicitly set
        base_url = cfg.get("base_url", "")
        is_default_url = base_url == "https://api.openai.com/v1"
        custom_url_set = bool(os.environ.get("OPENAI_BASE_URL", "") or self.get("custom_ai_api_url", ""))
        if is_default_url and not custom_url_set:
            warnings.append(
                "Base URL 使用默认值 https://api.openai.com/v1（未显式设置 OPENAI_BASE_URL 或 custom_ai_api_url）。"
            )

        # Check model
        model = cfg.get("model", "")
        if not model:
            warnings.append("模型未指定，将使用默认值 gpt-4o-mini。")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config_snapshot": {
                "agent_team_path": path if path and path != "未选择" else "",
                "api_key_configured": bool(api_key),
                "base_url": base_url,
                "model": model,
            },
        }

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
