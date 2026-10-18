---
name: faceless-video
description: Produce a narrated multi-scene faceless channel video (explainer, history, kids, picture story, fairy tale/myth) with a locked style, asset roster, 10 s five-cut blocks, external voiceover, music bed and captions, run on fal.ai + ElevenLabs. Use for "faceless video", "YouTube automation", "narrated explainer", "story video". Not for single clips, talking heads or ads.
---

# Faceless video (fal.ai)

Load `video-prompting` first.

## Intake (fixed order, only what is missing)

1. Channel type: Explainer / History / Kids / Fairy Tale & Myth / Picture Story.
2. Motion mode: animated clips or still pictures with camera moves.
3. Style (one look for the whole video, e.g. paper collage, flat 2D, storybook, cinematic).
4. Duration, aspect (default 16:9), subtitles yes/no, thumbnail yes/no — one question each.
5. Topic or script.

## Golden rules

1. **Lock models for the whole run.** Assets/style key: `bytedance/seedream/v5/pro/text-to-image`
   (+`/edit`). Clips: `minimax/h3/reference-to-video` (or Kling O3 reference-to-video).
   Voice: `elevenlabs/tts/eleven-v4` (or ElevenLabs connector). Music bed: `fal-ai/elevenlabs/music`
   instrumental only. Never swap mid-run.
2. **Every clip = one 10 s block of FIVE hard-cut shots (~2 s, none >2.5 s)** in ONE prompt
   (`SHOT 1 (0.0–2.0s): …` … `SHOT 5 (8.0–10.0s): …`). Kids: four cuts of 2.5 s.
3. **Count the cuts that came back** —
   `ffprobe -v error -select_streams v:0 -show_entries frame=pkt_pts_time -of csv=p=0 -f lavfi "movie=block.mp4,select=gt(scene\,0.3)" | wc -l`
   (flat styles: threshold 0.15 and look before regenerating). Too few → regenerate once with the
   shots spelled out; still short → drop one cut silently next time.
4. **Compose from the approved assets.** Every clip gets the asset images in order
   location → characters → props. Never generate from the style key alone; no objects on blank white.
5. **Pass `aspect_ratio` explicitly on every video call.**
6. **Characters never talk on screen** — "characters only emote and gesture, they do NOT talk".
   The narrator is added in post.

## Pipeline

0. Intake → 1. Style key image → 2. Asset roster (characters, locations, props; one image each,
   consistent with the key) → 3. Script + block plan (one 10 s block per beat; VO dense, ~2.5
   words/s) → 4. Generate blocks (after go + total price) → 5. Voiceover per block, fitted to 10 s →
   6. Assemble clean master (concat in order, VO at −16 LUFS, SFX/music under the voice) →
   7. Captions on the clean master (see video-finish) → 8. no automatic upscale →
   8b. thumbnail only if asked (thumbnail skill, same style key) → 9. deliver ONE file.

## Retry ladder (nsfw/failed)

Same prompt twice more → reword risky tokens (child, tight animal faces, aggressive poses) up to 2×
→ change framing → after ~8 attempts on one block stop and tell the user. Never drop a block, never
leave a gap, never strip references to get past moderation.

## QC before delivery

One file; all blocks in order; style + characters consistent; aspect + fps uniform; VO in sync;
captions burned with authored wording (if on); no brand/IP names anywhere.
