---
name: video-prompting
description: Core rules for writing AI video/image generation prompts and running paid fal.ai jobs safely (cost gate, reference ownership, prompt blocks, failure modes, pre-submit checklist). Load before ANY fal.ai generation in this repo, and before the other video skills (car-swap, reference-remix, ugc-video, faceless-video, thumbnail, character-sheet, product-photoshoot, video-finish).
---

# Video prompting + fal.ai run rules

Adapted from Higgsfield's production workflows (Katana / Ad Multiplier / Faceless), rebuilt to run
on fal.ai with the user's own key (`FAL_KEY`). Higgsfield itself is NOT used.

## 0. Money rule (non-negotiable)

- Never submit a paid fal.ai job without the user's explicit "go" for that exact job and price.
  Tests, "quick checks" and retries are paid jobs too.
- Before asking: get the live price (free):
  `curl -s -H "Authorization: Key $FAL_KEY" "https://api.fal.ai/v1/models/pricing?endpoint_id=<id>"`
  and the model page text (`https://fal.ai/models/<id>`, field `pricingInfoOverride`) when units are
  tokens/megapixels. If the two disagree, quote the range.
- Check the input schema (free) before writing params:
  `https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>` → `components.schemas.*Input`.
  Never send a field the schema does not list (e.g. Seedance 2.0 has no `seed`).
- Free, local work (ffprobe, ffmpeg, frame sheets, scene detection, dry runs) needs no approval.
- One validated job beats three speculative ones. Hand the user a finished master prompt; do not
  "try around" on their money.

## 1. Reference ownership (one job per input)

Every reference gets exactly one role; say it in the prompt.

| Input | Owns |
|---|---|
| Source video `@Video1` | camera, cuts, timing, motion, framing, environment, light (edit jobs) |
| Subject/product photos | identity, shape, color, markings, wheels, materials — the complete look |
| Location plate | architecture, materials, landmarks (only for newly generated scenes) |
| Style frame | palette, texture, rendering only — never identity or composition |
| Start frame | first frame only; later frames must be checked |

Never let a reference silently own something else (e.g. the background of a product photo).

## 2. Prompt blocks (use only the ones the shot needs, in this order)

1. **Reference ownership + locks** — which tag supplies what; what must not change.
2. **Causal context** (optional) — before-state → one meaningful end-state.
3. **Spatial map** — subject count, foreground/background, screen position, motion direction.
4. **One legible action** per shot. Multi-shot: `Shot 1 (0–2s): … Shot 2 (2–4s): …`.
5. **Camera** — framing/angle + at most one move with dose and limit ("short lateral move, ends before
   the car leaves frame"). A locked camera is valid.
6. **Light + texture** — motivated, matching the scene; photoreal anchors:
   `photorealistic real camera footage, natural paint reflections, real textures, natural film grain,
   not CGI, not 3D render, not cartoon`.
7. **End constraints** — identity/look locks, required text/no text, continuity, `No flickering.`

Rules: concrete observable instructions > repeated adjectives. English prompts; on-screen strings
verbatim in the user's language. Tags are case-exact: `@Video1`, `@Image1`, `@Element1`.
No URLs, media ids or job ids inside prompts.

## 3. Model routing on fal.ai (verify price + schema each time)

| Need | First choice | Notes |
|---|---|---|
| Swap/replace an object in an existing edit | `fal-ai/kling-video/o3/{standard,pro}/video-to-video/edit` | 3–15 s, ≥720 px, max 4 refs (element + images), `keep_audio` |
| New footage from references | `bytedance/seedance-2.0/reference-to-video`, `.../mini/...`, `alibaba/wan-3.0/reference-to-video` | regenerate the whole video → cuts can drift |
| Image → video | `fal-ai/kling-video/v3/pro/image-to-video`, `minimax/h3/image-to-video` | |
| Multi-shot blocks from assets | `minimax/h3/reference-to-video`, `fal-ai/kling-video/o3/pro/reference-to-video` | |
| Stills / assets | `fal-ai/nano-banana-pro`(+`/edit`), `bytedance/seedream/v5/pro/edit`, `openai/gpt-image-2/edit` | |
| Voice / SFX / music | `elevenlabs/tts/eleven-v4`, `fal-ai/elevenlabs/sound-effects/v2`, `fal-ai/elevenlabs/music` | or the ElevenLabs connector |
| Upscale (later, separate) | `topaz/upscale/video/precision`, `fal-ai/seedvr/upscale/video`, `fal-ai/bytedance-upscaler/upscale/video` | see video-finish |

## 4. Known failure modes (learned in this repo)

| Symptom | Cause | Fix |
|---|---|---|
| Original object returns after fast cuts | generative model (Seedance) re-creates the clip | use an edit model (Kling O3 Edit) |
| Plastic / cartoon look | Standard-tier smoothing + upscaler preset `aigc` | Pro tier, photoreal anchors, upscale with a realism preset or not at all |
| Interior/close-ups keep the old object | dark, motion-blurred shots get under-edited | name those shots explicitly, or regenerate only those segments |
| Text from reference photos leaks (license plates) | refs own "complete look" incl. plates | crop/blur plates in the refs before upload; prompt "license plates blank" is not enough |
| Fewer cuts than asked | model under-delivers | count cuts (`select='gt(scene,0.3)'`), regenerate once with explicit `SHOT n (a–bs)` |
| nsfw false positives | probabilistic | resubmit same prompt → reword risky tokens → change framing; never strip references |

## 5. Pre-submit checklist (every paid call)

- [ ] User approved this exact job + price.
- [ ] Params match the live schema; durations/resolution/aspect explicit.
- [ ] Every reference has one stated owner; all tags present, none dangling.
- [ ] Prompt contains the locks (what must stay) and the exclusions (what must never appear).
- [ ] No identity/garment/prop copied from an example instead of the user's inputs.
- [ ] Output plan: where audio comes from, how duration is checked, who upscales.
