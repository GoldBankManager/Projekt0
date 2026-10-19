---
name: video
description: Videos mit der Open-Source-Pipeline auf einer vast.ai-GPU erstellen, tauschen, analysieren und fertig rendern (Wan-VACE Reference-to-Video, Auto-Tausch, Analyse, Upscale). Benutzen, sobald der Nutzer ein Video generieren, ein Auto/Objekt in einem Clip ersetzen, Hooks/Clips analysieren oder die GPU starten/stoppen will.
---

# Video-Pipeline bedienen

Alles läuft aus `video_pipeline/` heraus. Die GPU-Arbeit passiert auf einer vast.ai-Instanz, gesteuert über `vast.py` (mieten/zerstören) und `remote.py` (Dateien, Jobs, Downloads). SSH/Jupyter werden nicht gebraucht.

**Geld-Regel aus CLAUDE.md gilt immer:** nie Guthaben aufladen; mieten oder sonstige Kosten nur nach ausdrücklichem OK für genau diese Aktion, mit Preis vorher.

## Der Ablauf, den der Nutzer erwartet

Der Nutzer schreibt `/video`, schickt Bilder/Clips (oder Links) und sagt grob, was er will. **Claude erledigt den Rest selbst** und fragt nur:
1. einmal nach dem **OK zum Mieten** (GPU, $/h, Reichweite des Guthabens) – nur wenn noch keine Instanz läuft,
2. nach der **Zielsetzung**, falls sie wirklich unklar ist (sonst sinnvoll annehmen und sagen, was angenommen wurde),
3. am Ende, ob die Instanz **zerstört** werden soll.

Zwischendurch kurz Bescheid geben (Instanz startet, installiert, Job läuft, fertig) – nicht bei jedem Befehl.

**Ziel ableiten, wenn der Nutzer nur Material schickt:**
| Material | Standard |
|---|---|
| Clip mit Auto + Fotos eines anderen Autos | `ref2video swap` (Auto tauschen), danach `finish` mit Originalton |
| Nur Foto(s) von Auto/Produkt/Person | `ref2video r2v` bzw. bei Personen `studio` Phantom / Stand-In, 9:16, 5 s |
| Nur Text-Idee | `generate wan22` (24 GB) oder `generate ltx2` wenn Ton gewünscht (48 GB+) |
| Links zu fremden Videos + „analysieren/Hooks“ | `fetch` + `analyze --ask` (Hook der ersten 2 s, Schnitttempo, Stil) |

## 0. Material finden

- Angehängte Dateien liegen in der Cloud-Sitzung unter **`/mnt/user-data/uploads/`** (auch `/mnt/attach/` prüfen): `ls -la /mnt/user-data/uploads /mnt/attach`.
- Ist ein Bild nur im Chat sichtbar, aber nicht als Datei vorhanden: den Nutzer um die Datei als Anhang oder um einen Link bitten.
- Links: TikTok/Reels/YouTube/X, Google-Drive- und Dropbox-Freigaben, direkte Bild-/Video-URLs – alles per `fetch` (die Instanz lädt selbst).

## 1. Instanz prüfen oder starten

```bash
cd video_pipeline
python vast.py status          # läuft schon eine? → weiter mit Schritt 2
python vast.py balance
python vast.py offers          # 24 GB: Standard | 48 GB+: --model 14b --gpu "RTX A6000" --max-price 0.9 | 80 GB: --gpu "A100 SXM4" --max-price 1.5
```
- Kleinste GPU wählen, die für die Aufgabe reicht (Tabelle in Schritt 3). Dem Nutzer Angebot, $/h und Stunden-Reichweite des Guthabens nennen, **auf OK warten**.
- Nach OK: `python vast.py start --offer <ID> --model 1.3b|14b -y`.
- Dann `python remote.py wait` **im Hintergrund** starten (10–25 min). In der Zwischenzeit Material vorbereiten und Prompts schreiben (`video-prompts`).
- `remote.py` sucht selbst den Weg zur Instanz: direkter Port, sonst HTTPS-Tunnel aus dem Instanz-Log. Klappt beides nicht: `python vast.py logs <ID>` prüfen; Notweg ist der Jupyter-Link aus `python vast.py status` (Nutzer lädt Dateien dort hoch, Befehle im Terminal).

## 2. Dateien auf die Instanz

- Anhänge: `python remote.py up /mnt/user-data/uploads/<datei> …` → landen in `in/` (Dateinamen ohne Leerzeichen bevorzugen)
- Links: `python remote.py fetch "<url>" --name clip.mp4`
- `python remote.py ls in`

## 3. Jobs (laufen nacheinander auf der GPU; lange Jobs im Hintergrund starten)

Vor jedem Prompt den Skill `video-prompts` anwenden. Für Hooks/Skripte/Copy: `marketing-os`, `social`, `youtube`, `copywriting`, `ad-creative`.

| Ziel | Befehl | GPU |
|---|---|---|
| Clip analysieren (Schnitte, Transkript, Szenen, Hook der ersten Sekunden) | `python remote.py run analyze in/clip.mp4 --ask "..."` | 24 GB |
| Auto im Clip ersetzen, Szene + Kamera bleiben | `python remote.py run ref2video swap --video in/clip.mp4 --ref in/a.jpg in/b.jpg --prompt "..." [--start 2 --max-seconds 6]` | 24 GB (1.3B) / 48+ (14B) |
| Neues Video aus Referenzbild(ern), VACE | `python remote.py run ref2video r2v --ref in/a.jpg --prompt "..." [--aspect 9:16]` | wie oben |
| Text/Bild → Video **mit Ton** (LTX-2) | `python remote.py run generate ltx2 --prompt "..." [--image in/a.jpg --enhance --seconds 8]` | 48+ GB |
| Text/Bild → Video, beste Bewegung (Wan2.2) | `python remote.py run generate wan22 --prompt "..." [--image in/a.jpg] [--big]` | 24 GB (5B) / 48+ (`--big`) |
| Studio (Wan2GP) einmalig installieren | `python remote.py run studio install` | – |
| Studio: Referenzen ins Video (Phantom), Multi-Referenz mit Ton (LTX-2.5 MSR), Gesicht halten (Stand-In/Lynx), Charakter animieren (animate2), Kamerafahrt (uni3c), lange Videos (sky_df_14B), sprechender Avatar (infinitetalk) | `python remote.py run studio run --model phantom_14B --ref in/a.jpg --prompt "..."` (Liste: `run studio models`; erst `--dry-run`) | je nach Modell |
| Fertig machen: RIFE 30/60 fps, Real-ESRGAN 4K, Ton, Untertitel | `python remote.py run finish out/<datei>.mp4 [--audio-from in/clip.mp4 --audio-offset 2] [--srt out/clip.srt] [--height 1080] [--fps 60]` | 24 GB |

- Bei der 1.3B-Instanz an ref2video immer `--model Wan-AI/Wan2.1-VACE-1.3B-diffusers --res 480p` anhängen. Bei 48-GB-Karten mit 14B: `--offload model`.
- Mehrere Versionen: `--takes 3`. Reproduzieren: `--seed N`.
- LTX-2-Videos haben eigenen Ton – `finish` behält ihn automatisch.
- Studio-Ergebnisse landen in `out/studio/`. Feinsteuerung: UI per SSH-Tunnel (`run studio ui`, Hinweise im Output), dort „Export Settings“ → JSON hochladen → `run studio run in/settings.json --prompt "..."`.
- Wenn das gewünschte Modell mehr VRAM braucht als die laufende Instanz hat: dem Nutzer sagen und eine größere GPU vorschlagen (neues OK nötig).

## 4. Ergebnis zum Nutzer

```bash
python remote.py get-new        # alle neuen *_final.mp4 → video_pipeline/downloads/
```
Dann die Datei mit SendUserFile schicken. Videos nicht committen.

## 5. Ende

`python vast.py status` zeigen, Kosten/h nennen und anbieten: `python vast.py stop <ID>` (zerstört Instanz + alle Dateien darauf; vorher alles Wichtige mit `get` holen). Erst nach OK ausführen.

## Prompts für Wan-VACE (englisch)

Aufbau: **Subjekt (genau) → Aktion (eine pro Clip) → Umgebung → Licht → Kamera → Stil**.
- Auto exakt benennen: Marke, Modell, Farbe, Felgen, Details. Die Referenzbilder werden automatisch freigestellt (`out/ref_*_cutout.png` prüfen).
- Kamera konkret: "low-angle tracking shot", "slow orbit", "drone shot following from behind", "handheld close-up".
- Licht: "golden hour", "wet asphalt reflecting neon", "overcast soft light".
- 1–3 Referenzbilder, keine Widersprüche zwischen Bild und Prompt.
- Lieber `--takes 3` als den Prompt endlos umschreiben.
- Hook: Die ersten 1–2 Sekunden müssen das Stärkste zeigen (Bewegung, Kontrast, Überraschung). Bei Analysen von Vorbildern gezielt nach dem Hook fragen (`--ask "What happens in the first 2 seconds that grabs attention?"`).

## Grenzen

- Wan erzeugt 16 fps, ~5 s pro Durchgang (swap stückelt längere Clips automatisch).
- Logos/Schrift verformen sich öfter als bei Seedance. Für Showreel-Edits mit exakter Kamerafahrt in neuer Szene bleibt `car_swap.py` (fal.ai, kostet pro Sekunde, nur mit OK).
