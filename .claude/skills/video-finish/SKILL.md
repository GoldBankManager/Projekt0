---
name: video-finish
description: Finishing for generated videos — assembly/concat, exact source-audio restore, music/voice mix, burned captions, upscale choice that keeps realism, and delivery QC gates. Use after any generation (car-swap, remix, UGC, faceless) or for "schneide zusammen", "Ton drunter", "Untertitel", "upscale auf 4K".
---

# Video finish

Load `video-prompting` before any paid step (upscalers are paid).

## Assembly

- ffprobe every input. Same codec/size/fps/audio → concat demuxer with stream copy; otherwise
  normalize only what the output needs. Hard cuts by default; no transitions unless asked.
- Verify after assembly: total duration, streams, first/last frame, every join (frame sheet around
  each cut). An exit code is not proof.
- Frame-exact splicing: `trim=start_frame=A:end_frame=B,setpts=PTS-STARTPTS` + `concat`; compare
  total frame count with the original.

## Audio

- Restore source audio exactly: extract the default stream (copy to .mka, fallback PCM), apply the
  measured offset (`adelay` for positive, `atrim=start` for negative), then
  `asetpts=PTS-STARTPTS,apad=whole_dur=D,atrim=duration=D`; map generated video + this audio, `-t D`.
  Never `-shortest` / `-itsoffset` (they shift or truncate the video).
- Music changes: keep speech intelligible (duck), trim music to the edit. Don't add music unasked.
- VO target −16 LUFS; SFX/music under the voice.

## Captions

Transcribe the actual audio (`fal-ai/wizper` / Whisper), align to the authored wording, burn on the
clean master, place in a measured free region (not over faces/product), inspect the encoded frames.

## Upscale (separate, after the edit is approved)

| Goal | Endpoint | Note |
|---|---|---|
| Keep realism, sharpen | `topaz/upscale/video/precision` | first choice for photoreal |
| Cheap clean upscale | `fal-ai/seedvr/upscale/video` | ~$0.001/MP |
| ByteDance upscaler | `fal-ai/bytedance-upscaler/upscale/video` | use `enhancement_preset: general`, `fidelity: high`; `aigc` makes paint look plastic |
| Better source instead | upscale the INPUT locally (lanczos) before generation | edit models then render natively higher |

Always compare original vs raw vs upscaled crops side by side before delivering.

## Delivery QC gates

Duration within max(1/fps, 0.1 s) of target · aspect within 1.5 % · short edge as planned ·
audio present iff intended · full decode OK · contact sheet reviewed · no stray text/watermarks.
Deliver one file, state what was and wasn't verified.
