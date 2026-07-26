import importlib
import sys


def test_importing_speech_does_not_import_edge_tts():
    """CI has no network and no edge-tts; importing the adapter must not need it."""
    sys.modules.pop("edge_tts", None)
    sys.modules.pop("tools.speech", None)

    importlib.import_module("tools.speech")

    assert "edge_tts" not in sys.modules
