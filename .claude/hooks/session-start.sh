#!/bin/bash
# Cloud-Sitzungen: vast.ai-CLI installieren, damit video_pipeline/vast.py und remote.py sofort laufen.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if ! command -v vastai >/dev/null 2>&1; then
  pip install -q --disable-pip-version-check vastai
fi

if [ -z "${VAST_API_KEY:-}" ]; then
  echo "Hinweis: VAST_API_KEY ist nicht gesetzt – vast.py/remote.py brauchen ihn (Umgebungs-Einstellungen → Umgebungsvariable)."
fi
