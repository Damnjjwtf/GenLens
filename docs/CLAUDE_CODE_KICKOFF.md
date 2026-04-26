# Claude Code Kickoff — Ship GenLens Score + Index

Paste this into Claude Code at the repo root. It assumes `CLAUDE.md` and
`BACKLOG.md` are already in place.

---

## Prompt

```
Read CLAUDE.md, BACKLOG.md, and GAPS.md before doing anything else.

Special note on GAPS.md: Review the "CRITICAL GAPS (block core features)"
section. These five gaps must be addressed in parallel with Score + Index:

1. User Workflow Logging System
2. Baseline Workflows Table
3. Tool Taxonomy & Master Tool List
4. Cross-Vertical Signal Handling
5. Semantic Deduplication

You can scope them into this session or defer some to Week 2. But do not
ship Score/Index without at least tackling gaps #2 and #3 (baselines and
tool taxonomy), as Score formula depends on them.

# Part 1: GenLens Score

Build in this order:

1. Migration: add a `scores` table to lib/db/schema.sql with columns:
   id, subject (text), subject_type (text: tool|workflow|template),
   vertical (text), score (int 0-100), components (jsonb),
   delta_30d (int, nullable), computed_at (timestamptz), and a unique
   index on (subject, subject_type, computed_at).

2. lib/score/compute.ts — pure function computeScore(inputs) that
   returns the score object shape from CLAUDE.md. Handle nulls by
   re-normalizing weights across present components.

3. lib/score/queries.ts — fetch the inputs for a given subject from
   the signals table. Use the existing Neon client from lib/db.ts.

4. lib/score/percentiles.ts — compute vertical_p95 for time_saved_hours
   and cost_saved_dollars. Cache results per vertical for 1 hour.

5. app/api/score/[subject]/route.ts — GET endpoint. Query params:
   subject_type, vertical. Computes score on demand, persists to
   `scores` table, returns the JSON shape from CLAUDE.md.

6. components/ScoreBadge.tsx — visual: large number (Lora, --accent
   for high, --accent2 for medium, --text2 for low), delta arrow
   underneath if delta_30d is non-null. Loading, empty, error states.

7. Add a Score column to TemplateLeaderboard.tsx and (when it exists)
   a tools index page.

# Part 2: GenLens Index

Build after Score is working end-to-end:

1. lib/index/compute.ts — function computeWeeklyIndex(weekStart) that
   diffs scores across the previous 7 days, returns top 5 risers, top 5
   fallers, new entrants. Pulls from the `scores` table only.

2. lib/index/synthesize.ts — Claude API call (claude-sonnet-4-20250514)
   that takes the diff result and produces narrative paragraphs per
   vertical plus a quotable one-liner per mover. System prompt must
   require citing source signals. No vibes-based explanations.

3. Migration: add an `index_issues` table — id, slug (YYYY-WW),
   week_start, week_end, payload (jsonb), published_at.

4. app/api/cron/weekly-index/route.ts — Vercel Cron, Mondays 09:00 UTC.
   Computes index, synthesizes, persists to index_issues, sends email
   to all subscribers via Resend.

5. app/index/page.tsx — public list of all past issues, indexable.
6. app/index/[slug]/page.tsx — public issue page, indexable. Each mover
   gets an anchor like #keyshot so vendors can link to their entry.
7. app/api/index/latest/route.ts — JSON API returning latest issue
   payload. CORS open. This is for tool vendors to embed their score.

8. Update vercel.json with the new cron schedule.

# Acceptance criteria

- `npm run build` passes
- `npx tsc --noEmit` passes
- Score endpoint returns valid JSON for at least one tool with real
  data from the signals table
- Index endpoint returns the latest issue (even if empty on first run)
- Public index page renders correctly in dark mode on mobile

# Constraints (from CLAUDE.md, repeating because they matter)

- No em dashes anywhere in user-facing text
- All confidence claims labeled (high), (medium), (low)
- Score must be deterministic (same inputs = same score)
- Never fabricate component values; missing → null + re-normalize
- Use Promise.allSettled for any parallel work
- Mobile-first responsive; loading/empty/error states on every component

When you finish each numbered step, run the build and type-check before
moving to the next. If something is ambiguous, check CLAUDE.md first,
then ask before guessing.
```

---

## Notes for Jonathan

- This prompt is conservative — it ships Score fully before starting
  Index, so if you run out of session you have one working feature
  rather than two half-features.
- The `scores` table with timestamps is what enables 30-day deltas and
  the Index diff. Don't skip it even if it feels like overkill on day 1.
- The public, indexable Index pages are a deliberate distribution play.
  Vendors will link to "their entry" → backlinks → SEO → category authority.
