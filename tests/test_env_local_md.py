"""Tests for env.py config loading — local_md, env_file, precedence."""

import os
import stat
from pathlib import Path

from lib import env


class TestLoadLocalMd:
    """Tests for load_local_md() YAML frontmatter parsing."""

    def test_parse_basic_frontmatter(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\nOPENAI_API_KEY: "sk-test123"\n---\n# Notes\n')
        result = env.load_local_md(f)
        assert result == {"OPENAI_API_KEY": "sk-test123"}

    def test_parse_unquoted_values(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\nKEY: value123\n---\n')
        result = env.load_local_md(f)
        assert result == {"KEY": "value123"}

    def test_parse_single_quotes(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text("---\nKEY: 'myvalue'\n---\n")
        result = env.load_local_md(f)
        assert result == {"KEY": "myvalue"}

    def test_parse_multiple_keys(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\nA: "val1"\nB: "val2"\nC: "val3"\n---\n')
        result = env.load_local_md(f)
        assert result == {"A": "val1", "B": "val2", "C": "val3"}

    def test_comments_ignored(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\n# This is a comment\nKEY: "value"\n---\n')
        result = env.load_local_md(f)
        assert result == {"KEY": "value"}

    def test_empty_lines_ignored(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\n\nKEY: "value"\n\n---\n')
        result = env.load_local_md(f)
        assert result == {"KEY": "value"}

    def test_missing_file_returns_empty(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        result = env.load_local_md(f)
        assert result == {}

    def test_no_frontmatter_returns_empty(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text("# Just markdown\nNo frontmatter here\n")
        result = env.load_local_md(f)
        assert result == {}

    def test_unclosed_frontmatter_returns_empty(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text("---\nKEY: value\nNo closing marker\n")
        result = env.load_local_md(f)
        assert result == {}

    def test_value_with_colon_in_quotes(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\nURL: "https://example.com"\n---\n')
        result = env.load_local_md(f)
        assert result == {"URL": "https://example.com"}

    def test_empty_value_skipped(self, tmp_path):
        f = tmp_path / "config.md"
        f.write_text('---\nEMPTY:\nKEY: "value"\n---\n')
        result = env.load_local_md(f)
        assert result == {"KEY": "value"}


class TestLoadEnvFile:
    """Tests for load_env_file() .env parsing."""

    def test_basic_env_file(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text('KEY=value\nANOTHER="quoted"\n')
        result = env.load_env_file(f)
        assert result == {"KEY": "value", "ANOTHER": "quoted"}

    def test_comments_and_blanks(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text('# comment\n\nKEY=value\n')
        result = env.load_env_file(f)
        assert result == {"KEY": "value"}

    def test_missing_file_returns_empty(self, tmp_path):
        f = tmp_path / "missing.env"
        result = env.load_env_file(f)
        assert result == {}

    def test_none_path_returns_empty(self):
        result = env.load_env_file(None)
        assert result == {}


class TestFilePermissions:
    """Tests for _check_file_permissions() warnings."""

    def test_warns_on_world_readable(self, tmp_path, capsys):
        f = tmp_path / "secrets.md"
        f.write_text('---\nKEY: "value"\n---\n')
        f.chmod(0o644)
        env.load_local_md(f)
        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "readable" in captured.err

    def test_no_warning_on_600(self, tmp_path, capsys):
        f = tmp_path / "secrets.md"
        f.write_text('---\nKEY: "value"\n---\n')
        f.chmod(0o600)
        env.load_local_md(f)
        captured = capsys.readouterr()
        assert "WARNING" not in captured.err


class TestSourceAvailability:
    """Tests for is_*_available() helpers."""

    def test_reddit_available_with_scrapecreators(self):
        config = {"SCRAPECREATORS_API_KEY": "sc-test"}
        assert env.is_reddit_available(config) is True

    def test_reddit_available_with_openai(self):
        config = {"OPENAI_API_KEY": "sk-test", "OPENAI_AUTH_STATUS": "ok"}
        assert env.is_reddit_available(config) is True

    def test_reddit_not_available(self):
        config = {}
        assert env.is_reddit_available(config) is False

    def test_tiktok_available(self):
        assert env.is_tiktok_available({"SCRAPECREATORS_API_KEY": "x"}) is True
        assert env.is_tiktok_available({}) is False

    def test_instagram_available(self):
        assert env.is_instagram_available({"SCRAPECREATORS_API_KEY": "x"}) is True
        assert env.is_instagram_available({}) is False

    def test_hackernews_always_available(self):
        assert env.is_hackernews_available() is True

    def test_polymarket_always_available(self):
        assert env.is_polymarket_available() is True

    def test_reddit_source_prefers_scrapecreators(self):
        config = {
            "SCRAPECREATORS_API_KEY": "sc-test",
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_AUTH_STATUS": "ok",
        }
        assert env.get_reddit_source(config) == "scrapecreators"

    def test_web_search_source_priority(self):
        config = {
            "PARALLEL_API_KEY": "p",
            "BRAVE_API_KEY": "b",
            "OPENROUTER_API_KEY": "o",
        }
        assert env.get_web_search_source(config) == "parallel"
        assert env.get_web_search_source({"BRAVE_API_KEY": "b"}) == "brave"
        assert env.get_web_search_source({"OPENROUTER_API_KEY": "o"}) == "openrouter"
        assert env.get_web_search_source({}) is None
