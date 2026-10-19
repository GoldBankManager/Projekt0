#!/usr/bin/env python3
"""
vast.py – GPU auf vast.ai mieten, Pipeline automatisch installieren, Status/Logs ansehen, Instanz zerstören

SETUP (einmalig):
  pip install vastai
  API-Key setzen   (Mac/Linux: export VAST_API_KEY="dein_key" | Windows: set VAST_API_KEY=dein_key)

BEISPIELE:
  python vast.py offers                          # günstigste RTX 4090 anzeigen
  python vast.py offers --gpu "RTX 5090"
  python vast.py start                           # günstigste zuverlässige 4090 mieten + alles installieren
  python vast.py start --gpu "A100 SXM4" --model 14b
  python vast.py status                          # laufende Instanzen, Kosten, Jupyter-Link
  python vast.py logs 1234567                    # Fortschritt der Installation
  python vast.py stop 1234567                    # Instanz ZERSTÖREN (stoppt alle Kosten)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

REPO_TAR = "https://github.com/GoldBankManager/Projekt0/archive/refs/heads/video-pipeline.tar.gz"
IMAGE = "pytorch/pytorch:2.7.1-cuda12.8-cudnn9-devel"
VRAM = {"1.3b": 24, "14b": 48}  # GB, die das Modell mindestens braucht


def vast(*args, raw=True):
    if not shutil.which("vastai"):
        sys.exit("vastai-CLI fehlt:  pip install vastai")
    if not os.getenv("VAST_API_KEY"):
        sys.exit("VAST_API_KEY ist nicht gesetzt.")
    r = subprocess.run(["vastai", *map(str, args), *(["--raw"] if raw else [])], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"vastai {' '.join(map(str, args))} fehlgeschlagen:\n{r.stderr or r.stdout}")
    return json.loads(r.stdout) if raw else r.stdout


def onstart(model):
    """Läuft beim Start auf der Instanz: Repo holen, setup_vast.sh ausführen, Ergebnis in /workspace/setup.log."""
    fetch = ("import urllib.request,tarfile,io;"
             f"tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen('{REPO_TAR}').read())).extractall('.')")
    return (f'mkdir -p /workspace && cd /workspace && python -c "{fetch}" '
            f"&& cd Projekt0-video-pipeline/video_pipeline "
            f"&& {{ bash setup_vast.sh {'1.3b' if model == '1.3b' else ''} "
            f"&& echo PIPELINE_READY || echo PIPELINE_FAILED; }} 2>&1 | tee /workspace/setup.log")


def find_offers(gpu, vram, max_price, disk, limit=10):
    query = (f"gpu_name={gpu.replace(' ', '_')} num_gpus=1 gpu_ram>={vram} disk_space>={disk} "
             f"reliability>0.98 inet_down>=300 cuda_vers>=12.8 dph<={max_price}")
    return vast("search", "offers", query, "-o", "dph_total", "--storage", disk, "--limit", limit)


def show_offers(offers):
    print(f"{'ID':>10}  {'GPU':<14} {'VRAM':>5} {'$/h':>6} {'Down':>7}  {'Zuverl.':>7}  Ort")
    for o in offers:
        print(f"{o['id']:>10}  {o['gpu_name']:<14} {o['gpu_ram'] / 1000:>4.0f}G {o['dph_total']:>6.3f} "
              f"{o.get('inet_down', 0):>5.0f}Mb  {o.get('reliability2', o.get('reliability', 0)):>7.3f}  "
              f"{o.get('geolocation', '?')}")


def jupyter_url(inst):
    port = (inst.get("ports") or {}).get("8080/tcp")
    if inst.get("public_ipaddr") and port and inst.get("jupyter_token"):
        return f"https://{inst['public_ipaddr']}:{port[0]['HostPort']}/?token={inst['jupyter_token']}"
    return "noch nicht bereit (oder in der Konsole: https://cloud.vast.ai/instances/)"


def main():
    p = argparse.ArgumentParser(description="vast.ai-GPU für die Video-Pipeline mieten und verwalten")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("offers", "start"):
        s = sub.add_parser(name)
        s.add_argument("--gpu", default="RTX 4090")
        s.add_argument("--model", default="1.3b", choices=list(VRAM), help="1.3b = Test/4090, 14b = beste Qualität")
        s.add_argument("--max-price", type=float, default=0.6, help="max. $/h")
        s.add_argument("--disk", type=int, default=150, help="GB Speicher")
    sub.choices["start"].add_argument("--offer", type=int, help="bestimmtes Angebot (ID aus 'offers')")
    sub.choices["start"].add_argument("-y", "--yes", action="store_true", help="ohne Rückfrage mieten")
    sub.add_parser("status")
    sub.add_parser("balance")
    for name in ("logs", "stop"):
        sub.add_parser(name).add_argument("id", type=int)
    sub.choices["stop"].add_argument("-y", "--yes", action="store_true")
    a = p.parse_args()

    if a.cmd == "balance":
        u = vast("show", "user")
        print(f"Guthaben: ${u.get('credit', 0):.2f}")

    elif a.cmd == "offers":
        show_offers(find_offers(a.gpu, VRAM[a.model], a.max_price, a.disk))

    elif a.cmd == "start":
        if a.offer:
            offer_id, price = a.offer, None
        else:
            offers = find_offers(a.gpu, VRAM[a.model], a.max_price, a.disk, limit=5)
            if not offers:
                sys.exit(f"Kein {a.gpu}-Angebot unter ${a.max_price}/h – --max-price erhöhen oder andere --gpu.")
            show_offers(offers)
            offer_id, price = offers[0]["id"], offers[0]["dph_total"]
        credit = vast("show", "user").get("credit", 0)
        print(f"\nMiete Angebot {offer_id}" + (f" für ${price:.3f}/h (≈ {credit / price:.0f} h mit ${credit:.2f})"
                                                  if price else "") + f", Modell {a.model}, {a.disk} GB Disk.")
        if not a.yes and input("Mieten? (j/n) ").strip().lower() not in ("j", "y", "ja", "yes"):
            return
        res = vast("create", "instance", offer_id, "--image", IMAGE, "--disk", a.disk,
                   "--ssh", "--jupyter", "--direct", "--onstart-cmd", onstart(a.model))
        iid = res.get("new_contract")
        print(f"✓ Instanz {iid} startet. Installation dauert ca. 15–25 min.")
        print(f"  Fortschritt:  python vast.py logs {iid}   (fertig bei 'PIPELINE_READY')")
        print(f"  Zerstören:    python vast.py stop {iid}")

    elif a.cmd == "status":
        insts = vast("show", "instances")
        if not insts:
            print("Keine Instanzen – es fallen keine Kosten an.")
        for i in insts:
            print(f"{i['id']}  {i.get('actual_status')}  {i.get('gpu_name')}  ${i.get('dph_total', 0):.3f}/h  "
                  f"Disk {i.get('disk_space', 0):.0f} GB")
            if i.get("ssh_host"):
                print(f"   SSH:     ssh -p {i['ssh_port']} root@{i['ssh_host']}")
            print(f"   Jupyter: {jupyter_url(i)}")

    elif a.cmd == "logs":
        print(vast("logs", a.id, "--tail", 60, raw=False))

    elif a.cmd == "stop":
        if not a.yes and input(f"Instanz {a.id} ZERSTÖREN? Alle Dateien darauf sind dann weg. (j/n) ").strip().lower() \
                not in ("j", "y", "ja", "yes"):
            return
        vast("destroy", "instance", a.id, "-y")
        print(f"✓ Instanz {a.id} zerstört – keine Kosten mehr.")


if __name__ == "__main__":
    main()
