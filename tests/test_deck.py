import pytest

from tools.deck import Deck, DeckError, Slide, Visual, load_deck

GOOD = {
    "title": "Checkout latency regression",
    "summary": "p99 doubled past 800ms.",
    "kind": "decision",
    "slides": [
        {
            "title": "What I found",
            "visual": {"type": "markdown", "value": "- p99 doubled"},
            "narration": "Latency held until twenty past two, then doubled.",
        }
    ],
}


def test_loads_a_valid_deck():
    deck = load_deck(GOOD)
    assert isinstance(deck, Deck)
    assert deck.title == "Checkout latency regression"
    assert deck.kind == "decision"
    assert deck.voice == "en-GB-RyanNeural"
    assert len(deck.slides) == 1
    assert deck.slides[0].visual.type == "markdown"


def test_voice_can_be_overridden():
    assert load_deck({**GOOD, "voice": "en-GB-SoniaNeural"}).voice == "en-GB-SoniaNeural"


def test_visual_may_be_omitted_and_defaults_to_none_type():
    data = {**GOOD, "slides": [{"title": "T", "narration": "N"}]}
    assert load_deck(data).slides[0].visual == Visual(type="none", value="")


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda d: d.pop("title"), "title"),
        (lambda d: d.update(kind="musical"), "kind"),
        (lambda d: d.update(slides=[]), "at least one slide"),
        (lambda d: d["slides"][0].update(narration=""), "slides[0].narration"),
        (lambda d: d["slides"][0]["visual"].update(type="hologram"), "slides[0].visual.type"),
        (lambda d: d["slides"][0]["visual"].update(value=""), "slides[0].visual.value"),
    ],
)
def test_rejects_bad_decks_naming_the_json_path(mutate, fragment):
    import copy

    data = copy.deepcopy(GOOD)
    mutate(data)
    with pytest.raises(DeckError) as err:
        load_deck(data)
    assert fragment in str(err.value)
