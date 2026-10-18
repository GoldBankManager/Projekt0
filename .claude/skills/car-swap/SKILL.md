---
name: car-swap
description: Replace a car (or any product/object/person) inside an existing edit while keeping every cut, camera move, timing, background and the original audio — Ad-Multiplier-style precision edit, run on fal.ai (Kling O3 Edit). Use for "car swap", "tausche das Auto", "replace the product in my video", "same edit with this car". Not for new footage from scratch (use reference-remix).
---

# Car swap / object swap in an existing edit

Load `video-prompting` first (money rule, ownership, checklist). Script: `kling_swap.py`
(Seedance fallback: `car_swap.py`).

## Stage 1 — intake (one turn, only what is missing)

1. Source edit (4–30 s; Kling Edit accepts 3–15 s per job → split longer edits at real cuts).
2. Reference photos of the new car: front 3/4, front, side, rear (+ rear 3/4, wheel). Same car.
3. Final resolution (generate at the model's native res; upscale is a separate later step).
4. Anything that must stay or go (interior, plates, logos, text).

Do not ask again for anything already stated.

## Stage 2 — probe + analyze (free)

```bash
ffprobe -v error -show_streams -show_format -of json edit.mp4
ffmpeg -i edit.mp4 -vf "select='gt(scene,0.25)',showinfo" -f null - 2>&1 | grep -o 'pts_time:[0-9.]*'
ffmpeg -i edit.mp4 -vf "fps=4,scale=110:-1,drawtext=text='%{pts\:hms}':x=2:y=2:fontsize=12:fontcolor=yellow:box=1,tile=10x5" -frames:v 1 sheet.jpg
```

Record: exact duration, fps, display aspect (rotation/SAR aware), audio stream + offset, and a shot
list with time ranges: wide / close-up / rear / wheel / interior / transition. Look at the sheet.
Interior and dark motion-blur shots are where swaps fail — list them explicitly.

## Stage 3 — prepare references (free)

- Crop or blur dealer plates / watermarks in the reference photos (they leak into the video).
- Kling limit: 4 refs total. `@Element1` = car (frontal 3/4 + up to 3 angles), `@Image1..3` = extra
  details (rear 3/4, wheel, interior only if the interior must change).
- Upscale a <720 px source locally to 1080 (lanczos) — Kling Pro then renders at 1080 natively.

## Stage 4 — master prompt (write once, validate, hand to user)

Template (COMPACT for one object; extend per shot when needed):

```
@Video1 is the source video. Replace only the car.
From the very first frame (start frame) until the very last frame, the car is the <color> <make model> from @Element1.
@Image1 and @Image2 show more details of the same <make model>.
Replace the original <color/model> car in every single shot, including wide shots, close-ups, side shots, rear shots and wheel shots<, and interior shots with the interior from @ImageN>.
Keep the exact camera movement, cuts, timing, speed, framing, background, buildings, ground, lighting, shadows and color grade of @Video1.
The car must match the references exactly from every angle: body shape, paint, wheels, brake calipers, headlights, taillights and proportions.
Realistic paint reflections and contact shadows that match the scene lighting.
Photorealistic real camera footage with natural film grain. Not CGI, not 3D render, not cartoon.
Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement.
The license plates are blank, without any text.
Logo on the back of the car reads "<badge>".
Do not change any logos. Do not change any symbols. Do not add characters.
Do not change, morph, merge, distort, duplicate or swap any logos or symbols.
No <old color> car in any frame. No flickering. No duplicated logos.
```

Validation: ≤3900 chars; every `@` tag used exists; no ids/URLs; old object excluded globally
("in every frame"); one replacement source per target; no unresolved "if" in the prompt.
Per-segment variant: `<a>-<b>s: keep everything exactly the same` / `<a>-<b>s: Replace only … from @Image1 …`
tiling the full duration.

## Stage 5 — run (only after explicit go + price)

```bash
python3 kling_swap.py --video edit.mp4 --car front34.jpg front.jpg side.jpg rear.jpg \
  --extra-images rear34.jpg wheel.jpg --prompt-file prompt.txt --model pro --upscale none --dry-run
```

`--dry-run` prints the estimate; drop it and add `-y` only after the user's go. One position at a
time; retry a technical failure once; never resubmit a pending job.

## Stage 6 — finalize + QC (free)

Restore the source audio with exact timing (no `-shortest`, no `-itsoffset`):

```bash
# offset = audio_start - video_start of the SOURCE (0 if unknown)
ffmpeg -y -i raw.mp4 -i edit.mp4 -filter_complex \
 "[1:a:0]asetpts=PTS-STARTPTS,apad=whole_dur=$DUR,atrim=duration=$DUR[a]" \
 -map 0:v:0 -map "[a]" -t $DUR -c:v copy -c:a aac -b:a 192k -movflags +faststart final.mp4
```

Gates: duration within max(1/fps, 0.1 s) of source; display aspect within 1.5 %; short edge as
planned; audio present iff source had audio; contact sheet shows the new car in EVERY shot incl.
first frame; no old color/interior; no leaked plate text. Report failures per shot with timestamps.

## Segment fix (when 1–2 shots fail)

Concatenate only the failing shots (frame-exact `trim=start_frame:end_frame`) into one ≥3 s clip,
regenerate that clip once with a shot-specific prompt, splice back frame-exact, verify the total
frame count equals the original. Cheaper than a full rerun.
