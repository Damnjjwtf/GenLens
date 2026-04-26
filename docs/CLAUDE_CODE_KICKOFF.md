# GenLens — Claude Code Kickoff
## Paste this at the start of every Claude Code session.

---

## What You Are Building

**GenLens for Creatives** — a full-stack SaaS that delivers daily AI-synthesized intelligence to creative technologists working in AI-accelerated visual production.

**Domain:** `genlens.app`
**Stack:** Next.js 14 (App Router), Neon Postgres, NextAuth v5, Resend, Anthropic Claude API (`claude-sonnet-4-20250514`), Tailwind CSS, Vercel Cron
**Design system:** Dark mode only. IBM Plex Mono + Lora + Playfair Display. Accent: #c8f04a (lime). Secondary: #f0a83c (amber). Background: #0e0e0e.

---

## What Already Exists (Phase 1 — DONE)

- Public landing page at `/`
- Invite-code auth (NextAuth v5, magic links via Resend)
- Dark mode, design system, fonts, colors
- User settings page
- Neon Postgres schema (migrations 001–003)
- Editorial UI shell

## What Was Built This Session (drop into repo, commit first)

These files exist and are ready to commit:

```
lib/migrations/004_growth_agent.sql   ← run this migration before anything else
lib/agent/growth-agent.ts             ← core agent pipeline
app/api/cron/growth-agent/route.ts    ← Vercel Cron endpoint
app/api/agent/queue/route.ts          ← queue CRUD API
app/admin/growth-agent/page.tsx       ← admin review UI
app/tools/[slug]/page.tsx             ← public tool directory pages
app/signals/[id]/page.tsx             ← public signal pages
scripts/seed-tools.ts                 ← tool manifest seed (22 tools)
vercel.json                           ← updated cron schedule
GROWTH_AGENT.md                       ← README for agent system
```

**Commit command:**
```bash
git add lib/migrations/004_growth_agent.sql lib/agent/growth-agent.ts \
  app/api/cron/growth-agent/route.ts app/api/agent/queue/route.ts \
  app/admin/growth-agent/page.tsx app/tools/[slug]/page.tsx \
  app/signals/[id]/page.tsx scripts/seed-tools.ts vercel.json GROWTH_AGENT.md
git commit -m "feat: growth agent, tool directory, signal pages, migration 004"
```

---

## FIRST TASK: Find and Replace Domain

Before touching anything else — find every instance of `genlens.io` in the codebase and replace with `genlens.app`. This includes:

- All hardcoded URLs in components
- OG/meta tags
- API routes
- The seed script (`scripts/seed-tools.ts`)
- Any README or doc files
- `GROWTH_AGENT.md`
- `vercel.json` if present

```bash
grep -r "genlens.io" . --include="*.ts" --include="*.tsx" --include="*.md" --include="*.json"
```

Review the list, then replace. Do not do a blind global replace — check each file.

---

## SECOND TASK: Run Migration + Seed

```bash
# Run migration 004
psql $DATABASE_URL -f lib/migrations/004_growth_agent.sql

# Seed tool directory (22 tools)
npx tsx scripts/seed-tools.ts
```

Verify the tools table populated:
```sql
SELECT canonical_name, slug, verticals, affiliate_url FROM tools ORDER BY slug;
```

---

## THIRD TASK: Build These (in order)

### 1. Discord Webhook Posting (half day)

**Why first:** Lowest friction social posting. No OAuth. No token refresh. Ship it today.

Create `app/api/agent/post/discord/route.ts`:

```typescript
// POST — takes an approved queue item ID, posts to Discord webhook
// Routes to correct channel based on item.vertical + item.output_type

// Env vars needed:
// DISCORD_WEBHOOK_GENERAL
// DISCORD_WEBHOOK_PRODUCT_PHOTOGRAPHY
// DISCORD_WEBHOOK_FILMMAKING
// DISCORD_WEBHOOK_DIGITAL_HUMANS
// DISCORD_WEBHOOK_TOOL_RELEASES      ← signal_type: tool_release
// DISCORD_WEBHOOK_LEGAL_ALERTS       ← dimension: 6
// DISCORD_WEBHOOK_HIRING             ← dimension: 7
// DISCORD_WEBHOOK_TEMPLATES          ← output_type: template_geo

// Discord message format:
// - Title as bold **text**
// - Summary paragraph
// - Delta chips as inline code `−6h` `−$1,200`
// - Source link
// - "Full briefing → genlens.app" footer
// - Max 2000 chars (Discord limit)
```

Add a "Post to Discord" button in `app/admin/growth-agent/page.tsx` that appears after a queue item is approved.

Also create this DB migration:

```sql
-- migration 005: platform tokens + post results
CREATE TABLE platform_tokens (
  id SERIAL PRIMARY KEY,
  platform VARCHAR NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  token_expires_at TIMESTAMP WITH TIME ZONE,
  account_id TEXT,
  account_name TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE post_results (
  id SERIAL PRIMARY KEY,
  queue_item_id INT REFERENCES growth_agent_queue(id),
  platform VARCHAR NOT NULL,
  platform_post_id TEXT,
  platform_post_url TEXT,
  status VARCHAR DEFAULT 'posted',
  impressions INT DEFAULT 0,
  engagements INT DEFAULT 0,
  clicks INT DEFAULT 0,
  posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  error_message TEXT
);
```

### 2. OG Image Generation for Signal Pages (half day)

Create `app/api/og/signal/[id]/route.ts` using `@vercel/og`:

```typescript
// Generates a social sharing image per signal
// Design: dark background (#0e0e0e), lime accent (#c8f04a)
// Layout:
//   - Top left: GENLENS wordmark + vertical badge
//   - Center: signal headline (large, Playfair Display or serif)
//   - Bottom: delta chips (−6h, −$1,200) + dimension label
//   - Bottom right: genlens.app
// Size: 1200×630 (standard OG)
// Install: npm install @vercel/og
```

### 3. Public Comparison Pages (1 day)

Create `app/compare/[slug]/page.tsx`:

- Public, no auth
- GEO-optimized — same pattern as `app/tools/[slug]/page.tsx`
- FAQ JSON-LD schema from `tool_comparisons.faq_schema`
- Shows: summary, Q&A blocks, both tool cards side by side with affiliate links
- CTA: "Get early access →"
- Metadata from `tool_comparisons` table

### 4. Weekly Index Archive Pages (1 day)

Create `app/index/[date]/page.tsx`:

- Public, no auth
- Shows GLI-PP, GLI-FM, GLI-DH index for that week
- Top 10 tools per vertical, biggest movers, new entries, exits
- Screenshot-shareable layout (Bloomberg Terminal aesthetic)
- Published every Monday at 8am via the Cron job

### 5. GAPS #0 — Creator Opt-Out (1–2 days, LEGAL BLOCKER)

Cannot launch the leaderboard publicly without this. Build before any creator data goes live.

```sql
ALTER TABLE leaderboard_creators
  ADD COLUMN IF NOT EXISTS opt_out_level VARCHAR DEFAULT NULL;
  -- NULL = no opt-out | 'leaderboard' = suppress from leaderboard | 'full' = remove all data
```

- Add "Claim or remove this profile" link to every public creator page footer
- Route to `/creators/opt-out?handle=[handle]`
- `opt_out_level = 'leaderboard'`: hide from leaderboard immediately, keep data
- `opt_out_level = 'full'`: delete all data within 24h, render "Profile removed" not 404
- Send confirmation email via Resend on opt-out

### 6. X + LinkedIn via Buffer (when above is done)

Buffer handles OAuth, token refresh, and scheduling. We connect via Buffer's API rather than directly to X/LinkedIn APIs.

- Buffer Publishing API: `POST https://api.bufferapp.com/1/updates/create.json`
- Requires: `BUFFER_ACCESS_TOKEN`, `BUFFER_PROFILE_IDS` (one per platform)
- In admin panel: after approving a social item, show "Send to Buffer" button
- Buffer queues it for the scheduled time already set in `growth_agent_queue.scheduled_for`

---

## Environment Variables Needed (add to .env.local)

```bash
# Existing
DATABASE_URL=
NEXTAUTH_SECRET=
NEXTAUTH_URL=https://genlens.app
ANTHROPIC_API_KEY=
RESEND_API_KEY=
CRON_SECRET=

# New — Growth Agent
# (no new vars needed beyond CRON_SECRET above)

# New — Discord
DISCORD_WEBHOOK_GENERAL=
DISCORD_WEBHOOK_PRODUCT_PHOTOGRAPHY=
DISCORD_WEBHOOK_FILMMAKING=
DISCORD_WEBHOOK_DIGITAL_HUMANS=
DISCORD_WEBHOOK_TOOL_RELEASES=
DISCORD_WEBHOOK_LEGAL_ALERTS=
DISCORD_WEBHOOK_HIRING=
DISCORD_WEBHOOK_TEMPLATES=

# New — Buffer (when ready)
BUFFER_ACCESS_TOKEN=
BUFFER_PROFILE_ID_X=
BUFFER_PROFILE_ID_LINKEDIN=
BUFFER_PROFILE_ID_REDDIT=
```

---

## Architecture Principles (never violate these)

1. **Nothing publishes without human approval.** Every agent output lands in `growth_agent_queue` with `status=draft`. Human approves. Then and only then does it publish.

2. **Tool directory is public.** `genlens.app/tools` has no auth gate. It is a growth surface, not a subscriber feature. Do not add auth middleware to `/tools/*`, `/signals/*`, `/compare/*`, or `/index/*`.

3. **Score number is public. Score breakdown is Pro.** Vendors need to see the number to backlink. The signal log driving it is subscriber-only.

4. **The domain is `genlens.app`.** Every URL, OG tag, canonical link, and sitemap entry uses this. No `genlens.io` anywhere.

5. **Onboarding copy:** "Early access beta, free to start." Not "invite-only."

6. **Discord server channels exist for each vertical + signal type.** Route posts to the right channel, not just #general.

---

## What NOT to Build Yet

- Brand character / synthetic editorial persona (deferred: after Score + Index publishing)
- GenLens Arbitrage (deferred: after Score live + 100 users logging workflows)
- Rate Card Generator (deferred: after Arbitrage)
- Score Decay (deferred: Score live 3+ months)
- Reddit direct API (use Buffer instead)
- Direct X API (use Buffer instead)
- Direct LinkedIn API (use Buffer instead)
- r/GenerativeArtDirector content automation (community is new, seed manually first)

---

## Affiliate Programs — Apply for These

As you build the tool pages, these programs need real URLs in the seed script. Apply in this order:

1. ElevenLabs — elevenlabs.io (affiliate program exists, ~22%)
2. HeyGen — heygen.com (affiliate program exists, ~25%)
3. Runway — runwayml.com (affiliate program exists, ~20%)
4. Synthesia — synthesia.io (affiliate program exists, ~20%)
5. Figma — figma.com/referral
6. Adobe — adobe.com/affiliates
7. Descript — descript.com/affiliates
8. PhotoRoom — photoroom.com/affiliates
9. Claid AI — claid.ai/affiliates
10. KeyShot — keyshot.com/partners

Replace placeholder `?ref=genlens` URLs in `scripts/seed-tools.ts` with real affiliate URLs as you get them. Re-run the seed script after each update — it upserts.

---

## r/GenerativeArtDirector

A subreddit for the Gen AD professional identity. Owned by GenLens. Content posted there is genuine intelligence, never marketing. The Growth Agent routes appropriate signals there via Buffer.

- Post: weekly Index, major tool signals, legal alerts, hiring signals
- Never post: GenLens product updates, pricing, calls to sign up
- Tone: trade publication posting to an industry group

---

## Key Files Reference

```
lib/db.ts                              Neon client
lib/auth.ts                            NextAuth config
lib/agent/growth-agent.ts              Growth Agent pipeline
lib/migrations/001_*.sql               Core schema
lib/migrations/004_growth_agent.sql    Queue, tools, comparisons, agent_runs
app/page.tsx                           Routes: Landing (public) or Dashboard (auth)
app/admin/growth-agent/page.tsx        Admin review UI
app/tools/[slug]/page.tsx              Public tool pages
app/signals/[id]/page.tsx              Public signal pages
app/api/cron/growth-agent/route.ts     Nightly agent cron
app/api/agent/queue/route.ts           Queue CRUD
scripts/seed-tools.ts                  Tool manifest + affiliate URLs
vercel.json                            Cron schedule
```

---

## If You Get Stuck

- Schema questions: check `lib/migrations/` in order (001 → 004)
- Agent questions: read `GROWTH_AGENT.md` in repo root
- Design questions: IBM Plex Mono for all UI text, Playfair Display for editorial headlines, #c8f04a for primary accent, #0e0e0e background, 0.5px borders everywhere
- Tone questions: "smart friend who's also a working creative" — warm, expert, direct, never corporate
