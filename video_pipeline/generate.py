#!/usr/bin/env python3
"""
generate.py – Text→Video und Bild→Video mit den neuesten offenen Modellen (über diffusers)

MODELLE:
  ltx2    LTX-2 (Lightricks): Video MIT TON in einem Durchgang, 24 fps, bis ~10 s. Braucht 48 GB+ (oder --offload)
  wan22   Wan2.2 TI2V-5B: sehr gute Bewegung, 720p, 24 fps, läuft auf RTX 4090 (24 GB)
          --big → Wan2.2 A14B (T2V bzw. I2V, MoE): beste Qualität, 16 fps, 48–80 GB

BEISPIELE:
  python generate.py ltx2 --prompt "A red Ferrari revs its engine in a tunnel, loud V12 roar echoing, slow dolly-in"
  python generate.py ltx2 --image in/car.jpg --prompt "The car drives off, tires screeching" --enhance
  python generate.py wan22 --prompt "Drone shot over a coastal road at sunset, a black SUV speeding" --aspect 9:16
  python generate.py wan22 --image in/car.jpg --prompt "Slow orbit around the car, rain drops" --big --takes 3
"""
import argparse
import random
import sys
from pathlib import Path

from PIL import Image

from common import fit_size, write_video

MODELS = {
    "ltx2": {"id": "Lightricks/LTX-2", "fps": 24, "base": 32, "frame_step": 8},
    "wan22": {"id": "Wan-AI/Wan2.2-TI2V-5B-Diffusers", "fps": 24, "base": 32, "frame_step": 4},
    "wan22-big-t2v": {"id": "Wan-AI/Wan2.2-T2V-A14B-Diffusers", "fps": 16, "base": 16, "frame_step": 4},
    "wan22-big-i2v": {"id": "Wan-AI/Wan2.2-I2V-A14B-Diffusers", "fps": 16, "base": 16, "frame_step": 4},
}
RES = {"480p": 832 * 480, "720p": 1280 * 720}
NEGATIVE = ("worst quality, low quality, blurry, jittery, inconsistent motion, distorted, deformed, morphing, "
            "flickering, watermark, subtitles, text artifacts, distorted logos, static, overexposed")


def model_key(a):
    if a.model == "wan22" and a.big:
        return "wan22-big-i2v" if a.image else "wan22-big-t2v"
    return a.model


def load_pipe(key, image, offload):
    import torch
    mid = MODELS[key]["id"]
    print(f"Lade {mid} … (beim ersten Mal wird das Modell heruntergeladen)")
    if key == "ltx2":
        from diffusers import LTX2ImageToVideoPipeline, LTX2Pipeline
        pipe = (LTX2ImageToVideoPipeline if image else LTX2Pipeline).from_pretrained(mid, torch_dtype=torch.bfloat16)
    else:
        from diffusers import AutoencoderKLWan, WanImageToVideoPipeline, WanPipeline
        vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
        pipe = (WanImageToVideoPipeline if image else WanPipeline).from_pretrained(
            mid, vae=vae, torch_dtype=torch.bfloat16)
    if offload == "model":
        pipe.enable_model_cpu_offload()
    elif offload == "seq":
        pipe.enable_sequential_cpu_offload()
    else:
        pipe.to("cuda")
    return pipe


def size_for(a, cfg, image):
    """Auflösung aus Bild-Seitenverhältnis (falls Bild) oder --aspect, passend zum Modell gerundet."""
    if image is not None:
        w, h = image.size
    else:
        w, h = (int(x) * 1000 for x in a.aspect.split(":"))
    return fit_size(w, h, RES[a.res], base=cfg["base"])


def main():
    p = argparse.ArgumentParser(description="Text/Bild → Video mit LTX-2 (mit Ton) oder Wan2.2")
    p.add_argument("model", choices=["ltx2", "wan22"])
    p.add_argument("--prompt", required=True, help="Englisch: Subjekt, Aktion, Umgebung, Licht, Kamera, (Ton bei ltx2)")
    p.add_argument("--image", type=Path, help="Startbild → Bild-zu-Video")
    p.add_argument("--negative", default=NEGATIVE)
    p.add_argument("--big", action="store_true", help="wan22: A14B statt 5B (48–80 GB VRAM)")
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--aspect", default="16:9", help="ohne --image: 16:9, 9:16, 1:1 …")
    p.add_argument("--res", default="720p", choices=list(RES))
    p.add_argument("--enhance", action="store_true", help="ltx2: Prompt automatisch ausbauen lassen")
    p.add_argument("--steps", type=int, default=None, help="Standard: 30 (ltx2) / 40 (wan22)")
    p.add_argument("--cfg", type=float, default=None, help="Standard: 3.0 (ltx2) / 5.0 (wan22)")
    p.add_argument("--offload", default=None, choices=["none", "model", "seq"],
                   help="Standard: model bei ltx2 und --big, sonst none")
    p.add_argument("--takes", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out", type=Path, default=Path("out"))
    a = p.parse_args()

    import torch
    key = model_key(a)
    cfg = MODELS[key]
    if a.image and not a.image.exists():
        sys.exit(f"Datei nicht gefunden: {a.image}")
    image = Image.open(a.image).convert("RGB") if a.image else None
    width, height = size_for(a, cfg, image)
    step = cfg["frame_step"]
    n = int(a.seconds * cfg["fps"]) // step * step + 1
    offload = a.offload or ("model" if key == "ltx2" or a.big else "none")
    steps = a.steps or (30 if key == "ltx2" else 40)
    guidance = a.cfg or (3.0 if key == "ltx2" else 5.0)
    a.out.mkdir(exist_ok=True)
    print(f"{key}: {width}x{height}, {n} Frames @ {cfg['fps']} fps ({n / cfg['fps']:.1f} s), {steps} Schritte")

    pipe = load_pipe(key, image, offload)
    base_seed = a.seed if a.seed is not None else random.randint(0, 2**31 - 1)
    stem = a.image.stem if a.image else "t2v"
    for t in range(a.takes):
        seed = base_seed + t
        print(f"\n=== Take {t + 1}/{a.takes} (seed {seed}) ===")
        kw = dict(prompt=a.prompt, negative_prompt=a.negative, width=width, height=height, num_frames=n,
                  num_inference_steps=steps, guidance_scale=guidance,
                  generator=torch.Generator().manual_seed(seed))
        if image is not None:
            kw["image"] = image.resize((width, height), Image.LANCZOS)
        path = a.out / f"{stem}_{key}_s{seed}_{cfg['fps']}fps.mp4"
        if key == "ltx2":
            from diffusers.utils import encode_video
            video, audio = pipe(**kw, frame_rate=cfg["fps"], enable_prompt_enhancement=a.enhance,
                                output_type="np", return_dict=False)
            encode_video(video[0], fps=cfg["fps"], audio=audio[0].float().cpu(),
                         audio_sample_rate=pipe.vocoder.config.output_sampling_rate, output_path=str(path))
        else:
            write_video(pipe(**kw, output_type="np").frames[0], path, cfg["fps"])
        print(f"    ✓ {path}  →  weiter mit: python finish.py {path}")


if __name__ == "__main__":
    main()
