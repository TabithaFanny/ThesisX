import os
from typing import List, Tuple


class TemplateManager:
    """Manage paper templates."""

    def __init__(self):
        self._template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "templates"
        )

    def get_template_list(self) -> List[Tuple[str, str]]:
        """Return list of (name, filepath) tuples."""
        templates = []
        if not os.path.exists(self._template_dir):
            return templates
        for filename in sorted(os.listdir(self._template_dir)):
            if filename.endswith(".md"):
                name = filename[:-3].replace("_", " ").title()
                filepath = os.path.join(self._template_dir, filename)
                templates.append((name, filepath))
        return templates

    def load_template(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
