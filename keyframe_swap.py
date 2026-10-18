#!/usr/bin/env python3
"""
keyframe_swap.py – Auto-Tausch über Keyframes: erst Standbilder exakt tauschen und prüfen, dann Video.
Das Videomodell muss das Auto nicht mehr aus Fotos erraten, sondern bekommt fertige Frames
im richtigen Winkel, Licht und Maßstab.

ABLAUF (3 Schritte, jeder einzeln aufrufbar):
  1) prep   Clip zuschneiden, Keyframes auswählen und als PNG speichern            (kostenlos)
  2) swap   Auto in jedem Keyframe per Bild-Editor tauschen + Vergleichsbild bauen (~$0.15/Frame)
            → review.jpg ansehen, falsche Frames mit --only neu machen
  3) video  Freigegebene Keyframes → Video-Edit → Upscale → Originalton

ENGINES:
  luma   Luma Ray 3.2 Video-Edit: Keyframes werden an die exakten Frame-Positionen geheftet
         (5 s oder 10 s pro Durchgang; 540p $0.144/s, 720p $0.216/s, 1080p $0.432/s)
  kling  Kling O3 Pro Edit: bis zu 4 Keyframes als Referenz, nicht fest verankert
         (3–15 s; $0.14/s; günstiger, aber weniger exakt)

BEISPIEL:
  python keyframe_swap.py prep  --video edit.mp4 --name gt3
  python keyframe_swap.py swap  --name gt3 --car front.jpg side.jpg rear.jpg
  python keyframe_swap.py swap  --name gt3 --car front.jpg side.jpg rear.jpg --only 48,96
  python keyframe_swap.py video --name gt3 --res 720p
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import fal_client

from car_swap import UPSCALE, UPSCALER, download, logs, probe, sh

LUMA = "luma/agent/ray/v3.2/video-to-video"
LUMA_PRICE = {"540p": 0.144, "720p": 0.216, "1080p": 0.432}  # $/s laut fal (Stand Okt 2026)
KLING = "fal-ai/kling-video/o3/pro/video-to-video/edit"
KLING_PRICE = 0.14
KLING_MAX_IMAGES = 4
EDITORS = {  # Endpoint, $/Bild
    "nano-banana-pro": ("fal-ai/nano-banana-pro/edit", 0.15),
    "seedream5":       ("bytedance/seedream/v5/pro/edit", 0.0675),
}
EDITOR_MAX_REFS = {"nano-banana-pro": 13, "seedream5": 9}  # + 1 Slot für den Frame selbst
IMAGE_ASPECTS = {"21:9": 21 / 9, "16:9": 16 / 9, "3:2": 3 / 2, "4:3": 4 / 3, "5:4": 5 / 4, "1:1": 1.0,
                 "4:5": 4 / 5, "3:4": 3 / 4, "2:3": 2 / 3, "9:16": 9 / 16}


def frame_prompt(n_car, extra):
    car_ref = "Image 2" if n_car == 1 else f"Images 2 to {n_car + 1}"
    lines = [
        "Image 1 is a single frame from a video.",
        f"{car_ref} show the new car" + (" from different angles." if n_car > 1 else "."),
        f"Replace only the car in Image 1 with the car from {car_ref}.",
        "Keep the exact same position, perspective, camera angle, scale, orientation and direction of travel "
        "as the original car in Image 1.",
        "The new car must match the references exactly: body shape, proportions, color, livery, rims, "
        "brake calipers, lights, grille, badges and numbers.",
        "Match the lighting, reflections, motion blur, depth of field, grain and color grade of Image 1, "
        "with realistic contact shadows on the ground.",
        "Keep everything else in Image 1 unchanged: background, road, people, other objects, "
        "all text, logos, captions and watermarks.",
        "Return the full frame with the same framing and composition as Image 1.",
    ]
    if extra:
        lines.append(extra.strip())
    return "\n".join(lines)


def video_prompt(engine, n_keys, extra):
    if engine == "kling":
        refs = " ".join(f"@Image{i + 1}" for i in range(n_keys))
        lines = [
            f"Replace only the car in @Video1 with the car shown in {refs}. "
            f"{refs} are frames of this exact video with the new car already in place.",
            "The car must look exactly like in these frames from every angle.",
        ]
    else:
        lines = [
            "Replace the car with the new car shown in the keyframes.",
            "The car must look exactly like in the keyframes from every angle: body shape, color, rims, "
            "lights, badges and proportions.",
        ]
    lines += [
        "Keep the camera motion, cuts, timing, background, lighting, color grading and every other element "
        "of the source video exactly the same.",
        "Preserve every caption, logo and on-screen text element exactly as it appears.",
        "No flickering, no morphing, no duplicated logos.",
    ]
    if extra:
        lines.append(extra.strip())
    return "\n".join(lines)


def fps_of(path):
    out = json.loads(sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=avg_frame_rate", "-of", "json", str(path)]))
    num, den = out["streams"][0]["avg_frame_rate"].split("/")
    return float(num) / float(den or 1)


def scene_cuts(path, thresh):
    """Zeitpunkte harter Schnitte (ffmpeg scene detection)."""
    r = sh(["ffprobe", "-v", "error", "-f", "lavfi", "-show_entries", "frame=pts_time", "-of", "csv=p=0",
            f"movie={path},select=gt(scene\\,{thresh})"])
    return [float(t) for t in r.split() if t.strip()]


def pick_keys(n_frames, fps, cuts, every, at):
    if at:
        idx = {min(n_frames - 1, round(t * fps)) for t in at}
    else:
        idx = {0, n_frames - 1}
        for t in cuts:  # Frame direkt nach dem Schnitt – dort taucht das Auto im neuen Winkel auf
            idx.add(min(n_frames - 1, round(t * fps)))
        step = max(1, round(every * fps))
        keys = sorted(idx)
        for a, b in zip(keys, keys[1:]):  # Lücken über "every" Sekunden auffüllen
            gaps = math.ceil((b - a) / step)
            for g in range(1, gaps):
                idx.add(a + round(g * (b - a) / gaps))
    return sorted(idx)[:64]


def load(project):
    f = project / "project.json"
    if not f.exists():
        sys.exit(f"Kein Projekt in {project} – zuerst 'prep' ausführen.")
    return json.loads(f.read_text())


def save(project, data):
    (project / "project.json").write_text(json.dumps(data, indent=2))


def cmd_prep(a):
    project = a.out / a.name
    (project / "frames").mkdir(parents=True, exist_ok=True)
    w, h, dur, _ = probe(a.video)
    avail = dur - a.start
    if a.engine == "luma":
        if avail < 2:
            sys.exit(f"Ab {a.start}s sind nur {avail:.1f}s übrig – zu kurz.")
        length = 10 if avail > 5.5 else 5
        if avail > 10.5:
            print(f"Hinweis: Clip ist {avail:.1f}s lang, Luma macht max. 10 s. "
                  f"Für den Rest später nochmal mit --start {a.start + 10:g} laufen lassen.")
    else:
        if avail < 3:
            sys.exit("Kling braucht mindestens 3 s.")
        length = min(avail, 15.0)
    real = min(avail, length)  # Luma will genau 5/10 s → Rest mit eingefrorenem letzten Frame auffüllen
    fps = round(fps_of(a.video)) or 30
    if min(w, h) < 720 and a.engine == "kling":
        print("Hinweis: Kling will mind. 720 px – Clip wird hochskaliert.")
    scale = "scale=-2:720" if (a.engine == "kling" and min(w, h) < 720 and w >= h) else \
            "scale=720:-2" if (a.engine == "kling" and min(w, h) < 720) else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    clip = project / "clip.mp4"
    pad = f",tpad=stop_mode=clone:stop_duration={length - real:.3f}" if length - real > 0.01 else ""
    sh(["ffmpeg", "-y", "-ss", str(a.start), "-i", str(a.video), "-t", str(length),
        "-vf", f"fps={fps},{scale}{pad}", "-af", "apad", "-t", str(length),
        "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(clip)])
    cw, ch, _, has_audio = probe(clip)
    n_frames = int(real * fps)  # nur echte Frames, nicht die aufgefüllten

    cuts = [] if a.at else scene_cuts(clip, a.scene)
    keys = pick_keys(n_frames, fps, cuts, a.every, a.at)
    sel = "+".join(f"eq(n\\,{k})" for k in keys)
    tmp = project / "frames" / "_tmp"
    tmp.mkdir(exist_ok=True)
    sh(["ffmpeg", "-y", "-i", str(clip), "-vf", f"select='{sel}'", "-fps_mode", "passthrough",
        str(tmp / "%04d.png")])
    extracted = sorted(tmp.glob("*.png"))
    if len(extracted) != len(keys):
        sys.exit(f"Frame-Extraktion fehlgeschlagen ({len(extracted)} statt {len(keys)} Frames).")
    for old in (project / "frames").glob("f_*.png"):
        old.unlink()
    for k, f in zip(keys, extracted):
        f.rename(project / "frames" / f"f_{k:04d}.png")
    tmp.rmdir()

    save(project, {"source": str(a.video), "start": a.start, "engine": a.engine, "fps": fps,
                   "length": length, "real_length": real, "size": [cw, ch], "has_audio": has_audio, "keys": keys,
                   "cuts": cuts})
    padded = f" (aufgefüllt von {real:.1f}s)" if pad else ""
    print(f"\nClip: {length:g}s{padded} @ {fps} fps, {cw}x{ch} | Schnitte erkannt: {len(cuts)}")
    print(f"Keyframes ({len(keys)}): " + ", ".join(f"#{k} ({k / fps:.2f}s)" for k in keys))
    print(f"Gespeichert in {project / 'frames'}")
    ed_price = EDITORS["nano-banana-pro"][1]
    print(f"\nNächster Schritt 'swap': ca. ${len(keys) * ed_price:.2f} ({len(keys)} × ${ed_price} Nano Banana Pro)")


def fit_to(src, dst, w, h):
    """Editor-Ergebnis exakt auf Frame-Größe bringen (skalieren + mittig zuschneiden)."""
    sh(["ffmpeg", "-y", "-i", str(src), "-vf",
        f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}", "-frames:v", "1", str(dst)])


def build_review(project, keys, w):
    """Vergleichsbild: links Original, rechts getauscht – eine Zeile pro Keyframe."""
    rows = []
    for k in keys:
        f, s = project / "frames" / f"f_{k:04d}.png", project / "keys" / f"k_{k:04d}.png"
        if s.exists():
            rows.append((f, s))
    if not rows:
        return None
    tw = min(640, w)
    inputs, filters = [], []
    for i, (f, s) in enumerate(rows):
        inputs += ["-i", str(f), "-i", str(s)]
        filters.append(f"[{2 * i}:v]scale={tw}:-2[a{i}];[{2 * i + 1}:v]scale={tw}:-2[b{i}];"
                       f"[a{i}][b{i}]hstack[r{i}]")
    stack = "".join(f"[r{i}]" for i in range(len(rows)))
    fc = ";".join(filters) + (f";{stack}vstack=inputs={len(rows)}[out]" if len(rows) > 1 else "")
    out = project / "review.jpg"
    sh(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[out]" if len(rows) > 1 else "[r0]",
        "-frames:v", "1", "-q:v", "3", str(out)])
    return out


def cmd_swap(a):
    project = a.out / a.name
    p = load(project)
    keys = p["keys"]
    if a.only:
        wanted = {int(x) for x in a.only.split(",")}
        missing = wanted - set(keys)
        if missing:
            sys.exit(f"Keine Keyframes mit Nummer {sorted(missing)}. Vorhanden: {keys}")
        keys = [k for k in keys if k in wanted]
    if len(a.car) > EDITOR_MAX_REFS[a.editor]:
        sys.exit(f"Max. {EDITOR_MAX_REFS[a.editor]} Autobilder für {a.editor}.")
    for img in a.car:
        if not img.exists():
            sys.exit(f"Datei nicht gefunden: {img}")

    endpoint, price = EDITORS[a.editor]
    prompt = frame_prompt(len(a.car), a.extra)
    print(f"\n--- FRAME-PROMPT ---\n{prompt}\n--------------------")
    print(f"{len(keys)} Frames × ${price} = ${len(keys) * price:.2f} ({a.editor})\n")
    if a.dry_run:
        return
    if not a.yes and input("Starten? (j/n) ").strip().lower() not in ("j", "y", "ja", "yes"):
        return

    w, h = p["size"]
    aspect = min(IMAGE_ASPECTS, key=lambda k: abs(IMAGE_ASPECTS[k] - w / h))
    (project / "keys").mkdir(exist_ok=True)
    (project / "keys" / "_raw").mkdir(exist_ok=True)
    car_urls = [fal_client.upload_file(str(c)) for c in a.car]

    for k in keys:
        print(f"Frame #{k} …")
        frame_url = fal_client.upload_file(str(project / "frames" / f"f_{k:04d}.png"))
        args = {"prompt": prompt, "image_urls": [frame_url] + car_urls, "num_images": 1}
        if a.editor == "nano-banana-pro":
            args.update({"aspect_ratio": aspect, "resolution": "2K", "output_format": "png"})
        else:
            args.update({"image_size": "auto_2K", "output_format": "png"})
        try:
            res = fal_client.subscribe(endpoint, arguments=args, with_logs=True, on_queue_update=logs)
        except Exception as e:  # einzelner Frame darf scheitern, Rest läuft weiter
            print(f"    ✗ Fehler: {e}")
            continue
        target = project / "keys" / f"k_{k:04d}.png"
        if target.exists():  # alte Version behalten
            v = 1
            while (project / "keys" / f"k_{k:04d}_v{v}.png").exists():
                v += 1
            shutil.move(target, project / "keys" / f"k_{k:04d}_v{v}.png")
        raw = download(res["images"][0]["url"], project / "keys" / "_raw" / f"k_{k:04d}.png")
        fit_to(raw, target, w, h)
        print(f"    ✓ {target}")

    review = build_review(project, p["keys"], w)
    if review:
        done = [k for k in p["keys"] if (project / "keys" / f"k_{k:04d}.png").exists()]
        print(f"\nVergleich (links Original, rechts neu): {review}")
        print("Zeilen von oben: " + ", ".join(f"{i + 1}=#{k}" for i, k in enumerate(done)))
    todo = [k for k in p["keys"] if not (project / "keys" / f"k_{k:04d}.png").exists()]
    if todo:
        print(f"Noch ohne getauschten Frame: {todo}")
    print("Falsche Frames neu machen:  swap ... --only " + ",".join(map(str, p["keys"][:2])))


def cmd_video(a):
    project = a.out / a.name
    p = load(project)
    engine = p["engine"]
    keys = [k for k in p["keys"] if (project / "keys" / f"k_{k:04d}.png").exists()]
    if not keys:
        sys.exit("Keine getauschten Keyframes – zuerst 'swap' ausführen.")
    missing = sorted(set(p["keys"]) - set(keys))
    if missing:
        print(f"Achtung: Frames {missing} haben keine getauschte Version und werden ausgelassen.")
    if engine == "kling" and len(keys) > KLING_MAX_IMAGES:  # gleichmäßig verteilt auswählen
        keys = [keys[round(i * (len(keys) - 1) / (KLING_MAX_IMAGES - 1))] for i in range(KLING_MAX_IMAGES)]

    length = p["length"]
    prompt = video_prompt(engine, len(keys), a.extra)
    cost = length * (LUMA_PRICE[a.res] if engine == "luma" else KLING_PRICE)
    up = 0 if a.upscale == "none" else math.ceil(length) * UPSCALE[a.upscale] * (2 if a.fps > 30 else 1)
    print(f"\n--- VIDEO-PROMPT ---\n{prompt}\n--------------------")
    label = f"Luma Ray 3.2 @ {a.res}, {len(keys)} verankerte Keyframes" if engine == "luma" \
        else f"Kling O3 Pro, {len(keys)} Keyframes als Referenz"
    print(f"{label} | {length:g}s")
    print(f"Kosten: ${cost + up:.2f}  (Video ${cost:.2f} + Upscale ${up:.2f})\n")
    if a.dry_run:
        return
    if not a.yes and input("Starten? (j/n) ").strip().lower() not in ("j", "y", "ja", "yes"):
        return

    print("Lade hoch …")
    clip_url = fal_client.upload_file(str(project / "clip.mp4"))
    key_urls = [fal_client.upload_file(str(project / "keys" / f"k_{k:04d}.png")) for k in keys]

    if engine == "luma":
        args = {"prompt": prompt, "video_url": clip_url, "keyframes": key_urls, "keyframe_indexes": keys,
                "duration": f"{int(length)}s", "resolution": a.res}
        if a.strength:
            args["edit_strength"] = a.strength
        res = fal_client.subscribe(LUMA, arguments=args, with_logs=True, on_queue_update=logs)
    else:
        res = fal_client.subscribe(KLING, arguments={
            "prompt": prompt, "video_url": clip_url, "image_urls": key_urls, "keep_audio": False,
        }, with_logs=True, on_queue_update=logs)

    take = 1
    while list(project.glob(f"take{take}_*")):
        take += 1
    tag = f"take{take}"
    vid_url = res["video"]["url"]
    final = download(vid_url, project / f"{tag}_{engine}.mp4")
    print(f"    ✓ {final}")

    if a.upscale != "none":
        print(f"Upscale → {a.upscale} …")
        up_res = fal_client.subscribe(UPSCALER, arguments={
            "video_url": vid_url, "target_resolution": a.upscale, "target_fps": a.fps,
            "enhancement_preset": "aigc", "enhancement_tier": "standard", "fidelity": "high",
        }, with_logs=True, on_queue_update=logs)
        final = download(up_res["video"]["url"], project / f"{tag}_{a.upscale}_noaudio.mp4")

    # Originalton drunterlegen und aufgefüllte Sekunden wieder abschneiden
    real = p.get("real_length", length)
    out = project / f"{tag}_final.mp4"
    audio = ["-i", str(project / "clip.mp4"), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"] \
        if p["has_audio"] else ["-map", "0:v:0"]
    sh(["ffmpeg", "-y", "-i", str(final), *audio, "-t", f"{real:.3f}",
        "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", str(out)])
    final = out
    print(f"    ✓ FERTIG: {final}")


def main():
    p = argparse.ArgumentParser(description="Auto-Tausch über geprüfte Keyframes")
    p.add_argument("--out", type=Path, default=Path("out"))
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("prep", help="Clip zuschneiden + Keyframes extrahieren (kostenlos)")
    s.add_argument("--video", required=True, type=Path)
    s.add_argument("--name", required=True, help="Projektname (Ordner unter out/)")
    s.add_argument("--engine", default="luma", choices=["luma", "kling"])
    s.add_argument("--start", type=float, default=0.0, help="Startzeit im Video (s)")
    s.add_argument("--every", type=float, default=2.0, help="Max. Abstand zwischen Keyframes (s)")
    s.add_argument("--scene", type=float, default=0.3, help="Schwelle Schnitterkennung (0–1)")
    s.add_argument("--at", type=lambda v: [float(x) for x in v.split(",")],
                   help='Keyframes manuell setzen, Sekunden im Clip, z. B. "0,1.5,4"')

    s = sub.add_parser("swap", help="Auto in den Keyframes tauschen")
    s.add_argument("--name", required=True)
    s.add_argument("--car", required=True, nargs="+", type=Path, help="Fotos vom neuen Auto")
    s.add_argument("--editor", default="nano-banana-pro", choices=list(EDITORS))
    s.add_argument("--only", help="Nur diese Frame-Nummern neu machen, z. B. 48,96")
    s.add_argument("--extra", default="", help="Zusätzliche Anweisungen (englisch)")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("-y", "--yes", action="store_true")

    s = sub.add_parser("video", help="Video aus den freigegebenen Keyframes erzeugen")
    s.add_argument("--name", required=True)
    s.add_argument("--res", default="720p", choices=list(LUMA_PRICE), help="nur Luma")
    s.add_argument("--strength", choices=[f"{m}_{i}" for m in ("adhere", "flex", "reimagine") for i in (1, 2, 3)],
                   help="Luma: wie nah am Original (adhere = am nächsten)")
    s.add_argument("--upscale", default="4k", choices=["1080p", "2k", "4k", "none"])
    s.add_argument("--fps", type=float, default=30)
    s.add_argument("--extra", default="")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("-y", "--yes", action="store_true")

    a = p.parse_args()
    {"prep": cmd_prep, "swap": cmd_swap, "video": cmd_video}[a.cmd](a)


if __name__ == "__main__":
    main()
