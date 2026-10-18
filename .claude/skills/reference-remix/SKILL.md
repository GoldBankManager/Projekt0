---
name: reference-remix
description: Build a NEW edit for the user's subject (car, product, person) in the visual language of a reference edit — rhythm, cuts, camera energy, textures, typography, music — Katana-style, run on fal.ai. Use for "mach so ein Edit wie das hier", "remix this edit with my car", "showreel in this style", or a brief with no footage (find a reference first). Not for swapping an object inside the reference footage itself (use car-swap).
---

# Reference remix (Katana method on fal.ai)

Load `video-prompting` first. Every reference deliverable is a remix: learn the reference's grammar
and author a new edit for the user's subject. Never rebuild it shot-for-shot, never swap the hero
inside the reference footage.

## 1. Task contract (write `work/task-contract.json`)

`explicit_locks` (attribute, scope, value, user words), `creative_freedoms`, `references`. A lock on
one element (song, opening shot, wording) binds only that element. The user's subject keeps its own
identity and look in every shot.

## 2. Find the reference (if none supplied)

Search current TikTok / Reels / Shorts for subject + mood + format. Shortlist ≤3, actually watch
(decode frames) — a title/thumbnail is not evidence. Pick one, record why.

## 3. Read the reference completely (free, local)

- Probe streams; keep the master untouched.
- Every-frame contact sheets in order (no gaps), per-second notes incl. the final partial second.
- Cut list (auto-detect, then correct by eye incl. 1-frame inserts).
- Energy map: flashes, shake bursts, punch-ins, whips, zooms, hits and cut rate per second.
- Per cut: content, camera + subject motion, text (wording, font shape, placement, animation),
  effects (start/peak/end, direction, easing), audio events.
- Music: track, pulse, structure, edit points, ending.

## 4. Creative plan (`work/creative-plan.json`)

- `output_target`: aspect, fps, duration, audio interval (user locks first, then reference evidence).
- Concept: one logline; for products/cars use a visual motif with setup → payoff, not a forced plot.
- Shot roles: hook, identity, detail, action, escalation, contrast, reveal, payoff — only those needed.
- Where the reference energy lands on the new timeline (same kinds/rates of effects).
- Asset map per shot: reuse supplied footage → still + code move → new generated clip.

## 5. Assets

- Subject references: the user's photos own identity + look. No generated "hero still" as identity.
- **Location plate** for every distinct new environment: one environment-only image
  (`fal-ai/nano-banana-pro` or `bytedance/seedream/v5/pro/text-to-image`, photoreal), inspected for
  stray people/cars, reused across all shots in that location.
- Stylised looks: one accepted keyframe becomes the style owner for later stills.

## 6. Generate (only after explicit go + total price for the whole finite plan)

- New shots: Seedance 2.0 reference-to-video or Kling O3 reference-to-video; pass subject refs AND
  the location plate as separate images, ownership stated per `@ImageN`.
- Prompt shape per clip: one camera move + dose/limit, one action, location ownership, look lock,
  `generate_audio: false` (audio comes from the real track).
- Multi-shot plate: `Shot n (a–bs)` slots of 2–4 s; plate duration = Σ slots.
- Run one canary per family, inspect, then the rest. ≤1 corrective retry per failed clip.
- Check every clip every 0.5 s at ≥960 px for anatomy, merging, identity, stray text; record bad
  ranges and keep in-points outside them.

## 7. Assemble (ffmpeg, free)

- Cut on the planned timeline; carry the reference energy as EDL camera work (punch-ins, shakes,
  whips) because generated plates come back calmer than the reference.
- Text: planned wording, rendered as a separate overlay with a verified font; no generated text.
- Music: the real track (supplied or licensed); SFX from real recordings; never synthesize music
  with code.
- Three internal reviews on the render: (1) timing/rhythm, (2) spatial motion/continuity,
  (3) detail/polish + energy rates. Fix assembly first; generative fixes only within the plan.

## 8. Deliver

Size-capped MP4 from the verified master, actual spend, any unresolved deviation. Never touch faces
with local code (no face paste/warp/retouch).
