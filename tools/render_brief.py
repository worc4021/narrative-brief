"""Orchestration: validated deck -> one self-contained HTML brief.

Ordering matters. Schema, figures and legibility are checked BEFORE any speech
synthesis, so a malformed deck costs zero seconds of TTS.

Speech synthesis is an injected callable, never imported at module scope, so the
test suite runs without network access.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from tools.deck import Deck, DeckError, load_deck
from tools.plates import AssetStore
from tools.visuals import MAX_WORDS_PER_SLIDE, Rendered, esc, render_visual, word_count

TEMPLATE = Path(__file__).with_name("player.html")
# max_mb (the caller's taste, e.g. "this brief is getting long") and the hard
# ceiling (a property of the publishing platform, e.g. "past here it stops
# being publishable") are independent: the hard ceiling does not scale with
# max_mb, so a tight --max-mb does not start refusing briefs that would
# otherwise publish fine.
HARD_LIMIT_MB = 8.0

Synth = Callable[[str, str], bytes]


class BriefTooLarge(RuntimeError):
    """Raised when the assembled brief exceeds the hard size limit."""


@dataclass(frozen=True)
class Result:
    html: str
    warnings: tuple[str, ...] = ()


TRANSPORT = """<footer class="transport">
    <div class="segs">__SEGS__</div>
    <div class="keys">
      <button class="key" id="prev" type="button" aria-label="Previous slide">
        <svg viewBox="0 0 24 24"><path d="M15 5v14l-9-7z"/></svg></button>
      <button class="key main" id="play" type="button" aria-label="Play">
        <svg viewBox="0 0 24 24"><path id="pic" d="M7 4v16l13-8z"/></svg></button>
      <button class="key" id="next" type="button" aria-label="Next slide">
        <svg viewBox="0 0 24 24"><path d="M9 5v14l9-7z"/></svg></button>
      <span class="time" id="time">—:—</span>
    </div>
  </footer>"""


def build(
    deck: Deck,
    *,
    synth: Synth | None = None,
    assets: AssetStore | None = None,
    max_mb: float = 4.0,
    hard_mb: float = HARD_LIMIT_MB,
) -> Result:
    """Assemble the brief. `synth=None` produces a read-only deck with no audio."""
    store = assets or AssetStore()
    warnings: list[str] = []

    # --- Phase 1: visuals and legibility. No TTS spend yet. -------------------
    fragments: list[str] = []
    for i, slide in enumerate(deck.slides):
        try:
            rendered = render_visual(slide.visual, store.src)
        except OSError:
            # A figure that is missing OR unreadable must not sink an otherwise
            # deliverable brief. OSError covers both: FileNotFoundError, and
            # PIL's UnidentifiedImageError for a corrupt or half-written capture
            # (an export interrupted part way is entirely realistic).
            # Report the path as given in the deck (not str(exc)'s Path repr,
            # which normalises to OS-native separators and would break on Windows).
            warnings.append(
                f"slide {i + 1}: figure could not be read: {slide.visual.value}; "
                f"rendering a placeholder"
            )
            rendered = Rendered('<p class="missing">figure unavailable</p>')
        warnings.extend(f"slide {i + 1}: {w}" for w in rendered.warnings)

        words = word_count(rendered.html)
        if words > MAX_WORDS_PER_SLIDE:
            warnings.append(
                f"slide {i + 1}: {words} words on screen (over {MAX_WORDS_PER_SLIDE}); "
                f"the narration should be carrying this"
            )
        fragments.append(rendered.html)

    warnings.extend(store.warnings)

    # --- Phase 2: narration. The slow, network-bound step. --------------------
    audio: list[str | None] = [None] * len(deck.slides)
    if synth is not None:
        for i, slide in enumerate(deck.slides):
            try:
                mp3 = synth(slide.narration, deck.voice)
            except Exception as exc:  # one bad slide must not sink the brief
                warnings.append(
                    f"slide {i + 1}: narration failed ({exc}); "
                    f"rendering it silent with the transcript shown"
                )
                continue
            audio[i] = f"data:audio/mpeg;base64,{base64.b64encode(mp3).decode('ascii')}"

        if not any(audio):
            warnings.append(
                "no narration could be synthesised; emitting a read-only brief"
            )

    has_audio = any(a is not None for a in audio)

    # --- Phase 3: assemble ----------------------------------------------------
    slides_html = "\n".join(
        f'<section class="slide{" is-current" if i == 0 else ""}{"" if audio[i] else " show-transcript"}" data-i="{i}">'
        f'<p class="eyebrow">{i + 1:02d} / {len(deck.slides):02d}</p>'
        f"<h2>{esc(slide.title)}</h2>"
        f'<div class="visual">{fragments[i]}</div>'
        f'<p class="transcript">{esc(slide.narration)}</p>'
        f"</section>"
        for i, slide in enumerate(deck.slides)
    )

    if has_audio:
        segs = "\n".join(
            f'<button class="seg" type="button" data-i="{i}" '
            f'aria-label="Slide {i + 1}"><span></span></button>'
            for i in range(len(deck.slides))
        )
        transport = TRANSPORT.replace("__SEGS__", segs)
        audio_html = "\n".join(
            f'<audio data-i="{i}" preload="auto" src="{src}"></audio>'
            for i, src in enumerate(audio)
            if src
        )
    else:
        transport = ""
        audio_html = ""

    html = TEMPLATE.read_text(encoding="utf-8")
    for token, value in {
        "__TITLE__": esc(deck.title),
        "__SUMMARY__": esc(deck.summary),
        "__SLIDES__": slides_html,
        "__TRANSPORT__": transport,
        "__AUDIO__": audio_html,
    }.items():
        html = html.replace(token, value)

    # --- Phase 4: budget ------------------------------------------------------
    size_mb = len(html.encode("utf-8")) / 1_000_000
    if size_mb > hard_mb:
        raise BriefTooLarge(
            f"brief is {size_mb:.1f} MB, over the {hard_mb:.1f} MB hard limit. "
            f"Narration is ~8 KB of artifact per second — shorten it, or cut slides."
        )
    if size_mb > max_mb:
        warnings.append(
            f"brief is {size_mb:.1f} MB, over the {max_mb} MB soft budget; "
            f"consider shortening the narration"
        )

    return Result(html=html, warnings=tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a narrated brief to one HTML file.")
    parser.add_argument("deck", type=Path, help="path to deck.json")
    parser.add_argument("-o", "--out", type=Path, required=True, help="output .html path")
    parser.add_argument("--voice", default=None, help="override the deck's voice")
    parser.add_argument("--no-audio", action="store_true", help="skip TTS; read-mode only")
    parser.add_argument("--max-mb", type=float, default=4.0, help="soft size budget")
    args = parser.parse_args(argv)

    try:
        deck = load_deck(json.loads(args.deck.read_text(encoding="utf-8")))
    except (OSError, DeckError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.voice:
        deck = replace(deck, voice=args.voice)

    synth = None
    if not args.no_audio:
        from tools.speech import edge_synth

        synth = edge_synth

    try:
        result = build(deck, synth=synth, max_mb=args.max_mb)
    except BriefTooLarge as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    args.out.write_text(result.html, encoding="utf-8")
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    kb = len(result.html.encode("utf-8")) / 1024
    print(f"wrote {args.out} ({kb:.0f} KB, {len(deck.slides)} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
