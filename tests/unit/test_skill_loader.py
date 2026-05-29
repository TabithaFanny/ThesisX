"""Tests for SkillLoader."""

import pytest
import json
import tempfile
from pathlib import Path
from app.core.skills.loader import SkillLoader, Skill


class TestSkillLoader:
    def test_load_local_skills_empty_dir(self, tmp_path):
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert skills == []

    def test_load_json_skill(self, tmp_path):
        skill_file = tmp_path / "academic_polish.json"
        skill_file.write_text(json.dumps({
            "name": "学术润色",
            "description": "Polish academic writing",
            "prompt": "You are an academic writing assistant.",
            "category": "editing",
        }), encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert len(skills) == 1
        assert skills[0].name == "学术润色"
        assert skills[0].category == "editing"

    def test_load_markdown_skill(self, tmp_path):
        # JSON code block format is reliable
        skill_file = tmp_path / "logic_review.md"
        skill_file.write_text("""```json
{"name": "逻辑审查", "description": "Review logical consistency", "prompt": "检查论文逻辑一致性。", "category": "review"}
```
""", encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert len(skills) == 1
        assert skills[0].name == "逻辑审查"
        assert skills[0].category == "review"

    def test_load_markdown_with_json_block(self, tmp_path):
        skill_file = tmp_path / "citation_verify.md"
        skill_file.write_text("""```json
{"name": "引用核查", "description": "Verify citations", "prompt": "Check citation format.", "category": "review"}
```
""", encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert len(skills) == 1
        assert skills[0].name == "引用核查"

    def test_load_ignores_nonexistent(self, tmp_path):
        (tmp_path / "valid.json").write_text(json.dumps({
            "name": "Valid", "description": "", "prompt": ""
        }), encoding="utf-8")
        (tmp_path / "invalid.badext").write_text("invalid", encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert len(skills) == 1
        assert skills[0].name == "Valid"


class TestSkillLoaderRendering:
    def test_render_empty(self, tmp_path):
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        md = loader.render_selected_skills_md(skills)
        assert "未加载" in md
        assert "# Selected Skills" in md

    def test_render_with_skills(self, tmp_path):
        skill_file = tmp_path / "polish.json"
        skill_file.write_text(json.dumps({
            "name": "Academic Polish",
            "description": "Polish academic writing",
            "prompt": "Polish this text.",
            "category": "editing",
        }), encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        md = loader.render_selected_skills_md(skills)
        assert "Academic Polish" in md
        assert "Polish this text." in md


class TestSkill:
    def test_skill_from_file_json(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(json.dumps({
            "name": "Test Skill",
            "description": "Test description",
            "prompt": "Test prompt text",
            "category": "writing",
        }), encoding="utf-8")
        loader = SkillLoader(base_dir=tmp_path)
        skills = loader.load_local_skills()
        assert len(skills) == 1
        assert skills[0].name == "Test Skill"
        assert skills[0].file_path == str(path)
