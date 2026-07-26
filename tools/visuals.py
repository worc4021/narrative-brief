"""Visual types -> HTML fragments, plus the mechanically checkable legibility rules.

The SVG font floor derives from render geometry: a slide card is at most ~600 CSS px
wide, so font-size F in a viewBox of width W renders at F * 600 / W CSS px. Holding
that at or above ~13 px gives the 0.022 * W floor.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from tools.deck import Visual

SVG_FONT_RATIO = 0.022
MAX_WORDS_PER_SLIDE = 40


@dataclass(frozen=True)
class Rendered:
    html: str
    warnings: tuple[str, ...] = ()


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def word_count(html: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", html).split())


def _inline(text: str) -> str:
    """Escape, then apply the inline markdown subset: **bold** and `code`."""
    out = esc(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`(.+?)`", r"<code>\1</code>", out)
    return out


def _markdown(src: str) -> str:
    """A deliberately tiny subset: '- ' bullets, **bold**, `code`, and paragraphs."""
    parts: list[str] = []
    bullets: list[str] = []

    def flush() -> None:
        if bullets:
            parts.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for raw in src.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith("- "):
            bullets.append(_inline(line[2:].strip()))
        else:
            flush()
            parts.append(f"<p>{_inline(line)}</p>")
    flush()
    return "".join(parts)


def _svg_warnings(svg: str) -> tuple[str, ...]:
    box = re.search(r'viewBox\s*=\s*"[\d.\-]+\s+[\d.\-]+\s+([\d.]+)', svg)
    if not box:
        return ('svg has no viewBox; cannot check the legibility floor',)

    floor = SVG_FONT_RATIO * float(box.group(1))
    sizes = [float(s) for s in re.findall(r'font-size\s*=\s*"([\d.]+)', svg)]
    sizes += [float(s) for s in re.findall(r"font-size\s*:\s*([\d.]+)", svg)]
    small = sorted({s for s in sizes if s < floor})
    if not small:
        return ()
    return (
        f"svg font-size {', '.join(str(s) for s in small)} is below the "
        f"{floor:.1f} floor for this viewBox; text will be hard to read on a phone",
    )


def render_visual(visual: Visual, image_src: Callable[[str], str]) -> Rendered:
    """Render one slide's visual to an HTML fragment plus any legibility warnings."""
    kind = visual.type

    if kind == "none":
        return Rendered("")

    if kind == "markdown":
        return Rendered(_markdown(visual.value))

    if kind == "mermaid":
        return Rendered(f'<pre class="mermaid">{esc(visual.value)}</pre>')

    if kind == "svg":
        return Rendered(visual.value, _svg_warnings(visual.value))

    if kind == "image":
        src = image_src(visual.value)
        return Rendered(
            f'<button class="plate" type="button" aria-label="Zoom figure">'
            f'<img src="{src}" alt="{esc(visual.value)}" /></button>'
        )

    raise ValueError(f"unhandled visual type {kind!r}")
