---
name: brief
description: Produce a narrated visual briefing - slides plus voiceover, published as an Artifact for phone review. Use when the user asks to be briefed, walked through, or shown what happened rather than told in text ("brief me", "walk me through the results", "make me a video", "explain this visually"), and when an agent is blocked on a decision the user must make while away from their desk.
---

# Narrated visual briefings

Turn findings into a short narrated slide deck, published as an Artifact the user
opens on their phone.

## When to use this

Use it when the user asks to be shown rather than told, or when you are blocked on a
decision only they can make and they are away from the desk.

**Do not use it when a paragraph would do.** A brief costs ~40 seconds to render and a
minute of their attention. If the answer fits in three sentences, write three sentences.

## The four shapes

Set `kind` to whichever fits; it governs how you structure the deck.

| `kind` | Structure |
|---|---|
| `recap` | What the problem was -> what you changed -> what broke -> where you are stuck |
| `results` | What was run -> what the plots show -> the anomaly -> what it means |
| `concept` | The thing being explained -> how it works -> why it is built that way |
| `decision` | The situation -> the options with trade-offs -> your recommendation -> **the explicit question** |

## Writing the narration

Narration is written **for the ear**, not the eye.

- Short sentences. One idea each.
- **Speak numbers rather than expecting them to be read off an axis.** "The ninety-ninth
  percentile crosses eight hundred milliseconds at twenty past two" beats a slide where
  they must squint at a tick label.
  This is the core technique: the voice carries precision, which frees the visual to
  carry only shape. It is what makes phone-sized figures work at all.
- Never "as you can see" - they may be in read mode with no audio.
- Spell out units and symbols the way you would say them aloud.
- Target 90 seconds to 3 minutes total. Hard stop at 4.

See `references/narration-style.md` for worked before/after examples of each rule.

## Visuals

One idea per slide. Slide *count* is nearly free (the fixed chrome is about 11 KB, and
each extra slide adds roughly 0.2 KB of markup); only narration *length* costs, at
roughly 8 KB of artifact per second. **Prefer more, shorter slides over fewer dense
ones** - it suits a phone better anyway.

- `markdown` for statements and short bullets. Under 40 words on screen.
- `mermaid` for flow, sequence and architecture. Rendered natively by the Artifact
  runtime - no library, no bytes.
- `svg` for charts you author from numbers you hold. Keep `font-size` at or above
  `0.022 x viewBox width` or it will be unreadable on a phone.
- `image` for captured figures.

### Capturing figures

Whatever plotting tool produced it, **enlarge the figure's fonts before you export it**,
then write it straight to disk and reference that path in the deck.

Default axis and tick label sizes are chosen for a monitor. On a phone they become
unreadable, and no amount of downscaling afterwards recovers them - the renderer scales
the image to about 1000 px wide, so whatever was 8 pt in the original is smaller still by
the time it reaches the screen. Setting the font size at export time is the one variable
that decides whether the figure is worth including.

Export at roughly 150 DPI and at least 1000 px wide. Prefer writing to a file and passing
the path over routing a large image back through the conversation.

Crop a figure to the region that carries the argument. If a detail matters, say it in
the narration rather than expecting them to find it.

## Producing the brief

1. Write `deck.json` into the scratchpad, using its absolute path. See
   `references/deck-schema.md` for the fields and a worked example.
2. Render it with **one** command. The renderer imports as a package
   (`tools.render_brief`), so it must run with the plugin root as its working directory
   and `-m`, not by pointing `python` at the `.py` file directly. The plugin root is two
   levels above this skill's base directory (`skills/brief/`), which is given to you when
   this skill loads (a line of the form "Base directory for this skill: `<path>`").
   Substitute the real absolute paths below - do not pass the placeholders literally:

```bash
uv run --directory "<plugin-root>" --with edge-tts --with pillow python -m tools.render_brief "<absolute path to deck.json>" -o "<absolute path to brief.html>"
```

   (`${CLAUDE_PLUGIN_ROOT}` may also resolve to the plugin root where the harness expands
   it, but the skill's own base directory is the one guaranteed to be available here.)

   This must stay a single command: every extra distinct command you run is another
   chance to trip a permission prompt, and in a remote session nobody may be there to
   answer it.

   Add `--no-audio` to iterate on visuals without waiting for narration - it skips TTS
   entirely and produces a read-only brief: no audio player, and the page opens in read
   mode with every slide on one scrollable page and its transcript shown.

3. Publish `brief.html` with the `Artifact` tool. Give it a favicon and a one-sentence
   description.
4. If the brief is a `decision` and the user is away, call `PushNotification` with the
   decision needed - not "brief ready".

Read any warnings the renderer prints. They name the slide and the measured value.
