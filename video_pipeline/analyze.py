#!/usr/bin/env python3
"""
analyze.py – Video analysieren: Szenen/Schnitte, Transkript + Untertitel, Bildbeschreibung pro Szene

  Szenen        PySceneDetect  (findet jeden Schnitt)
  Sprache       faster-whisper (Transkript + .srt-Untertitel, erkennt die Sprache automatisch)
  Beschreibung  Qwen2.5-VL     (Vision-Language-Modell: "was passiert in dieser Szene?")

BEISPIELE:
  python analyze.py edit.mp4                         # alles
  python analyze.py edit.mp4 --no-describe           # ohne VLM (schnell, wenig VRAM)
  python analyze.py edit.mp4 --ask "Welches Auto ist zu sehen? Marke, Modell, Farbe."
  python analyze.py edit.mp4 --vlm Qwen/Qwen2.5-VL-3B-Instruct   # kleineres Modell

Ergebnis: out/<name>_analysis.json, out/<name>.srt, out/<name>_scenes/ (Keyframes)
"""
import argparse
import json
from pathlib import Path

from common import probe, read_frames

DEFAULT_ASK = ("Describe this video scene precisely: subjects (e.g. car make/model/color), environment, "
               "lighting, camera movement and shot type. Answer in 2-4 sentences.")


def detect_scenes(path, threshold):
    from scenedetect import ContentDetector, detect
    scenes = detect(str(path), ContentDetector(threshold=threshold))
    if not scenes:  # kein Schnitt → ganzes Video ist eine Szene
        return [(0.0, probe(path)[2])]
    secs = lambda t: t.seconds if hasattr(type(t), "seconds") else t.get_seconds()
    return [(secs(s), secs(e)) for s, e in scenes]


def transcribe(path, model_name):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cuda", compute_type="float16")
    segments, info = model.transcribe(str(path), vad_filter=True)
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segments]
    return info.language, segs


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def write_srt(segs, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n")


def keyframes(path, start, end, n, width):
    """n gleichmäßig verteilte Frames aus einer Szene."""
    w, h, *_ = probe(path)
    height = int(h * width / w) // 2 * 2
    dur = max(end - start, 0.1)
    return read_frames(path, n / dur, width, height, max_frames=n, start=start)


def load_vlm(name):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    print(f"Lade {name} …")
    model = AutoModelForImageTextToText.from_pretrained(name, torch_dtype=torch.bfloat16, device_map="cuda")
    return model, AutoProcessor.from_pretrained(name)


def describe(vlm, images, question, max_tokens=200):
    model, processor = vlm
    msgs = [{"role": "user", "content": [*({"type": "image", "image": im} for im in images),
                                         {"type": "text", "text": question}]}]
    inputs = processor.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True,
                                           return_dict=True, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    return processor.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()


def main():
    p = argparse.ArgumentParser(description="Video analysieren (Szenen, Sprache, Bildinhalt)")
    p.add_argument("video", type=Path)
    p.add_argument("--threshold", type=float, default=27.0, help="Schnitt-Empfindlichkeit (kleiner = mehr Schnitte)")
    p.add_argument("--whisper", default="large-v3", help="Whisper-Modell (tiny/base/small/medium/large-v3)")
    p.add_argument("--no-transcribe", action="store_true")
    p.add_argument("--no-describe", action="store_true")
    p.add_argument("--vlm", default="Qwen/Qwen2.5-VL-7B-Instruct")
    p.add_argument("--ask", default=DEFAULT_ASK, help="Frage an das VLM pro Szene")
    p.add_argument("--frames", type=int, default=4, help="Keyframes pro Szene für das VLM")
    p.add_argument("--out", type=Path, default=Path("out"))
    a = p.parse_args()

    if not a.video.exists():
        raise SystemExit(f"Datei nicht gefunden: {a.video}")
    a.out.mkdir(exist_ok=True)
    w, h, dur, fps, has_audio = probe(a.video)
    result = {"file": str(a.video), "width": w, "height": h, "duration": round(dur, 2),
              "fps": round(fps, 3), "has_audio": has_audio}
    print(f"{a.video.name}: {w}x{h}, {dur:.1f}s, {fps:.2f} fps, Ton: {'ja' if has_audio else 'nein'}")

    print("1/3 Szenen erkennen …")
    scenes = detect_scenes(a.video, a.threshold)
    result["scenes"] = [{"index": i, "start": round(s, 2), "end": round(e, 2)} for i, (s, e) in enumerate(scenes)]
    print(f"    {len(scenes)} Szenen")

    if has_audio and not a.no_transcribe:
        print("2/3 Transkribieren …")
        lang, segs = transcribe(a.video, a.whisper)
        result["language"], result["transcript"] = lang, segs
        srt = a.out / f"{a.video.stem}.srt"
        write_srt(segs, srt)
        print(f"    Sprache: {lang}, {len(segs)} Segmente → {srt}")
    else:
        print("2/3 Transkribieren übersprungen")

    shots = a.out / f"{a.video.stem}_scenes"
    shots.mkdir(exist_ok=True)
    vlm = None if a.no_describe else load_vlm(a.vlm)
    print("3/3 Keyframes" + ("" if a.no_describe else " + Beschreibung") + " …")
    for sc in result["scenes"]:
        imgs = keyframes(a.video, sc["start"], sc["end"], a.frames, width=768)
        if not imgs:
            continue
        kf = shots / f"scene_{sc['index']:03}.jpg"
        imgs[len(imgs) // 2].save(kf, quality=90)
        sc["keyframe"] = str(kf)
        if vlm:
            sc["description"] = describe(vlm, imgs, a.ask)
            print(f"    [{sc['start']:6.1f}s] {sc['description']}")

    out = a.out / f"{a.video.stem}_analysis.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ {out}")


if __name__ == "__main__":
    main()
