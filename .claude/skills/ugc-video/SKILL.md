---
name: ugc-video
description: Produce UGC-style creator videos (review, product-only voiceover, unboxing, try-on, tutorial, website tour) with hooks, monologue craft and anti-slop rules, run on fal.ai. Use for "UGC video", "creator review", "TikTok ad with a person talking", "unboxing video", "tutorial clip". Not for scripts only or footage edits.
---

# UGC video (fal.ai)

Load `video-prompting` first.

## Formats (pick exactly one; review is the default)

| Format | Result |
|---|---|
| review | one adult creator demonstrates a product or tells a story (product optional) |
| product | product is hero, off-screen voiceover, no on-camera speaker |
| unboxing | creator opens packaging and reacts |
| try-on | creator wears an item, shows fit/texture |
| tutorial | creator demonstrates use with `Step N` labels |
| website | real captured website/app with a presenter |

A product URL identifies the product; it does not make it a website tour.

## Truth contract (every run)

- `approved_claims` is the complete allowlist (can be empty). Never invent purchases, results,
  before/after, ratings, reviews, numbers or lived experience.
- Generated creator = host/demonstrator, never a customer with history.
- First-person experience only if the user supplied that exact script as their own.

## Duration + word budget

≤10 s ≈ 12–20 words · 11–12 s ≈ 20–28 · 13–15 s ≈ 28–35. Long videos = several clips stitched.
Greeting/product intro only in clip 1; later clips continue mid-thought.

## Story spine (pick one, brainstorm ≥3 first)

Demonstration Discovery · Mechanism Loop · Alternate Use · Guided Comparison · Behind-the-Concept ·
Interrupted Storytime · GRWM With Stakes · New-Place Mini-Vlog · Day-in-the-Life With a Twist ·
Product Reveal · POV Frame · Process Win · FAQ Reply · Green-Screen Commentary · Feature Checklist ·
Host Question · Baseline-to-Demo · Silent Flex · ASMR.
Exactly ONE "but then" twist. Product enters at 40–60 % of runtime as a supporting actor; CTA lives
inside the resolution. The story must survive with the product deleted.

## Hook (one pattern for clip 1)

H1 Impact Action (mid-action frame one) · H2 Mid-Sentence Confession · H3 Pattern Interrupt ·
H4 Freeze-Reaction (≤0.7 s hold) · H5 Hostile Open · H6 Quirk-First · H7 Mechanism-First ·
H8 Product Cold Open. Write it as one plain staging sentence.

## Anti-slop

- First word is never: OK/Okay/Alright/So/Um/Well/Like/Wait/Hold on/OMG/Hey guys/Stop scrolling.
- Banned: literally, obsessed, game-changer, holy grail, changed my life, hits different, elevate,
  seamless, effortless.
- One peak reaction per clip. Emotion lives in the words: one vowel stretch, 1–2 CAPS spikes, one
  broken sentence at the peak. No written dramatic pauses.
- Persona: NATURAL tier by default (warm, genuine, one human-scale peak). Write the persona as one
  sentence and repeat it verbatim in every prompt.

## Pipeline

1. Creator reference: user photo (consenting adult) or a generated adult portrait
   (`fal-ai/nano-banana-pro`, full-body, seamless white studio, natural skin texture).
2. Optional storyboard still per clip (`fal-ai/nano-banana-pro/edit` with creator + product refs).
3. Clips: `bytedance/seedance-2.0/reference-to-video` with refs [board, creator, product],
   `generate_audio: true` for native speech, aspect 9:16. Prompt = persona sentence + cut-by-cut
   action + the exact spoken line in quotes + "no on-screen text" (tutorial: only `Step N` labels).
4. Check each clip: identity/product continuity, duration, speech matches the line, no stray text.
   Regenerate only failed clips (once).
5. Assemble + captions → `video-finish`.
