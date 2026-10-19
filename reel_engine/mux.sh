#!/usr/bin/env bash
# Legt die SFX-Spur unter das gerenderte Video und erzeugt die Lieferdateien in <reel>/final/.
#   reel_engine/mux.sh reels/havvambau_01 [musik.mp3]
set -euo pipefail
REEL="$1"; MUSIC="${2:-}"
NAME="$(basename "$REEL")"
mkdir -p "$REEL/final"
ffmpeg -y -v error -i "$REEL/out/video_only.mp4" -i "$REEL/out/sfx.wav" -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$REEL/final/${NAME}_mit_sfx.mp4"
echo "✓ $REEL/final/${NAME}_mit_sfx.mp4"
if [ -n "$MUSIC" ]; then
  ffmpeg -y -v error -i "$REEL/out/video_only.mp4" -i "$REEL/out/sfx.wav" -i "$MUSIC" \
    -filter_complex "[2:a]aresample=48000,volume=0.8[m];[1:a][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$REEL/final/${NAME}_vorschau_mit_musik.mp4"
  echo "✓ $REEL/final/${NAME}_vorschau_mit_musik.mp4"
fi
