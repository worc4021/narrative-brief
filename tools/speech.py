"""edge-tts adapter. The ONLY module that touches the speech engine.

`import edge_tts` lives inside the function on purpose: the test suite must run
on a machine with no network and no engine installed.
"""

from __future__ import annotations

import asyncio


def edge_synth(text: str, voice: str) -> bytes:
    """Synthesise `text` to MP3 bytes (24 kHz / 48 kbps mono) using edge-tts."""
    import edge_tts

    async def run() -> bytes:
        buf = bytearray()
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk["type"] == "audio":
                buf.extend(chunk["data"])
        if not buf:
            raise RuntimeError(f"edge-tts returned no audio for voice {voice!r}")
        return bytes(buf)

    return asyncio.run(run())
