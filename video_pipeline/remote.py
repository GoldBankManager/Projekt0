#!/usr/bin/env python3
"""
remote.py – Pipeline auf der vast.ai-Instanz fernsteuern (aus dem Chat oder vom eigenen PC).

Findet die laufende Instanz (Label "video-pipeline") über VAST_API_KEY. Override: PIPE_URL=http://ip:port

BEISPIELE:
  python remote.py wait                                  # warten bis Installation fertig ist
  python remote.py health
  python remote.py up auto_front.jpg auto_side.jpg clip.mp4     # → in/
  python remote.py fetch "https://www.tiktok.com/@x/video/123"  # Instanz lädt selbst (yt-dlp)
  python remote.py run ref2video swap --video in/clip.mp4 --ref in/auto_front.jpg --prompt "..."
  python remote.py run finish out/clip_swap_s1_16fps.mp4 --audio-from in/clip.mp4
  python remote.py ls out
  python remote.py get out/clip_swap_s1_final.mp4        # → ./downloads/
  python remote.py get-new                               # alle neuen *_final.mp4 holen
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from vast import LABEL, PORT, pipe_token, vast

DOWNLOADS = Path(__file__).resolve().parent / "downloads"
CACHE_FILE = Path(__file__).resolve().parent / ".pipe_url"  # zuletzt funktionierende Adresse


def base_url(instance_id=None):
    if os.getenv("PIPE_URL"):
        return os.environ["PIPE_URL"].rstrip("/")
    insts = [i for i in vast("show", "instances") if i.get("label") == LABEL or i.get("id") == instance_id]
    if instance_id:
        insts = [i for i in insts if i["id"] == instance_id]
    if not insts:
        sys.exit("Keine Pipeline-Instanz gefunden. Erst mieten:  python vast.py start")
    i = max(insts, key=lambda x: x.get("start_date") or 0)
    if i.get("actual_status") != "running":
        sys.exit(f"Instanz {i['id']} läuft noch nicht (Status: {i.get('actual_status')}). Gleich nochmal versuchen.")
    cache = CACHE_FILE.read_text().split() if CACHE_FILE.exists() else []
    if len(cache) == 2 and cache[0] == str(i["id"]) and reachable(cache[1]):
        return cache[1]
    port = (i.get("ports") or {}).get(f"{PORT}/tcp")
    candidates = [f"http://{i['public_ipaddr']}:{port[0]['HostPort']}"] if port and i.get("public_ipaddr") else []
    # Ausweg, falls der Chat-Proxy den direkten Port blockt: HTTPS-Tunnel aus dem Instanz-Log (tunnel.sh)
    try:
        logs = vast("logs", i["id"], "--tail", "400", raw=False)
    except SystemExit:
        logs = ""
    candidates += list(dict.fromkeys(reversed(re.findall(r"PIPE_TUNNEL=(https://[a-z0-9-]+\.trycloudflare\.com)", logs))))
    for url in candidates:
        if reachable(url):
            CACHE_FILE.write_text(f"{i['id']} {url}")
            return url
    sys.exit(f"Job-Server von Instanz {i['id']} (noch) nicht erreichbar – direkt: {candidates[:1] or 'kein Port'}, "
             f"Tunnel: {candidates[1:] or 'noch keiner im Log'}. In 1–2 min nochmal versuchen.")


def reachable(url):
    """Antwortet dort unser Server? (401 ohne Token zählt als erreichbar)"""
    try:
        urllib.request.urlopen(f"{url}/health", timeout=8)
        return True
    except urllib.error.HTTPError as e:
        return e.code == 401
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return False


class Pipe:
    def __init__(self, instance_id=None):
        self.url, self.token = base_url(instance_id), pipe_token()

    def call(self, method, path, data=None, raw=None, out=None, timeout=60):
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        req = urllib.request.Request(f"{self.url}/{path}", data=body, method=method,
                                     headers={"Authorization": f"Bearer {self.token}"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if out:
                    with open(out, "wb") as f:
                        while chunk := r.read(1 << 20):
                            f.write(chunk)
                    return out
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"{method} /{path}: HTTP {e.code} {e.read()[:300].decode(errors='replace')}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise ConnectionError(f"Server nicht erreichbar ({self.url}): {e}")

    def follow(self, job_id):
        """Log live mitlesen, bis der Job fertig ist."""
        seen = []
        while True:
            j = self.call("GET", f"jobs/{job_id}")
            new = j["log"][len(seen):] if j["log"][:len(seen)] == seen else j["log"][-5:]
            for line in new:
                print("   ", line)
            seen = j["log"]
            if j["status"] in ("done", "failed"):
                mins = (j.get("ended", 0) - j.get("started", j.get("ended", 0))) / 60
                print(f"{'✓' if j['status'] == 'done' else '✗'} Job {job_id} {j['status']} nach {mins:.1f} min")
                return j
            time.sleep(10)


def main():
    p = argparse.ArgumentParser(description="vast.ai-Pipeline fernsteuern")
    p.add_argument("--id", type=int, help="bestimmte Instanz-ID")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("wait")
    sub.add_parser("up").add_argument("files", nargs="+", type=Path)
    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("--name")
    r = sub.add_parser("run")
    r.add_argument("script", choices=["analyze", "ref2video", "generate", "studio", "finish"])
    r.add_argument("args", nargs=argparse.REMAINDER)
    r.add_argument("--no-wait", action="store_true")
    sub.add_parser("jobs")
    sub.add_parser("job").add_argument("job_id")
    sub.add_parser("ls").add_argument("dir", nargs="?", default="out", choices=["in", "out"])
    g = sub.add_parser("get")
    g.add_argument("paths", nargs="+")
    sub.add_parser("get-new", help="alle *_final.mp4 aus out/ holen, die lokal noch fehlen")
    a = p.parse_args()

    if a.cmd == "wait":
        print("Warte auf die Instanz … (Start + Installation dauern ca. 10–25 min)")
        deadline = time.time() + 50 * 60
        while time.time() < deadline:
            try:
                pipe = Pipe(a.id)
                h = pipe.call("GET", "health", timeout=15)
                if h["ready"]:
                    print(f"✓ Bereit über {pipe.url} – GPU: {h['gpu']}, frei: {h['disk_free_gb']} GB")
                    return
            except (SystemExit, ConnectionError):
                pass
            time.sleep(30)
        sys.exit("Nach 50 min nicht bereit – Log ansehen: python vast.py logs <ID>")

    pipe = Pipe(a.id)
    if a.cmd == "health":
        print(json.dumps(pipe.call("GET", "health"), indent=2, ensure_ascii=False))

    elif a.cmd == "up":
        for f in a.files:
            if not f.exists():
                sys.exit(f"Datei nicht gefunden: {f}")
            print(f"↑ {f.name} ({f.stat().st_size / 2**20:.1f} MB)")
            print("   ", pipe.call("PUT", f"files/in/{f.name}", raw=f.read_bytes(), timeout=600)["saved"])

    elif a.cmd == "fetch":
        print(pipe.call("POST", "fetch", {"url": a.url, "name": a.name}, timeout=900))

    elif a.cmd == "run":
        j = pipe.call("POST", "jobs", {"script": a.script, "args": a.args})
        print(f"Job {j['id']}: {a.script} {' '.join(a.args)}")
        if not a.no_wait:
            sys.exit(0 if pipe.follow(j["id"])["status"] == "done" else 1)

    elif a.cmd == "jobs":
        for j in pipe.call("GET", "jobs"):
            print(f"{j['id']}  {j['status']:<8} {j['script']} {' '.join(j['args'])[:80]}")

    elif a.cmd == "job":
        pipe.follow(a.job_id)

    elif a.cmd == "ls":
        for f in pipe.call("GET", f"files/{a.dir}/"):
            print(f"{f['mb']:>8.1f} MB  {f['name']}")

    elif a.cmd in ("get", "get-new"):
        DOWNLOADS.mkdir(exist_ok=True)
        paths = a.paths if a.cmd == "get" else [
            f["name"] for f in pipe.call("GET", "files/out/")
            if f["name"].endswith("_final.mp4") and not (DOWNLOADS / Path(f["name"]).name).exists()]
        if not paths:
            print("Nichts Neues.")
        for path in paths:
            dst = pipe.call("GET", f"files/{path}", out=DOWNLOADS / Path(path).name, timeout=1800)
            print(f"↓ {dst}")


if __name__ == "__main__":
    main()
