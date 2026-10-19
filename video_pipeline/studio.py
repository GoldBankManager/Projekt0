#!/usr/bin/env python3
"""
studio.py – Wan2GP (deepbeepmeep/Wan2GP) als „Studio“ auf der GPU-Instanz: über 100 Video-Modelle mit wenig VRAM

Was es zusätzlich zur Pipeline kann (Modellname für --model):
  phantom_14B           Personen/Objekte aus Referenzbildern ins Video (Reference-to-Video)
  ltx2_25_22B_msr       LTX-2.5 mit 1–4 Referenz-Subjekten, Video MIT TON
  vace_standin_14B, lynx    Gesicht/Person konsistent halten (Referenz = Gesicht-Nahaufnahme)
  animate2              Charakterbild mit Bewegung/Mimik/Kamera aus einem Vorlage-Video animieren
  uni3c                 präzise Kamerafahrt um ein Startbild
  sky_df_14B            SkyReels-2: sehr lange Videos (> 5 s)
  hunyuan_custom        Person mit Identität ins Video übertragen
  infinitetalk          sprechender Avatar aus Bild + Audio
  … alle: python studio.py models

BEFEHLE (auf der Instanz bzw. über: python remote.py run studio …):
  python studio.py install                      # einmalig, ~5–10 min (eigene venv, stört die Pipeline nicht)
  python studio.py models [suchwort]
  python studio.py run --model phantom_14B --ref in/auto.jpg --prompt "..." [--seed 1 --frames 81]
  python studio.py run in/meine_settings.json [--prompt "..." --seed 5]    # exportierte UI-Einstellungen
  python studio.py ui                           # Web-Oberfläche auf localhost:7860 (per SSH-Tunnel öffnen)

Tipp: Für feine Einstellungen einmal in der UI bauen → „Export Settings“ → als JSON nach in/ hochladen →
mit `run` beliebig oft mit anderem Prompt/Seed wiederholen.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WGP = Path("/workspace/Wan2GP")
VENV = Path("/workspace/wan2gp-env")
PY = VENV / "bin" / "python"
OUT = ROOT / "out" / "studio"


def run(cmd, **kw):
    print("$", " ".join(map(str, cmd)))
    r = subprocess.run([str(c) for c in cmd], **kw)
    if r.returncode != 0:
        sys.exit(r.returncode)


def need_install():
    if not (PY.exists() and (WGP / "wgp.py").exists()):
        sys.exit("Studio ist noch nicht installiert:  python studio.py install")


def install():
    if not (WGP / ".git").exists():
        run(["git", "clone", "--depth", "1", "https://github.com/deepbeepmeep/Wan2GP", WGP])
    else:
        run(["git", "-C", WGP, "pull", "--ff-only"])
    if not PY.exists():
        run([sys.executable, "-m", "venv", VENV])
    pip = [PY, "-m", "pip", "install", "-q"]
    # Wan2GP empfiehlt torch 2.10; cu128 läuft auf mehr vast-Maschinen als cu130
    if subprocess.run([*pip, "torch==2.10.0", "torchvision==0.25.0", "torchaudio==2.10.0",
                       "--index-url", "https://download.pytorch.org/whl/cu128"]).returncode != 0:
        run([*pip, "torch==2.10.0", "torchvision==0.25.0", "torchaudio==2.10.0",
             "--index-url", "https://download.pytorch.org/whl/cu130"])
    run([*pip, "-r", WGP / "requirements.txt"], cwd=WGP)
    print("✓ Studio installiert. Modelle werden beim ersten Benutzen automatisch geladen.")


def models(term=""):
    need_install()
    for f in sorted((WGP / "defaults").glob("*.json")):
        try:
            m = json.loads(f.read_text())["model"]
        except (KeyError, json.JSONDecodeError):
            continue
        line = f"{f.stem:<34} {m.get('name', '')}"
        if term.lower() in (line + m.get("description", "")).lower():
            print(line)


def factory_settings(model):
    """Die Standard-Einstellungen, die die Wan2GP-UI für dieses Modell vorbelegen würde (ohne die UI zu starten)."""
    out = OUT / f"_defaults_{model}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    code = ("import json, os, sys; sys.argv = ['wgp.py']; import wgp; "
            "json.dump(wgp.get_default_settings(os.environ['STUDIO_MODEL']), open(os.environ['STUDIO_OUT'], 'w'))")
    r = subprocess.run([str(PY), "-c", code], cwd=WGP, capture_output=True, text=True,
                       env={**os.environ, "STUDIO_MODEL": model, "STUDIO_OUT": str(out)})
    if r.returncode != 0 or not out.exists():
        sys.exit(f"Standard-Einstellungen für {model} nicht ladbar (Modellname? → studio.py models):\n{r.stderr[-1500:]}")
    return {**json.loads(out.read_text()), "model_type": model}


def abs_media(path):
    p = Path(path)
    return str(p if p.is_absolute() else (ROOT / p).resolve())


def run_job(a):
    need_install()
    if a.settings:
        settings = json.loads(Path(a.settings).read_text())
        tasks = settings if isinstance(settings, list) else [settings]
    else:
        if not a.model or not a.prompt:
            sys.exit("Entweder eine Settings-JSON angeben oder --model und --prompt.")
        tasks = [factory_settings(a.model)]
    for t in tasks:  # Overrides aus der Kommandozeile
        params = t.get("params", t)
        for key, val in (("model_type", a.model), ("prompt", a.prompt), ("seed", a.seed),
                         ("video_length", a.frames), ("num_inference_steps", a.steps), ("resolution", a.resolution)):
            if val is not None:
                params[key] = val
        if a.ref:
            params["image_refs"] = [abs_media(r) for r in a.ref]
        if a.image:
            params["image_start"] = abs_media(a.image)
        if a.video:
            params["video_guide"] = abs_media(a.video)
        if a.audio:
            params["audio_guide"] = abs_media(a.audio)
    OUT.mkdir(parents=True, exist_ok=True)
    job = OUT / "_last_settings.json"
    job.write_text(json.dumps(tasks if len(tasks) > 1 else tasks[0], indent=2, ensure_ascii=False))
    cmd = [PY, "wgp.py", "--process", job, "--output-dir", OUT, "--verbose", "1"]
    run(cmd + (["--dry-run"] if a.dry_run else []), cwd=WGP)
    if not a.dry_run:
        new = sorted(OUT.glob("*.mp4"), key=lambda f: f.stat().st_mtime)[-len(tasks):]
        for f in new:
            print(f"    ✓ {f.relative_to(ROOT)}  →  weiter mit: python finish.py {f.relative_to(ROOT)}")


def ui():
    need_install()
    log = Path("/workspace/studio_ui.log")
    subprocess.Popen([str(PY), "wgp.py", "--server-port", "7860"], cwd=WGP,
                     stdout=open(log, "w"), stderr=subprocess.STDOUT, start_new_session=True)
    print("Studio-UI startet auf localhost:7860 (Log: /workspace/studio_ui.log).")
    print("Öffnen per SSH-Tunnel vom eigenen PC:  ssh -p <PORT> root@<IP> -L 7860:localhost:7860")
    print("→ dann im Browser http://localhost:7860   (SSH-Befehl: python vast.py status)")


def main():
    p = argparse.ArgumentParser(description="Wan2GP-Studio auf der GPU-Instanz")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("install")
    sub.add_parser("models").add_argument("term", nargs="?", default="")
    sub.add_parser("ui")
    r = sub.add_parser("run")
    r.add_argument("settings", nargs="?", type=Path, help="Settings-JSON (aus „Export Settings“)")
    r.add_argument("--model", help="Modell, z. B. phantom_14B (siehe: studio.py models)")
    r.add_argument("--prompt")
    r.add_argument("--ref", nargs="+", help="Referenzbilder (Personen/Objekte)")
    r.add_argument("--image", help="Startbild")
    r.add_argument("--video", help="Steuer-/Vorlage-Video (z. B. für animate2)")
    r.add_argument("--audio", help="Audio (z. B. für infinitetalk)")
    r.add_argument("--seed", type=int)
    r.add_argument("--frames", type=int, help="Anzahl Frames (video_length)")
    r.add_argument("--steps", type=int)
    r.add_argument("--resolution", help="z. B. 1280x720 oder 832x480")
    r.add_argument("--dry-run", action="store_true", help="nur prüfen, nichts erzeugen")
    a = p.parse_args()

    if a.cmd == "install":
        install()
    elif a.cmd == "models":
        models(a.term)
    elif a.cmd == "ui":
        ui()
    else:
        run_job(a)


if __name__ == "__main__":
    main()
