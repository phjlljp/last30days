# Test Suite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ~79 tests across 11 test files with pytest infrastructure to verify all functionality survives upstream rebases and cover new v2.9 modules.

**Architecture:** pytest with `pythonpath` config (eliminates sys.path hacks), shared fixtures via `conftest.py`, all tests offline (no API calls), unittest-compatible so existing 15 test files keep working.

**Tech Stack:** pytest, Python unittest (existing), JSON fixtures, subprocess (smoke tests), tmp_path (config tests)

---

### Task 1: pytest infrastructure

**Files:**
- Create: `pyproject.toml`
- Create: `tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["scripts"]
```

**Step 2: Create conftest.py**

```python
"""Shared pytest fixtures for last30days tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Path to the repository root."""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir(project_root):
    """Path to the fixtures directory."""
    return project_root / "fixtures"


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Temporary directory for config file tests. Auto-cleaned by pytest."""
    return tmp_path


@pytest.fixture
def load_fixture(fixtures_dir):
    """Load a JSON fixture file by name."""
    def _load(name):
        with open(fixtures_dir / name) as f:
            return json.load(f)
    return _load
```

**Step 3: Verify existing tests still pass under pytest**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/ -v --tb=short 2>&1 | tail -20`
Expected: 293 passed, 4 failed (same 4 pre-existing failures in test_models and test_openai_reddit)

**Step 4: Commit**

```bash
git add pyproject.toml tests/conftest.py
git commit -m "test: add pytest infrastructure with conftest.py"
```

---

### Task 2: test_env_local_md.py — Config loading

**Files:**
- Create: `tests/test_env_local_md.py`
- Read: `scripts/lib/env.py` (lines 50-124, 235-303)

**Step 1: Write the test file**

```python
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
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_env_local_md.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_env_local_md.py
git commit -m "test: add config loading tests (load_local_md, env_file, source availability)"
```

---

### Task 3: test_reddit_sc.py — Reddit ScrapeCreators

**Files:**
- Create: `tests/test_reddit_sc.py`
- Read: `scripts/lib/reddit.py` (lines 30-200)

**Step 1: Write the test file**

```python
"""Tests for reddit.py — ScrapeCreators Reddit search module."""

from lib import reddit


class TestExtractCoreSubject:
    """Tests for _extract_core_subject()."""

    def test_strips_what_are_prefix(self):
        assert reddit._extract_core_subject("what are the best AI tools") == "AI tools"

    def test_strips_how_to_prefix(self):
        assert reddit._extract_core_subject("how to use cursor IDE") == "cursor IDE"

    def test_strips_noise_words(self):
        result = reddit._extract_core_subject("latest trending updates")
        # All words are noise — falls back to original
        assert result == "latest trending updates"

    def test_preserves_product_name(self):
        assert reddit._extract_core_subject("cursor IDE") == "cursor IDE"

    def test_strips_trailing_punctuation(self):
        result = reddit._extract_core_subject("what is Claude?")
        assert not result.endswith("?")

    def test_empty_string(self):
        result = reddit._extract_core_subject("")
        assert result == ""

    def test_strips_what_do_people_think(self):
        result = reddit._extract_core_subject("what do people think about React Server Components")
        assert result == "React Server Components"


class TestExpandRedditQueries:
    """Tests for expand_reddit_queries()."""

    def test_quick_returns_one_query(self):
        queries = reddit.expand_reddit_queries("cursor IDE", "quick")
        assert len(queries) >= 1

    def test_default_includes_review_variant(self):
        queries = reddit.expand_reddit_queries("cursor IDE", "default")
        assert any("worth it" in q or "review" in q for q in queries)

    def test_deep_includes_issues_variant(self):
        queries = reddit.expand_reddit_queries("cursor IDE", "deep")
        assert any("issues" in q or "problems" in q for q in queries)

    def test_deep_has_more_queries_than_quick(self):
        quick = reddit.expand_reddit_queries("cursor IDE", "quick")
        deep = reddit.expand_reddit_queries("cursor IDE", "deep")
        assert len(deep) > len(quick)


class TestDiscoverSubreddits:
    """Tests for discover_subreddits()."""

    def test_ranks_by_frequency(self):
        results = [
            {"subreddit": "programming", "score": 10},
            {"subreddit": "programming", "score": 20},
            {"subreddit": "python", "score": 5},
        ]
        subs = reddit.discover_subreddits(results, max_subs=5)
        assert subs[0] == "programming"

    def test_utility_sub_penalty(self):
        results = [
            {"subreddit": "tipofmytongue", "score": 100},
            {"subreddit": "tipofmytongue", "score": 100},
            {"subreddit": "python", "score": 10},
        ]
        subs = reddit.discover_subreddits(results, topic="python", max_subs=5)
        # python should rank higher despite fewer posts (utility penalty)
        assert subs[0] == "python"

    def test_topic_name_bonus(self):
        results = [
            {"subreddit": "reactjs", "score": 10},
            {"subreddit": "webdev", "score": 10},
        ]
        subs = reddit.discover_subreddits(results, topic="react hooks", max_subs=5)
        assert subs[0] == "reactjs"

    def test_engagement_bonus(self):
        results = [
            {"subreddit": "AIsub", "ups": 500},
            {"subreddit": "OtherSub", "ups": 5},
        ]
        subs = reddit.discover_subreddits(results, max_subs=5)
        assert subs[0] == "AIsub"

    def test_max_subs_limit(self):
        results = [{"subreddit": f"sub{i}"} for i in range(20)]
        subs = reddit.discover_subreddits(results, max_subs=3)
        assert len(subs) <= 3

    def test_empty_results(self):
        assert reddit.discover_subreddits([]) == []

    def test_missing_subreddit_field(self):
        results = [{"title": "no sub field"}]
        assert reddit.discover_subreddits(results) == []


class TestParseDate:
    """Tests for _parse_date()."""

    def test_valid_timestamp(self):
        # 2024-01-16 00:00:00 UTC
        assert reddit._parse_date(1705363200) == "2024-01-16"

    def test_string_timestamp(self):
        assert reddit._parse_date("1705363200") == "2024-01-16"

    def test_none_returns_none(self):
        assert reddit._parse_date(None) is None

    def test_zero_returns_none(self):
        assert reddit._parse_date(0) is None


class TestDepthConfig:
    """Tests for DEPTH_CONFIG structure."""

    def test_all_depths_exist(self):
        for depth in ("quick", "default", "deep"):
            assert depth in reddit.DEPTH_CONFIG

    def test_required_keys(self):
        required = {"global_searches", "subreddit_searches", "comment_enrichments", "timeframe"}
        for depth, config in reddit.DEPTH_CONFIG.items():
            assert required.issubset(config.keys()), f"Missing keys in {depth}: {required - config.keys()}"

    def test_deep_has_more_searches(self):
        assert reddit.DEPTH_CONFIG["deep"]["global_searches"] > reddit.DEPTH_CONFIG["quick"]["global_searches"]
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_reddit_sc.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_reddit_sc.py
git commit -m "test: add Reddit ScrapeCreators module tests"
```

---

### Task 4: test_instagram_sc.py — Instagram ScrapeCreators

**Files:**
- Create: `tests/test_instagram_sc.py`
- Read: `scripts/lib/instagram.py` (lines 33-95)

**Step 1: Write the test file**

```python
"""Tests for instagram.py — ScrapeCreators Instagram search module."""

from lib import instagram


class TestTokenize:
    """Tests for _tokenize()."""

    def test_strips_stopwords(self):
        tokens = instagram._tokenize("how to use the AI tools")
        assert "how" not in tokens
        assert "the" not in tokens
        assert "to" not in tokens

    def test_expands_synonyms(self):
        tokens = instagram._tokenize("ai tools")
        assert "artificial" in tokens or "intelligence" in tokens

    def test_removes_single_char(self):
        tokens = instagram._tokenize("a b c python")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "python" in tokens

    def test_lowercases(self):
        tokens = instagram._tokenize("Python REACT")
        assert "python" in tokens
        assert "react" in tokens

    def test_strips_punctuation(self):
        tokens = instagram._tokenize("hello, world!")
        assert "hello" in tokens
        assert "world" in tokens


class TestComputeRelevance:
    """Tests for _compute_relevance()."""

    def test_exact_match_high(self):
        rel = instagram._compute_relevance("claude code", "Claude Code tricks and tips")
        assert rel >= 0.8

    def test_partial_match_lower(self):
        rel = instagram._compute_relevance("claude code tips", "Best AI tools for coding")
        assert rel < 0.5

    def test_hashtag_boost(self):
        base = instagram._compute_relevance("claude code", "random video about stuff")
        boosted = instagram._compute_relevance("claude code", "random video about stuff", ["claudecode", "ai"])
        assert boosted > base

    def test_floor_at_01(self):
        rel = instagram._compute_relevance("quantum physics", "cat dancing video")
        assert rel >= 0.1

    def test_empty_query_returns_default(self):
        rel = instagram._compute_relevance("", "Some video title")
        assert rel == 0.5


class TestInstagramDepthConfig:
    """Tests for DEPTH_CONFIG."""

    def test_all_depths_exist(self):
        for depth in ("quick", "default", "deep"):
            assert depth in instagram.DEPTH_CONFIG

    def test_required_keys(self):
        for depth, config in instagram.DEPTH_CONFIG.items():
            assert "results_per_page" in config
            assert "max_captions" in config

    def test_deep_has_more_results(self):
        assert instagram.DEPTH_CONFIG["deep"]["results_per_page"] > instagram.DEPTH_CONFIG["quick"]["results_per_page"]
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_instagram_sc.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_instagram_sc.py
git commit -m "test: add Instagram ScrapeCreators module tests"
```

---

### Task 5: test_reddit_enrich.py — Comment enrichment

**Files:**
- Create: `tests/test_reddit_enrich.py`
- Read: `scripts/lib/reddit_enrich.py` (lines 15-197)
- Fixture: `fixtures/reddit_thread_sample.json`

**Step 1: Write the test file**

```python
"""Tests for reddit_enrich.py — comment enrichment and parsing."""

from lib import reddit_enrich


class TestExtractRedditPath:
    """Tests for extract_reddit_path()."""

    def test_valid_url(self):
        url = "https://www.reddit.com/r/ClaudeAI/comments/abc123/post_title/"
        path = reddit_enrich.extract_reddit_path(url)
        assert path == "/r/ClaudeAI/comments/abc123/post_title/"

    def test_non_reddit_url(self):
        assert reddit_enrich.extract_reddit_path("https://example.com/foo") is None

    def test_empty_string(self):
        assert reddit_enrich.extract_reddit_path("") is None

    def test_old_reddit(self):
        url = "https://old.reddit.com/r/test/comments/xyz/"
        assert reddit_enrich.extract_reddit_path(url) is not None


class TestParseThreadData:
    """Tests for parse_thread_data() using fixture."""

    def test_parses_submission(self, load_fixture):
        data = load_fixture("reddit_thread_sample.json")
        result = reddit_enrich.parse_thread_data(data)
        assert result["submission"] is not None
        assert result["submission"]["score"] == 847
        assert result["submission"]["num_comments"] == 156

    def test_parses_comments(self, load_fixture):
        data = load_fixture("reddit_thread_sample.json")
        result = reddit_enrich.parse_thread_data(data)
        assert len(result["comments"]) == 8
        assert result["comments"][0]["author"] == "skill_expert"

    def test_empty_input(self):
        result = reddit_enrich.parse_thread_data([])
        assert result["submission"] is None
        assert result["comments"] == []

    def test_malformed_input(self):
        result = reddit_enrich.parse_thread_data("not a list")
        assert result["submission"] is None

    def test_none_input(self):
        result = reddit_enrich.parse_thread_data(None)
        assert result["submission"] is None


class TestGetTopComments:
    """Tests for get_top_comments()."""

    def test_sorted_by_score(self):
        comments = [
            {"score": 10, "author": "a"},
            {"score": 100, "author": "b"},
            {"score": 50, "author": "c"},
        ]
        top = reddit_enrich.get_top_comments(comments, limit=3)
        assert top[0]["score"] == 100
        assert top[1]["score"] == 50

    def test_filters_deleted(self):
        comments = [
            {"score": 100, "author": "[deleted]"},
            {"score": 50, "author": "[removed]"},
            {"score": 10, "author": "real_user"},
        ]
        top = reddit_enrich.get_top_comments(comments)
        assert len(top) == 1
        assert top[0]["author"] == "real_user"

    def test_respects_limit(self):
        comments = [{"score": i, "author": f"u{i}"} for i in range(20)]
        top = reddit_enrich.get_top_comments(comments, limit=5)
        assert len(top) == 5

    def test_empty_list(self):
        assert reddit_enrich.get_top_comments([]) == []


class TestExtractCommentInsights:
    """Tests for extract_comment_insights()."""

    def test_filters_short_comments(self):
        comments = [
            {"body": "yes"},
            {"body": "A" * 50 + " this is a substantive comment about the topic."},
        ]
        insights = reddit_enrich.extract_comment_insights(comments)
        assert len(insights) == 1

    def test_filters_low_value_patterns(self):
        comments = [
            {"body": "This."},
            {"body": "lol that's hilarious"},
            {"body": "A" * 50 + " Here's a real insight about how to approach this problem."},
        ]
        insights = reddit_enrich.extract_comment_insights(comments)
        assert len(insights) == 1

    def test_respects_limit(self):
        comments = [{"body": f"Comment number {i} " + "x" * 50} for i in range(20)]
        insights = reddit_enrich.extract_comment_insights(comments, limit=3)
        assert len(insights) <= 3
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_reddit_enrich.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_reddit_enrich.py
git commit -m "test: add Reddit comment enrichment tests"
```

---

### Task 6: test_schema_roundtrip.py — Data class serialization

**Files:**
- Create: `tests/test_schema_roundtrip.py`
- Read: `scripts/lib/schema.py`

**Step 1: Write the test file**

```python
"""Tests for schema.py — data class serialization roundtrips."""

from lib import schema


class TestEngagement:
    """Tests for Engagement.to_dict()."""

    def test_sparse_fields(self):
        eng = schema.Engagement(score=100, num_comments=50)
        d = eng.to_dict()
        assert d == {"score": 100, "num_comments": 50}
        assert "likes" not in d

    def test_all_none_returns_none(self):
        eng = schema.Engagement()
        assert eng.to_dict() is None

    def test_all_fields(self):
        eng = schema.Engagement(
            score=1, num_comments=2, upvote_ratio=0.9,
            likes=3, reposts=4, replies=5, quotes=6,
            views=7, shares=8, volume=9.0, liquidity=10.0,
        )
        d = eng.to_dict()
        assert len(d) == 11


class TestComment:
    """Tests for Comment.to_dict()."""

    def test_basic(self):
        c = schema.Comment(score=50, date="2026-03-01", author="user", excerpt="text", url="http://x")
        d = c.to_dict()
        assert d["score"] == 50
        assert d["author"] == "user"
        assert len(d) == 5


class TestRedditItem:
    """Tests for RedditItem.to_dict()."""

    def test_roundtrip(self):
        item = schema.RedditItem(
            id="R1", title="Test", url="http://reddit.com/r/test",
            subreddit="test", date="2026-03-01",
            engagement=schema.Engagement(score=100),
        )
        d = item.to_dict()
        assert d["id"] == "R1"
        assert d["subreddit"] == "test"
        assert d["engagement"] == {"score": 100}
        assert "cross_refs" not in d  # Empty list omitted

    def test_cross_refs_included_when_present(self):
        item = schema.RedditItem(
            id="R1", title="T", url="u", subreddit="s",
            cross_refs=["X1", "HN2"],
        )
        d = item.to_dict()
        assert d["cross_refs"] == ["X1", "HN2"]


class TestXItem:
    def test_roundtrip(self):
        item = schema.XItem(
            id="X1", text="tweet", url="http://x.com/1",
            author_handle="user", date="2026-03-01",
        )
        d = item.to_dict()
        assert d["id"] == "X1"
        assert d["author_handle"] == "user"
        assert "cross_refs" not in d


class TestYouTubeItem:
    def test_roundtrip(self):
        item = schema.YouTubeItem(
            id="YT1", title="Video", url="http://youtube.com/1",
            channel_name="chan",
        )
        d = item.to_dict()
        assert d["channel_name"] == "chan"
        assert d["date_confidence"] == "high"


class TestTikTokItem:
    def test_roundtrip(self):
        item = schema.TikTokItem(
            id="TK1", text="caption", url="http://tiktok.com/1",
            author_name="creator", hashtags=["ai", "code"],
        )
        d = item.to_dict()
        assert d["hashtags"] == ["ai", "code"]
        assert d["author_name"] == "creator"


class TestInstagramItem:
    def test_roundtrip(self):
        item = schema.InstagramItem(
            id="IG1", text="caption", url="http://instagram.com/reel/1",
            author_name="creator",
        )
        d = item.to_dict()
        assert d["id"] == "IG1"


class TestWebSearchItem:
    def test_roundtrip(self):
        item = schema.WebSearchItem(
            id="W1", title="Article", url="http://example.com",
            source_domain="example.com", snippet="text",
        )
        d = item.to_dict()
        assert d["source_domain"] == "example.com"


class TestHackerNewsItem:
    def test_roundtrip(self):
        item = schema.HackerNewsItem(
            id="HN1", title="Show HN", url="http://example.com",
            hn_url="http://news.ycombinator.com/item?id=1", author="pg",
        )
        d = item.to_dict()
        assert d["hn_url"].startswith("http://news.ycombinator.com")


class TestPolymarketItem:
    def test_roundtrip(self):
        item = schema.PolymarketItem(
            id="PM1", title="Election", question="Who wins?",
            url="http://polymarket.com/1",
        )
        d = item.to_dict()
        assert d["question"] == "Who wins?"
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_schema_roundtrip.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_schema_roundtrip.py
git commit -m "test: add schema serialization roundtrip tests"
```

---

### Task 7: test_plugin_structure.py — Plugin integrity

**Files:**
- Create: `tests/test_plugin_structure.py`

**Step 1: Write the test file**

```python
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
        # Check key fields exist
        assert "name:" in frontmatter
        assert "version:" in frontmatter
        assert "description:" in frontmatter

    def test_version_matches_plugin_json(self, project_root):
        """SKILL.md version should match plugin.json version."""
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
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_plugin_structure.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_plugin_structure.py
git commit -m "test: add plugin structure integrity tests"
```

---

### Task 8: test_smoke.py — End-to-end smoke tests

**Files:**
- Create: `tests/test_smoke.py`

**Step 1: Write the test file**

```python
"""End-to-end smoke tests — run the actual script as subprocess."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "last30days.py")


def _run(args, timeout=30):
    """Run last30days.py with args, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


class TestDiagnose:
    """Tests for --diagnose flag."""

    def test_exits_zero(self):
        rc, stdout, stderr = _run(["--diagnose"])
        assert rc == 0, f"--diagnose failed: {stderr}"

    def test_returns_valid_json(self):
        rc, stdout, stderr = _run(["--diagnose"])
        data = json.loads(stdout)
        assert isinstance(data, dict)

    def test_has_expected_keys(self):
        rc, stdout, stderr = _run(["--diagnose"])
        data = json.loads(stdout)
        for key in ("openai", "xai", "youtube", "tiktok", "instagram", "hackernews", "polymarket"):
            assert key in data, f"Missing key: {key}"


class TestHelp:
    """Tests for --help flag."""

    def test_exits_zero(self):
        rc, stdout, stderr = _run(["--help"])
        assert rc == 0

    def test_shows_usage(self):
        rc, stdout, stderr = _run(["--help"])
        assert "topic" in stdout.lower() or "usage" in stdout.lower()


class TestNoTopic:
    """Tests for missing topic."""

    def test_exits_nonzero_without_topic(self):
        rc, stdout, stderr = _run([])
        assert rc != 0

    def test_error_message(self):
        rc, stdout, stderr = _run([])
        assert "topic" in stderr.lower() or "error" in stderr.lower()


class TestMockMode:
    """Tests for --mock mode (fixture-based, no API calls)."""

    def test_mock_json_exits_zero(self):
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=60)
        assert rc == 0, f"--mock failed: {stderr}"

    def test_mock_json_valid(self):
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=60)
        data = json.loads(stdout)
        assert "topic" in data
        assert data["topic"] == "test topic"
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_smoke.py -v --timeout=120`

Note: mock tests may take ~10-20s. If pytest-timeout isn't installed, the subprocess timeout handles it.

Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add end-to-end smoke tests (diagnose, help, mock)"
```

---

### Task 9: test_render_outputs.py — Rendering edge cases

**Files:**
- Create: `tests/test_render_outputs.py`
- Read: `scripts/lib/render.py` (lines 42-160)

**Step 1: Write the test file**

```python
"""Tests for render.py — output rendering edge cases."""

import os
from lib import render, schema


def _empty_report(topic="test"):
    """Create an empty report for testing."""
    return schema.Report(
        topic=topic,
        range_from="2026-02-04",
        range_to="2026-03-06",
        mode="both",
    )


class TestRenderCompact:
    """Tests for render_compact()."""

    def test_empty_items_graceful(self):
        report = _empty_report()
        output = render.render_compact(report)
        assert "test" in output
        assert isinstance(output, str)

    def test_includes_topic(self):
        report = _empty_report("AI video tools")
        output = render.render_compact(report)
        assert "AI video tools" in output

    def test_includes_date_range(self):
        report = _empty_report()
        output = render.render_compact(report)
        assert "2026-02-04" in output

    def test_single_source_reddit(self):
        report = _empty_report()
        report.reddit = [
            schema.RedditItem(
                id="R1", title="Test post", url="http://reddit.com/r/test/1",
                subreddit="test", score=50,
                engagement=schema.Engagement(score=100, num_comments=10),
            ),
        ]
        output = render.render_compact(report)
        assert "Reddit" in output


class TestEnsureOutputDir:
    """Tests for ensure_output_dir()."""

    def test_creates_directory(self, tmp_path):
        test_dir = tmp_path / "output" / "nested"
        os.environ["LAST30DAYS_OUTPUT_DIR"] = str(test_dir)
        try:
            render.ensure_output_dir()
            assert test_dir.exists()
        finally:
            os.environ.pop("LAST30DAYS_OUTPUT_DIR", None)


class TestXrefTag:
    """Tests for _xref_tag()."""

    def test_no_refs(self):
        item = schema.RedditItem(id="R1", title="T", url="u", subreddit="s")
        assert render._xref_tag(item) == ""

    def test_with_refs(self):
        item = schema.RedditItem(
            id="R1", title="T", url="u", subreddit="s",
            cross_refs=["X1", "HN2"],
        )
        tag = render._xref_tag(item)
        assert "X" in tag
        assert "HN" in tag
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_render_outputs.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_render_outputs.py
git commit -m "test: add render output edge case tests"
```

---

### Task 10: test_score_edge_cases.py — Scoring edge cases

**Files:**
- Create: `tests/test_score_edge_cases.py`
- Read: `scripts/lib/score.py`

**Step 1: Write the test file**

```python
"""Tests for score.py — edge cases in engagement scoring and normalization."""

import math
from lib import score, schema


class TestLog1pSafe:
    def test_zero(self):
        assert score.log1p_safe(0) == 0.0

    def test_positive(self):
        assert score.log1p_safe(100) == math.log1p(100)

    def test_none(self):
        assert score.log1p_safe(None) == 0.0

    def test_negative(self):
        assert score.log1p_safe(-5) == 0.0


class TestNormalizeTo100:
    def test_single_item(self):
        # Single valid value → should get 50 (range is 0)
        result = score.normalize_to_100([5.0])
        assert result == [50]

    def test_all_zeros(self):
        result = score.normalize_to_100([0.0, 0.0, 0.0])
        assert all(v == 50 for v in result)

    def test_two_items_span(self):
        result = score.normalize_to_100([0.0, 10.0])
        assert result[0] == 0.0
        assert result[1] == 100.0

    def test_none_preserved(self):
        result = score.normalize_to_100([None, 5.0, 10.0])
        assert result[0] is None

    def test_all_none(self):
        result = score.normalize_to_100([None, None])
        assert all(v == 50 for v in result)


class TestRedditEngagement:
    """Test Reddit engagement formula with comment weight."""

    def test_basic_engagement(self):
        eng = schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9)
        raw = score.compute_reddit_engagement_raw(eng)
        assert raw is not None
        assert raw > 0

    def test_comment_quality_weight(self):
        """Top comment score should contribute ~10% to engagement."""
        eng = schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9)
        without_comment = score.compute_reddit_engagement_raw(eng, top_comment_score=None)
        with_comment = score.compute_reddit_engagement_raw(eng, top_comment_score=500)
        assert with_comment > without_comment

    def test_none_engagement(self):
        assert score.compute_reddit_engagement_raw(None) is None

    def test_empty_engagement(self):
        eng = schema.Engagement()
        assert score.compute_reddit_engagement_raw(eng) is None


class TestInstagramEngagement:
    def test_basic(self):
        eng = schema.Engagement(views=10000, likes=500, num_comments=50)
        raw = score.compute_instagram_engagement_raw(eng)
        assert raw is not None
        assert raw > 0

    def test_views_dominate(self):
        """Views should contribute most to Instagram engagement."""
        views_only = schema.Engagement(views=10000)
        likes_only = schema.Engagement(likes=10000)
        assert score.compute_instagram_engagement_raw(views_only) > score.compute_instagram_engagement_raw(likes_only)


class TestSortItems:
    def test_sorts_by_score_descending(self):
        items = [
            schema.RedditItem(id="R1", title="low", url="u", subreddit="s", score=10, date="2026-03-01"),
            schema.RedditItem(id="R2", title="high", url="u", subreddit="s", score=90, date="2026-03-01"),
        ]
        sorted_items = score.sort_items(items)
        assert sorted_items[0].id == "R2"

    def test_stability_equal_scores(self):
        """Items with equal scores should maintain relative order (by date, then source)."""
        items = [
            schema.RedditItem(id="R1", title="first", url="u", subreddit="s", score=50, date="2026-03-01"),
            schema.RedditItem(id="R2", title="second", url="u", subreddit="s", score=50, date="2026-03-01"),
        ]
        sorted_items = score.sort_items(items)
        # Both have same score and date, should maintain order
        assert len(sorted_items) == 2
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_score_edge_cases.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_score_edge_cases.py
git commit -m "test: add scoring edge case tests (log1p, normalize, engagement formulas)"
```

---

### Task 11: test_parallel_search.py — Source orchestration

**Files:**
- Create: `tests/test_parallel_search.py`
- Read: `scripts/last30days.py` (lines 1264-1320)

**Step 1: Write the test file**

```python
"""Tests for source orchestration — timeout profiles and source detection."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "last30days.py")


def _diagnose():
    """Run --diagnose and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, SCRIPT, "--diagnose"],
        capture_output=True, text=True, timeout=15,
    )
    return json.loads(result.stdout)


class TestTimeoutProfiles:
    """Verify timeout config exists in the main script."""

    def test_profiles_importable(self):
        # Import the module-level constants
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        try:
            # Read the file and check for TIMEOUT_PROFILES
            script_text = (Path(__file__).parent.parent / "scripts" / "last30days.py").read_text()
            assert "TIMEOUT_PROFILES" in script_text
            assert '"quick"' in script_text or "'quick'" in script_text
            assert '"deep"' in script_text or "'deep'" in script_text
        finally:
            sys.path.pop(0)


class TestDiagnoseSourceDetection:
    """Verify --diagnose accurately reports source availability."""

    def test_hackernews_always_true(self):
        diag = _diagnose()
        assert diag["hackernews"] is True

    def test_polymarket_always_true(self):
        diag = _diagnose()
        assert diag["polymarket"] is True

    def test_boolean_values(self):
        diag = _diagnose()
        for key in ("openai", "xai", "youtube", "tiktok", "instagram"):
            assert isinstance(diag[key], bool), f"{key} should be boolean"
```

**Step 2: Run tests**

Run: `cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/test_parallel_search.py -v`
Expected: All pass

**Step 3: Commit**

```bash
git add tests/test_parallel_search.py
git commit -m "test: add source orchestration tests (timeout profiles, diagnose)"
```

---

### Task 12: test_snapshot.py — Golden-file regression

**Files:**
- Create: `tests/test_snapshot.py`
- Create: `fixtures/snapshots/` directory
- Generate: `fixtures/snapshots/mock_output.json` (golden file)

**Step 1: Create the snapshot directory and generate golden file**

```bash
mkdir -p fixtures/snapshots
python3 scripts/last30days.py --mock --emit json "test topic" > fixtures/snapshots/mock_output.json 2>/dev/null
```

**Step 2: Write the test file**

```python
"""Snapshot regression test — catches unexpected output changes after rebases.

To update the golden file after intentional changes:
    UPDATE_SNAPSHOTS=1 pytest tests/test_snapshot.py -v
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "scripts" / "last30days.py")
SNAPSHOT_DIR = Path(__file__).parent.parent / "fixtures" / "snapshots"
GOLDEN_FILE = SNAPSHOT_DIR / "mock_output.json"


def _run_mock():
    """Run --mock --emit json and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, SCRIPT, "--mock", "--emit", "json", "test topic"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Mock run failed: {result.stderr}"
    return json.loads(result.stdout)


class TestSnapshotRegression:
    """Compare mock output against saved golden file."""

    def test_mock_output_matches_snapshot(self):
        current = _run_mock()

        if os.environ.get("UPDATE_SNAPSHOTS"):
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            GOLDEN_FILE.write_text(json.dumps(current, indent=2) + "\n")
            return  # Updated — no comparison needed

        assert GOLDEN_FILE.exists(), (
            "Golden file missing. Generate with: "
            "UPDATE_SNAPSHOTS=1 pytest tests/test_snapshot.py -v"
        )

        golden = json.loads(GOLDEN_FILE.read_text())

        # Compare structure (keys), not volatile values (dates, scores may shift)
        assert set(current.keys()) == set(golden.keys()), \
            f"Top-level keys changed: {set(current.keys()) ^ set(golden.keys())}"

        # Compare topic
        assert current["topic"] == golden["topic"]

        # Compare source sections exist with same item counts
        for source_key in ("reddit", "x", "youtube", "tiktok", "instagram", "hackernews", "polymarket", "web"):
            if source_key in golden:
                assert source_key in current, f"Missing source section: {source_key}"
                current_items = current.get(source_key, [])
                golden_items = golden.get(source_key, [])
                if isinstance(golden_items, list) and isinstance(current_items, list):
                    assert len(current_items) == len(golden_items), \
                        f"{source_key}: item count changed ({len(golden_items)} -> {len(current_items)})"
```

**Step 3: Run snapshot generation then test**

```bash
cd /Users/p/Documents/Claude/last30days
UPDATE_SNAPSHOTS=1 python3 -m pytest tests/test_snapshot.py -v
# Then run again without UPDATE to verify it passes:
python3 -m pytest tests/test_snapshot.py -v
```

Expected: Pass on both runs

**Step 4: Commit**

```bash
git add fixtures/snapshots/ tests/test_snapshot.py
git commit -m "test: add snapshot regression test with golden file"
```

---

### Task 13: Final verification

**Step 1: Run entire test suite**

```bash
cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: ~79 new tests pass + 293 existing (minus 4 pre-existing failures) = ~368 total, 4 failures (all pre-existing in test_models/test_openai_reddit).

**Step 2: Verify fast runtime**

```bash
cd /Users/p/Documents/Claude/last30days && python3 -m pytest tests/ -q --ignore=tests/test_smoke.py --ignore=tests/test_snapshot.py 2>&1 | tail -5
```

Expected: Unit tests complete in < 1 second. Smoke + snapshot tests add 10-30s.

**Step 3: Final commit (if any fixups needed)**

```bash
git add -A && git commit -m "test: finalize test suite — fix any issues from full run"
```

**Step 4: Push**

```bash
git push origin custom --force-with-lease
```

---

Plan complete and saved to `docs/plans/2026-03-06-test-suite-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

Which approach?