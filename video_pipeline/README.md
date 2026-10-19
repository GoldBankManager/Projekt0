# Video-Pipeline (100 % Open Source, läuft auf einer gemieteten GPU)

Lokaler Ersatz für `car_swap.py` (Seedance über fal.ai): keine Kosten pro Sekunde, nur die GPU-Miete.

```
 Clip ──► analyze.py ─────► Szenen, Untertitel (.srt), Beschreibung pro Szene (JSON)
   │
   ├────► ref2video.py ───► Auto tauschen / Referenzbild → Video (Wan-VACE)
 Text/Bild ─► generate.py ─► Video mit Ton (LTX-2) oder beste Bewegung (Wan2.2)
 Referenzen ─► studio.py ──► Wan2GP: Phantom, LTX-2.5 MSR, Stand-In, Lynx, Animate 2, Uni3C, SkyReels …
              │
              └──► finish.py ► RIFE 30/60 fps, Real-ESRGAN auf 1080p (bis 4K), Ton, Untertitel ──► *_final.mp4
```

## Welche Repos wofür

| Schritt | Repo / Modell | Wofür |
|---|---|---|
| Analyse: Schnitte | [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | erkennt jeden Schnitt und teilt den Clip in Szenen |
| Analyse: Sprache | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (Whisper large-v3) | Transkript und `.srt`-Untertitel |
| Analyse: Bildinhalt | [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) | beschreibt jede Szene, beantwortet Fragen (`--ask`) |
| Masken | [Ultralytics YOLO11-seg](https://github.com/ultralytics/ultralytics) | findet das Auto in jedem Frame und stellt die Referenzbilder frei |
| **Reference-to-Video** | [Wan2.1-VACE](https://github.com/ali-vilab/VACE) über [diffusers](https://github.com/huggingface/diffusers) | malt das Referenz-Auto in die Maske (`swap`) oder baut ein neues Video aus Referenzbildern (`r2v`) |
| **Text/Bild → Video mit Ton** | [LTX-2](https://github.com/Lightricks/LTX-2) über diffusers (`generate.py ltx2`) | Video + Geräusche/Musik/Dialog in einem Durchgang |
| **Text/Bild → Video** | [Wan2.2](https://github.com/Wan-Video/Wan2.2) TI2V-5B / A14B über diffusers (`generate.py wan22`) | beste offene Bewegungsqualität |
| **Studio** | [Wan2GP](https://github.com/deepbeepmeep/Wan2GP) (`studio.py`) | Phantom, LTX-2.5 MSR (1–4 Referenzen + Ton), Stand-In, Lynx, VACE 2.2, Animate 2, Uni3C, SkyReels-2, HunyuanCustom, InfiniteTalk – mit wenig VRAM |
| Zwischenbilder | [RIFE v4.26](https://github.com/hzwer/Practical-RIFE) über [ccvfi](https://github.com/EutropicAI/ccvfi) | 16/24 → 30/60 fps per KI |
| Upscale | [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) über [spandrel](https://github.com/chaiNNer-org/spandrel) | 720p → 1080p (Standard) oder 4K, auch hochkant (1080x1920) |
| Rendern | [FFmpeg](https://ffmpeg.org) | Ton, Untertitel, Encoding |
| Links laden | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | TikTok/Reels/YouTube-Vorbilder auf die Instanz |

Wissen für Claude (Skills in `.claude/skills/`): `video` (Bedienung), `video-prompts` (Prompt-Regeln je Modell), Marketing-Skills aus [marketingskills](https://github.com/coreyhaines31/marketingskills), [marketing-os](https://github.com/Yuzzyuk/marketing-os) (Hook-Engine) und [claude-youtube](https://github.com/AgriciDaniel/claude-youtube) – siehe `.claude/skills/THIRD_PARTY.md`.

## vast.ai: welche GPU?

| GPU | ca. $/h | Modell | Für 9 $ |
|---|---|---|---|
| RTX 4090 (24 GB) | 0,30–0,45 | `Wan-AI/Wan2.1-VACE-1.3B-diffusers`, 480p | ca. 20–30 h, gut zum Testen |
| RTX A6000 / L40S (48 GB) | 0,40–0,90 | 14B mit `--offload model` | ca. 10–20 h |
| A100 / H100 (80 GB) | 1,00–2,00 | 14B, 720p, schnell | ca. 5–9 h |

**Auto-Stopp:** Nach 30 min ohne Anfrage und ohne Job stoppt sich die Instanz selbst (`PIPE_IDLE_MIN`). Danach fallen keine GPU-Kosten mehr an, nur Speicher (wenige Cent pro Tag), bis sie zerstört wird.

Beim Mieten: Template **PyTorch (CUDA 12)**, mindestens **150 GB Disk**. Die Instanz am Ende **zerstören (Destroy)**, nicht nur stoppen, sonst kostet der Speicher weiter.

## Automatisch mieten und installieren (`vast.py`)

```bash
pip install vastai
export VAST_API_KEY="..."                 # Key von https://cloud.vast.ai/manage-keys/
python vast.py balance                    # Guthaben
python vast.py offers                     # günstigste RTX 4090 ansehen
python vast.py start                      # mieten (mit Rückfrage), Pipeline installiert sich selbst
python vast.py logs <ID>                  # warten bis "PIPELINE_READY"
python vast.py status                     # Jupyter-Link und SSH-Befehl
python vast.py stop <ID>                  # ZERSTÖREN, keine Kosten mehr
python vast.py resume <ID>                # gestoppte Instanz fortsetzen
```

### Fernsteuern ohne SSH (`remote.py`, spricht mit `server.py` auf der Instanz)

```bash
python remote.py wait                                     # bis die Installation fertig ist
python remote.py up auto.jpg clip.mp4                     # → in/
python remote.py fetch "https://www.tiktok.com/@x/video/1" --name vorbild.mp4
python remote.py run ref2video swap --video in/clip.mp4 --ref in/auto.jpg --prompt "..."
python remote.py run finish out/clip_swap_s1_16fps.mp4 --audio-from in/clip.mp4
python remote.py get-new                                  # fertige Videos → downloads/
```

Das Token für den Server wird aus `VAST_API_KEY` abgeleitet und muss nirgends gespeichert werden. In Claude Code reicht `/video`.
Alternativ geht es über den Jupyter-Link im Ordner `/workspace/Projekt0-master/video_pipeline/` mit den Befehlen unten.

## Setup von Hand (einmal pro Instanz, ca. 10–20 min, meistens Modell-Download)

```bash
git clone https://github.com/GoldBankManager/Projekt0
cd Projekt0/video_pipeline
bash setup_vast.sh          # 14B-Modell (48–80 GB GPU)
bash setup_vast.sh 1.3b     # kleines Modell (RTX 4090)
source ~/.bashrc
```

Dateien hochladen: `scp -P <port> clip.mp4 auto*.jpg root@<ip>:~/Projekt0/video_pipeline/`, oder in Jupyter per Drag & Drop.

## Benutzung

```bash
# 1) Analysieren
python analyze.py clip.mp4
python analyze.py clip.mp4 --ask "Welches Auto ist zu sehen? Marke, Modell, Farbe, Felgen."

# 2a) Auto tauschen: Szene und Kamerafahrt bleiben, nur das Auto ist neu
python ref2video.py swap --video clip.mp4 --ref front.jpg side.jpg \
    --prompt "A matte black Lamborghini Huracan drifting through a neon-lit tunnel, cinematic"

# 2b) Reference-to-Video: Referenzbild + Prompt ergibt eine neue Szene
python ref2video.py r2v --ref porsche.jpg --aspect 9:16 \
    --prompt "The car drives along a coastal road at sunset, drone shot following from behind"

# Auf der RTX 4090:
python ref2video.py r2v --ref car.jpg --prompt "..." --model Wan-AI/Wan2.1-VACE-1.3B-diffusers --res 480p

# 3) Fertig machen: 30 fps, 1080p, Originalton  (4K: --res 2160)
python finish.py out/clip_swap_s123_16fps.mp4 --audio-from clip.mp4
```

Tipps:
- **Prompt auf Englisch**, und das Referenz-Auto genau beschreiben (Marke, Farbe, Felgen). Das hilft VACE stark.
- **1–3 Referenzbilder**. Sie werden automatisch freigestellt, Kontrolle in `out/ref_*_cutout.png`.
- `--takes 3` erzeugt drei Versionen mit unterschiedlichem Seed. Mit `--seed` lässt sich eine Version wiederholen.
- Ein Durchgang erzeugt ~5 s (81 Frames). `swap` verarbeitet längere Clips automatisch in Stücken, `--max-seconds` begrenzt die Länge.
- Wenn Schatten oder Kanten des alten Autos stehen bleiben: `--grow 20`.

## Grenzen (ehrlich)

- Der **Showreel-Modus** von `car_swap.py` (nur die Kamerafahrt übernehmen, Szene komplett neu) ist mit offenen Modellen deutlich schwächer als mit Seedance und deshalb hier nicht eingebaut. `swap` (Szene bleibt) und `r2v` (komplett neu) funktionieren gut.
- **Logos und Schriftzüge** verformen sich bei offenen Modellen öfter.
- Wan arbeitet mit 16 fps. `finish.py` rechnet die Zwischenbilder mit RIFE dazu (Fallback: `--interp ffmpeg`).
- MAGREF, Kaleido und SkyReels-V3 sind (noch) nicht eingebaut – sie fehlen in diffusers und Wan2GP; Phantom und LTX-2.5 MSR decken Multi-Referenz ab.
- Die GPU-Teile (Modelle) sind noch **nicht auf einer echten GPU getestet**. Beim ersten Lauf auf vast.ai kann noch eine Kleinigkeit zu fixen sein.

## Studio (Wan2GP) – wann welches Modell

| Ziel | `--model` |
|---|---|
| Personen/Objekte aus Referenzbildern ins Video | `phantom_14B` |
| 1–4 Referenzen, Video mit Ton | `ltx2_25_22B_msr` |
| Gesicht/Person konsistent halten | `vace_standin_14B`, `lynx` |
| Charakterbild mit Bewegung aus Vorlage-Video animieren | `animate2` |
| Kamerafahrt um ein Startbild | `uni3c` |
| Sehr lange Videos | `sky_df_14B` |
| Person mit Identität (nur Menschen) | `hunyuan_custom` (⚠️ Tencent-Lizenz schließt die EU aus) |
| Sprechender Avatar aus Bild + Audio | `infinitetalk` |

```bash
python studio.py install                      # einmalig (eigene venv)
python studio.py models phantom               # Modelle suchen
python studio.py run --model phantom_14B --ref in/auto.jpg in/fahrer.jpg --prompt "..." --dry-run
python studio.py run --model phantom_14B --ref in/auto.jpg in/fahrer.jpg --prompt "..."
python studio.py ui                           # Oberfläche, per SSH-Tunnel: ssh -p <PORT> root@<IP> -L 7860:localhost:7860
```
