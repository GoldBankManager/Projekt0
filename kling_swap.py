#!/usr/bin/env python3
"""
kling_swap.py – Car Swap in einem fertigen Edit mit Kling O3 Edit (fal.ai) + Upscale (ByteDance Upscaler).
Kling O3 Edit verändert das vorhandene Video (statt es neu zu generieren): Schnitte, Kamera und Szene bleiben.

SETUP: pip install fal-client requests | ffmpeg | export FAL_KEY="dein_key"

BILDER (max. 4 Referenzen insgesamt, das Auto-Element zählt als 1):
  --car     Hauptbild + bis zu 3 weitere Winkel vom SELBEN Auto  (= @Element1)
  --extra-images  bis zu 3 weitere Bilder, z. B. Innenraum      (= @Image1, @Image2, …)

BEISPIEL:
  python kling_swap.py --video edit.mp4 --car front34.jpg front.jpg side.jpg rear.jpg \
      --extra-images interior.jpg --prompt-file prompt.txt --upscale 1080p --dry-run
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import fal_client
import requests

MODELS = {  # $/s Output laut fal-Pricing-API
    "standard": ("fal-ai/kling-video/o3/standard/video-to-video/edit", 0.14),
    "pro":      ("fal-ai/kling-video/o3/pro/video-to-video/edit", 0.168),  # laut Modellseite
}
UPSCALER = "fal-ai/bytedance-upscaler/upscale/video"
UPSCALE = {"1080p": 0.0072, "2k": 0.0144, "4k": 0.0288}  # $/s bei 30fps, Tier "standard"
MAX_REFS = 4


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Fehler bei: {' '.join(cmd)}\n{r.stderr[-1500:]}")
    return r.stdout


def probe(path):
    out = json.loads(sh(["ffprobe", "-v", "error", "-print_format", "json",
                         "-show_streams", "-show_format", str(path)]))
    v = next(s for s in out["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in out["streams"])
    return int(v["width"]), int(v["height"]), float(out["format"]["duration"]), has_audio


def download(url, path):
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return path


def logs(update):
    if isinstance(update, fal_client.InProgress):
        for l in update.logs:
            print("   ", l["message"])


def main():
    p = argparse.ArgumentParser(description="Car Swap im Edit: Kling O3 Edit + Upscale")
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--car", required=True, nargs="+", type=Path, help="Hauptbild + bis zu 3 Winkel (@Element1)")
    p.add_argument("--extra-images", nargs="*", type=Path, default=[], help="Weitere Bilder (@Image1 …)")
    p.add_argument("--prompt-file", required=True, type=Path)
    p.add_argument("--model", default="standard", choices=list(MODELS))
    p.add_argument("--upscale", default="1080p", choices=["1080p", "2k", "4k", "none"])
    p.add_argument("--out", type=Path, default=Path("out"))
    p.add_argument("--dry-run", action="store_true", help="Nur prüfen + Kosten schätzen")
    p.add_argument("-y", "--yes", action="store_true", help="Ohne Rückfrage starten")
    a = p.parse_args()

    if len(a.car) > 4:
        sys.exit("Element: max. 1 Hauptbild + 3 Winkel.")
    if 1 + len(a.extra_images) > MAX_REFS:
        sys.exit(f"Max. {MAX_REFS} Referenzen (Element + Bilder) – also max. {MAX_REFS - 1} Extra-Bilder.")
    for f in [a.video, a.prompt_file, *a.car, *a.extra_images]:
        if not f.exists():
            sys.exit(f"Datei nicht gefunden: {f}")

    w, h, dur, has_audio = probe(a.video)
    if not 3 <= dur <= 15:
        sys.exit(f"Kling O3 Edit braucht 3–15 s, Video hat {dur:.1f} s.")
    if min(w, h) < 720:
        sys.exit(f"Kling O3 Edit braucht mind. 720 px, Video hat {w}x{h}.")

    prompt = a.prompt_file.read_text(encoding="utf-8").strip()
    endpoint, rate = MODELS[a.model]
    print(f"\n--- PROMPT ---\n{prompt}\n--------------")
    print(f"\nClip: {dur:.1f}s | {w}x{h} | Element: {len(a.car)} Bilder | Extra: {len(a.extra_images)}")
    up = 0 if a.upscale == "none" else dur * UPSCALE[a.upscale]
    if rate:
        print(f"Kosten ca.: ${dur * rate + up:.2f}  (Kling ${dur * rate:.2f} + Upscale ${up:.2f})\n")
    else:
        print(f"Kosten: Kling {a.model} – Preis siehe fal, Upscale ${up:.2f}\n")
    if a.dry_run:
        return
    if not a.yes and input("Starten? (j/n) ").strip().lower() not in ("j", "y", "ja", "yes"):
        return

    a.out.mkdir(exist_ok=True)
    print("Lade Dateien hoch …")
    video_url = fal_client.upload_file(str(a.video))
    car_urls = [fal_client.upload_file(str(f)) for f in a.car]
    extra_urls = [fal_client.upload_file(str(f)) for f in a.extra_images]

    args = {
        "prompt": prompt,
        "video_url": video_url,
        "elements": [{"frontal_image_url": car_urls[0], "reference_image_urls": car_urls[1:] or [car_urls[0]]}],
        "keep_audio": True,
    }
    if extra_urls:
        args["image_urls"] = extra_urls

    tag = f"{a.video.stem}_kling"
    print(f"1/2 Kling O3 Edit ({a.model}) …")
    res = fal_client.subscribe(endpoint, arguments=args, with_logs=True, on_queue_update=logs)
    kling_url = res["video"]["url"]
    final = download(kling_url, a.out / f"{tag}.mp4")
    print(f"    ✓ {final}")

    if a.upscale != "none":
        print(f"2/2 Upscale → {a.upscale} …")
        up_res = fal_client.subscribe(UPSCALER, arguments={
            "video_url": kling_url,
            "target_resolution": a.upscale,
            "target_fps": 30,
            "enhancement_preset": "aigc",
            "enhancement_tier": "standard",
            "fidelity": "high",
        }, with_logs=True, on_queue_update=logs)
        final = download(up_res["video"]["url"], a.out / f"{tag}_{a.upscale}_noaudio.mp4")

        # Originalton wieder drunterlegen (Upscaler liefert kein Audio)
        if has_audio:
            with_audio = a.out / f"{tag}_{a.upscale}_final.mp4"
            sh(["ffmpeg", "-y", "-i", str(final), "-i", str(a.video), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest", str(with_audio)])
            final = with_audio

    print(f"    ✓ FERTIG: {final}")


if __name__ == "__main__":
    main()
