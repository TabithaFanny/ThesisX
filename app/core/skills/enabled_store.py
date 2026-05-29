"""EnabledSkillsStore — persists which skills are enabled (Vision 3.8).

Stores enabled skill file names in ~/.wenbiao/skills_enabled.json.
"""

from __future__ import annotations

import json
from pathlib import Path


class EnabledSkillsStore:
    """Persist which skills are enabled for AI injection."""

    FILE = Path.home() / ".wenbiao" / "skills_enabled.json"

    def __init__(self):
        self._enabled: set[str] = set()

    def load(self) -> set[str]:
        """Load enabled skill names from disk."""
        if not self.FILE.exists():
            return set()
        try:
            data = json.loads(self.FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._enabled = set(data)
            else:
                self._enabled = set()
        except Exception:
            self._enabled = set()
        return self._enabled

    def save(self, enabled: set[str]) -> None:
        """Save enabled skill names to disk."""
        self.FILE.parent.mkdir(parents=True, exist_ok=True)
        self.FILE.write_text(
            json.dumps(sorted(enabled), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_enabled(self, skill_name: str) -> bool:
        return skill_name in self._enabled

    def enable(self, skill_name: str) -> None:
        self._enabled.add(skill_name)
        self.save(self._enabled)

    def disable(self, skill_name: str) -> None:
        self._enabled.discard(skill_name)
        self.save(self._enabled)

    def toggle(self, skill_name: str) -> bool:
        """Toggle enabled state. Returns new state (True=enabled)."""
        if skill_name in self._enabled:
            self.disable(skill_name)
            return False
        else:
            self.enable(skill_name)
            return True
