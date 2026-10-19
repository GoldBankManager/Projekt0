# Stil-Vorlagen für HavvamBau-Reels

Vom Kunden (Ahmet) geschickte Referenzen. Das ist die Stilrichtung für alle Reels.
Die Edits sind bewusst „krass“: Wir orientieren uns daran, auch wenn wir nicht 1:1 auf dem Level sind.

| Datei | Was | Was wir übernehmen |
|---|---|---|
| `referenzen/stil_01_radlader_edit.mp4` (+ `_frames.jpg`) | Volvo-Radlader-Edit (@meester_edits) | Schnitte exakt auf den Beat, Whip-Pans mit Motion Blur, Speed-Ramps, Nahaufnahmen von Logo, Rad und Kabine. Top-Down-Shot auf einem gelb glühenden Uhr-Zifferblatt, Maschine „springt“. |
| `referenzen/stil_02_motion_design_logos.mp4` (+ `_frames.jpg`) | Motion-Design-Logo-Reel (fyrmotion) | Text, der sich eintippt (mit Block-Cursor), einzelne Wörter farbig hervorgehoben, cleane Logo-Builds auf Weiß oder Verlauf, Formen, die sich zum Logo zusammensetzen. |
| `referenzen/stil_03_previs_split_screen.mp4` (+ `_frames.jpg`) | „Seedance 2.5 with previsualization in Blender“ | Split-Screen: oben das fertige Bild, unten die graue 3D-Szene (Clay/Previs) mit identischer Kamera. Labels mittig in Weiß. |
| `referenzen/musik_havvambau_01.mp3` | Track für Reel 01 (9,8 s, 166 BPM) | Nur zum Timing. Die Musik legt der Kunde selbst drunter, wir liefern Video + SFX. |

## Regeln für den Schnitt
- **Erster Frame = Bewegung**, kein Logo, kein ruhiges Bild. Hook-Text spätestens nach 0,5 s.
- **Jeder Schnitt liegt auf einem Beat** aus der Beat-Map (`reels/<reel>/timeline.json`). Kein Shot länger als ~0,7 s, außer Drop und Logo.
- **Break in der Musik = Freeze-Frame** (entsättigt, Vignette), **Hi-Hat-Roll = Tick-Schnitte** (Uhr, Zoom-Stufen).
- **Drop = Reveal**: Flash auf Weiß, alles wird farbig und groß, Zeitlupe mit Staubexplosion, Markenname slammt rein.
- **SFX an jedem Schnitt** (Whoosh endet *auf* dem Schnitt, Impact *auf* dem Beat). Tick-Sounds im Roll, Riser + Reverse-Cymbal vor dem Drop, kurze Stille direkt vor dem Drop, Boom auf dem Drop.
- **Ende = Logo-Build auf Weiß**, Wortmarke Buchstabe für Buchstabe, Untertitel auf den letzten Hits.
- Format 1080×1920, 30 fps, 9–15 s. Gut loopbar.

## Marke
- Gelb `#F5B800` (Baumaschinen-Gelb), Schwarz `#111`, Weiß.
- Schriften: **Anton** (Headlines/Slams), **Inter** (Text/Typing).
- Claim: „Ihr Projekt. Unser Handwerk.“ / „Wir schaffen die Grundlage.“
- Leistungen: Erdarbeiten, Fundamente (auch für Wärmepumpen), Pflaster & Außenanlagen, Garten- & Landschaftsbau. Region: Augsburg & Umgebung. Web: havvambau.de
- Ein echtes Logo-File gibt es noch nicht im Repo. Bisher ist es ein Platzhalter: ein „H“ aus zwei gelben Pfeilern und einem schwarzen Balken.
