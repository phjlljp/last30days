"""Tests for render.py — output rendering edge cases."""

import os
from lib import render, schema


def _empty_report(topic="test"):
    """Create an empty report for testing."""
    return schema.Report(
        topic=topic,
        range_from="2026-02-04",
        range_to="2026-03-06",
        generated_at="2026-03-06T00:00:00+00:00",
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
