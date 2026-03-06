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
        capture_output=True, text=True, timeout=120,
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
            return

        assert GOLDEN_FILE.exists(), (
            "Golden file missing. Generate with: "
            "UPDATE_SNAPSHOTS=1 pytest tests/test_snapshot.py -v"
        )

        golden = json.loads(GOLDEN_FILE.read_text())

        # Compare structure (keys), not volatile values (dates, scores may shift).
        # Error keys (e.g. tiktok_error, instagram_error) come and go depending
        # on live API availability, so exclude them from the comparison.
        def _stable_keys(d):
            return {k for k in d.keys() if not k.endswith("_error")}

        assert _stable_keys(current) == _stable_keys(golden), \
            f"Top-level keys changed: {_stable_keys(current) ^ _stable_keys(golden)}"

        # Compare topic
        assert current["topic"] == golden["topic"]

        # Sources that use real fixtures in mock mode (deterministic counts).
        # Only reddit and x are fully mocked; youtube/tiktok/instagram use
        # yt-dlp and ScrapeCreators (live), and hackernews/polymarket hit
        # their live APIs too.
        MOCKED_SOURCES = {"reddit", "x"}

        # Compare source sections exist with same item counts
        for source_key in ("reddit", "x", "youtube", "tiktok", "instagram", "hackernews", "polymarket", "web"):
            if source_key in golden:
                assert source_key in current, f"Missing source section: {source_key}"
                current_items = current.get(source_key, [])
                golden_items = golden.get(source_key, [])
                if isinstance(golden_items, list) and isinstance(current_items, list):
                    if source_key in MOCKED_SOURCES:
                        # Fully mocked — exact count must match
                        assert len(current_items) == len(golden_items), \
                            f"{source_key}: item count changed ({len(golden_items)} -> {len(current_items)})"
                    else:
                        # Live sources: just verify the list type is preserved
                        # (count varies between runs due to live API responses)
                        assert isinstance(current_items, list), \
                            f"{source_key}: expected list, got {type(current_items).__name__}"
