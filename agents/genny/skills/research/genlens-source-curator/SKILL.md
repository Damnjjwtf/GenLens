---
name: genlens-source-curator
description: Curate, audit, add, retire, and quality-check GenLens sources for Genny's daily intelligence briefings.
required_tools:
  - terminal
---

# GenLens Source Curator

Use this skill when Jonathan asks to improve Genny's sources, add a tool/source, make the brief more current, audit weak coverage, or stop product-homepage/link-dump behavior.

## Source Standard

Only promote a source into daily briefing flow when it can produce current, source-backed signals:

- Tool releases, model releases, SDK/API changes, pricing/licensing changes, rights/compliance changes.
- Production workflow shifts, pipeline case studies, benchmark results, time/cost deltas.
- Credible trade/editorial coverage from publications that regularly cover creative production.
- GitHub releases/Atom feeds for open-source tools where release notes are production-relevant.
- Curated search/news feeds only when official feeds do not exist; keep them tightly scoped to a tool plus production terms.

Do not promote:

- Product homepages, pricing pages, generic feature pages, category pages, stale listicles, SEO "best tools" posts, generic how-to posts.
- Vendor pages without a feed unless they are used as watch-only verification sources.
- Feeds that repeatedly produce no publishable leads.

## Workflow

1. Run the fast audit:

```bash
/root/.hermes/profiles/genny/scripts/genlens_audit_sources.py \
  --limit 8 \
  --out /root/.hermes/profiles/genny/state/source_audit.md
```

2. Identify `needs-replacement` sources, `quiet-feed` sources, and verticals with no qualified feed signals.

3. For a new source, verify it before adding:

```bash
curl -L -s -o /tmp/genlens_feed_test.out -w "%{http_code}" --max-time 10 "FEED_URL"
file -b /tmp/genlens_feed_test.out
```

Valid RSS/Atom should return HTTP 200 and XML/Atom/RSS content. If it returns HTML, keep it manual/watch-only or use a tightly scoped news-search feed.

4. Edit `/root/.hermes/profiles/genny/data/genny_sources.json`.

5. Re-run the audit and compose a preview:

```bash
/root/.hermes/profiles/genny/scripts/genlens_audit_sources.py \
  --limit 8 \
  --out /root/.hermes/profiles/genny/state/source_audit.md

/root/.hermes/profiles/genny/scripts/genlens_compose_brief.py \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12 \
  --out /root/.hermes/profiles/genny/state/latest_brief.md
```

6. Report what changed:

- Sources added.
- Sources demoted to watch-only.
- Quiet feeds that are valid but produced no current signal.
- Sources marked `needs-replacement`.
- Vertical coverage gaps that remain.

## Current Tool Priorities

Keep these on deck as high-priority source targets:

- Figma Weave: AI media generation, product mockups, brand/content workflow, design/motion workflow.
- ComfyUI: GitHub releases, workflow engine changes, node/model support, production automation, video pipelines.
- fal: image/video model hosting, latency/cost, model releases, inference infrastructure, production deployment stories.

## Rule

If the source pool is weak, say so. Do not pad the brief. Better to report a coverage gap than ship a fake-looking briefing.
