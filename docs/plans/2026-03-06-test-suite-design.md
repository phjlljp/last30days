# Test Suite Design: Rebase-Confidence + Coverage

**Date:** 2026-03-06
**Goal:** Verify all functionality survives upstream syncs, cover new v2.9 modules, catch regressions.

## Infrastructure

### `pyproject.toml` (pytest section)
- `testpaths = ["tests"]`
- `pythonpath = ["scripts"]` — eliminates `sys.path.insert` hack
- Existing unittest tests run unchanged under pytest

### `tests/conftest.py`
- `fixtures_dir` — path to `fixtures/`
- `tmp_config_dir` — temp directory for config file tests (auto-cleanup)
- `project_root` — path to repo root for plugin structure tests

## A — Seam Tests (rebase danger zones)

### 1. `test_env_local_md.py` — Config loading (custom branch)
- YAML frontmatter parsing: basic, unquoted, single-quoted, comments, empty lines
- Edge cases: missing file, no frontmatter, unclosed frontmatter, colon in value, empty value
- `.env` file parsing
- Config precedence: env vars > `.local.md` > `.env`
- File permission warnings

### 2. `test_reddit_sc.py` — Reddit ScrapeCreators (v2.9)
- `_extract_core_subject()`: prefix stripping, noise word removal, product preservation
- `expand_reddit_queries()`: query count by depth (quick/default/deep)
- `discover_subreddits()`: ranking, utility penalty, name bonus, engagement bonus
- `_parse_date()`: valid timestamp, None input
- Depth config key validation

### 3. `test_instagram_sc.py` — Instagram ScrapeCreators (v2.8)
- `_tokenize()`: stopwords, synonyms, single-char removal
- `_compute_relevance()`: exact match, partial, hashtag boost, floor, empty query
- Depth config key validation

### 4. `test_reddit_enrich.py` — Comment enrichment
- `extract_reddit_path()`: valid URL, non-reddit URL
- `parse_thread_data()`: with comments, empty/malformed input
- `get_top_comments()`: sorted by score, filters deleted
- Uses `fixtures/reddit_thread_sample.json`

### 5. `test_schema_roundtrip.py` — Data class serialization
- `Engagement.to_dict()`: sparse fields, all-None
- All 6 item types: `RedditItem`, `XItem`, `YouTubeItem`, `TikTokItem`, `InstagramItem`, `WebSearchItem`
- `Comment.to_dict()`
- `cross_refs` key omitted when empty

### 6. `test_plugin_structure.py` — Plugin integrity (custom branch)
- `plugin.json`: valid JSON, required keys, `"skills"` key, fork URL
- `skills/last30days/SKILL.md`: exists, frontmatter parses with name/version/description
- Root `SKILL.md` does NOT exist
- `hooks/hooks.json`: valid JSON
- `commands/setup.md`: exists
- Hook script exists

### 7. `test_smoke.py` — End-to-end
- `--diagnose`: exits 0, valid JSON, expected keys
- `--help`: exits 0
- `--mock --topic "test"`: exits 0 (if supported)

## B — Pipeline Tests (depth coverage)

### 8. `test_render_outputs.py`
- Empty items, single source, multi-source report structure
- Context snippet length limits
- Output dir creation

### 9. `test_score_edge_cases.py`
- `log1p_safe()`: zero, negative
- `normalize_to_100()`: single item, all zeros
- Sort stability with equal scores
- Instagram engagement formula
- Reddit comment weight (10%)

### 10. `test_parallel_search.py`
- Timeout profiles (quick/default/deep)
- Source selection flags
- Diagnose source detection

## C — Snapshot Regression

### 11. `test_snapshot.py`
- `--mock --emit json --topic "test"` output matches golden file
- Update with `UPDATE_SNAPSHOTS=1 pytest tests/test_snapshot.py`
- Golden file stored at `fixtures/snapshots/mock_output.json`

## Summary

| Category | Files | Tests | Purpose |
|----------|-------|-------|---------|
| A — Seam | 7 | ~60 | Rebase conflict zones + new modules |
| B — Pipeline | 3 | ~18 | Render/score/orchestration depth |
| C — Snapshot | 1 | 1 | Catch-all regression |
| Infra | 2 | — | pyproject.toml + conftest.py |
| **Total** | **13** | **~79** | |

All tests run offline (no API calls). Expected runtime: < 1 second.
