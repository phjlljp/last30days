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
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=120)
        assert rc == 0, f"--mock failed: {stderr}"

    def test_mock_json_valid(self):
        rc, stdout, stderr = _run(["--mock", "--emit", "json", "test topic"], timeout=120)
        data = json.loads(stdout)
        assert "topic" in data
        assert data["topic"] == "test topic"
