---
name: genlens-tool-curator
description: Extract, check, and curate tools mentioned by GenLens sources into a review queue before updating the canonical tools manifest.
required_tools:
  - terminal
---

# GenLens Tool Curator

Use this skill when Jonathan asks whether tools appearing in sources should be checked, curated, tracked, added to the manifest, or mapped to verticals.

## Rule

Do not auto-add every mentioned tool. Curate first.

## Gate

- `known`: already exists in `genlens_tools_manifest.md`; update metadata/vertical relevance only if the source shows a new capability, pricing/licensing change, workflow shift, or production use case.
- `review`: appears in source-backed output but is not in the manifest; keep in `tool_candidates.json` until checked.
- `ignore`: generic SaaS, unrelated creator fluff, stale SEO listicles, or no clear AI creative-production workflow impact.
- `promote`: add to the canonical manifest only when it appears in an official release/source, two trusted sources, or one strong production case study with concrete workflow impact.

## Workflow

1. Make sure a current brief exists:

```bash
/root/.hermes/profiles/genny/scripts/genlens_compose_brief.py \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12 \
  --out /root/.hermes/profiles/genny/state/latest_brief.md
```

2. Run the tool curator:

```bash
/root/.hermes/profiles/genny/scripts/genlens_curate_tools.py \
  --brief /root/.hermes/profiles/genny/state/latest_brief.md \
  --out /root/.hermes/profiles/genny/data/tool_candidates.json \
  --markdown /root/.hermes/profiles/genny/state/tool_curator_report.md
```

3. Review `tool_candidates.json` before changing `genlens_tools_manifest.md`.

4. Report:

- Known tools seen.
- New candidates needing review.
- Candidates ignored or demoted.
- Any manifest updates made.

## Priority Tools

Watch these closely:

- Figma Weave / Weavy
- ComfyUI
- fal / fal.ai
- Runway Aleph
- Veo / Sora / Kling / Luma
- V-Ray / Corona / Enscape / Unreal Engine / Blender

## Principle

The tool graph is part of the GenLens product. Sources produce signals; signals update tool knowledge; tool knowledge makes the briefing smarter.
