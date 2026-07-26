# Writing narration for the ear

The listener cannot re-read a sentence, and may be walking. Three rules, each with a
real before and after.

## 1. Speak the numbers

The voice carries precision so the visual does not have to. This is what makes a
phone-sized figure work at all.

> **Eye:** "p99 exceeds 800ms from 14:20 (see fig. 3), a >2x regression."
>
> **Ear:** "From twenty past two the ninety-ninth percentile passes eight hundred
> milliseconds — more than twice what it was."

Symbols, units and operators get spoken the way you would say them aloud: `1e-8`
becomes "one times ten to the minus eight", `>=` becomes "at least".

## 2. Never point at the screen

They may be in read mode with no audio, or looking away.

> **Eye:** "As you can see in the plot above, the orange trace departs first."
>
> **Ear:** "The orange trace, which is the cache miss rate, climbs first."

Name the thing instead of gesturing at it.

## 3. One idea per slide

A dense paragraph becomes three slides. Slide count is nearly free; only narration
length costs.

> **Eye, one slide:** "The overnight run completed with 40 of 42 checks passing. The two
> failures both hit the checkout endpoint above 800ms and both began after the cache
> change deployed, which suggests a configuration problem rather than a code defect, so
> the fix is likely the expiry policy rather than the handler."

> **Ear, three slides:**
>
> 1. *Run finished* — "Forty of the forty two checks passed overnight."
> 2. *The two failures match* — "Both failures hit checkout, and both started right after
>    the cache change went out."
> 3. *So it is configuration* — "That points at the expiry policy, not the handler. The
>    fix is configuration, not code."

## Length

Ninety seconds to three minutes. Hard stop at four. If it will not fit, the brief is
trying to do two jobs — split it.
