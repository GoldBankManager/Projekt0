#!/usr/bin/env python3
"""
server.py – kleiner Job-Server auf der GPU-Instanz, damit Claude (oder remote.py) die Pipeline fernsteuern kann.

Startet automatisch nach setup_vast.sh (siehe vast.py). Nur Python-Standardbibliothek.
Auth: Header "Authorization: Bearer $PIPE_TOKEN". Jobs laufen nacheinander (eine GPU).

  GET  /health                 Status, GPU, Warteschlange
  PUT  /files/in/<name>        Datei hochladen (Body = Dateiinhalt)
  POST /fetch                  {"url": ..., "name": optional}  Instanz lädt selbst herunter (yt-dlp oder direkt)
  GET  /files/<in|out>/        Dateien auflisten
  GET  /files/<pfad>           Datei herunterladen
  POST /jobs                   {"script": "ref2video", "args": [...]}  → {"id": ...}
  GET  /jobs  /jobs/<id>       Status + Log-Ende
"""
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIRS = {"in": ROOT / "in", "out": ROOT / "out"}
LOGS = ROOT / "jobs"
SCRIPTS = {"analyze", "ref2video", "generate", "studio", "finish"}
TOKEN = os.environ.get("PIPE_TOKEN", "")
READY = Path(os.environ.get("PIPE_READY_FILE", "/workspace/setup.log"))
ENV_FILE = Path("/workspace/pipeline.env")

jobs, q = {}, queue.Queue()


def worker():
    while True:
        job = q.get()
        job.update(status="running", started=time.time())
        env = {**os.environ, "HF_HOME": "/workspace/hf"}
        if ENV_FILE.exists():  # von setup_vast.sh: HF_HOME, CUDA-Bibliotheken für faster-whisper
            for line in ENV_FILE.read_text().splitlines():
                k, _, v = line.partition("=")
                if k and v:
                    env[k] = f"{v}:{env.get(k, '')}".rstrip(":") if k == "LD_LIBRARY_PATH" else v
        with open(LOGS / f"{job['id']}.log", "w") as log:
            p = subprocess.run([sys.executable, "-u", f"{job['script']}.py", *job["args"]],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        job.update(status="done" if p.returncode == 0 else "failed", code=p.returncode, ended=time.time())


def safe_path(rel):
    p = (ROOT / rel).resolve()
    if not any(p == d or d in p.parents for d in DIRS.values()):
        raise PermissionError(rel)
    return p


def gpu():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
                               "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        return None


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body=None, raw=None, ctype="application/json"):
        data = raw if raw is not None else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        if TOKEN and self.headers.get("Authorization") == f"Bearer {TOKEN}":
            return True
        self.send(401, {"error": "unauthorized"})
        return False

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def job_view(self, j, tail=40):
        log = LOGS / f"{j['id']}.log"
        lines = log.read_text(errors="replace").replace("\r", "\n").splitlines() if log.exists() else []
        return {**j, "log": [l for l in lines if l.strip()][-tail:]}

    def do_GET(self):
        if not self.authed():
            return
        path = self.path.split("?")[0].strip("/")
        if path == "health":
            ready = READY.exists() and "PIPELINE_READY" in READY.read_text(errors="replace")
            busy = [j["id"] for j in jobs.values() if j["status"] in ("queued", "running")]
            return self.send(200, {"ready": ready, "gpu": gpu(), "busy": busy,
                                   "disk_free_gb": round(shutil.disk_usage(ROOT).free / 2**30)})
        if path == "jobs":
            return self.send(200, [self.job_view(j, tail=3) for j in jobs.values()])
        if path.startswith("jobs/"):
            j = jobs.get(path[5:])
            return self.send(200, self.job_view(j)) if j else self.send(404, {"error": "unknown job"})
        if path.startswith("files/"):
            try:
                p = safe_path(path[6:])
            except PermissionError:
                return self.send(403, {"error": "forbidden"})
            if p.is_dir():
                return self.send(200, [{"name": str(f.relative_to(ROOT)), "mb": round(f.stat().st_size / 2**20, 1)}
                                       for f in sorted(p.rglob("*")) if f.is_file() and "_work" not in f.parts])
            if p.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(p.stat().st_size))
                self.end_headers()
                with open(p, "rb") as f:
                    shutil.copyfileobj(f, self.wfile, 1 << 20)
                return
        self.send(404, {"error": "not found"})

    def do_PUT(self):
        if not self.authed():
            return
        path = self.path.strip("/")
        try:
            p = safe_path(path[6:]) if path.startswith("files/in/") else None
        except PermissionError:
            p = None
        if not p:
            return self.send(403, {"error": "nur nach files/in/ hochladen"})
        p.parent.mkdir(parents=True, exist_ok=True)
        left = int(self.headers.get("Content-Length", 0))
        with open(p, "wb") as f:
            while left > 0:
                chunk = self.rfile.read(min(left, 1 << 20))
                if not chunk:
                    break
                f.write(chunk)
                left -= len(chunk)
        self.send(200, {"saved": str(p.relative_to(ROOT))})

    def do_POST(self):
        if not self.authed():
            return
        path = self.path.strip("/")
        try:
            req = json.loads(self.body() or b"{}")
        except json.JSONDecodeError:
            return self.send(400, {"error": "kein JSON"})
        if path == "jobs":
            if req.get("script") not in SCRIPTS or not isinstance(req.get("args", []), list):
                return self.send(400, {"error": f"script muss eines von {sorted(SCRIPTS)} sein"})
            j = {"id": uuid.uuid4().hex[:8], "script": req["script"], "args": [str(a) for a in req.get("args", [])],
                 "status": "queued", "created": time.time()}
            jobs[j["id"]] = j
            q.put(j)
            return self.send(200, j)
        if path == "fetch":
            return self.send(200, fetch(req.get("url", ""), req.get("name")))
        self.send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        pass


def fetch(url, name=None):
    """Datei oder Social-Media-Video (TikTok, Reels, YouTube …) direkt auf die Instanz laden."""
    if not url.startswith(("http://", "https://")):
        return {"error": "ungültige URL"}
    DIRS["in"].mkdir(exist_ok=True)
    if Path(url.split("?")[0]).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"):
        dst = DIRS["in"] / (name or Path(url.split("?")[0]).name)
        urllib.request.urlretrieve(url, dst)
        return {"saved": str(dst.relative_to(ROOT))}
    tmpl = str(DIRS["in"] / (f"{Path(name).stem}.%(ext)s" if name else "%(title).60s_%(id)s.%(ext)s"))
    p = subprocess.run([sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
                        "--restrict-filenames", "-o", tmpl, "--print", "after_move:filepath", url],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return {"error": p.stderr[-800:]}
    return {"saved": str(Path(p.stdout.strip().splitlines()[-1]).relative_to(ROOT))}


def main():
    if not TOKEN:
        sys.exit("PIPE_TOKEN fehlt")
    for d in (*DIRS.values(), LOGS):
        d.mkdir(exist_ok=True)
    threading.Thread(target=worker, daemon=True).start()
    port = int(os.environ.get("PIPE_PORT", 8000))
    print(f"Job-Server läuft auf Port {port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
