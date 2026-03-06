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
    def test_basic_engagement(self):
        eng = schema.Engagement(score=100, num_comments=50, upvote_ratio=0.9)
        raw = score.compute_reddit_engagement_raw(eng)
        assert raw is not None
        assert raw > 0

    def test_comment_quality_weight(self):
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
        items = [
            schema.RedditItem(id="R1", title="first", url="u", subreddit="s", score=50, date="2026-03-01"),
            schema.RedditItem(id="R2", title="second", url="u", subreddit="s", score=50, date="2026-03-01"),
        ]
        sorted_items = score.sort_items(items)
        assert len(sorted_items) == 2
