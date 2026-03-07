# last30days Implementation Tasks

## Setup & Configuration
- [x] Create directory structure
- [x] Write SPEC.md
- [x] Write TASKS.md
- [x] Write SKILL.md with proper frontmatter

## Core Library Modules
- [x] scripts/lib/env.py - Environment and API key loading
- [x] scripts/lib/dates.py - Date range and confidence utilities
- [x] scripts/lib/cache.py - TTL-based caching
- [x] scripts/lib/http.py - HTTP client with retry
- [x] scripts/lib/models.py - Auto model selection
- [x] scripts/lib/schema.py - Data structures
- [x] scripts/lib/openai_reddit.py - OpenAI Responses API
- [x] scripts/lib/xai_x.py - xAI Responses API
- [x] scripts/lib/reddit_enrich.py - Reddit thread JSON fetcher
- [x] scripts/lib/normalize.py - Schema normalization
- [x] scripts/lib/score.py - Popularity scoring
- [x] scripts/lib/dedupe.py - Near-duplicate detection
- [x] scripts/lib/render.py - Output rendering

## Main Script
- [x] scripts/last30days.py - CLI orchestrator

## Fixtures
- [x] fixtures/openai_sample.json
- [x] fixtures/xai_sample.json
- [x] fixtures/reddit_thread_sample.json
- [x] fixtures/models_openai_sample.json
- [x] fixtures/models_xai_sample.json

## Tests (upstream)
- [x] tests/test_dates.py
- [x] tests/test_cache.py
- [x] tests/test_models.py
- [x] tests/test_score.py
- [x] tests/test_dedupe.py
- [x] tests/test_normalize.py
- [x] tests/test_render.py
- [x] tests/test_bird_x.py
- [x] tests/test_codex_auth.py
- [x] tests/test_cross_source.py
- [x] tests/test_hackernews.py
- [x] tests/test_openai_reddit.py
- [x] tests/test_polymarket.py
- [x] tests/test_tiktok.py
- [x] tests/test_youtube_relevance.py

## Tests (custom branch — rebase confidence + coverage)
- [x] pyproject.toml — pytest config with pythonpath
- [x] tests/conftest.py — shared fixtures
- [x] tests/test_env_local_md.py — config loading (load_local_md, env_file, source availability)
- [x] tests/test_reddit_sc.py — Reddit ScrapeCreators (extract, expand, discover, parse)
- [x] tests/test_instagram_sc.py — Instagram ScrapeCreators (tokenize, relevance, depth config)
- [x] tests/test_reddit_enrich.py — comment enrichment (parse, top comments, insights)
- [x] tests/test_schema_roundtrip.py — data class serialization for all item types
- [x] tests/test_plugin_structure.py — plugin.json, SKILL.md location, hooks, commands
- [x] tests/test_smoke.py — end-to-end (--diagnose, --help, --mock)
- [x] tests/test_render_outputs.py — render edge cases (empty items, xref tags)
- [x] tests/test_score_edge_cases.py — scoring (log1p, normalize, engagement formulas)
- [x] tests/test_parallel_search.py — source orchestration (timeout profiles, diagnose)
- [x] tests/test_snapshot.py — golden-file regression

## Validation
- [x] Run tests in mock mode
- [x] Demo --emit=compact
- [x] Demo --emit=context
- [x] Verify file tree
