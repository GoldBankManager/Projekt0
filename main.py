#!/usr/bin/env python3
"""
main.py – Beispiel: Seedance 2.5 Text-to-Video über die Higgsfield-API (offizielles SDK higgsfield-client)

SETUP (einmalig):
  pip install -r requirements.txt
  Zugangsdaten als HF_KEY="key-id:key-secret" in .env.local (wird nicht committet)
  oder als Umgebungsvariable HF_KEY setzen. Werte niemals ausgeben oder committen.

ACHTUNG: Jeder Aufruf ist eine kostenpflichtige Generierung bei Higgsfield (siehe Geld-Regel in CLAUDE.md).
"""
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

import higgsfield_client
from higgsfield_client import NSFW, Cancelled, Completed, CredentialsMissedError, Failed, HiggsfieldClientError

MODEL = "bytedance/seedance-2.5/text-to-video"
ARGUMENTS = {
    "prompt": "A cinematic scene at sunset",
    "duration": 5,
    "resolution": "720p",
    "aspect_ratio": "16:9",
}


def video_url(result):
    """URL aus der Antwort holen; das Ergebnis liegt laut Modell-Doku im Feld `video`."""
    video = result.get("video")
    if isinstance(video, list):
        video = video[0] if video else None
    if isinstance(video, dict):
        return video.get("url")
    return video if isinstance(video, str) else None


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env.local")  # setzt HF_KEY, ohne ihn auszugeben

    last = {"status": None}

    def on_update(status):
        if type(status) is not type(last["status"]):
            print(f"  Status: {type(status).__name__}")
        last["status"] = status

    try:
        result = higgsfield_client.subscribe(
            MODEL,
            arguments=ARGUMENTS,
            on_enqueue=lambda request_id: print(f"Auftrag angenommen: {request_id}"),
            on_queue_update=on_update,
        )
    except CredentialsMissedError:
        sys.exit("Keine Zugangsdaten: HF_KEY (key-id:key-secret) in .env.local oder als Umgebungsvariable setzen.")
    except HiggsfieldClientError as e:
        sys.exit(f"Higgsfield-API-Fehler: {e}")
    except httpx.HTTPError as e:
        sys.exit(f"Verbindung zur Higgsfield-API fehlgeschlagen: {e}")

    status = last["status"]
    reported = str(result.get("status", "")).lower()
    if isinstance(status, NSFW) or reported == "nsfw":
        sys.exit("Abgelehnt: Die Anfrage wurde von der Moderation als NSFW markiert – kein Video erzeugt.")
    if isinstance(status, Cancelled) or reported in ("canceled", "cancelled"):
        sys.exit("Abgebrochen: Die Anfrage wurde storniert – kein Video erzeugt.")
    if isinstance(status, Failed) or reported == "failed":
        sys.exit(f"Fehlgeschlagen: {result.get('error') or result.get('detail') or 'keine Details'}")
    if not isinstance(status, Completed) and reported != "completed":
        sys.exit(f"Unerwarteter Endstatus ({type(status).__name__ if status else reported or 'unbekannt'}) – kein Erfolg.")

    url = video_url(result)
    if not url:
        sys.exit(f"Fertig gemeldet, aber keine Video-URL in der Antwort (Felder: {sorted(result)}).")
    print(url)


if __name__ == "__main__":
    main()
