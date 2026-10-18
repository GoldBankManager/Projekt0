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

---

# Version 3: Kinetische Typografie (`video_v3.html`)

**Feedback:** „Besser machen.“ Neue Stil-Referenz: Instagram-Reel `Den9zOltiZ2` (kinetische Typografie). Musik bleibt `assets/music/track.mp3` (9,8 s, gleiches Beat-Raster).

**Stil der Referenz (85 % übernommen):** reinweißer Grund · fette Grotesk (Inter 800, enges Spacing) · Schwarz/Weiß + **Rot als einziger Akzent** · schwarze Panels, die über das Bild wischen und alles darunter invertieren (Difference-Blend) · Buchstaben fliegen gestaffelt mit Bewegungsunschärfe ein · Outline-Geisterkopien · gestapelte, scrollende Wort-Wiederholungen · verstreute, rotierende rote Buchstaben, die sich zum Wort sortieren · riesiger Outline-Buchstabe als Zoom-Durchflug · kumulativer Wort-Stapel (neues Wort groß, alte schrumpfen nach oben) mit Raster-Kreis · Text, der um eine schwarze Linse läuft · roter Punkt, der rollt und eine Linie zieht · Buchstaben auf einer Welle, die sich glätten.
**15 % Marke:** HavvamBau-Logo in der Linse und am Ende, Inhalte und Kontakt von havvambau.de. Die Akzentfarbe ist in **einer** Variable (`--accent`) und lässt sich auf Markengrün umstellen.

| Zeit (Beat) | Szene | Animation |
|---|---|---|
| 0,00–1,40 | **„Ihre Wärmepumpe“** | Schwarzes Panel wischt rein (Invertierung), Buchstaben fliegen mit Blur ein, auf 0,68 wird das Bild schwarz, Outline-Geister ziehen durch. |
| 1,40–2,85 | **„bestellt?“ → „Fundament?“** | Panel wischt raus · „bestellt?“ fliegt rein · auf 1,77 füllt ein scrollender Stapel „Fundament?“ das Bild · auf 2,13 wird ein „a“ rot · der Stapel verschwimmt, nur das rote „a“ bleibt. |
| 2,85–4,30 | **„Sie braucht eine Grundlage.“** | Verstreute rote Buchstaben fliegen rotierend ein und sortieren sich zu „Grundlage.“ (Wort fertig auf 3,57, das „a“ bleibt rot) · riesiges Outline-„G“ wächst · Zoom durch das „G“. |
| 4,30–5,38 | **Build-up: Wir machen** | Kumulativer Stapel auf den 3 Hits: AUSHUB. (4,30) · AUFMASS. (4,66) · FUNDAMENT. (5,02), Panel springt jeweils die Hälfte, Raster-Kreis dahinter. Der Punkt von „Fundament.“ ist rot. |
| 5,38–5,74 | **Stille** | Alles fällt weg, nur der rote Punkt bleibt und wächst. |
| **5,74 DROP** | **Linse** | Der Punkt explodiert zur schwarzen Linse mit dem HAVVAMBAU-Logo, „WIR SCHAFFEN DIE GRUNDLAGE •“ läuft um die Linse, Pulse auf 6,10 / 6,47. |
| 6,83–7,55 | **Punkt rollt** | Die Linse fällt raus, der rote Punkt springt, rollt und zieht eine Linie, die den CTA aufdeckt. |
| 7,55–9,80 | **CTA** | „Jetzt Projekt“ / **„anfragen.“** · **0174 5652015** kommt auf einer Welle und glättet sich (7,91) · havvambau**.**de (8,27, roter Punkt) · Logo + „Augsburg & Umgebung“ (8,64) · ruhiger Push-in bis zum Ende. |

**Kamera:** Durchgehender leichter Push-in mit Mikro-Rotation, Kicks auf den Hits, Whip-Zooms an den Szenengrenzen.
**Sound:** Musik + SFX (Whooshes bei Buchstaben-Flügen, Klicks, Pop beim roten Punkt, Rollgeräusch, Riser in den Drop, Impact auf dem Drop).

---

# Version 4: langsamer, neue Texte, mehr Bilder (`video_v4.html`, `sound_v4.py`)

**Feedback:** „Zu schnell, man kann nichts lesen. Texte und Visuelles anpassen. Mehr Bilder.“

**Musik verlängert (18,5 s statt 9,8 s):** Intro + Build-up unverändert · der Drop-Takt (5,74–8,63 s) läuft **4×**, jeweils mit Lautstärke-Ausgleich (der Clip fadet im Original schon ab dem Drop aus) und 12-ms-Crossfade genau auf dem Downbeat · danach der originale Ausklang. Gleiches Beat-Raster wie vorher, also bleibt alles synchron.

| Zeit | Szene | Bild / Text |
|---|---|---|
| 0–2,9 | Hook | „Ihre **Wärmepumpe**“ → „ist bestellt?“ · Wärmepumpen-Illustration fällt ins Bild |
| 2,9–4,3 | Frage | Stapel „Fundament?“ · Box „Und wer macht das“ · rotes „a“ |
| 4,3–5,7 | Problem | „Ohne **Grundlage** steht nichts.“ · Wärmepumpe kippt um, Boden reißt · Stille: roter Punkt |
| 5,7–8,6 | DROP | Linse mit Logo + umlaufendem Slogan · „Wir schaffen die **Grundlage.**“ · „Erdarbeiten · Fundamente · Außenanlagen“ |
| 8,6–14,4 | Leistungen (je 1,45 s) | **Aushub.** (Bagger gräbt) · **Fundament.** (Kiesbett, Platte, Wärmepumpe setzt auf) · **Pflaster.** (Steine ploppen ein) · **Gartenbau.** (Baum wächst, Hecken) · Schwarz/Weiß wechselt per Panel |
| 14,4–18,5 | CTA | Punkt rollt → „Jetzt Projekt **anfragen.**“ · Telefon-Icon + **0174 5652015** · havvambau.de · Logo · „Augsburg & Umgebung“ (4 s stehen lassen) |

---

# Version 5: Mehrwert-Checkliste (`video_v5.html`, `sound_v5.py`)

**Feedback:** „Mehr Informationen, was der Zuschauer rausnehmen soll, damit er dranbleibt.“

**Retention-Mechanik:** Das Video verspricht früh einen konkreten Nutzen („4 Dinge, die das Fundament Ihrer Wärmepumpe können muss“) und löst ihn sichtbar ein: Zähler *Checkliste 1/4 … 4/4*, Fortschrittsbalken oben, ein roter Haken pro Punkt. Erst nach Punkt 4 kommen Marke und CTA.
**Inhalt:** allgemeines Fachwissen ohne konkrete Zahlen oder Leistungsversprechen. Dazu ein ehrlicher Hinweis, dass die Anlagentechnik der Fachbetrieb setzt (laut Website).
**Musik:** Drop-Takt 6× → 24,3 s.

| Zeit | Szene | Inhalt |
|---|---|---|
| 0–2,9 | Hook | „Ihre **Wärmepumpe** ist bestellt?“ + Illustration |
| 2,9–4,3 | Versprechen | Große Outline-„4“, Box „Checkliste“: „Dinge, die das **Fundament** Ihrer Wärmepumpe können **muss.**“ |
| 4,3–5,7 | Problem | „Sonst **kippt sie** oder sackt ab.“ Die Pumpe kippt, der Boden reißt. Stille → roter Punkt |
| 5,7 DROP | | Roter Flash |
| 5,7–8,6 | 1/4 **Tragfähig.** | „Verdichtetes Kiesbett, frostfrei gegründet.“ Kiesbett füllt sich, Platte fällt ein, Last-Pfeile, Bemaßung „frostfrei“ |
| 8,6–11,5 | 2/4 **Waagerecht.** | „Exakt ausgerichtet, so wie es der Hersteller verlangt.“ Platte + Wasserwaage richten sich aus, die Libelle wandert in die Mitte |
| 11,5–14,4 | 3/4 **Kondenswasser.** | „Muss ablaufen können, sonst bildet sich im Winter Eis.“ Tropfen fallen ins Kiesbett |
| 14,4–17,3 | 4/4 **Leitungsweg.** | „Graben zum Haus einplanen, danach die Fläche wiederherstellen.“ Graben öffnet sich, Leitungen laufen, Pflaster schließt ihn |
| 17,3–20,2 | Marke | Linse mit Logo + Slogan · „Aushub · Fundament · Leitungsweg · Pflaster“ · „Wir schaffen die **Grundlage.**“ · „Die Anlagentechnik setzt Ihr Fachbetrieb.“ |
| 20,2–24,3 | CTA | „Jetzt Projekt **anfragen.**“ · 0174 5652015 · havvambau.de · Logo · Augsburg & Umgebung |

---

# Version 6: saubere Musik, leisere SFX, bessere Texte (`video_v6.html`, `sound_v6.py`)

**Feedback:** „Die Musik spackt. Musik lauter, SFX leichter. Die Texte sind ein bisschen dumm.“

**Musik-Fix (in `sound_v4.extend`, gilt für alle verlängerten Versionen):**
- Die Kicks liegen im Audio bei 5,739 s / 8,632 s, also nicht auf dem gerundeten Raster (5,744 / 8,636). Bisher wurde 5–10 ms *nach* dem Anschlag geschnitten, dadurch fehlte jedem wiederholten Takt die Kick-Attacke → Stolpern. Jetzt wird der Anschlag im Audio gesucht und 30 ms davor geschnitten.
- Der Crossfade hat die Teile überlappt und jede Wiederholung um 12 ms verkürzt (Drift gegenüber dem Bild). Jetzt blendet jeder Teil in seine echte Fortsetzung aus, die Länge bleibt exakt.
- Crossfade 150 ms beat-matched: Beide Schnittpunkte liegen gleich weit vor ihrem Kick, also spielt der echte nächste Kick, während der wiederholte Takt darunter einblendet. Gemessen: Alle 7 Kicks liegen auf ±0,5 ms auf dem Raster, kein Pegeleinbruch an den Schnittstellen.

**Mix:** SFX-Gain 0,55 → 0,30 und nur noch ein Effekt pro Ereignis (keine Flatter-/Tipp-Teppiche mehr). Gesamt −13 LUFS.

**Texte (wie ein Profi, der einen Tipp gibt):**
„Wärmepumpe bestellt?“ → **4** (groß, rot) „Vor dem Liefertermin klären: Punkte für den Aufstellplatz.“ → „Sie steht dort viele Jahre. Also: einmal richtig.“ → Check 1/4 **Fester Grund.** „Verdichteter Kies, frostfrei gegründet. Da sackt nichts nach.“ · 2/4 **Exakt in Waage.** „Genau so, wie es der Hersteller vorgibt.“ · 3/4 **Wasser muss weg.** „Die Anlage tropft. Ohne Ablauf wird’s im Winter glatt.“ · 4/4 **Leitungsweg.** „Graben zum Haus gleich mit einplanen. Danach wird alles wieder sauber geschlossen.“ → **„Das alles machen wir.“** + Linse/Logo + „Wir schaffen die Grundlage.“ + „Die Wärmepumpe selbst installiert Ihr Fachbetrieb.“ → „Liefertermin steht? **Rufen Sie an.**“ 0174 5652015 · havvambau.de

---

# Version 7: komplett neues Video, „Nur 4 Infos fürs Angebot“ (`video_v7.html`, `sound_v7.py`)

**Feedback:** „Komplett neues Video.“
**Idee:** Der Zuschauer lernt, was er für ein Angebot schicken muss. Das nimmt die Hemmschwelle („kein fertiger Plan nötig“) und führt direkt zum CTA.
**Quellen (havvambau.de):** Anfrage: „Sie brauchen noch keinen fertigen Plan.“ · „Eine Anfrage. Kein Auftrag.“ · „Ahmet Yüksel · Ihr Ansprechpartner“. Garten- & Landschaftsbau: „Für ein passendes Angebot brauchen wir zunächst eine Beschreibung, Fotos und ungefähre Maße.“ Einsatzgebiet: „Nennen Sie … die Postleitzahl und den Ort. Bei Erdarbeiten helfen Angaben zur Zufahrt, Durchgangsbreite …“ sowie die Orte Augsburg, Friedberg, Gersthofen, Neusäß, Stadtbergen, Königsbrunn.
**Bildwelt neu:** Jeder Punkt läuft auf einem animierten Smartphone (Kamera, Maße, Karte, Zufahrt). Stil, Musik, Tempo und Mix wie in V6.

| Zeit | Szene | Inhalt |
|---|---|---|
| 0–2,9 | Hook | „Neuer Weg?“ · „Neue Terrasse?“ · „Neue Einfahrt?“ (auf den Hits, Invertier-Panel) |
| 2,9–4,3 | Entlastung | „Für ein Angebot brauchen Sie keinen ~~fertigen~~ Plan.“ (roter Strich auf dem Hit) |
| 4,3–5,7 | Versprechen | „Nur **4** Infos.“ → roter Punkt → Flash auf dem Drop |
| 5,7–8,6 | 1/4 **Fotos vom Bereich.** | Handykamera, 3 Auslöser auf dem Beat, Thumbnails |
| 8,6–11,5 | 2/4 **Ungefähre Maße.** | Draufsicht mit Maßpfeilen „ca. 6 m / ca. 3 m“ |
| 11,5–14,4 | 3/4 **PLZ und Ort.** | Karte mit den Orten des Einsatzgebiets, Pin, Radius |
| 14,4–17,3 | 4/4 **Die Zufahrt.** | Tor vermessen „Breite?“, Minibagger fährt durch |
| 17,3–20,2 | Marke | „Das war’s.“ · „Den Rest klären wir persönlich.“ · „Eine Anfrage. Kein Auftrag.“ · Logo · Leistungs-Laufband |
| 20,2–24,3 | CTA | „Infos schicken auf **havvambau.de**“ · „oder direkt anrufen:“ 0174 5652015 · „Ahmet Yüksel · Ihr Ansprechpartner“ · Logo |

---

# Version 8: V7 in Markenfarben (`video_v8.html`, Ton = `sound_v7.py`)

**Feedback:** „Achte darauf, dass die Farben im Video unserem Branding entsprechen.“
**Farben (Website-CSS + Logo):** Paper `#ede8df` (Grund) · Ink `#221f1b` (Text, dunkle Szenen, „HAVVAM“) · Green `#1e4a4d` (Akzent, „BAU“) · Sage `#b5c4ac` (Akzent auf dunklem Grund) · Muted/Grau ergibt sich aus der Abbildung.
**Umsetzung:** Die Szenen sind in Schwarz/Weiß + Rot + Blau gebaut und laufen komplett durch eine affine Farbmatrix (`#brand`, feColorMatrix in sRGB): Schwarz → Ink, Weiß → Paper, Rot → Green, Blau → Sage. Weil sie linear ist, bleiben Kantenglättung, Blur und das Difference-Panel (Schwarz/Weiß-Wechsel) exakt. Gemessen im fertigen MP4: Paper #ece6dd, Ink #221d1a (±2 durch die yuv420p-Kodierung).
**Auf dunklen Karten (2/4, 4/4):** Maßpfeile, Baggerschaufel, Haken und Fortschrittsbalken in Sage statt Grün, damit sie lesbar bleiben.

---

# Version 9: ruhig und lesbar (`video_v9.html`), wartet auf den ganzen Song

**Feedback:** „Die Hintergrundmusik startet immer wieder neu! Die Szenen vergehen zu schnell, es schaut zu durcheinander aus.“
**Ursache Musik:** Der gelieferte Clip ist nur 9,8 s lang. In V4–V8 wurde der 2,9-s-Drop-Takt 4–6× wiederholt, das hört man als ständigen Neustart. Lösung: Der Kunde schickt den kompletten Song, das Video wird ohne Wiederholungen darauf geschnitten.
**Ursache Unruhe:** Pro Takt (2,9 s) liefen Titel, Untertitel, Animation, Fortschritt, Haken und Schwarz/Weiß-Wechsel gleichzeitig.
**Neu:** eine Aussage pro Szene · 3,5–4,5 s Standzeit · Zeilen blenden nacheinander weich ein (0,7 s, 0,35 s versetzt) · 0,55 s Überblendung · keine Wisch-Panels, kein Buchstaben-Flug · Markenfarben direkt (Paper, Ink, Green, Sage, Muted, Line) · Markenschrift Outfit · 36,5 s.
**Szenen:** Hook „Neuer Weg, Terrasse oder Einfahrt geplant?“ · „Für ein Angebot brauchen Sie keinen fertigen Plan. Nur diese 4 Infos.“ · Info 1–4 auf dem Smartphone (Fotos, Maße, PLZ/Ort, Zufahrt) · „Den Rest klären wir persönlich. Eine Anfrage. Kein Auftrag. Unverbindlich. Persönlich. Direkt.“ · CTA mit Logo, „Ihr Projekt. Unser Handwerk.“, havvambau.de, 0174 5652015, Ansprechpartner.
**Nächster Schritt:** Song analysieren (BPM, Takte, Abschnitte) und die Szenenstarts in `SC` auf Taktanfänge legen.

---

# Version 10: ruhige Version auf dem Song ohne Wiederholung (`video_v10.html`, `sound_v10.py`)

**Musik:** Der Kunde hat zwei Dateien geschickt. `d7191014…u6phlez5dpi2.mp3` ist identisch mit `track.mp3` (9,8 s). Neu ist `track2.mp3` (16,5 s): derselbe Song (83 BPM), der Drop-Groove, beginnt auf einem Taktanfang.
**Zusammenschnitt ohne Loop:** `track.mp3` bis kurz nach dem Drop-Schlag (5,74 s), danach `track2.mp3` komplett. Die Position kommt aus der Kreuzkorrelation der Onset-Hüllkurven (alt 5,70 s ↔ neu 2,777 s, Versatz 2,923 s, im 2-Takt-Abstand bestätigt). Daraus wird `track2` genau einen Takt später gesetzt, mit 40-ms-Crossfade und Lautheitsangleich. Gemessenes Beat-Raster: Versatz 0,000 s vor dem Übergang, −0,002 s direkt danach, −0,016 s nach 15 s. Am Ende 1,2 s Fade-out, weil `track2` mitten im Takt abbricht. **Gesamt 22,35 s.**
**Video:** Layout und Markenfarben/-schrift aus V9, eine Szene pro Takt, Wechsel auf den Taktanfängen. Texte auf eine Aussage pro Szene gekürzt, Untertitel höchstens 4 Wörter: „Neuer Weg, Terrasse oder Einfahrt geplant?“ · „Kein fertiger Plan nötig. Für ein Angebot reichen 4 Infos.“ (Drop) · Fotos vom Bereich – Handyfotos reichen. · Ungefähre Maße – Grob geschätzt reicht. · PLZ und Ort – Für Anfahrt und Termin. · Die Zufahrt – Wie breit ist der Weg? · Logo, „Eine Anfrage. Kein Auftrag.“, havvambau.de, 0174 5652015, Augsburg & Umgebung.
