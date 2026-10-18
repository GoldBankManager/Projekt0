#!/usr/bin/env python3
"""
car_swap.py – Supercar-Edits mit Seedance 2.0 Mini/Standard (480p/720p) + Upscale auf 4K (ByteDance Upscaler) über fal.ai
Prompt-Aufbau wie beim "Supercar Showreel Spin"-Preset: Video = nur Kamerabewegung, Bilder = Szene + Auto.

SETUP (einmalig):
  pip install fal-client requests
  ffmpeg installieren   (Mac: brew install ffmpeg | Windows: winget install ffmpeg)
  API-Key setzen        (Mac/Linux: export FAL_KEY="dein_key" | Windows: set FAL_KEY=dein_key)

BILDER (max. 9 insgesamt bei Seedance 2.0):
  --bg        1 Hintergrund/Szene          (optional; ohne --bg bleibt die Szene aus dem Video)
  --interior  1 Innenraum                  (optional)
  --car       bis zu 9 Winkel vom SELBEN Auto (mit bg + interior: max. 7)

BEISPIELE:
  # Showreel-Modus: Kamerafahrt aus dem Video, neue Szene + neues Auto
  python car_swap.py --video spin.mp4 --bg garage.jpg --interior cockpit.jpg \
      --car front.jpg side.jpg rear.jpg 34front.jpg 34rear.jpg --brand "Porsche"

  # Swap-Modus: Szene aus dem Video behalten, nur Auto tauschen
  python car_swap.py --video edit.mp4 --car front.jpg side.jpg rear.jpg

  # Nur Kosten anzeigen / 3 Versionen mit verschiedenen Seeds
  python car_swap.py --video spin.mp4 --car a.jpg b.jpg --dry-run
  python car_swap.py --video spin.mp4 --car a.jpg b.jpg --takes 3
"""
import argparse
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import fal_client
import requests

MODELS = {  # $/s Output; Input-Video kostet zusätzlich 0.6x davon (laut fal)
    "mini":     ("bytedance/seedance-2.0/mini/reference-to-video", {"480p": 0.0721, "720p": 0.1547}),
    "standard": ("bytedance/seedance-2.0/reference-to-video",      {"480p": 0.136,  "720p": 0.302}),
}
UPSCALER = "fal-ai/bytedance-upscaler/upscale/video"

# Preise laut fal (Stand Okt 2026) – nur für die Schätzung, abgerechnet wird von fal
VIDEO_INPUT_FACTOR = 0.6       # Input-Video wird mit 0.6x des Output-Preises berechnet
UPSCALE = {"1080p": 0.0072, "2k": 0.0144, "4k": 0.0288}  # $/s bei 30fps, Tier "standard"
MAX_IMAGES = 9

ASPECTS = {"21:9": 21 / 9, "16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1.0, "3:4": 3 / 4, "9:16": 9 / 16}


def tags(nums):
    return " ".join(f"@Image{n}" for n in nums)


def build_prompt(has_bg, has_interior, n_car, brand, extra):
    """Nummeriert die @ImageX-Referenzen passend zur Reihenfolge der Uploads."""
    i = 1
    bg = interior = None
    if has_bg:
        bg, i = i, i + 1
    if has_interior:
        interior, i = i, i + 1
    car = list(range(i, i + n_car))
    car_ref = tags(car)
    multi = n_car > 1

    lines = []
    if has_bg:
        lines += [
            "@Video1 is the camera movement reference only.",
            "Copy the exact camera movement, speed, timing and framing of @Video1 "
            f"and apply it to our scene from @Image{bg}.",
            "Do not copy the car, background or any objects from @Video1.",
            "",
            f"Use @Image{bg} as the background and environment of the scene.",
        ]
    else:
        lines += [
            "Keep the scene of @Video1: same camera movement, timing, framing, background, "
            "lighting and color grade.",
            "Only the car changes. Keep the car on the same ground positions and path "
            "with correct real-world scale.",
        ]
    if has_interior:
        lines.append(f"Change the interior of the car with @Image{interior}.")
    lines += [
        "",
        f"Replace the car with the car from {car_ref}"
        + (", which show the same car from different angles." if multi else "."),
        "The car must match the references exactly from every angle: body shape, color, livery, "
        "rims, lights, numbers and proportions.",
        "Realistic reflections and contact shadows that match the scene lighting.",
        "",
        "Do not change any logos.",
        "Do not change any text.",
        "Do not change any symbols.",
        "Do not add characters.",
        "Do not change, morph, merge, distort, duplicate or swap any logos, text or symbols.",
        "No flickering.",
        "No duplicated logos.",
    ]
    if brand:
        lines.append(f'The logo on the back of the car reads "{brand}".')
    if extra:
        lines += ["", extra.strip()]
    return "\n".join(lines)


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
    w, h = int(v["width"]), int(v["height"])
    # Handyvideos sind oft quer gespeichert + Rotations-Flag; ffmpeg dreht beim Encoden automatisch
    rot = v.get("tags", {}).get("rotate") or next(
        (d.get("rotation") for d in v.get("side_data_list", []) if "rotation" in d), 0)
    if abs(int(float(rot))) % 180 == 90:
        w, h = h, w
    return w, h, float(out["format"]["duration"]), has_audio


def prepare_input(src, workdir):
    """Seedance will Referenzvideos zwischen ~640x640 und ~834x1112 Pixel, 2–15 s, < 50 MB."""
    w, h, dur, _ = probe(src)
    if dur < 2:
        sys.exit("Video ist kürzer als 2 Sekunden – Seedance braucht mindestens 2 s.")
    px = w * h
    target = min(max(px, 409_600), 900_000)
    f = math.sqrt(target / px)
    rnd = math.ceil if target > px else math.floor  # beim Hochskalieren aufrunden, sonst < Mindestgröße
    nw, nh = rnd(w * f / 2) * 2, rnd(h * f / 2) * 2
    out = workdir / f"{src.stem}_ref720.mp4"
    sh(["ffmpeg", "-y", "-i", str(src), "-t", "15", "-vf", f"scale={nw}:{nh}",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", str(out)])
    return out, min(dur, 15.0), nw, nh


def nearest_aspect(w, h):
    r = w / h
    return min(ASPECTS, key=lambda k: abs(ASPECTS[k] - r))


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
    p = argparse.ArgumentParser(description="Supercar-Edit: Seedance 2.0 (720p) + 4K Upscale")
    p.add_argument("--video", required=True, type=Path, help="Referenzclip (Kamerafahrt / geklonter Edit)")
    p.add_argument("--car", required=True, nargs="+", type=Path, help="Bilder vom Auto aus verschiedenen Winkeln")
    p.add_argument("--bg", type=Path, help="Hintergrund/Szene (aktiviert Showreel-Modus)")
    p.add_argument("--interior", type=Path, help="Innenraum-Bild")
    p.add_argument("--brand", default="", help='Schriftzug hinten, z. B. "Porsche"')
    p.add_argument("--extra", default="", help="Zusätzliche Anweisungen (englisch)")
    p.add_argument("--prompt-file", type=Path, help="Eigener Prompt statt des generierten (Reihenfolge: bg, interior, car)")
    p.add_argument("--takes", type=int, default=1, help="Anzahl Versionen (je eigener Seed)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--model", default="mini", choices=list(MODELS), help="mini = günstig, standard = beste Qualität")
    p.add_argument("--res", default="720p", choices=["480p", "720p"])
    p.add_argument("--upscale", default="4k", choices=["1080p", "2k", "4k", "none"])
    p.add_argument("--fps", type=float, default=30, help="Ziel-FPS beim Upscale (>30 = doppelte Kosten)")
    p.add_argument("--ai-audio", action="store_true", help="Seedance-Sound statt Originalton")
    p.add_argument("--out", type=Path, default=Path("out"))
    p.add_argument("--show-prompt", action="store_true", help="Prompt anzeigen und beenden")
    p.add_argument("--dry-run", action="store_true", help="Nur Kosten schätzen, nichts ausführen")
    p.add_argument("-y", "--yes", action="store_true", help="Ohne Rückfrage starten")
    a = p.parse_args()

    images = ([a.bg] if a.bg else []) + ([a.interior] if a.interior else []) + a.car
    if len(images) > MAX_IMAGES:
        free = MAX_IMAGES - (len(images) - len(a.car))
        sys.exit(f"Zu viele Bilder ({len(images)}). Seedance 2.0 erlaubt max. {MAX_IMAGES} – "
                 f"mit deinem Hintergrund/Innenraum also max. {free} Autowinkel.")
    for img in images:
        if not img.exists():
            sys.exit(f"Datei nicht gefunden: {img}")

    if a.prompt_file:
        prompt = a.prompt_file.read_text(encoding="utf-8").strip()
    else:
        prompt = build_prompt(bool(a.bg), bool(a.interior), len(a.car), a.brand, a.extra)
    mode = "Showreel (Kamera aus Video, Szene aus Bild)" if a.bg else "Swap (Szene aus Video)"
    print(f"\nModus: {mode}\n\n--- PROMPT ---\n{prompt}\n--------------")
    if a.show_prompt:
        return

    a.out.mkdir(exist_ok=True)
    work = a.out / "_work"
    work.mkdir(exist_ok=True)

    ref, in_dur, rw, rh = prepare_input(a.video, work)
    _, _, _, src_has_audio = probe(a.video)
    out_dur = int(min(max(round(in_dur), 4), 15))
    aspect = nearest_aspect(rw, rh)

    # Kostenschätzung laut fal: Output voll + Input-Video 0.6x
    endpoint, prices = MODELS[a.model]
    rate = prices[a.res]
    seed_cost = out_dur * rate + in_dur * rate * VIDEO_INPUT_FACTOR
    up = 0 if a.upscale == "none" else out_dur * UPSCALE[a.upscale] * (2 if a.fps > 30 else 1)
    print(f"\nClip: {in_dur:.1f}s → Output {out_dur}s | Format {aspect} | {len(images)} Bilder")
    print(f"Modell: Seedance 2.0 {a.model} @ {a.res}")
    print(f"Pro Take:  ${seed_cost + up:.2f}  (Seedance ${seed_cost:.2f} + Upscale ${up:.2f})")
    if a.takes > 1:
        print(f"Gesamt ({a.takes} Takes): ${a.takes * (seed_cost + up):.2f}")
    print()

    if a.dry_run:
        return
    if not a.yes and input("Starten? (j/n) ").strip().lower() not in ("j", "y", "ja", "yes"):
        return

    print("Lade Dateien hoch …")
    ref_url = fal_client.upload_file(str(ref))
    image_urls = [fal_client.upload_file(str(img)) for img in images]

    base_seed = a.seed if a.seed is not None else random.randint(0, 2**31 - 1)
    for t in range(a.takes):
        seed = base_seed + t
        if a.model == "mini":  # Mini ignoriert den Seed – Takes variieren trotzdem, sind aber nicht reproduzierbar
            tag = f"{a.video.stem}_{a.car[0].stem}_take{t + 1}"
            print(f"\n=== Take {t + 1}/{a.takes} (Mini: kein Seed) ===")
        else:
            tag = f"{a.video.stem}_{a.car[0].stem}_s{seed}"
            print(f"\n=== Take {t + 1}/{a.takes} (seed {seed}) ===")

        print(f"1/2 Seedance 2.0 {a.model} ({a.res}) …")
        args = {
            "prompt": prompt,
            "video_urls": [ref_url],
            "image_urls": image_urls,
            "resolution": a.res,
            "duration": str(out_dur),
            "aspect_ratio": aspect,
            "generate_audio": a.ai_audio,
        }
        if a.model != "mini":  # Mini hat keinen seed-Parameter
            args["seed"] = seed
        res = fal_client.subscribe(endpoint, arguments=args, with_logs=True, on_queue_update=logs)
        v720_url = res["video"]["url"]
        final = download(v720_url, a.out / f"{tag}_{a.res}.mp4")
        print(f"    ✓ {final}")

        if a.upscale != "none":
            print(f"2/2 Upscale → {a.upscale} …")
            up_res = fal_client.subscribe(UPSCALER, arguments={
                "video_url": v720_url,
                "target_resolution": a.upscale,
                "target_fps": a.fps,
                "enhancement_preset": "aigc",
                "enhancement_tier": "standard",
                "fidelity": "high",
            }, with_logs=True, on_queue_update=logs)
            final = download(up_res["video"]["url"], a.out / f"{tag}_{a.upscale}_noaudio.mp4")

        # Originalton (Musik/Sound vom Edit) wieder drunterlegen
        if not a.ai_audio and src_has_audio:
            with_audio = a.out / f"{tag}_{a.upscale if a.upscale != 'none' else a.res}_final.mp4"
            sh(["ffmpeg", "-y", "-i", str(final), "-i", str(a.video), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-af", "apad", "-shortest", str(with_audio)])  # zu kurzen Ton mit Stille auffüllen statt Video abzuschneiden
            final = with_audio

        print(f"    ✓ FERTIG: {final}")


if __name__ == "__main__":
    main()
