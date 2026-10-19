---
name: video-prompts
description: Gute Prompts für KI-Videomodelle schreiben (Wan2.1/2.2, VACE, LTX-2 mit Ton, Phantom, Seedance, Kling, Veo). Benutzen, bevor ein Videoprompt für generate.py, ref2video.py, studio.py oder car_swap.py geschrieben wird, oder wenn der Nutzer fragt, wie man ein Modell richtig promptet.
---

# Videoprompts, die funktionieren

Immer auf **Englisch**, konkret, filmisch. Eine Szene = eine klare Aktion.

## Grundgerüst (alle Modelle)

```
[Shot type + camera move], [subject in exact detail] [one clear action], [environment], [lighting], [mood/style], [sound – only for audio models]
```

Beispiel:
> Low-angle tracking shot, a matte black Lamborghini Huracán STO with bronze rims accelerates out of a wet tunnel, neon tube lights streaking across the glossy paint, night, cinematic teal-orange grade, shallow depth of field.

## Regeln

1. **Subjekt exakt**: Marke, Modell, Farbe, Material, Details (Felgen, Lackfinish, Kleidung). Vage → generisch.
2. **Eine Aktion pro Clip** (~5 s). Mehrere Ereignisse → mehrere Clips oder Time-Codes (nur LTX-2/Seedance, s. u.).
3. **Kamera ist Pflicht**: sonst entscheidet das Modell. Vokabular: static tripod, slow push-in / dolly in, pull-out, tracking shot, orbit / arc shot, crane up, drone shot, whip pan, handheld, low-angle, top-down, extreme close-up, macro.
4. **Licht** setzt die Qualität: golden hour, blue hour, overcast soft light, hard rim light, volumetric light, neon reflections on wet asphalt, studio softbox.
5. **Physik/Details** benennen, die glaubwürdig machen: tire smoke, water spray, dust kicked up, reflections, motion blur on background.
6. **Keine Widersprüche** zu Referenzbildern (Farbe/Modell im Prompt = Farbe/Modell im Bild).
7. **Negativ-Prompt** nutzen (die Skripte haben gute Standards): morphing, flickering, distorted logos, extra wheels, text artifacts.
8. **Varianten statt Perfektion**: `--takes 3`, dann den besten Seed weiterverwenden.

## Modellspezifisch

| Modell | Worauf achten |
|---|---|
| **Wan2.1-VACE** (`ref2video.py`) | Prompt beschreibt das **Ergebnis**, inkl. Referenz-Subjekt ("a white Porsche 911 GT3 RS…"). Swap: Szene aus dem Clip mit erwähnen, damit Licht passt. 1–3 freigestellte Referenzen. |
| **Wan2.2** (`generate.py wan22`) | Liebt lange, detaillierte Prompts (60–120 Wörter). Kamera + Licht + Farbstimmung ausschreiben. I2V: Bild nicht nochmal komplett beschreiben, sondern **Bewegung** und Kamera. |
| **LTX-2** (`generate.py ltx2`) | Erzeugt **Ton**: Geräusche/Musik/Dialog in den Prompt ("the V12 roars, tires screech, echo in the tunnel"). Chronologisch schreiben, wie ein Drehbuchabsatz. `--enhance` baut kurze Prompts automatisch aus. |
| **LTX-2.5 MSR / Phantom** (`studio.py`) | Jede Referenz im Prompt benennen ("the man from the first image drives the red car from the second image"). Referenzen mit ruhigem/weißem Hintergrund. |
| **Stand-In / Lynx** (`studio.py`) | Referenz = scharfe Gesichts-Nahaufnahme, weißer Hintergrund. Prompt beschreibt Szene + Kleidung, nicht das Gesicht. |
| **Seedance / Kling / Veo** (bezahlt) | Time-Codes für Multi-Shot: `[0-4s] … [4-8s] … [8-12s] …`, je Shot: Einstellung, Kamera, Aktion, Ton. @Image/@Video-Referenzen klar zuordnen (siehe `car_swap.py`). |

## Time-Code-Muster (LTX-2, Seedance, Veo)

```
[0-3s] Extreme close-up, static: rain drops on the carbon hood, engine idle rumble.
[3-6s] Hard cut, low-angle tracking shot: the car launches, rear tires spray water, V8 roar.
[6-10s] Drone shot pulling up and back, the car's taillights streak through the neon city, music swells.
```

## Hook (erste 1–2 Sekunden)

- Mit dem **stärksten Bild** starten: Bewegung auf die Kamera zu, extremer Close-up, Kontrast, etwas Unerwartetes.
- Kein langsames Establishing am Anfang bei Shorts/Reels.
- Ton-Hook bei LTX-2: lauter, markanter Sound im ersten Moment (Motorstart, Bass-Drop).
- Für Hook-Texte, Psychologie und Copy: Skills `marketing-os` (Hook-Engine), `copywriting`, `marketing-psychology`, `social`, `youtube`.

## Wenn es schlecht aussieht

| Problem | Lösung |
|---|---|
| Objekt verformt sich / morpht | kürzere Aktion, weniger Bewegung, Kamera ruhiger, Negativ-Prompt "morphing" |
| Logo/Schrift kaputt | Logo nicht im Prompt erwähnen, nah ans Referenzbild, später im Schnitt drüberlegen |
| Zu wenig Bewegung | Verben stärker (accelerates, drifts, bursts), Kamera-Bewegung angeben |
| Falsche Farbe | Farbe 2× nennen (Subjekt + Detail), Referenz mit neutralem Licht |
| Flackern | `finish.py` (RIFE) statt höherer FPS im Modell, `--steps` erhöhen |

Quellen/Inspiration: [awesome-seedance](https://github.com/ZeroLu/awesome-seedance) (Time-Code- und Werbe-Beispiele), [awesome-ai-video-prompts](https://github.com/geekjourneyx/awesome-ai-video-prompts), Wan2.2-/LTX-2-Prompt-Guides der Hersteller.
