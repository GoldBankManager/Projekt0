# HavvamBau – Reel „Wir schaffen die Grundlage“

**Format:** 1080×1920 (9:16, Reels/TikTok/Shorts) · 60 fps · 32,5 s · H.264
**Zielgruppe:** Hausbesitzer in Augsburg & Umgebung, die gerade eine Wärmepumpe bestellt haben oder Außenarbeiten planen.
**Kernidee:** Jede Wärmepumpe braucht erst einen Platz. Eine im Code gebaute Querschnitt-Illustration zeigt, wie aus Rasen ein tragfähiger Aufstellplatz wird. Das Ende löst mit dem eigenen Slogan auf: *„Wir schaffen die Grundlage.“*
**Bildwelt:** **Keine Fotos von der Website.** Alles ist Vektor-Illustration (SVG) und Typografie in den Markenfarben. Von der Website stammen nur Texte, Farben, die Schrift Outfit und das Logo.
**Ehrlichkeit:** Laut Website übernimmt der Fachbetrieb die Anlagentechnik, HavvamBau alles Bauliche. Daraus wird bewusst ein Story-Beat statt einer übertriebenen Behauptung.

## Marke (von havvambau.de)
| Token | Wert |
|---|---|
| Paper (Hintergrund) | `#ede8df` |
| Ink (Text) | `#221f1b` |
| Green (Akzent / „BAU“) | `#1e4a4d` |
| Deep | `#1b2e2e` |
| Sage | `#b5c4ac` |
| Line | `#d2cec2` |
| Schrift | Outfit (Webfont der Website) |
| Motiv | Eckwinkel oben links / unten rechts (aus dem Logo-Post) |

## Storyboard (Schnitte auf einem 120-BPM-Raster = 0,5 s)

| Zeit | Szene | Bild | Text / Animation |
|---|---|---|---|
| **0,0–4,0** | **HOOK** | Illustration: Rasen im Querschnitt, eine Wärmepumpe fällt vom Himmel, schlägt mit Staubwolke auf, kippt weg, im Boden reißen Risse | „WÄRMEPUMPE“ → „BESTELLT?“ knallen rein (Scale + Blur + Kamerawackler). Dann: „Dann braucht sie zuerst eine **Grundlage.**“ mit grünem Balken. Die Pumpe wird nach oben weggezogen. |
| 4,0–12,0 | **So entsteht ein Aufstellplatz** (4 × 2 s) | Derselbe Querschnitt, langsamer Push-in | Fortschrittsbalken oben. 01 AUSHUB: Rasen ab, 3 Baggerschaufeln, Erde fliegt auf den Haufen · 02 AUFMASS: Maßband fährt aus, Tiefenpfeil, Badge „passt ✓“ · 03 FUNDAMENT: Kiesbett füllt sich, Betonplatte, Abziehlatte · 04 FERTIG: Pflaster ploppt rein, Erdhaufen weg, Wärmepumpe wird abgesetzt, Lüfter dreht, Haken |
| 12,0–14,0 | **Tempo-Burst** | Illustration abgedunkelt, Kamera zieht auf | Ein Wort pro Beat: SAUBER. PRÄZISE. VERLÄSSLICH. (Anspruch laut Website) |
| 14,0–17,0 | **Die Pointe** | Paper-Hintergrund, Eckwinkel | „Die Technik? Macht der Fachbetrieb.“ → „Alles drumherum? **Wir.**“ |
| 17,0–22,0 | **Leistungen** | Paper | „Was wir noch machen:“ + Walzen-Liste, die mittlere Leistung wird groß: Erdarbeiten · Baggerarbeiten · Pflaster · Gartenbau · Renovierung · Umbau · Abbruch · Montage |
| 22,0–26,0 | **Ablauf** | Paper | Linie zeichnet sich, 3 Punkte: 01 Anfragen (Vorhaben kurz schildern) · 02 Abstimmen (Details persönlich klären) · 03 Umsetzen (Sauber und verlässlich) |
| **26,0–32,5** | **ENDE + CTA** | Paper, Eckwinkel zeichnen sich | Logo HAVVAM**BAU** baut sich Buchstabe für Buchstabe auf. „Wir schaffen die Grundlage.“ (Rückbezug zum Hook) → CTA-Button **„Jetzt Projekt anfragen“** (pulsiert), ☎ 0174 5652015, havvambau.de, „Augsburg & Umgebung“. Die letzten 2 s bleiben stehen, damit man es lesen kann. |

## Warum das funktioniert
- **Hook (0–1 s):** Direkte Frage an eine klar definierte Zielgruppe plus ein Aufprall mit Kamerawackler stoppen das Scrollen. Die kippende Pumpe macht das Problem sofort sichtbar.
- **Open Loop:** „Grundlage“ im Hook wird erst im Ende mit dem Slogan aufgelöst.
- **Zeigen statt behaupten:** Jeder Arbeitsschritt ist animiert und auf einen Blick verständlich, auch ohne Ton.
- **Rhythmus:** Die Schnitte liegen auf dem Beat, die Burst-Sequenz bringt in der Mitte neue Energie.
- **CTA:** Eine klare Handlung (Projekt anfragen) und zwei Wege (Telefon, Website), lange genug zum Ablesen.

## Technik
- `video.html`: eine Szene als HTML/CSS. `window.renderFrame(t)` setzt alle Zustände deterministisch für Zeit *t*, ohne CSS-Animationen, damit jedes Frame reproduzierbar ist.
- `render.mjs`: Playwright/Chromium gibt jedes Frame exakt aus und reicht es an ffmpeg weiter (H.264, yuv420p, faststart).
- `sound.py`: synthetisches Sounddesign (Beat 120 BPM, Impacts bei Hook/Logo, Effekte für Bagger, Maßband, Kies, Pflaster). Es gibt zusätzlich eine Version **ohne Ton** für Plattform-Musik.

---

# Version 2: Referenz-Stil + Musik-Sync (`video_v2.html`)

**Feedback:** Den Stil der Referenz zu 85 % übernehmen, flüssigere Kamerafahrten, die gelieferte Musik nehmen und das Video beat-genau darauf schneiden. SFX sind ausdrücklich erlaubt.

**Musik (`assets/music/track.mp3`, 9,8 s):** 166 BPM (Halbtakt 83 BPM → Viertel = 0,723 s, Achtel = 0,3615 s).
Takte: **0,00 · 2,85 · 5,74 (DROP) · 8,63 (Ausklang)**. Starke Achtel-Hits: 0,68 · 1,77 · 2,13 · 2,85 · 3,57 · 4,30 · 4,66 · 5,02 · 5,74 · 6,10 · 6,47 · 7,55 · 7,91 · 8,27 · 8,63. Bei 5,38 s Stille vor dem Drop. Der Track fadet am Ende aus → **das Video ist so lang wie die Musik (9,8 s)**, ohne Loop.

**Stil-Übernahme aus der Referenz:** heller Papiergrund mit feinem Raster, großen dünnen Kreisbögen und Bauplan-Skizzen · Barcode · kleine Lexikon-Textblöcke („Grundlage – …“) · schwarze Label-Boxen · schwarze Eckwinkel mit weichem Schatten · Outline-Badges · Inter (Regular/Bold gemischt) + Instrument Serif Italic + Anton Condensed · orangener Glow-Strich mit Augen-Icon und Sucher-Ecken · brauner Marker-Kreis · Objekte mit weichen Schatten (hier als Vektor-Illustrationen: Wärmepumpe, Fundament-Querschnitt, Notizblock, Stifte) · Buchstaben tauchen mit Blur einzeln auf · Tiefenunschärfe im Vordergrund · Film-Grain · Vignette.
**Die 15 % Marke:** HavvamBau-Logo, Grün `#1e4a4d` im Logo/CTA, Inhalte und Texte von havvambau.de. **Weiterhin keine Website-Fotos.**

**Kamera:** Alles liegt auf einer durchgehenden Papier-Fläche. Eine virtuelle Kamera driftet ständig (leichter Push-in + Rotation) und macht auf den Beats schnelle Schwenks mit echter richtungsabhängiger Bewegungsunschärfe (aus der Kamerageschwindigkeit berechnet). Vor dem Drop fährt die Kamera in den Notizblock hinein; auf dem Drop zoomt sie aus dem Logo heraus.

| Zeit (Beat) | Szene | Inhalt |
|---|---|---|
| 0,00–2,85 (Takt 1) | **Hook** | „Ihre **Wärmepumpe**“ (0,0) · „ist bestellt. Und das“ (0,68) · Sucher-Ecken + Glow-Strich + Auge: **„Fundament?“** (2,13). Wärmepumpe schiebt sich mit Schatten ins Bild, unscharfe Vordergrund-Pumpe, Barcode, Lexikon-Text, Badges. |
| 2,85–4,30 | **Grundlage** (Whip-Schwenk nach unten) | Schwarze Box „Sie braucht eine“ (2,85) · „Saubere“ (3,21) · **„Grundlage.“** mit Glow (3,57). Fundament-Querschnitt mit Wärmepumpe fährt hoch, Bauplan-Skizzen, Lexikon „Grundlage – …“. |
| 4,30–5,38 | **Notizblock** (Whip-Schwenk) | Serif-Kursiv „Wir übernehmen:“ · Stempel auf den Build-up-Hits: AUSHUB (4,30) · AUFMASS (4,66) · FUNDAMENT (5,02) + Marker-Kreis. Stifte mit Schatten. |
| 5,38–5,74 | **Rush** | Kamera rast in den Notizblock (Zoom + Blur) in die Stille. |
| **5,74 DROP** | **Marke** | Logo-Slam mit Eckwinkeln, Shake, Flash · „Wir schaffen die *Grundlage.*“ (6,10/6,47) · Leistungs-Badges ploppen auf Achteln. |
| 7,19–9,80 | **CTA** (Schwenk nach unten, Landung auf 7,55) | Box „Ihr Projekt?“ · **„Jetzt anfragen.“** · **0174 5652015** (Marker-Kreis 7,91) · havvambau.de (Glow 8,27) · „Augsburg & Umgebung“ · „Unverbindlich. Persönlich. Direkt.“ Ruhiger Push-in bis zum Ende. |

**SFX über der Musik** (wie im Referenz-SFX-Pack): Tipp-Klicks beim Buchstaben-Reveal, Whooshes bei den Schwenks, Kamera-Shutter bei Eckwinkeln, Shine beim Glow, Papier-Rascheln beim Notizblock, Marker-Kritzeln beim Kreis, Kies-Rieseln beim Fundament, Riser in den Drop, Impact auf dem Drop, Pops bei den Badges.
