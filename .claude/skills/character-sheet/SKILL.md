---
name: character-sheet
description: Build consistent character sheets / model sheets / turnarounds / expression sheets with a slot-based prompt and an anti-AI "unretouched" realism engine; optionally render on fal.ai. Use for "character sheet", "model sheet", "turnaround", "consistent character", or before any video that needs the same person/character across shots.
---

# Character sheet

Load `video-prompting` before rendering. Default = output the prompt only; render on explicit ask
(`fal-ai/nano-banana-pro` or `bytedance/seedream/v5/pro/text-to-image`, 16:9 for multi-view sheets).

## Principles

1. Photoreal = anti-retouch: visible pores, natural asymmetry, matte skin, no beauty filter.
2. Original characters only — no real person's likeness, no copyrighted characters.
3. Adults read as adults: defined jaw/cheekbones, mature proportions, no babyface.
4. Iterations carry every established detail forward unchanged; change only what is asked.

## Slot order (one comma-separated paragraph)

```
[COMPOSITION], identical original [subject] on all views, pure white seamless studio background,
professional character sheet presentation, [IDENTITY age + skin], [FACE shape, jaw, cheekbones,
nose, lips], [EYES + "naturally muted catchlights, no oversized specular glare in the iris"],
[EYEBROWS], [HAIR color, length, style, finish, parting], [REALISM MODULE], [BODY],
[WARDROBE top → layers → bottom → belt → shoes → jewelry → bag/"no bag"], [LIGHTING], [QUALITY TAIL],
[NEGATIVE TAIL]
```

## Compositions

- split-screen (default): left full-body standing head-to-toe, right tight chest-up close-up.
- turnaround: front, 3/4, side, back in a row.
- expression sheet: one full body + grid of head-and-shoulders expressions.
- outfit variations: same character in N outfits.

## Realism module (photoreal-unretouched)

`visible fine skin texture with natural pores, fine lines, subtle asymmetries, natural visible makeup with slightly uneven blending, faint natural blush, slight natural sheen rather than glossy finish, no digital smoothing, no beauty filter, no AI-airbrushed look, matte-to-natural complexion`
Lighting: `soft diffused studio lighting without harsh reflections`.
Quality tail: `natural anatomy, high-end but unretouched commercial photography style, cinematic realism, 4K, sharp focus on skin texture detail`.
Other presets: editorial-polished, anime-2d, 3d-stylized, game-concept (swap render/lighting/tail).

## Negative tail

`no text, no watermark, no logos, no frame borders` + for split-screen: `single subject only, exactly one person, no duplicate figures, no mannequin, no props, empty seamless studio, left panel standing full-body not cropped not sitting, right panel tight close-up not full body` + adults: `no babyface` + photoreal: `no beauty filter, no airbrushing, no plastic skin`.
