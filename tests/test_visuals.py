from tools.deck import Visual
from tools.visuals import Rendered, esc, render_visual, word_count

STUB = lambda path: f"data:image/webp;base64,STUB[{path}]"


def test_none_visual_renders_nothing():
    out = render_visual(Visual(), STUB)
    assert out == Rendered(html="", warnings=())


def test_markdown_bullets_bold_and_code():
    md = "Cache notes:\n- **p99** doubled\n- try `staggered_ttl`"
    html = render_visual(Visual("markdown", md), STUB).html
    assert "<p>Cache notes:</p>" in html
    assert "<ul>" in html and html.count("<li>") == 2
    assert "<strong>p99</strong>" in html
    assert "<code>staggered_ttl</code>" in html


def test_markdown_escapes_html():
    html = render_visual(Visual("markdown", "a < b & c"), STUB).html
    assert "&lt;" in html and "&amp;" in html
    assert "<b>" not in html


def test_mermaid_is_escaped_and_wrapped():
    html = render_visual(Visual("mermaid", "flowchart TD\n A-->B"), STUB).html
    assert html.startswith('<pre class="mermaid">')
    assert "A--&gt;B" in html


def test_svg_passes_through_untouched():
    svg = '<svg viewBox="0 0 600 300"><text font-size="17">ok</text></svg>'
    out = render_visual(Visual("svg", svg), STUB)
    assert out.html == svg
    assert out.warnings == ()


def test_svg_below_font_floor_warns():
    svg = '<svg viewBox="0 0 600 300"><text font-size="9">tiny</text></svg>'
    out = render_visual(Visual("svg", svg), STUB)
    assert len(out.warnings) == 1
    assert "font-size" in out.warnings[0]
    assert "13.2" in out.warnings[0]


def test_svg_without_a_viewbox_warns_that_the_floor_is_uncheckable():
    # Reachable whenever an agent authors a viewBox-less (or single-quoted) svg;
    # this warning is the only feedback it gets that the check was skipped.
    svg = "<svg width='600' height='300'><text font-size='9'>tiny</text></svg>"
    out = render_visual(Visual("svg", svg), STUB)
    assert out.html == svg  # still passed through verbatim
    assert out.warnings == ("svg has no viewBox; cannot check the legibility floor",)

    # A single-quoted viewBox is not recognised either, and reports the same way
    # rather than silently claiming the floor was checked.
    single = "<svg viewBox='0 0 600 300'><text font-size='9'>tiny</text></svg>"
    assert render_visual(Visual("svg", single), STUB).warnings == (
        "svg has no viewBox; cannot check the legibility floor",
    )


def test_image_uses_the_resolver_and_is_zoomable():
    html = render_visual(Visual("image", "figs/latency.png"), STUB).html
    assert 'class="plate"' in html
    assert "STUB[figs/latency.png]" in html


def test_word_count_ignores_markup():
    assert word_count("<p>one two</p><ul><li>three</li></ul>") == 3


def test_esc_handles_the_three_dangerous_characters():
    assert esc('<a & "b">') == "&lt;a &amp; &quot;b&quot;&gt;"
