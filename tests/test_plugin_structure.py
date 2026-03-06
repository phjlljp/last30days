"""Tests for plugin structure integrity — verifies custom branch layout."""

import json
from pathlib import Path


class TestPluginJson:
    """Tests for .claude-plugin/plugin.json."""

    def test_valid_json(self, project_root):
        path = project_root / ".claude-plugin" / "plugin.json"
        assert path.exists(), "plugin.json missing"
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_required_keys(self, project_root):
        data = json.loads((project_root / ".claude-plugin" / "plugin.json").read_text())
        for key in ("name", "description", "version", "author", "license"):
            assert key in data, f"Missing required key: {key}"

    def test_has_skills_key(self, project_root):
        data = json.loads((project_root / ".claude-plugin" / "plugin.json").read_text())
        assert "skills" in data, "Custom branch should have 'skills' key"
        assert isinstance(data["skills"], list)

    def test_fork_url(self, project_root):
        data = json.loads((project_root / ".claude-plugin" / "plugin.json").read_text())
        assert "phjlljp/last30days" in data.get("repository", ""), \
            "Repository should point to fork"


class TestSkillMd:
    """Tests for SKILL.md location and content."""

    def test_exists_in_skills_dir(self, project_root):
        path = project_root / "skills" / "last30days" / "SKILL.md"
        assert path.exists(), "SKILL.md should be in skills/last30days/"

    def test_root_skill_md_removed(self, project_root):
        assert not (project_root / "SKILL.md").exists(), \
            "Root SKILL.md should not exist (moved to skills/)"

    def test_frontmatter_parses(self, project_root):
        text = (project_root / "skills" / "last30days" / "SKILL.md").read_text()
        assert text.startswith("---"), "SKILL.md should have YAML frontmatter"
        end = text.find("\n---", 3)
        assert end > 0, "SKILL.md frontmatter should have closing ---"
        frontmatter = text[4:end]
        assert "name:" in frontmatter
        assert "version:" in frontmatter
        assert "description:" in frontmatter

    def test_version_matches_plugin_json(self, project_root):
        plugin = json.loads((project_root / ".claude-plugin" / "plugin.json").read_text())
        text = (project_root / "skills" / "last30days" / "SKILL.md").read_text()
        end = text.find("\n---", 3)
        frontmatter = text[4:end]
        for line in frontmatter.splitlines():
            if line.strip().startswith("version:"):
                version = line.split(":", 1)[1].strip().strip('"').strip("'")
                assert version == plugin["version"], \
                    f"SKILL.md version {version} != plugin.json version {plugin['version']}"
                return
        assert False, "No version found in SKILL.md frontmatter"


class TestHooksAndCommands:
    """Tests for hooks and commands structure."""

    def test_hooks_json_valid(self, project_root):
        path = project_root / "hooks" / "hooks.json"
        assert path.exists(), "hooks.json missing"
        data = json.loads(path.read_text())
        assert "SessionStart" in data

    def test_setup_command_exists(self, project_root):
        path = project_root / "commands" / "setup.md"
        assert path.exists(), "setup.md command missing"

    def test_check_config_script_exists(self, project_root):
        path = project_root / "hooks" / "scripts" / "check-config.sh"
        assert path.exists(), "check-config.sh missing"
