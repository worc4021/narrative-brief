import re

import pytest

from tools.deck import load_deck
from tools.render_brief import BriefTooLarge, build

DECK = {
    "title": "Checkout latency regression",
    "summary": "p99 doubled past 800ms.",
    "kind": "results",
    "slides": [
        {"title": "One", "visual": {"type": "markdown", "value": "- a"}, "narration": "First."},
        {"title": "Two", "visual": {"type": "mermaid", "value": "flowchart TD\n A-->B"},
         "narration": "Second."},
    ],
}


def test_no_audio_build_omits_audio_and_transport():
    out = build(load_deck(DECK), synth=None)
    assert "<audio" not in out.html
    assert 'class="transport"' not in out.html
    assert out.html.count('class="slide') == 2


def test_no_unreplaced_tokens():
    out = build(load_deck(DECK), synth=None)
    assert not re.search(r"__[A-Z]+__", out.html)


def test_output_is_a_fragment_with_a_title():
    out = build(load_deck(DECK), synth=None)
    assert "<title>" in out.html
    assert not re.search(r"<!doctype|<html|<body[ >]", out.html, re.I)


def test_both_theme_mechanisms_present():
    html = build(load_deck(DECK), synth=None).html
    assert "@media (prefers-color-scheme:dark)" in html
    assert ':root[data-theme="dark"]' in html
    assert ':root[data-theme="light"]' in html


def test_read_mode_is_css_not_a_second_copy():
    html = build(load_deck(DECK), synth=None).html
    assert "body.reading .slide" in html
    assert html.count(">One</h2>") == 1  # each slide title appears exactly once


def test_titles_and_narration_are_escaped():
    deck = load_deck({**DECK, "slides": [
        {"title": "a <b> & c", "narration": "x <y>"},
    ]})
    html = build(deck, synth=None).html
    assert "&lt;b&gt;" in html and "<b>" not in html


def test_wordy_slide_warns():
    words = " ".join(f"w{i}" for i in range(60))
    deck = load_deck({**DECK, "slides": [
        {"title": "Dense", "visual": {"type": "markdown", "value": words},
         "narration": "n"},
    ]})
    assert any("40" in w for w in build(deck, synth=None).warnings)


def test_oversized_brief_fails_loudly():
    deck = load_deck(DECK)
    with pytest.raises(BriefTooLarge) as err:
        build(deck, synth=None, hard_mb=0.000001)
    assert "MB" in str(err.value)


def test_over_soft_budget_warns_without_raising():
    out = build(load_deck(DECK), synth=None, max_mb=0.000001)
    assert any("soft budget" in w for w in out.warnings)


def test_missing_image_renders_a_placeholder_rather_than_crashing():
    deck = load_deck({**DECK, "slides": [
        {"title": "Gone", "visual": {"type": "image", "value": "no/such.png"},
         "narration": "n"},
    ]})
    out = build(deck, synth=None)
    assert "figure unavailable" in out.html
    assert any("no/such.png" in w for w in out.warnings)


def test_unreadable_image_renders_a_placeholder_rather_than_crashing(tmp_path):
    # A corrupt or half-written PNG (an export interrupted part way) raises
    # PIL.UnidentifiedImageError, not FileNotFoundError. The spec requires the
    # placeholder for "missing OR unreadable", so build() must survive both.
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"\x89PNG\r\n\x1a\n" + b"not actually an image")

    deck = load_deck({**DECK, "slides": [
        {"title": "Broken", "visual": {"type": "image", "value": str(corrupt)},
         "narration": "n"},
    ]})
    out = build(deck, synth=None)
    assert "figure unavailable" in out.html
    assert any("corrupt.png" in w for w in out.warnings)


def test_main_reports_a_missing_deck_cleanly(tmp_path, capsys):
    from tools.render_brief import main

    code = main([str(tmp_path / "nope.json"), "-o", str(tmp_path / "out.html")])
    assert code == 2
    assert "nope.json" in capsys.readouterr().err


FAKE_MP3 = b"\xff\xfb\x90\x00" + b"\x00" * 1020


def fake_synth(text, voice):
    assert text and voice
    return FAKE_MP3


def test_audio_build_emits_one_audio_element_per_slide():
    out = build(load_deck(DECK), synth=fake_synth)
    assert out.html.count("data:audio/mpeg;base64,") == 2
    assert 'class="transport"' in out.html


def test_one_failing_slide_degrades_to_silent_and_does_not_raise():
    def flaky(text, voice):
        if text == "First.":
            raise RuntimeError("voice service unavailable")
        return FAKE_MP3

    out = build(load_deck(DECK), synth=flaky)
    assert out.html.count("data:audio/mpeg;base64,") == 1
    assert any("slide 1" in w and "narration failed" in w for w in out.warnings)
    assert 'class="slide is-current show-transcript"' in out.html


def test_total_failure_yields_a_read_only_brief():
    def dead(text, voice):
        raise RuntimeError("offline")

    out = build(load_deck(DECK), synth=dead)
    assert "<audio" not in out.html
    assert 'class="transport"' not in out.html
    assert any("read-only" in w for w in out.warnings)


def test_audio_data_i_carries_the_true_slide_index_when_synthesis_fails():
    # The player keys its audio array by data-i, not by DOM order, because only
    # narrated slides emit an audio element. If these ever became 0,1 again the
    # player would play slide 2's narration over slide 1.
    deck = load_deck({**DECK, "slides": [
        {"title": "One", "narration": "First."},
        {"title": "Two", "narration": "Second."},
        {"title": "Three", "narration": "Third."},
    ]})

    def flaky(text, voice):
        if text == "First.":
            raise RuntimeError("voice service unavailable")
        return FAKE_MP3

    html = build(deck, synth=flaky).html
    assert re.findall(r'<audio data-i="(\d+)"', html) == ["1", "2"]
    # every slide still gets its own progress segment, so seg index == slide index
    assert re.findall(r'<button class="seg" type="button" data-i="(\d+)"', html) == [
        "0", "1", "2",
    ]


def test_synth_receives_the_decks_voice():
    seen = []
    build(load_deck({**DECK, "voice": "en-GB-SoniaNeural"}),
          synth=lambda t, v: seen.append(v) or FAKE_MP3)
    assert seen == ["en-GB-SoniaNeural", "en-GB-SoniaNeural"]
