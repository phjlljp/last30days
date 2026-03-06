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
        script_text = (Path(__file__).parent.parent / "scripts" / "last30days.py").read_text()
        assert "TIMEOUT_PROFILES" in script_text
        assert '"quick"' in script_text or "'quick'" in script_text
        assert '"deep"' in script_text or "'deep'" in script_text


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
