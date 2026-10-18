---
name: thumbnail
description: Cinematic YouTube / Instagram / Reels thumbnails and video covers — 16 click frameworks, house prompt structure, identity lock, emotion casting, camera takes, split frames, text overlay policy and surgical tweaks — run on fal.ai (Nano Banana Pro, Seedream edit, GPT Image 2). Use for "thumbnail", "video cover", "reel cover".
---

# Thumbnail (fal.ai)

Load `video-prompting` first. Main render: `fal-ai/nano-banana-pro` (4K, one call per variant,
never `num_images` for different prompts). Tweaks: `bytedance/seedream/v5/pro/edit`
(fallback `fal-ai/bytedance/seedream/v4.5/edit`). 3D logo: `openai/gpt-image-2/edit`.

## Gates before rendering

- **Character gate:** person in frame + no face photo → ask once: you / a specific person (send a
  photo) / generated person / people-free. Never invent a person silently.
- **Text gate:** default is a CLEAN render with no text. Bake text only on explicit request;
  otherwise add the headline later as an overlay.
- **Variants:** single or a set (~4: emotions × camera takes, cap 16).
- Reference thumbnail = style example only (analyze by eye), never sent to the model. Ask once:
  match it closely or unique take.

## Frameworks (brainstorm ≥5, pick/combine; must open an information gap, stay truthful)

1 Before/After · 2 Social UI (generic bubble/review card) · 3 Three-Step Progression ·
4 Compelling Screenshot (real frame) · 5 Posed Portrait (default) · 6 Posed Action Shot ·
7 Highlight a Day (DAY N badge) · 8 Graphical (diagram, non-photoreal) · 9 Landscape ·
10 Map/Aerial · 11 Product · 12 Adding Text · 13 Repetition of Objects · 14 Size Difference ·
15 News Clip (generic lower third) · 16 Amplified Reality (one element exaggerated, plausible).
Readability test: emotion + hero element must read at ~120 px wide.

## House prompt (blocks in this order)

1. Frame: `Bold, punchy YouTube-thumbnail composite — poster-grade, photoreal and high-impact, NOT a muted cinematic movie still, <ratio> aspect ratio, single unified frame — no split-screen, everything blends organically across the same continuous shot.`
2. `SCENE BRIEF (must be depicted exactly): …` (if given)
3. Text: `No text, no readable UI labels, no watermark.` (or the explicit TEXT line)
4. SUBJECT(s) LARGE (40–60 % of frame, chest-up, foreground) + Identity Lock per photo + `Expression: …`
5. KEY ELEMENTS (signature props, oversized, flying toward camera)
6. LOGO (exactly as provided, or 3D render)
7. LOCATION
8. COMPOSITION (power third, strong separation, depth layering)
9. BACKGROUND (bold saturated color field, gradient, vignette — blended, not divided)
10. LIGHTING (people): strong KEY light, soft DREAM fill, bright BACK + HAIR rim light
11. GRADE: `vivid high-impact color grade, punchy high contrast, rich saturated colors, deep blacks, crisp and glossy, poster-punchy.`

With 2+ images, first line: `IMAGE REFERENCES: image 1 = CHARACTER 1 face reference; image 2 = brand logo.`

**Identity Lock:** `CHARACTER N: the person from attached face reference #K — IDENTITY LOCK: reproduce this exact person with a photographic identity match — same bone structure, eye shape, nose, lips, jawline, skin tone, hairline and hair texture. Do NOT beautify, do NOT average with other faces, do NOT restyle the face. Expression: <phrase>.`

**Emotions:** shock (mouth open gasp, wide eyes) · hype (ecstatic grin, blazing eyes) · fear ·
confusion (one brow raised) · determination (locked jaw) · smug (knowing smirk) · charisma (calm
magnetic gaze, faint half-smile) · disgust · awe (jaw dropped) · rage · laugh (head back).

**Takes:** 1 designed · 2 `ALTERNATE TAKE: low-angle hero shot…` · 3 `ALTERNATE TAKE: extreme close-up punch-in…` · 4 `ALTERNATE TAKE: wider dynamic shot with a subtle dutch tilt…`

**Split frames** only when asked (before/after, versus, side by side): replace block 1 with
`SPLIT-FRAME thumbnail … divided into N halves/panels by clean bold seams…` + `No labels, no captions, no words on or between the panels.`

## After render

Check identity vs photo, no stray text, readability at 120 px. Re-render same prompt max 2×.
Text overlay: 2–6 words, free quarter, never over the face; styles Beast (white + heavy black stroke
+ shadow), Fire (yellow→red gradient), Neon Lime (#D4FF3F glow), Clean Glass, Marker.
Tweaks (Seedream edit, finished render as input): change ONLY expression / background / bg color /
rim color — "keep everything else pixel-faithful".
