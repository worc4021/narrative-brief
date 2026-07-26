# narrative-brief

A Claude Code plugin that turns an agent's findings into a short narrated slide deck —
a self-contained HTML file, published as an Artifact — so you can review what happened
from your phone instead of reading a wall of text at your desk.

It exists for the case where you asked an agent to do something, walked away, and now
either want to see the results or are blocked on a decision only you can make. The
`brief` skill (`skills/brief/SKILL.md`) teaches an agent when to reach for this, how to
structure the four kinds of brief (`recap`, `results`, `concept`, `decision`), and how
to write narration for the ear rather than the eye. The renderer (`tools/render_brief.py`)
turns a validated `deck.json` into one HTML file with slides, mermaid diagrams, SVG
charts, zoomable image plates, and per-slide TTS narration via `edge-tts`.

Only two third-party runtime dependencies, project-wide: `edge-tts` (narration) and
`pillow` (image transcoding). No install step — both are pulled on demand by `uv run`.

## Install

Run both from an interactive `claude` terminal — these open a dialog, so they will not
work from a non-interactive session:

```text
/plugin marketplace add https://github.com/worc4021/narrative-brief
```

```text
/plugin install narrative-brief@narrative-brief
```

The `plugin@marketplace` form is not a typo: this repository is both. A local directory
works as a marketplace too, so `/plugin marketplace add /path/to/narrative-brief` is
equivalent if you have cloned it.

Then add the allowlist entry below in any repo where you want to produce briefs.

Once installed, you do not invoke this by name. Ask for what you want — "brief me on
what you've done", "walk me through the results", "show me what happened" — and the
skill triggers on the request. That is deliberate: a slash command may not exist in
every client, and the point of this tool is reaching you on a phone.

`uv` must be on `PATH`. Nothing else needs installing: `edge-tts` and `pillow` are
pulled on demand at render time.

## Rendering a brief

The renderer is a package (`tools/render_brief.py` imports as `tools.render_brief`), so
it must be invoked with `-m` and with the plugin root — the directory containing
`tools/` — as the working directory. Pointing `python` straight at the `.py` file fails
with `ModuleNotFoundError: No module named 'tools'`. When an agent runs this from inside
`skills/brief/SKILL.md`, the plugin root is two levels above that skill's own base
directory, which the harness gives it when the skill loads (`${CLAUDE_PLUGIN_ROOT}` may
also resolve to it where the harness expands that variable, but it is not guaranteed to
survive into an agent-composed shell command the way a skill's own base directory is).
Give it the deck and output paths as absolute paths too, since the command's working
directory is the plugin root, not wherever the deck was written:

```bash
uv run --directory "<plugin-root>" --with edge-tts --with pillow python -m tools.render_brief "<absolute path to deck.json>" -o "<absolute path to brief.html>"
```

Add `--no-audio` to skip TTS and iterate on visuals only, instead of waiting on
narration synthesis. It produces a read-only brief: no audio player, and the page opens
in read mode, so every slide is on one scrollable page with its transcript shown. That
matters on a phone — with no transport bar there are no on-screen controls and no
keyboard, so scrolling is the only navigation left. The same happens automatically when
every slide's narration fails to synthesise.

This must stay **one** command — do not split it into a separate synthesise step and
assemble step, and do not run anything else alongside it. Every additional distinct
command an agent runs against this repo is a separate chance to trip a permission
prompt, and the person meant to answer that prompt may be away from their desk with no
way to see it (see below): one command means one prompt to allowlist, not an
open-ended number of them.

## Install the allowlist entry (required)

Add to `.claude/settings.json` in any repo where you want briefs:

```json
{ "permissions": { "allow": ["Bash(uv run --directory * --with edge-tts --with pillow python -m tools.render_brief *)"] } }
```

Without this, rendering a brief can raise a permission prompt. In a remote session that
prompt may never reach you, and the session will sit blocked — so the feature would work
only when you are near the desktop, which is exactly when you do not need it. The whole
point of this tool is reviewing agent work from a phone while away from the machine;
an unanswerable permission prompt turns that into a silent hang instead.
