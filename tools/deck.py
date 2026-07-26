"""Deck schema: JSON in, validated dataclasses out.

Validation runs before any figure work or speech synthesis, so a typo in the
deck costs zero seconds of TTS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

KINDS = ("recap", "results", "concept", "decision")
VISUAL_TYPES = ("markdown", "mermaid", "svg", "image", "none")
DEFAULT_VOICE = "en-GB-RyanNeural"


class DeckError(ValueError):
    """Raised when a deck is malformed. Message names the offending JSON path."""


@dataclass(frozen=True)
class Visual:
    type: str = "none"
    value: str = ""


@dataclass(frozen=True)
class Slide:
    title: str
    narration: str
    visual: Visual = field(default_factory=Visual)


@dataclass(frozen=True)
class Deck:
    title: str
    summary: str
    kind: str
    slides: tuple[Slide, ...]
    voice: str = DEFAULT_VOICE


def _text(data: dict, key: str, path: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DeckError(f"{path}{key} must be a non-empty string")
    return value.strip()


def _visual(data: object, path: str) -> Visual:
    if data is None:
        return Visual()
    if not isinstance(data, dict):
        raise DeckError(f"{path}visual must be an object")

    kind = data.get("type", "none")
    if kind not in VISUAL_TYPES:
        raise DeckError(
            f"{path}visual.type must be one of {', '.join(VISUAL_TYPES)}; got {kind!r}"
        )

    value = data.get("value", "")
    if not isinstance(value, str):
        raise DeckError(f"{path}visual.value must be a string")
    if kind != "none" and not value.strip():
        raise DeckError(f"{path}visual.value must be non-empty for type {kind!r}")

    return Visual(type=kind, value=value if kind == "none" else value.strip())


def load_deck(data: dict) -> Deck:
    """Validate a parsed deck.json, raising DeckError naming the JSON path."""
    if not isinstance(data, dict):
        raise DeckError("deck must be a JSON object")

    title = _text(data, "title", "")
    summary = _text(data, "summary", "")

    kind = data.get("kind")
    if kind not in KINDS:
        raise DeckError(f"kind must be one of {', '.join(KINDS)}; got {kind!r}")

    voice = data.get("voice", DEFAULT_VOICE)
    if not isinstance(voice, str) or not voice.strip():
        raise DeckError("voice must be a non-empty string")

    raw_slides = data.get("slides")
    if not isinstance(raw_slides, list) or not raw_slides:
        raise DeckError("slides must be a list with at least one slide")

    slides = []
    for i, raw in enumerate(raw_slides):
        path = f"slides[{i}]."
        if not isinstance(raw, dict):
            raise DeckError(f"slides[{i}] must be an object")
        slides.append(
            Slide(
                title=_text(raw, "title", path),
                narration=_text(raw, "narration", path),
                visual=_visual(raw.get("visual"), path),
            )
        )

    return Deck(
        title=title,
        summary=summary,
        kind=kind,
        slides=tuple(slides),
        voice=voice.strip(),
    )
