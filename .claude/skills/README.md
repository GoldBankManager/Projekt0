# Video-Skills (Higgsfield-Wissen, ausgeführt über fal.ai)

Die Arbeitsabläufe und Prompt-Regeln stammen aus den Higgsfield-Workflows. Ausgeführt wird alles mit
deinem eigenen fal.ai-Key (`FAL_KEY`), ohne Higgsfield-Credits. Claude Code lädt diese Skills in
diesem Repo automatisch.

| Skill | Wofür | Higgsfield-Vorlage |
|---|---|---|
| `video-prompting` | Grundregeln für jeden Lauf: Kosten-Freigabe, welche Referenz was bestimmt, Prompt-Aufbau, typische Fehler, Checkliste | Katana + Ad Multiplier |
| `car-swap` | Auto/Produkt/Objekt im fertigen Edit tauschen; Schnitte, Kamera und Ton bleiben | Ad Multiplier (Edit) |
| `reference-remix` | Neues Edit im Stil eines Vorbild-Edits für dein Auto/Produkt | Katana |
| `ugc-video` | Creator-Videos: Review, Unboxing, Try-on, Tutorial, Produkt mit Voiceover | UGC Video |
| `faceless-video` | Erzählte Kanal-Videos (Explainer, History, Kids, Story) | Faceless Video |
| `thumbnail` | YouTube-/Reel-Cover mit 16 Klick-Konzepten | Thumbnail Generation |
| `character-sheet` | Gleichbleibende Charaktere über mehrere Shots | Character Sheet |
| `product-photoshoot` | Packshots, Lifestyle-Bilder, Banner, Karussells | Product Photoshoot |
| `video-finish` | Zusammenschneiden, Ton, Untertitel, Upscale ohne Plastik-Look, Endkontrolle | Video Montage + Ad Multiplier |

**Regel Nr. 1 in jedem Skill:** Claude startet keinen kostenpflichtigen fal.ai-Job ohne dein
ausdrückliches Go für genau diesen Job und Preis.

Scripts im Repo: `kling_swap.py` (Car Swap mit Kling O3 Edit), `car_swap.py` (Seedance).
