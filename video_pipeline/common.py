"""Gemeinsame Helfer für die Pipeline-Skripte (ffmpeg/ffprobe, Frames lesen/schreiben)."""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Fehler bei: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def probe(path):
    """Breite, Höhe (nach Rotation), Dauer, FPS, hat Ton."""
    out = json.loads(sh(["ffprobe", "-v", "error", "-print_format", "json",
                         "-show_streams", "-show_format", path]))
    v = next(s for s in out["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in out["streams"])
    w, h = int(v["width"]), int(v["height"])
    rot = v.get("tags", {}).get("rotate") or next(
        (d.get("rotation") for d in v.get("side_data_list", []) if "rotation" in d), 0)
    if abs(int(float(rot))) % 180 == 90:
        w, h = h, w
    num, den = v.get("avg_frame_rate", "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    return w, h, float(out["format"]["duration"]), fps, has_audio


def fit_size(w, h, max_pixels, base=16):
    """Größte Auflösung mit gleichem Seitenverhältnis, <= max_pixels, Seiten durch `base` teilbar."""
    f = min(1.0, (max_pixels / (w * h)) ** 0.5)
    return max(base, int(w * f) // base * base), max(base, int(h * f) // base * base)


def read_frames(path, fps, width, height, max_frames=None, start=0.0):
    """Video als Liste von PIL-Bildern, auf feste FPS und Größe gebracht."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start}", "-i", path,
           "-vf", f"fps={fps},scale={width}:{height}:flags=lanczos"]
    if max_frames:
        cmd += ["-frames:v", str(max_frames)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run([str(c) for c in cmd], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg konnte {path} nicht lesen:\n{r.stderr.decode()[-1500:]}")
    size = width * height * 3
    return [Image.frombytes("RGB", (width, height), r.stdout[i:i + size])
            for i in range(0, len(r.stdout) - size + 1, size)]


def write_video(frames, path, fps, crf=16):
    """PIL-Bilder oder numpy-Arrays (0–1 float oder uint8) als H.264-MP4 speichern. Nimmt auch Generatoren."""
    import itertools
    import numpy as np
    it = iter(frames)
    first = next(it)
    h, w = np.asarray(first).shape[:2]
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-crf", str(crf), "-preset", "slow",
                          "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in itertools.chain([first], it):
        a = np.asarray(f)
        if a.dtype != np.uint8:
            a = (np.clip(a, 0, 1) * 255).round().astype(np.uint8)
        p.stdin.write(a[..., :3].tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit(f"ffmpeg konnte {path} nicht schreiben")
    return Path(path)
