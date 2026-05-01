# GenLens — Claude Code Agent Instructions

These are standing instructions for any Claude Code session in this repo.
Read this file before starting work.

---

## PROJECT CONTEXT

GenLens is daily intelligence for creative technologists working in
AI-accelerated visual production. Three active verticals, three deferred.

Stack: Next.js 14 (App Router), Neon Postgres, NextAuth v5, Resend,
Anthropic Claude API (`claude-haiku-4-5-20251001` for the classifier,
`claude-sonnet-4-6` for the Growth Agent and Index editorial),
Tailwind, Vercel. Models are imported from `lib/constants.ts` —
update there, not in scattered string literals.

**Active verticals:**
1. Product Photography (hard goods, soft goods, lifestyle)
2. Commercial Filmmaking (VFX, color grading, motion)
3. Digital Humans (synthetic actors, voice, animation)

**Deferred verticals (see BACKLOG.md):**
4. Music Production / Audio
5. AI-Accelerated Design / Motion Graphics
6. Fashion / Apparel / Textile Design

See `GENLENS_CLAUDE_CODE_BRIEF.md` for full architecture,
`GENLENS_FOR_CREATIVES_COMPLETE_SPEC.md` for product spec,
and `TOOLS_MANIFEST.md` for canonical list of 130+ tools.

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

## OPT-OUT & CREATOR PRIVACY RULES

The leaderboard and creator pages are public. This requires strict opt-out handling.

**Leaderboard opt-out levels:**
- `opt_out_level = NULL` (default): creator visible on leaderboard, signals attributed
- `opt_out_level = 'leaderboard'`: creator visible in signals & templates, NOT ranked
- `opt_out_level = 'full'`: creator removed entirely, historical signals anonymized

**On every public creator page:**
- Add footer link: "Not you? Claim or remove this profile"
- If `opt_out_level = 'full'`, render "Profile removed at creator's request" instead of 404
- If claimed by creator (FK user_id set), show "Claimed by [creator name]" + edit link

**Processing SLA:**
- Full removal: within 24 hours (email verification required)
- Leaderboard suppression: immediate (no verification)
- Claims: immediate (require email match)

**Do NOT:**
- Display a creator on the leaderboard if `opt_out_level` is set
- Attribute signals to a creator if `opt_out_level = 'full'`
- Create new creator entries from scraped data without consent (only ingest data; only show publicly if opt-in)

---

## BACKLOG & GAPS WORKFLOW

When working on adjacent code, check both `BACKLOG.md` and `GAPS.md`.

**BACKLOG.md** — features we've deliberately shelved (Score Arbitrage,
Rate Card, etc.) + three deferred verticals (Music, Motion Graphics, Fashion).
Explicit revisit triggers for each.

**GAPS.md** — critical gaps that block full product launch, organized by
category (critical, UX, data quality, future surfaces). Includes a
"minimum viable checklist" for Phase 2 launch. **Opt-out mechanism is gap #0.**

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

---

## CROSS-DEVICE SYNC PROTOCOL

GenLens development happens across multiple devices (desktop, laptop, phone).
This protocol ensures continuity and clarity across sessions.

### Session Startup (All Devices)

1. **Fetch latest changes**
   ```bash
   git fetch origin
   git pull origin claude/check-project-status-RRBad
   ```

2. **Read NEXT_STEPS.md**
   - Current blockers
   - Next actions in order
   - Gap status
   - Open questions

3. **Check .env.local exists** (if needed for this session)
   - Contains DATABASE_URL, ANTHROPIC_API_KEY, etc.
   - Not in repo (git-ignored for security)
   - Create if missing: `touch .env.local` + ask user

### Session Work

- Commit frequently with clear messages
- Push after each logical unit (feature, bug fix, schema change)
- Update code, not NEXT_STEPS.md (let the next session do that)

### Session Shutdown (Before Closing)

1. **Final commit + push**
   ```bash
   git add -A
   git commit -m "..."
   git push -u origin claude/check-project-status-RRBad
   ```

2. **Update NEXT_STEPS.md** with:
   - What was completed (checked off items)
   - New blockers discovered
   - Updated gap status
   - Next actions (in priority order)
   - New questions or decisions needed

3. **Commit NEXT_STEPS.md**
   ```bash
   git add NEXT_STEPS.md
   git commit -m "docs: update NEXT_STEPS.md — session complete"
   git push
   ```

### Merge & Promote

Once feature is tested + verified:
```bash
git push origin claude/check-project-status-RRBad
# Then merge PR #1 on GitHub to main
```

After merge, update `## CURRENT FOCUS` in CLAUDE.md and create a new `claude/next-feature` branch for the next item.
