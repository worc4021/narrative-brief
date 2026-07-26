# Deck schema

Top level — all required except `voice`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | Non-empty. Shown in the top bar and as the artifact title |
| `summary` | string | Non-empty. One line, shown above the first slide |
| `kind` | string | `recap` \| `results` \| `concept` \| `decision` |
| `voice` | string | Optional. Defaults to `en-GB-RyanNeural` |
| `slides` | array | At least one |

Each slide — `visual` is optional and defaults to `{"type":"none"}`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | Non-empty |
| `narration` | string | Non-empty. This is spoken AND shown as the transcript |
| `visual` | object | `{"type": ..., "value": ...}` |

Visual types — `value` must be non-empty for every type except `none`:

| `type` | `value` holds |
|---|---|
| `markdown` | `- ` bullets, `**bold**`, `` `code` ``, plain paragraphs. Nothing else |
| `mermaid` | Mermaid source. Rendered natively by the Artifact runtime |
| `svg` | A complete `<svg>` element with a `viewBox` |
| `image` | Path to a PNG on disk. Transcoded to WebP, deduplicated by content |
| `none` | Ignored. A narration-only beat |

Validation errors name the JSON path, e.g. `slides[2].visual.type must be one of ...`.

## Worked example

```json
{
  "title": "Checkout latency regression after the cache change",
  "summary": "p99 doubled from two twenty. Three options, recommendation inside.",
  "kind": "decision",
  "slides": [
    {
      "title": "What the run showed",
      "visual": { "type": "image", "value": "scratch/latency.png" },
      "narration": "The overnight load test finished. Checkout tracked the old build closely until twenty past two, then the ninety-ninth percentile ran away from four hundred milliseconds to over eight hundred inside about two minutes."
    },
    {
      "title": "Where it comes from",
      "visual": { "type": "mermaid", "value": "flowchart LR\n  A[cache entry expires] --> B[request misses]\n  B --> C[connection pool saturates]\n  C --> D[refill is slower]\n  D --> A" },
      "narration": "It is a feedback loop. An expiring entry causes a miss, the miss saturates the connection pool, and a saturated pool makes the refill slower still, so the next expiry lands on an already-degraded system."
    },
    {
      "title": "Three options",
      "visual": { "type": "markdown", "value": "- **Stagger the expiry** with a random offset\n- **Raise the pool ceiling** to sixty connections\n- **Shorten the time to live** to thirty seconds" },
      "narration": "Staggering the expiry is a one line change but needs a load test to confirm. Raising the pool ceiling is free but moves the pressure onto the database. Shortening the time to live only makes the misses more frequent."
    },
    {
      "title": "What I need from you",
      "visual": { "type": "none", "value": "" },
      "narration": "I recommend staggering the expiry, and re-running the load test this week to confirm it. Shall I go ahead, or would you rather raise the pool ceiling and keep the current expiry?"
    }
  ]
}
```
