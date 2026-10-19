#!/usr/bin/env bash
# Einmal auf der gemieteten vast.ai-Maschine ausführen (Template: "PyTorch" mit CUDA 12.x):
#   git clone https://github.com/GoldBankManager/Projekt0 && cd Projekt0/video_pipeline && bash setup_vast.sh
# Optional: bash setup_vast.sh 1.3b   → lädt nur das kleine Modell (RTX 4090 / 24 GB)
set -euo pipefail
cd "$(dirname "$0")"

MODEL="Wan-AI/Wan2.1-VACE-14B-diffusers"
[[ "${1:-}" == "1.3b" ]] && MODEL="Wan-AI/Wan2.1-VACE-1.3B-diffusers"

# Modelle auf /workspace speichern (bleibt erhalten, solange die Instanz nicht zerstört wird)
export HF_HOME="${HF_HOME:-/workspace/hf}"
mkdir -p "$HF_HOME"

echo "== System-Pakete =="
SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq ffmpeg git libgl1 libglib2.0-0 > /dev/null

echo "== Python-Pakete =="
python -c "import torch; assert torch.cuda.is_available(), 'Keine GPU gefunden'; print('GPU:', torch.cuda.get_device_name(0), round(torch.cuda.get_device_properties(0).total_memory / 2**30), 'GB')"
pip install -q -r requirements.txt

# faster-whisper (CTranslate2) findet die CUDA-Bibliotheken aus den pip-Paketen sonst nicht
LIBS=$(python - <<'EOF' || true
import importlib
paths = []
for m in ("nvidia.cublas.lib", "nvidia.cudnn.lib"):
    try:
        paths.append(list(importlib.import_module(m).__path__)[0])
    except Exception:
        pass
print(":".join(paths))
EOF
)
if [[ -n "$LIBS" ]] && ! grep -q "video_pipeline" ~/.bashrc; then
    echo "export LD_LIBRARY_PATH=$LIBS:\${LD_LIBRARY_PATH:-}  # video_pipeline" >> ~/.bashrc
    echo "export HF_HOME=$HF_HOME  # video_pipeline" >> ~/.bashrc
fi

echo "== Modelle vorladen (spart später bezahlte Wartezeit) =="
python - "$MODEL" <<'EOF'
import sys
from huggingface_hub import snapshot_download
for repo in (sys.argv[1], "Qwen/Qwen2.5-VL-7B-Instruct", "Systran/faster-whisper-large-v3"):
    print("  ", repo)
    snapshot_download(repo)
from ultralytics import YOLO
YOLO("yolo11x-seg.pt")
EOF

echo
echo "✓ Fertig. Neues Terminal öffnen (oder: source ~/.bashrc), dann z. B.:"
echo "  python analyze.py clip.mp4"
echo "  python ref2video.py swap --video clip.mp4 --ref auto.jpg --prompt \"...\""
echo "  python finish.py out/clip_swap_s123_16fps.mp4 --audio-from clip.mp4"
