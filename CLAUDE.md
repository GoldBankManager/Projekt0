# Projekt0 – KI-Videoproduktion

Ziel: Videos erstellen, Autos/Objekte in Clips tauschen, Clips und Hooks analysieren. Bevorzugt mit Open Source auf einer gemieteten vast.ai-GPU.

- `video_pipeline/`: Open-Source-Pipeline (Wan-VACE, YOLO, Whisper, Qwen-VL, Real-ESRGAN, FFmpeg). **Bedienung: Skill `/video`** (`.claude/skills/video/SKILL.md`). Details in `video_pipeline/README.md`.
  - `vast.py` mietet und zerstört die GPU, `remote.py` steuert die Jobs auf der Instanz, `server.py` läuft auf der Instanz.
- `car_swap.py`: bezahlte Alternative über fal.ai (Seedance 2.0), nur mit OK.
- Der Start-Hook installiert die vast.ai-CLI. `VAST_API_KEY` kommt aus den Umgebungs-Einstellungen. Den Key nie ausgeben oder in Dateien schreiben.
- Mit dem Nutzer Deutsch sprechen. Videoprompts auf Englisch.
- **Format: Standard 9:16** (TikTok/Reels/Shorts), ausgeliefert als 1080x1920. 16:9 (1920x1080) nur, wenn der Nutzer es will, das Ausgangsmaterial quer ist oder die Szene klar davon profitiert (breite Fahrszenen, YouTube) – dann kurz sagen, warum.

## Geld und Guthaben (gilt immer, für alle Dienste: vast.ai, fal.ai und jeden anderen bezahlten Anbieter)

- **Niemals Guthaben aufladen**, keine Zahlungsmethode hinzufügen, kein Auto-Aufladen einrichten. Auch nicht, wenn das Guthaben leer ist. Dann stoppen und Bescheid sagen.
- **Alles, was Geld kostet, nur mit ausdrücklichem OK des Nutzers für genau diese Aktion**: GPU mieten (`vast.py start`), bezahlte API-Aufrufe (z. B. `car_swap.py`), Speicher, Bandbreite usw. Vorher Preis pro Stunde bzw. pro Aufruf und das geschätzte Gesamtbudget nennen.
- Ein OK gilt nur für die genannte Aktion, nicht für spätere.
- `vast.py start -y` und `car_swap.py -y` nie ohne dieses OK benutzen.
- Laufende vast.ai-Instanzen nicht vergessen: nach der Arbeit den Status zeigen und das Zerstören anbieten.
- **Auto-Stopp (Wunsch des Nutzers):** Die Instanz stoppt sich nach 30 min ohne Anfrage und ohne laufenden Job selbst (nur stoppen, nie selbst zerstören). Gestoppt = keine GPU-Kosten, nur Speicher. `vast.py resume <ID>` startet sie wieder und kostet wieder pro Stunde → vorher OK holen. Gestoppte Instanzen beim nächsten Chat erwähnen und das Zerstören anbieten.
