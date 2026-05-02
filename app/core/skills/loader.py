"""Skill loader — reads local skill definitions from ~/.wenbiao/skills/.

Supports JSON (.json) and Markdown (.md) with JSON body.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    """A named writing/paper skill that can be injected into the context."""

    name: str
    description: str
    prompt: str
    category: str = "general"
    file_path: str = ""


class SkillLoader:
    """Scans ~/.wenbiao/skills/ for skill definition files."""

    SKILLS_DIR = Path.home() / ".wenbiao" / "skills"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.skills_dir = Path(base_dir or self.SKILLS_DIR).expanduser()

    def load_local_skills(self) -> list[Skill]:
        """Load all skill files from the skills directory.

        Supported formats:
        - JSON (.json) — {"name": "...", "description": "...", "prompt": "...", "category": "..."}
        - Markdown (.md) — JSON body between ```json fences, or YAML frontmatter

        Returns an empty list if the skills directory does not exist.
        """
        if not self.skills_dir.is_dir():
            return []

        skills: list[Skill] = []
        for path in self.skills_dir.iterdir():
            if path.is_file() and path.suffix.lower() in (".json", ".md"):
                skill = self._load_file(path)
                if skill:
                    skills.append(skill)
        return skills

    def _load_file(self, path: Path) -> Skill | None:
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                return self._parse_json(text, str(path))
            elif path.suffix.lower() == ".md":
                return self._parse_markdown(text, str(path))
        except Exception:
            return None

    def _parse_json(self, text: str, file_path: str) -> Skill | None:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                stem = Path(file_path).stem
                return Skill(
                    name=str(data.get("name", stem)),
                    description=str(data.get("description", "")),
                    prompt=str(data.get("prompt", "")),
                    category=str(data.get("category", "general")),
                    file_path=file_path,
                )
        except Exception:
            pass
        return None

    def _parse_markdown(self, text: str, file_path: str) -> Skill | None:
        """Parse Markdown with optional YAML frontmatter or JSON code block.

        YAML frontmatter format:
        ---
        name: Academic Polish
        description: Polish academic writing
        category: editing
        ---
        # Academic Polish

        Your paper writing prompt here...

        JSON code block format:
        ```json
        {"name": "Academic Polish", "description": "...", "prompt": "..."}
        ```
        """
        # Try YAML frontmatter
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()
                skill = self._parse_yaml_frontmatter(frontmatter, str(path))
                if skill:
                    # If prompt is empty in frontmatter, use body
                    if not skill.prompt:
                        skill.prompt = body.strip()
                    return skill

        # Try JSON code block
        json_match = re.search(
            r"```json\s*(\{.*?\})\s*```", text, re.DOTALL
        )
        if json_match:
            return self._parse_json(json_match.group(1), file_path)

        # Fallback: treat as plain markdown with filename as name
        name = path.stem.replace("-", " ").replace("_", " ").title()
        return Skill(
            name=name,
            description=f"Skill from {path.name}",
            prompt=text.strip()[:1000],
            category="general",
            file_path=file_path,
        )

    def _parse_yaml_frontmatter(self, text: str, file_path: str) -> Skill | None:
        """Parse simple YAML frontmatter (flat key: value pairs)."""
        data: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ": " in line:
                key, val = line.split(": ", 1)
                data[key.strip()] = val.strip().strip('"').strip("'")
            elif ":" in line:
                key = line.split(":")[0].strip()
                data[key] = ""
        if not data:
            return None
        stem = Path(file_path).stem
        return Skill(
            name=data.get("name", stem),
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            category=data.get("category", "general"),
            file_path=file_path,
        )

    def render_selected_skills_md(self, skills: list[Skill]) -> str:
        """Render a selected_skills.md compatible markdown list."""
        if not skills:
            return "# Selected Skills\n\n（未加载任何本地技能）\n"
        lines = ["# Selected Skills", ""]
        for s in skills:
            lines.append(f"## {s.name}")
            if s.description:
                lines.append(f"*{s.description}*")
            lines.append("")
            lines.append(s.prompt)
            lines.append("")
        return "\n".join(lines)
