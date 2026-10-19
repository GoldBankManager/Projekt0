#!/usr/bin/env python3
"""
finish.py – Nachbearbeitung & Rendern: flüssiger (FPS hoch), schärfer (Upscale bis 4K), Ton + Untertitel drauf

  FPS        ffmpeg minterpolate  (16 fps von Wan → 30/60 fps)
  Upscale    Real-ESRGAN über spandrel (x4 auf der GPU, danach exakt auf Zielhöhe skaliert)
  Ton        Originalton aus dem Quellclip wieder drunterlegen (wie in car_swap.py)
  Untertitel .srt aus analyze.py einbrennen

BEISPIELE:
  python finish.py out/edit_swap_s123_16fps.mp4 --audio-from edit.mp4            # 30 fps, 4K, Originalton
  python finish.py out/clip.mp4 --height 1080 --fps 60
  python finish.py out/clip.mp4 --srt out/edit.srt --upscale none
"""
import argparse
import urllib.request
from pathlib import Path

from common import probe, read_frames, sh, write_video

WEIGHTS = {  # Real-ESRGAN-Gewichte (BSD-3), werden beim ersten Mal geladen
    "x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "general": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
}
CACHE = Path.home() / ".cache" / "video_pipeline"


def interpolate(src, dst, fps):
    """Bewegungskompensierte Zwischenbilder (CPU). Läuft auf der kleinen Auflösung, also vor dem Upscale."""
    sh(["ffmpeg", "-y", "-v", "error", "-i", src,
        "-vf", f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
        "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", dst])
    return dst


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


def upscale(src, dst, height, name):
    w, h, _, fps, _ = probe(src)
    width = round(w * height / h / 2) * 2
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
    p.add_argument("--height", type=int, default=2160, help="Zielhöhe: 1080, 1440, 2160 (4K)")
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
    _, h, _, fps, _ = probe(cur)

    if a.fps and abs(a.fps - fps) > 0.01:
        print(f"1/3 FPS {fps:g} → {a.fps:g} …")
        cur = interpolate(cur, work / f"{a.video.stem}_{a.fps:g}fps.mp4", a.fps)

    if a.height and a.height != h:
        print(f"2/3 Upscale auf {a.height}p …")
        dst = work / f"{a.video.stem}_{a.height}p.mp4"
        if a.upscale == "none" or a.height <= h:
            sh(["ffmpeg", "-y", "-v", "error", "-i", cur, "-vf", f"scale=-2:{a.height}:flags=lanczos",
                "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", dst])
            cur = dst
        else:
            cur = upscale(cur, dst, a.height, a.upscale)

    print("3/3 Ton / Untertitel …")
    out = a.out or a.video.parent / f"{a.video.stem.removesuffix('_16fps')}_final.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", cur]
    if a.audio_from and probe(a.audio_from)[4]:
        cmd += ["-ss", str(a.audio_offset), "-i", a.audio_from, "-map", "0:v:0", "-map", "1:a:0",
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
