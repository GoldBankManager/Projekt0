#!/usr/bin/env python3
"""
ref2video.py – Reference-to-Video mit Wan-VACE (Open Source, läuft lokal auf der GPU – Ersatz für car_swap.py/Seedance)

MODI:
  swap  Szene + Kamerafahrt aus dem Video bleiben, nur das Auto wird durch das Referenz-Auto ersetzt.
        Ablauf: YOLO-Segmentierung findet das Auto in jedem Frame → Maske → Wan-VACE malt das
        Referenz-Auto in die Maske. Längere Clips werden in 81-Frame-Stücken mit Überlappung erzeugt.
  r2v   Reines Reference-to-Video: Referenzbilder (Auto, Person, Produkt …) + Prompt → neues Video.

GPU / MODELL:
  --model Wan-AI/Wan2.1-VACE-14B-diffusers   beste Qualität, 48–80 GB VRAM (A6000/L40S/A100/H100)
  --model Wan-AI/Wan2.1-VACE-1.3B-diffusers  zum Testen, läuft auf RTX 4090 (24 GB), nur 480p
  Zu wenig VRAM → --offload model (etwas langsamer) oder --offload seq (sehr langsam, braucht viel RAM)

BEISPIELE:
  # Auto im Clip tauschen (wie car_swap.py Swap-Modus)
  python ref2video.py swap --video edit.mp4 --ref front.jpg side.jpg \
      --prompt "A white Porsche 911 GT3 RS drifting on a wet race track at night"

  # Reference-to-Video: Auto aus Bildern in eine neue Szene setzen
  python ref2video.py r2v --ref porsche.jpg --res 720p \
      --prompt "The car drives along a coastal road at sunset, drone shot following from behind"

  # 3 Versionen, schneller Test mit dem kleinen Modell
  python ref2video.py r2v --ref car.jpg --prompt "..." --takes 3 --model Wan-AI/Wan2.1-VACE-1.3B-diffusers --res 480p
"""
import argparse
import random
import sys
from pathlib import Path

from PIL import Image, ImageFilter

from common import fit_size, probe, read_frames, write_video

FPS = 16              # Wan erzeugt nativ 16 fps – finish.py interpoliert danach auf 30/60
CHUNK = 81            # Frames pro Durchgang (~5 s); muss 4k+1 sein
RES = {"480p": 832 * 480, "720p": 1280 * 720}
VEHICLES = [2, 3, 5, 7]  # COCO-Klassen: car, motorcycle, bus, truck
NEGATIVE = ("bright tones, overexposed, static, blurred details, subtitles, watermark, text, worst quality, "
            "low quality, JPEG compression residue, deformed, disfigured, duplicated objects, morphing, "
            "flickering, distorted logos, extra wheels, messy background")


def load_pipe(model_id, res, offload):
    import torch
    from diffusers import AutoencoderKLWan, WanVACEPipeline
    from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler

    print(f"Lade {model_id} … (beim ersten Mal wird das Modell heruntergeladen)")
    vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanVACEPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.bfloat16)
    pipe.scheduler = UniPCMultistepScheduler.from_config(
        pipe.scheduler.config, flow_shift=5.0 if res == "720p" else 3.0)
    if offload == "model":
        pipe.enable_model_cpu_offload()
    elif offload == "seq":
        pipe.enable_sequential_cpu_offload()
    else:
        pipe.to("cuda")
    return pipe


def load_yolo(name):
    from ultralytics import YOLO
    return YOLO(name)


def vehicle_mask(yolo, frame, grow):
    """Maske (weiß = neu generieren) des größten Fahrzeugs im Bild, um `grow` Pixel vergrößert. None = nichts gefunden."""
    import numpy as np
    import cv2
    r = yolo(np.asarray(frame)[..., ::-1], classes=VEHICLES, verbose=False)[0]
    if r.masks is None or len(r.masks) == 0:
        return None
    polys = r.masks.xy
    areas = [cv2.contourArea(p.astype(np.float32)) if len(p) >= 3 else 0 for p in polys]
    m = np.zeros((frame.height, frame.width), np.uint8)
    cv2.fillPoly(m, [polys[int(np.argmax(areas))].astype(np.int32)], 255)
    if grow:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow * 2 + 1, grow * 2 + 1)))
    return Image.fromarray(m)


def cutout(yolo, path):
    """Referenzbild: Fahrzeug freistellen und auf weißen Hintergrund setzen (so mag es VACE am liebsten)."""
    img = Image.open(path).convert("RGB")
    m = vehicle_mask(yolo, img, grow=4)
    if m is None:
        print(f"    (kein Fahrzeug in {path.name} erkannt – nehme das Bild unverändert)")
        return img
    white = Image.new("RGB", img.size, (255, 255, 255))
    return Image.composite(img, white, m.filter(ImageFilter.GaussianBlur(2))).crop(m.getbbox())


def frames_4k1(n):
    """Nächste gültige Frame-Anzahl >= n (Wan braucht 4k+1)."""
    return n + (-(n - 1)) % 4


def run_swap(a, pipe, yolo, refs, seed):
    import torch
    w, h, dur, _, _ = probe(a.video)
    width, height = fit_size(w, h, RES[a.res])
    max_frames = int(min(dur - a.start, a.max_seconds) * FPS)
    frames = read_frames(a.video, FPS, width, height, max_frames=max_frames, start=a.start)
    if len(frames) < 5:
        sys.exit("Clip zu kurz.")
    print(f"    {len(frames)} Frames @ {FPS} fps, {width}x{height} – suche Fahrzeug-Masken …")

    masks, last = [], None
    for f in frames:
        m = vehicle_mask(yolo, f, a.grow)
        last = m if m is not None else last
        masks.append(last)
    if all(m is None for m in masks):
        sys.exit("In keinem Frame wurde ein Fahrzeug gefunden.")
    first = next(m for m in masks if m is not None)
    masks = [m if m is not None else first for m in masks]  # Lücken am Anfang auffüllen

    out, pos, overlap = [], 0, a.overlap
    while pos < len(frames):
        start = max(0, pos - overlap) if out else 0
        seg = frames[start:start + CHUNK]
        seg_masks = masks[start:start + CHUNK]
        keep = pos - start  # schon erzeugte Frames, die als feste Vorgabe mitlaufen
        n = frames_4k1(len(seg))
        seg_video = out[-keep:] + seg[keep:] if keep else list(seg)
        black = Image.new("L", (width, height), 0)
        seg_masks = [black] * keep + seg_masks[keep:]
        seg_video += [seg_video[-1]] * (n - len(seg_video))
        seg_masks += [seg_masks[-1]] * (n - len(seg_masks))
        print(f"    Frames {start}–{start + len(seg) - 1} ({n} inkl. Auffüllen) …")
        res = pipe(video=seg_video, mask=seg_masks, reference_images=refs,
                   prompt=a.prompt, negative_prompt=a.negative,
                   height=height, width=width, num_frames=n,
                   num_inference_steps=a.steps, guidance_scale=a.cfg,
                   generator=torch.Generator().manual_seed(seed), output_type="pil").frames[0]
        new = res[keep:len(seg)]
        out += new
        pos = start + len(seg)
    return out


def run_r2v(a, pipe, refs, seed):
    import torch
    w, h = map(int, a.aspect.split(":"))
    width, height = fit_size(w * 1000, h * 1000, RES[a.res])
    n = frames_4k1(int(a.seconds * FPS))
    print(f"    {n} Frames @ {FPS} fps, {width}x{height}")
    return pipe(reference_images=refs, prompt=a.prompt, negative_prompt=a.negative,
                height=height, width=width, num_frames=n,
                num_inference_steps=a.steps, guidance_scale=a.cfg,
                generator=torch.Generator().manual_seed(seed), output_type="pil").frames[0]


def main():
    p = argparse.ArgumentParser(description="Reference-to-Video mit Wan-VACE (lokal, Open Source)")
    p.add_argument("mode", choices=["swap", "r2v"])
    p.add_argument("--ref", required=True, nargs="+", type=Path, help="Referenzbilder (1–3 empfohlen)")
    p.add_argument("--prompt", required=True, help="Szene auf Englisch beschreiben (Auto, Farbe, Umgebung, Kamera)")
    p.add_argument("--negative", default=NEGATIVE)
    p.add_argument("--video", type=Path, help="Nur swap: Clip, in dem das Auto ersetzt wird")
    p.add_argument("--start", type=float, default=0.0, help="swap: Startsekunde im Clip")
    p.add_argument("--max-seconds", type=float, default=10.0, help="swap: max. Länge (länger = mehr Durchgänge)")
    p.add_argument("--overlap", type=int, default=8, help="swap: Frames Überlappung zwischen Durchgängen")
    p.add_argument("--grow", type=int, default=12, help="swap: Maske um N Pixel vergrößern (Schatten/Kanten)")
    p.add_argument("--seconds", type=float, default=5.0, help="r2v: Länge (max. ~5 s)")
    p.add_argument("--aspect", default="9:16", help="r2v: 9:16 (Standard, TikTok/Reels/Shorts), 16:9, 1:1")
    p.add_argument("--res", default="720p", choices=list(RES))
    p.add_argument("--model", default="Wan-AI/Wan2.1-VACE-14B-diffusers")
    p.add_argument("--offload", default="none", choices=["none", "model", "seq"])
    p.add_argument("--yolo", default="yolo11x-seg.pt", help="Segmentierungsmodell (ultralytics)")
    p.add_argument("--no-cutout", action="store_true", help="Referenzbilder nicht freistellen")
    p.add_argument("--steps", type=int, default=30)
    p.add_argument("--cfg", type=float, default=5.0)
    p.add_argument("--takes", type=int, default=1, help="Anzahl Versionen (je eigener Seed)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out", type=Path, default=Path("out"))
    a = p.parse_args()

    if a.mode == "swap" and not a.video:
        sys.exit("swap braucht --video")
    for f in a.ref + ([a.video] if a.video else []):
        if not f.exists():
            sys.exit(f"Datei nicht gefunden: {f}")
    if len(a.ref) > 3:
        print("Hinweis: Mehr als 3 Referenzbilder machen VACE eher schlechter als besser.")
    if a.mode == "r2v" and a.seconds > 5.1:
        print("Hinweis: Wan erzeugt am stabilsten ~5 s (81 Frames) – längere Clips driften.")
        if a.seconds > 10:
            a.seconds = 10
    a.out.mkdir(exist_ok=True)

    need_yolo = a.mode == "swap" or not a.no_cutout
    yolo = load_yolo(a.yolo) if need_yolo else None
    refs = [Image.open(r).convert("RGB") if a.no_cutout else cutout(yolo, r) for r in a.ref]
    if not a.no_cutout:
        for r, img in zip(a.ref, refs):
            img.save(a.out / f"ref_{r.stem}_cutout.png")

    pipe = load_pipe(a.model, a.res, a.offload)
    base_seed = a.seed if a.seed is not None else random.randint(0, 2**31 - 1)
    stem = a.video.stem if a.video else a.ref[0].stem
    for t in range(a.takes):
        seed = base_seed + t
        print(f"\n=== Take {t + 1}/{a.takes} (seed {seed}) ===")
        frames = run_swap(a, pipe, yolo, refs, seed) if a.mode == "swap" else run_r2v(a, pipe, refs, seed)
        path = write_video(frames, a.out / f"{stem}_{a.mode}_s{seed}_{FPS}fps.mp4", FPS)
        print(f"    ✓ {path}  →  weiter mit: python finish.py {path}"
              + (f" --audio-from {a.video}" if a.video else "")
              + (f" --audio-offset {a.start:g}" if a.video and a.start else ""))


if __name__ == "__main__":
    main()
