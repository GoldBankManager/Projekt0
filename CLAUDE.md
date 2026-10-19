# Projekt0 – Content-Werkstatt (HavvamBau & Supercar-Edits)

## Kunde: HavvamBau
Baufirma aus Augsburg (havvambau.de), Ansprechpartner Ahmet Yüksel.
Leistungen: Erdarbeiten/Aushub, Fundamente (auch Wärmepumpen-Fundamente), Pflaster & Außenanlagen, Garten- & Landschaftsbau.
Ziel aktuell: **Reichweite** auf Instagram/TikTok mit „krassen“ Reels. Kommunikation auf Deutsch, locker.

**Vor jedem neuen Reel `vorlagen/STIL.md` lesen.** Dort stehen die Stil-Referenzen des Kunden
(Videos + Frame-Übersichten in `vorlagen/referenzen/`), Schnitt-Regeln und Markenfarben.

## Aufbau
- `reel_engine/` – generische Render-Engine: HTML-Seite mit `window.renderFrame(t)` → Headless Chromium → MP4.
  - `render.mjs <reel-dir>` rendert das ganze Video (`--workers 2`), `--stills 0.5,2.1` Standbilder,
    `--debug views.json` beliebige Kamera/Pose-Ansichten (nur Szenen mit `window.debugRender`).
  - `mux.sh <reel-dir>` legt die SFX-Spur an und erzeugt die finalen Dateien.
- `reels/<name>/` – ein Reel = `timeline.json` (Beat-Map, einzige Timing-Quelle), `index.html` + `scene.js`
  (Three.js-Szene + Overlays), `sfx.py` (synthetische SFX, getaktet auf dieselbe Beat-Map), `final/` (Ergebnisse).
- `car_swap.py` – Supercar-Edits über fal.ai (Seedance 2.0 + 4K-Upscale). `FAL_KEY` muss gesetzt sein.

## Setup (frische Session)
```bash
cd reel_engine && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install && cd ..
pip install numpy scipy librosa
```
Chromium liegt unter `/opt/pw-browsers/chromium`. Rendering läuft über SwiftShader (CPU), ca. 0,5 s pro Frame pro Worker.

## Workflow für ein neues Reel
1. Musik analysieren (librosa: Beats, Onsets, Break, Drop) → `timeline.json`.
2. Shots auf die Beats legen (`scene.js`), mit `--stills` prüfen und iterieren.
3. `python3 reels/<name>/sfx.py --music <track>` → `out/sfx.wav` (+ `preview_mix.wav` zum Sync-Check).
4. `node reel_engine/render.mjs reels/<name>` → `out/video_only.mp4`, dann `reel_engine/mux.sh reels/<name>`.
5. Geliefert wird **Video + SFX ohne Musik** (die Musik legt der Kunde selbst drunter) plus eine Vorschau mit Musik.
