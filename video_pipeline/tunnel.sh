#!/usr/bin/env bash
# HTTPS-Tunnel (Cloudflare Quick Tunnel, kein Konto nötig) zum Job-Server – Ausweg, falls der direkte
# Port aus dem Chat nicht erreichbar ist. Die URL steht danach in /workspace/tunnel_url und im Instanz-Log
# (Zeile "PIPE_TUNNEL=…"), wo remote.py sie über die vast-API findet. Zugriff bleibt per Token geschützt.
set -u
BIN=/workspace/cloudflared
LOG=/workspace/tunnel.log
PORT="${PIPE_PORT:-8000}"

[[ -x "$BIN" ]] || python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64', '$BIN')" && chmod +x "$BIN"

for attempt in 1 2 3; do
    : > "$LOG"
    "$BIN" tunnel --no-autoupdate --url "http://localhost:$PORT" > "$LOG" 2>&1 &
    for _ in $(seq 60); do
        URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | head -1)
        if [[ -n "$URL" ]]; then
            echo "$URL" > /workspace/tunnel_url
            echo "PIPE_TUNNEL=$URL"
            wait
            break
        fi
        sleep 2
    done
    echo "Tunnel-Versuch $attempt fehlgeschlagen, neuer Versuch …"
    kill %1 2>/dev/null
    sleep 5
done
