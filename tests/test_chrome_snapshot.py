import re
from pathlib import Path

import pytest

from tools.deck import load_deck
from tools.render_brief import build

SNAPSHOT = Path(__file__).parent / "snapshots" / "chrome.html"

MINIMAL = {
    "title": "Snapshot",
    "summary": "Fixed input for the chrome snapshot.",
    "kind": "concept",
    "slides": [{"title": "Only slide", "narration": "Only narration."}],
}

# Minimal valid MP3 header for testing; synth returns this for every narration
FAKE_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 1020


def _fake_synth(text: str, voice: str) -> bytes:
    """Fake synth that returns fixed audio bytes for testing."""
    return FAKE_MP3


def current_chrome() -> str:
    """The brief with all payloads stripped, so only player chrome remains."""
    html = build(load_deck(MINIMAL), synth=_fake_synth).html
    # Strip all data: URIs to baseline markers. Assumes they sit inside double quotes;
    # if a future template emits data: inside single-quoted strings, adjust the pattern.
    return re.sub(r"data:[^\"]+", "data:STRIPPED", html)


def test_player_chrome_matches_snapshot():
    if not SNAPSHOT.exists():
        pytest.fail(
            f"no snapshot yet. Review the output, then write it:\n"
            f"  python -c \"from tests.test_chrome_snapshot import current_chrome, SNAPSHOT; "
            f"SNAPSHOT.parent.mkdir(exist_ok=True); "
            f"SNAPSHOT.write_text(current_chrome(), encoding='utf-8')\""
        )
    assert current_chrome() == SNAPSHOT.read_text(encoding="utf-8"), (
        "Player chrome changed. If intended, delete tests/snapshots/chrome.html "
        "and re-run to regenerate, then review the diff in the commit."
    )
