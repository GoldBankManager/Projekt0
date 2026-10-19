#!/usr/bin/env python3
"""
finish.py – Nachbearbeitung & Rendern: flüssiger (FPS hoch), schärfer (Upscale bis 4K), Ton + Untertitel drauf

  FPS        RIFE v4.26 (KI-Zwischenbilder, 16 fps von Wan → 30/60 fps); Fallback: ffmpeg minterpolate
  Upscale    Real-ESRGAN über spandrel (x4 auf der GPU, danach exakt auf 1080p/1440p/4K skaliert)
  Ton        Originalton aus dem Quellclip wieder drunterlegen (wie in car_swap.py)
  Untertitel .srt aus analyze.py einbrennen

BEISPIELE:
  python finish.py out/edit_swap_s123_16fps.mp4 --audio-from edit.mp4            # 30 fps, 1080p, Originalton
  python finish.py out/clip.mp4 --res 2160 --fps 60                             # 4K, 60 fps
  python finish.py out/clip.mp4 --srt out/edit.srt --upscale none
"""
import argparse
import re
import urllib.request
from pathlib import Path

from common import probe, read_frames, sh, write_video

WEIGHTS = {  # Real-ESRGAN-Gewichte (BSD-3), werden beim ersten Mal geladen
    "x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "general": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
}
CACHE = Path.home() / ".cache" / "video_pipeline"


def interpolate_ffmpeg(src, dst, fps):
    """Bewegungskompensierte Zwischenbilder (CPU) – Fallback ohne GPU."""
    sh(["ffmpeg", "-y", "-v", "error", "-i", src,
        "-vf", f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
        "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", dst])
    return dst


def interpolate_rife(src, dst, fps):
    """RIFE v4.26: KI-Zwischenbilder für beliebige Ziel-FPS. Läuft vor dem Upscale auf der kleinen Auflösung."""
    import numpy as np
    import torch
    from ccvfi import AutoModel, ConfigType
    w, h, _, fps_in, _ = probe(src)
    frames = read_frames(src, fps_in, w, h)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    CACHE.mkdir(parents=True, exist_ok=True)
    model = AutoModel.from_pretrained(ConfigType.RIFE_IFNet_v426_heavy, device=dev, fp16=dev.type == "cuda",
                                      model_dir=str(CACHE))
    dtype = torch.float16 if dev.type == "cuda" else torch.float32
    scale = 1.0 if h <= 1080 else 0.5  # Fluss bei großen Bildern auf halber Auflösung schätzen

    def tensor(f):
        return torch.from_numpy(np.asarray(f).copy()).permute(2, 0, 1)[None].to(dev, dtype) / 255

    def frames_out():
        for k in range(int((len(frames) - 1) * fps / fps_in) + 1):
            t = k * fps_in / fps
            i = min(int(t), len(frames) - 1)
            frac = t - i
            if frac < 1e-3 or i == len(frames) - 1:
                yield np.asarray(frames[i])
                continue
            y = model.inference(torch.stack([tensor(frames[i]), tensor(frames[i + 1])], 1), timestep=frac, scale=scale)
            yield (y[0].permute(1, 2, 0).float().clamp(0, 1).cpu().numpy() * 255).round().astype(np.uint8)

    return write_video(frames_out(), dst, fps, crf=14)


def load_upscaler(name):
    import torch
    from spandrel import ModelLoader
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / Path(WEIGHTS[name]).name
    if not path.exists():
        print(f"    lade {path.name} …")
        urllib.request.urlretrieve(WEIGHTS[name], path)
    model = ModelLoader().load_from_file(path).cuda().eval()
    if model.supports_half:
        model.half()
    return model, torch


def target_size(w, h, res):
    """„1080p“ = kurze Seite 1080 – also 1920x1080 quer und 1080x1920 hochkant."""
    for rw, rh in ((16, 9), (9, 16), (1, 1), (4, 5), (4, 3), (3, 4)):  # fast Standardformat → exakt (z. B. 832x464)
        if abs(w / h - rw / rh) / (rw / rh) < 0.03:
            return (round(res * rw / rh / 2) * 2, res) if rw >= rh else (res, round(res * rh / rw / 2) * 2)
    f = res / min(w, h)
    return round(w * f / 2) * 2, round(h * f / 2) * 2


def upscale(src, dst, width, height, name):
    w, h, _, fps, _ = probe(src)
    model, torch = load_upscaler(name)
    dtype = torch.float16 if model.supports_half else torch.float32

    def frames():
        import numpy as np
        from PIL import Image
        for f in read_frames(src, fps, w, h):
            x = torch.from_numpy(np.asarray(f)).permute(2, 0, 1)[None].to("cuda", dtype) / 255
            with torch.no_grad():
                y = model(x).clamp(0, 1)[0].permute(1, 2, 0).float().cpu().numpy()
            yield np.asarray(Image.fromarray((y * 255).round().astype("uint8")).resize(
                (width, height), Image.LANCZOS))

    print(f"    {w}x{h} → {width}x{height} (Real-ESRGAN {name})")
    return write_video(frames(), dst, fps, crf=14)


def main():
    p = argparse.ArgumentParser(description="FPS hoch, Upscale, Ton + Untertitel")
    p.add_argument("video", type=Path)
    p.add_argument("--fps", type=float, default=30, help="Ziel-FPS (0 = unverändert)")
    p.add_argument("--interp", default="rife", choices=["rife", "ffmpeg"], help="Zwischenbilder: rife = KI, ffmpeg = CPU")
    p.add_argument("--res", "--height", dest="res", type=int, default=1080,
                   help="Ziel: 1080 (Standard, Social Media), 1440, 2160 (4K); kurze Seite, gilt auch hochkant; 0 = unverändert")
    p.add_argument("--upscale", default="x4plus", choices=[*WEIGHTS, "none"],
                   help="x4plus = beste Qualität, general = schneller, none = nur skalieren")
    p.add_argument("--audio-from", type=Path, help="Ton aus diesem Clip übernehmen")
    p.add_argument("--audio-offset", type=float, default=0.0, help="Startsekunde im Ton-Clip (= --start bei ref2video)")
    p.add_argument("--srt", type=Path, help="Untertitel einbrennen")
    p.add_argument("--out", type=Path, default=None)
    a = p.parse_args()

    work = a.video.parent / "_work"
    work.mkdir(parents=True, exist_ok=True)
    cur = a.video
    w, h, _, fps, _ = probe(cur)

    if a.fps and abs(a.fps - fps) > 0.01:
        print(f"1/3 FPS {fps:g} → {a.fps:g} …")
        interp = interpolate_rife if a.interp == "rife" else interpolate_ffmpeg
        cur = interp(cur, work / f"{a.video.stem}_{a.fps:g}fps.mp4", a.fps)

    if a.res and a.res != min(w, h):
        tw, th = target_size(w, h, a.res)
        print(f"2/3 Skalieren {w}x{h} → {tw}x{th} …")
        dst = work / f"{a.video.stem}_{a.res}p.mp4"
        if a.upscale == "none" or a.res < min(w, h):
            sh(["ffmpeg", "-y", "-v", "error", "-i", cur, "-vf", f"scale={tw}:{th}:flags=lanczos",
                "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", dst])
            cur = dst
        else:
            cur = upscale(cur, dst, tw, th, a.upscale)

    print("3/3 Ton / Untertitel …")
    out = a.out or a.video.parent / f"{re.sub(r'_\d+fps$', '', a.video.stem)}_final.mp4"
    audio = a.audio_from or (a.video if probe(a.video)[4] else None)  # z. B. LTX-2: eigenen Ton behalten
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", cur]
    if audio and probe(audio)[4]:
        cmd += ["-ss", str(a.audio_offset), "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
                "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest"]
    if a.srt:
        style = "FontName=Arial,FontSize=14,Outline=2,Shadow=0,MarginV=40"
        srt = str(a.srt.resolve()).replace("\\", "/").replace(":", r"\:")
        cmd += ["-vf", f"subtitles='{srt}':force_style='{style}'",
                "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "copy"]
    sh(cmd + [out])
    print(f"✓ FERTIG: {out}")


if __name__ == "__main__":
    main()
