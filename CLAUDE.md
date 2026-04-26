# GenLens — Claude Code Agent Instructions

These are standing instructions for any Claude Code session in this repo.
Read this file before starting work.

---

## PROJECT CONTEXT

GenLens is daily intelligence for creative technologists working in
AI-accelerated visual production (product photography, filmmaking,
digital humans). It scrapes 130+ sources across 10 dimensions and
synthesizes daily briefings.

Stack: Next.js 14 (App Router), Neon Postgres, NextAuth v5, Resend,
Anthropic Claude API (`claude-sonnet-4-20250514`), Tailwind, Vercel.

See `GENLENS_CLAUDE_CODE_BRIEF.md` for full architecture and
`GENLENS_FOR_CREATIVES_COMPLETE_SPEC.md` for product spec.

---

## CURRENT FOCUS

Phase 2 in progress. The two new product surfaces being built are:

1. **GenLens Score** — single 0-100 number per tool / workflow / template
   that bundles speed gain, cost gain, quality, and adoption velocity.
   Becomes the citable noun. Like a credit score for "should I adopt this?"

2. **GenLens Index** — published weekly, like the S&P 500 but for AI
   creative tools. "This week's biggest movers." Citable in industry press.

Both are downstream of the existing scraper + signals table. They are
synthesis + ranking layers on top of data we already collect (Dimensions
5 and 10 in the spec: Cost & Time Delta, and Benchmark + Leaderboard).

Do **not** build Arbitrage, Rate Card Generator, Score Decay, Personal
Arbitrage Alerts, or the share-card growth loop yet. These are deferred.
See `BACKLOG.md` for the full list and revisit conditions.

---

## GENLENS SCORE — DESIGN PRINCIPLES

The Score is a 0-100 composite. Inputs come from the `signals` table
(`time_saved_hours`, `cost_saved_dollars`, `quality_improvement_percent`,
`trending_score`).

Score should reflect:
- **Speed gain** — how much time the tool saves vs. baseline
- **Cost gain** — how much money it saves vs. baseline
- **Quality delta** — output quality improvement
- **Adoption velocity** — how fast creators are adopting it (trending_score)

Two scoring entities:
- `tool_scores` — per tool (KeyShot, Runway, ElevenLabs, etc.)
- `template_scores` — per workflow template

Score is recomputed nightly. Store score history so we can show movers.

Score must be:
- Defensible (every input traceable to a signal_id)
- Stable (one bad scrape shouldn't move it 20 points)
- Comparable across tools in the same vertical

---

## GENLENS INDEX — DESIGN PRINCIPLES

The Index is a weekly snapshot, published every Monday.

Three indices, one per vertical:
- **GLI-PP** (Product Photography Index)
- **GLI-FM** (Filmmaking Index)
- **GLI-DH** (Digital Humans Index)

Each index publishes:
- Top 10 tools by current Score
- Biggest movers (week-over-week Score change, up and down)
- New entries (tools that crossed a Score threshold this week)
- Notable exits (tools that dropped below threshold)

Output formats:
- Public web page (`/index` or `/index/[vertical]`)
- Email section in the weekly briefing
- JSON API endpoint (for future syndication)

Index page must be screenshot-friendly. People will share these.

---

## CODING CONVENTIONS

(Inherited from the original brief, restated here for the agent.)

1. Use `@neondatabase/serverless` for database (not pg or prisma)
2. Use `next-auth@5` (v5 beta for App Router compatibility)
3. All API routes use Next.js App Router format (`route.ts`)
4. Scraper uses `Promise.allSettled` (don't fail all if one source fails)
5. Rate limit: max 5 concurrent scrapes, 1 second delay between batches
6. Content hash for dedup: SHA-256 of `title + source_url`
7. Taxonomy classification: Claude API call per batch of 10 signals
8. Cache scraped data in Neon (2-hour TTL for live feeds, 24-hour for blogs)
9. All dates in UTC, convert to user timezone on display
10. No em dashes in any output text, replace with commas or colons
11. Mobile-first responsive design
12. Dark mode by default
13. Every component has loading + empty + error states

---

## DESIGN TOKENS

```css
:root {
  --bg: #0e0e0e;
  --bg2: #161616;
  --bg3: #1e1e1e;
  --border: #2a2a2a;
  --text: #e8e4dc;
  --text2: #9a9690;
  --accent: #c8f04a;      /* lime, builder/technical signals */
  --accent2: #f0a83c;     /* amber, creative/trend signals */
  --red: #f04a4a;
  --blue: #5ab4f0;
  --purple: #b07af0;
  --font-mono: 'IBM Plex Mono', monospace;
  --font-serif: 'Lora', serif;
  --font-display: 'Playfair Display', serif;
}
```

Vertical accents: Product Photography lime, Filmmaking amber, Digital
Humans purple.

---

## OUTPUT RULES (for any Claude-generated text in the product)

- No em dashes anywhere. Use commas or colons.
- No fabricated stats. Only use numbers traceable to a signal_id.
- Frame for creatives, not retailers. Warm, expert, direct.
- Cite source tool/company by name (e.g., "Runway dropped X today").
- Confidence labels in summaries: (high), (medium), (low) per claim.

---

## BACKLOG & GAPS WORKFLOW

When working on adjacent code, check both `BACKLOG.md` and `GAPS.md`.

**BACKLOG.md** — features we've deliberately shelved (Score Arbitrage,
Rate Card, etc.) with explicit revisit triggers.

**GAPS.md** — critical gaps that block full product launch, organized by
category (critical, UX, data quality, future surfaces). Includes a
"minimum viable checklist" for Phase 2 launch.

If you notice that a deferred item's revisit condition is now met, or a
gap's blocker condition is satisfied, surface it in your response.
Do not start building items from either file unless explicitly asked.

---

## WHEN UNSURE

If a feature decision is ambiguous, prefer:
- Defensibility over cleverness
- Stability over freshness
- Citable artifacts over private dashboards
- Shipping Score + Index well, not adding a fourth surface

Ask before adding new dependencies or new top-level routes.
