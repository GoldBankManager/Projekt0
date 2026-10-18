---
name: product-photoshoot
description: Finished product / car stills — studio packshots, lifestyle scenes, hero banners, carousels, ad packs, conceptual CGI-style shots, restyles — with one consistent product identity across the set, run on fal.ai (Nano Banana Pro). Use for "packshot", "product photos", "car photos for the dealer listing", "hero banner", "carousel". Not for video or thumbnails.
---

# Product photoshoot (fal.ai)

Load `video-prompting` first. Model: `fal-ai/nano-banana-pro` (+`/edit` with product refs), 2K,
one call per variant. Refinement: same model `/edit` with the latest result of that index.

## Modes (pick by deliverable; platform beats environment)

product-shot · lifestyle-scene · closeup-with-person · pinterest-pin · hero-banner ·
social-carousel (3–10 slides) · ad-creative-pack · virtual-model-tryout · conceptual-product ·
restyle (keep subject + composition, change look).

## Intake

Parse first; ask only blocking gaps (product description/image, style, count, ratio) in ONE question.
"full auto" / "just do it" → 3 variants, clean studio, 1:1, product colors, no questions.

## Prompt contract

- English, named sections from the mode; exact on-image strings verbatim.
- Product is the hero in every image: exact shape, markings, colors, materials from the reference.
- Lighting/palette/composition/surface described concretely — never photographer, magazine,
  retailer or competitor names in prompts.
- Append negatives: `no extra text, no watermark, no distorted logos, no extra products, no warped geometry`.
- Variants differ materially (composition, scene, hook), not just seed.

## One identity across the set

Supplied product photo → use it as the reference for every image. Text-only product → render
index 0 first, inspect, then use that result as the reference for all others.

## Refinement

Only for an observed defect or a specific user correction; ≤2 refinements per index; change only the
named defect, keep everything else. Deliver final images + one sentence (mode, look, ratio).
