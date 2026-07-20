---
name: genlens-editorial-ops
description: Coordinate Genny's source scout, content curator, tool curator, role radar, and product lab before publishing a GenLens digest.
required_tools:
  - terminal
---

# GenLens Editorial Ops

Use this skill for digest quality failures, sparse briefings, duplicate articles, stale sources, weak content, or when Jonathan asks why the curator agents are not acting together.

## Required Command

Run the coordinating pipeline:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_editorial_ops.py \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12
```

To publish only after it passes the gate:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_editorial_ops.py \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12 \
  --send
```

## Agents In Harmony

- Source Scout: validates source health and classifies sources.
- Content Curator: applies recency, dedupe, relevance, and source-quality gates.
- Tool Curator: extracts accepted tool mentions into the review queue.
- Role Radar: converts accepted market signals into roles and proof builds.
- Product Lab: turns repeated gaps into GenLens product opportunities.

## Publish Rule

If the preflight gate fails, do not pretend the brief is good. Report the source/content gap and show `/root/.hermes/profiles/genny/state/editorial_preflight.md`.
