# GenLens: Session Recap (May 5, 2026)
## Paste this at the start of a new chat to continue where we left off.

---

## What Shipped This Session (May 5, 2026)

**✅ COMPLETED:**

1. **Code Audit & Optimization** (PR #3)
   - Consolidated N+1 queries (3x getAllTools → memoized)
   - Batched sequential INSERTs (300+ queries → 2 operations)
   - Extracted slug utility (7 duplications → 1 function)
   - Single-pass tool grouping

2. **Real Signals to Dashboard**
   - Added timestamps to demo signals
   - Dashboard fetches live signals from scraper (falls back to demo if empty)
   - Displays time/cost deltas, source, relative dates (Today, Xd ago)

3. **GenLens Score Engine** (COMPLETE)
   - `lib/score/compute.ts`: computeScore() + pickBaseline() functions
   - **Formula:** score = (speed × 0.40) + (cost × 0.30) + (quality × 0.20) + (adoption × 0.10)
   - **Components:** Speed (time vs 2h baseline) + Cost ($ vs $150 baseline) + Quality (0-100) + Adoption (trending)
   - Migration 008: `tool_scores` + `tool_score_history` tables
   - Cron job at `/api/cron/score` runs nightly at 2:50 AM UTC
   - Reads signals from last 30 days, groups by (tool, vertical), mirrors max score to tools.current_score

4. **Documentation Updated**
   - GAPS.md: Marked Score + Signals complete, flagged Creator opt-out as CRITICAL blocker

---

## Current State (May 5, 2026)

### What's Live

| Feature | Status | Location |
|---------|--------|----------|
| Tool Taxonomy | ✅ 50+ tools | migration 005, seed scripts |
| Baseline Workflows | ✅ 15 baselines | migration 006 |
| Tool Directory | ✅ Public /tools | app/tools/page.tsx |
| Tool Detail Pages | ✅ Public /tools/[slug] | app/tools/[slug]/page.tsx |
| Dashboard | ✅ Auth-gated /dashboard | app/dashboard.tsx |
| Ticker | ✅ Live signal scroll | components/Ticker.tsx |
| MainFeed | ✅ Real + demo signals | components/MainFeed.tsx |
| Sidebar | ✅ Stats + top tools | components/Sidebar.tsx |
| Score Computation | ✅ Engine complete | lib/score/compute.ts |
| Scraper | ✅ 130+ sources | lib/scraper/orchestrator.ts |
| Real Signals | ✅ Flowing to dashboard | signals table populated by scraper |

### What's NOT Done Yet

| Feature | Blocker? | Effort | Next Actions |
|---------|----------|--------|--------------|
| Creator Opt-Out | CRITICAL | 2-3 days | Add opt_out_level column, claim flow, removal SLA |
| User Workflow Logging | HIGH | 3-4 days | user_workflows table, POST /api/workflows, UI |
| Index Generation | MEDIUM | 1-2 days | Top 10 tools, movers (week-over-week), new entries |
| Score Display on Tools | MEDIUM | 1 day | Wire tool_scores table to /tools pages |
| Leaderboard | CRITICAL | 3-5 days | Blocked by Creator opt-out |

---

## Database State

**Tables created:**
- tools (50+ rows seeded)
- tool_aliases (200+ alias rows)
- baseline_workflows (15 rows)
- signals (populated by scraper, status='classified')
- tool_scores (one per tool, updated nightly by cron)
- tool_score_history (daily snapshots for movers)

**Key columns:**
- signals: tool_ids (INT[]), time_saved_hours, cost_saved_dollars, quality_improvement_percent, trending_score, vertical, dimension
- tools: current_score (mirrored from tool_scores daily)
- tool_scores: (tool_slug, vertical, score, speed_score, cost_score, quality_score, adoption_score, snapshot_date)

---

## Recent PRs

- **#3** — Audit fixes: queries, batching, slug deduplication
- **#5** — Add /start and /end slash commands
- **#6** — Fix Vercel build (lazy-init neon)

---

## Getting Started (Next Session)

**Sign in to test dashboard:**
- URL: genlens-dwd13dhtg-damnjjwtfs-projects.vercel.app
- Click "Sign in" → /auth/invite
- Code: `GENLENS2026`
- You'll see demo signals (or real ones if scraper ran)

**To run scraper:**
```bash
curl -X GET https://genlens-dwd13dhtg-damnjjwtfs-projects.vercel.app/api/cron/scrape \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

**Next Priority:**
1. Creator opt-out (legal blocker for leaderboard)
2. Wire scores to tool pages (display current_score)
3. Index generation (weekly snapshots)
- Dedup engine (SHA-256 now; Claude embeddings + cosine similarity planned — GAPS #5)
- Taxonomy classifier (tags each signal: vertical, dimension, workflow stage, tool names)
- Vercel Cron orchestrator (nightly, parallel, logged)
- Tool Taxonomy / Manifest (130+ canonical tools, aliases → one tool_id)

### Layer 1 — Intelligence Core (private, subscriber value)
- Daily briefing — Claude synthesis across 10 dimensions, per vertical
- Signal feed dashboard — filterable by vertical × dimension
- Email delivery (Resend, screenshot-ready, media product design)
- Workflow templates — indexed, ranked, community-sourced
- Creator leaderboard — ranked by vertical, tool stack, production speed
- Archive — past briefings, searchable (Pro-gated beyond 7 days)

### Layer 2 — Public Intelligence (no auth, growth engine)
- **Tool directory** — `genlens.app/tools` — public, SEO/GEO anchor, affiliate revenue. NOT in subscriber dashboard. Exists to pull strangers in, not serve subscribers.
- **Tool pages** — `genlens.app/tools/[slug]` — per tool: GEO summary, Q&A blocks, FAQ schema, affiliate link, recent signals, Score (when live), comparison links
- **Comparison pages** — `genlens.app/compare/[a]-vs-[b]` — GEO gold. "ElevenLabs vs HeyGen" type queries
- **Signal pages** — `genlens.app/signals/[id]` — shareable URL, freemium hook (action item gated)
- **Weekly Index** — `genlens.app/index/[date]` — GLI-PP, GLI-FM, GLI-DH. Monday 8am, no auth, screenshot-shareable
- **Embeddable Score badge** — vendor embed, auto-updates nightly (needs score dispute mechanism first)

### Layer 3 — Growth Surface
- Growth Agent (see full spec below)
- Social posting agent (X, LinkedIn, Discord — see spec below)
- Public signal URLs with OG cards
- Creator share cards (leaderboard rank, branded)
- Quarterly Hiring Report PDF (B2B lead gen, Dimension 7 signals)

### Layer 4 — Monetization
- Free: 1 vertical, 7-day archive, limited signals
- Pro $19/mo: all 3 verticals, all 10 dimensions, leaderboard, templates, full archive
- Studio $99/mo: multi-user, API, team settings, Slack integration
- Enterprise $499+/mo: white-label, custom sources, priority support
- Affiliate revenue: tool directory links (earns at zero subscribers)

### Layer 5 — Backlog / Deferred
- GenLens Arbitrage (revisit: Score live + 100 users logging workflows)
- Rate Card Generator (revisit: after Arbitrage)
- Score Decay (revisit: Score live 3+ months)
- Brand character / synthetic editorial persona (spec now, build when Score + Index publishing)

---

## Tool Directory — Key Decisions

- **Public, no auth.** Tool directory is a distribution mechanism, not a subscriber feature. Auth-gating kills affiliate revenue, GEO indexing, and the freemium funnel simultaneously.
- **What subscribers get instead:** personalized "tools I'm tracking" view inside the dashboard — filtered signals, compatibility notes, contextual intelligence. Reference vs. intelligence.
- **Partial gate option (medium confidence):** Show Score number publicly (vendors need it for backlinks), but Score breakdown and signal log = Pro feature. This is the right line.
- **Comparison pages and legal brief pages** also public — pure GEO assets.

---

## Growth Agent — Built Files

The Growth Agent system was fully built. Files to drop into repo root:

| File | Purpose |
|---|---|
| `lib/migrations/004_growth_agent.sql` | DB migration — run first. Creates growth_agent_queue, tools, tool_comparisons, agent_runs. Patches signals table. |
| `lib/agent/growth-agent.ts` | Core pipeline. Reads signals → calls Claude → writes to queue. Never auto-publishes. |
| `app/api/cron/growth-agent/route.ts` | Vercel Cron endpoint + admin manual trigger |
| `app/api/agent/queue/route.ts` | Queue CRUD — approve, reject, edit, publish |
| `app/admin/growth-agent/page.tsx` | Admin review UI — split pane, inline edit, approve/reject |
| `app/tools/[slug]/page.tsx` | Public tool directory pages (GEO + affiliate) |
| `app/signals/[id]/page.tsx` | Public signal pages (freemium gate) |
| `scripts/seed-tools.ts` | Populates tools table — 22 tools seeded, affiliate URLs as placeholders |
| `vercel.json` | Cron schedule: scraper 2am, agent 3am, Index 7am Monday |
| `GROWTH_AGENT.md` | Full README for the agent system |

**Cron schedule:**
- `0 2 * * *` — scraper
- `0 3 * * *` — growth agent
- `0 7 * * 1` — Monday Index post

**Still to build for Growth Agent:**
- `app/api/og/signal/[id]/route.ts` — OG image per signal (use `@vercel/og`)
- `app/compare/[slug]/page.tsx` — public comparison page
- `app/index/[date]/page.tsx` — weekly Index archive page
- Social API integration for one-click posting (see Social Posting Agent below)
- Quarterly Hiring Report PDF generator

---

## Social Posting Agent — Status + Full Spec

**Current status:** The Growth Agent (built above) produces social drafts and queues them in `growth_agent_queue`. What's NOT built yet is the actual posting layer — the API connections that take an approved draft and push it to X, LinkedIn, and Discord automatically. That is the Social Posting Agent. It's the next thing to build after the Growth Agent queue is working.

### What it does

Takes an approved item from `growth_agent_queue` → posts it to one or more platforms → logs the result → optionally tracks engagement back.

Human is always in the loop for approval. The agent never posts without an approved status on the queue item.

### Platforms + APIs

**X (Twitter)**
- API: Twitter API v2, OAuth 2.0 with PKCE
- Endpoint: `POST /2/tweets`
- Rate limit: 1 tweet per 15 min on free tier; 300/month. Sufficient for daily posts.
- Requires: `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_REFRESH_TOKEN`
- Thread support: chain tweet IDs via `reply.in_reply_to_tweet_id`

**LinkedIn**
- API: LinkedIn Marketing API (Community Management API)
- Endpoint: `POST /rest/posts` (UGC Posts)
- Requires: `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`
- Token expires every 60 days — needs refresh flow or use a scheduler like Buffer as middleware
- Rate limit: 150 requests/day

**Discord**
- API: Discord Webhook (simplest) or Bot API
- Webhook approach: no OAuth, just a webhook URL per channel, POST JSON
- Requires: `DISCORD_WEBHOOK_URL_PP` (product photography channel), `DISCORD_WEBHOOK_URL_FM` (filmmaking), `DISCORD_WEBHOOK_URL_DH` (digital humans), `DISCORD_WEBHOOK_URL_GENERAL`
- No rate limit concerns at GenLens posting volume
- Discord is the lowest friction to ship — start here

**Reddit** (future, not MVP)
- API: Reddit API + OAuth
- Post to: r/filmmaking, r/productphotography, r/digitalhumans, r/AIArt
- Requires careful tone — Reddit punishes promotional posting hard. Only useful if posting genuine signal intelligence, never marketing copy.

### Build plan

**Step 1 (ship now): Discord webhook posting**
One file. No OAuth. Webhook URL per channel. When a `social_discord` item is approved in the queue, POST to the right webhook based on `vertical`. Done in an afternoon.

**Step 2: X posting via API**
Requires OAuth setup + token storage in DB. Add `platform_tokens` table. Post on approve.

**Step 3: LinkedIn posting via API**
Same token pattern. LinkedIn token refresh is the painful part — build a refresh cron or accept manual re-auth every 60 days.

**Step 4: Buffer/Zapier as middleware (optional)**
If direct API maintenance is too heavy, route through Buffer. Approve in admin → Buffer queues it → Buffer posts at scheduled time. Costs ~$15/mo but removes API maintenance burden entirely. Reasonable tradeoff at early stage.

### New DB table needed

```sql
CREATE TABLE platform_tokens (
  id SERIAL PRIMARY KEY,
  platform VARCHAR NOT NULL,        -- x | linkedin | discord
  access_token TEXT,
  refresh_token TEXT,
  token_expires_at TIMESTAMP WITH TIME ZONE,
  account_id TEXT,                  -- platform user/page ID
  account_name TEXT,                -- display name for admin UI
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE post_results (
  id SERIAL PRIMARY KEY,
  queue_item_id INT REFERENCES growth_agent_queue(id),
  platform VARCHAR NOT NULL,
  platform_post_id TEXT,            -- ID returned by platform API
  platform_post_url TEXT,           -- Direct URL to the post
  status VARCHAR DEFAULT 'posted',  -- posted | failed | deleted
  impressions INT DEFAULT 0,
  engagements INT DEFAULT 0,
  clicks INT DEFAULT 0,
  posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  error_message TEXT
);
```

### New API route

`app/api/agent/post/route.ts` — takes an approved queue item ID + target platforms, calls the right platform APIs, writes to `post_results`, updates `growth_agent_queue.status` to `published`.

### Admin panel addition

Add a "Post to" section in the detail pane of the admin panel. After approving a draft, checkboxes appear: `[ ] X  [ ] LinkedIn  [ ] Discord`. Hit "Post now" or "Schedule". One button, multi-platform.

### Discord server structure (build this first)

```
#general
#announcements          ← weekly Index posts, major signals
#product-photography    ← vertical-specific daily signals
#filmmaking             
#digital-humans         
#tool-releases          ← new tool signals cross-posted here
#legal-alerts           ← Dimension 6 signals only
#hiring                 ← Dimension 7 signals only
#templates              ← template spotlight posts
```

Each channel gets its own webhook URL. The Growth Agent tags each queue item with its vertical + signal_type. The posting agent routes to the right channel automatically.

---

## Critical Gaps (unchanged from prior session)

Full list in `GAPS.md`. Top blockers:

**#0 Creator Opt-Out Mechanism (legal blocker — build before leaderboard goes public)**
- `leaderboard_creators.opt_out_level` (NULL / 'leaderboard' / 'full')
- "Claim or remove this profile" footer link on every public creator page
- Full removal within 24h, leaderboard suppression immediate

**#1 User Workflow Logging** — no `user_workflows` table. Score personalization needs it.

**#2 Baseline Workflows Table** — "traditional rendering = 14h" denominator. Score is unanchored without it.

**#3 Tool Taxonomy** — built in migration 004. Canonical names + aliases → one tool_id.

**#5 Semantic Deduplication** — SHA-256 only catches exact dupes. Need Claude embeddings + cosine similarity.

---

## GEO Strategy Summary

GEO = Generative Engine Optimization. Getting cited by ChatGPT, Perplexity, Gemini, Claude when users ask about tools.

Every approved GEO block adds to tool pages, comparison pages, signal pages. Structured as: direct Q&A answers, confidence labels, source attribution, FAQ JSON-LD schema, visible last-updated dates.

Flywheel: scraper pulls signal → agent writes GEO block → human approves → tool page updates → AI engine indexes it → creator asks AI engine about [tool] → GenLens cited → creator visits page → affiliate click or signup.

Compounds nightly. After 90 days: thousands of citable pages. Zero manual content effort.

---

## What to Do Next (revised order)

1. Register `genlens.app`. Check `genlens.com` — buy if available at standard pricing, redirect to .app.

2. Find-and-replace all `genlens.io` references in codebase → `genlens.app`.

3. Drop Growth Agent files into repo, run migration 004, seed tools:
   ```
   psql $DATABASE_URL -f lib/migrations/004_growth_agent.sql
   npx tsx scripts/seed-tools.ts
   ```

4. Apply for affiliate programs: Runway, ElevenLabs, HeyGen, Synthesia first. Then Figma, Adobe, Descript, PhotoRoom, Claid.

5. Build GAPS #0 (opt-out mechanism) — legal blocker before leaderboard goes public.

6. Build Discord posting (Step 1 of Social Posting Agent) — one afternoon, highest leverage, lowest friction.

7. Build `app/compare/[slug]/page.tsx` and `app/index/[date]/page.tsx` — public GEO surfaces.

8. Build `app/api/og/signal/[id]/route.ts` — OG image per signal for social sharing.

9. X posting API (Step 2 of Social Posting Agent).

10. LinkedIn posting API (Step 3).

---

## Affiliate Programs — Status

| Tool | Program | ~Commission | Status |
|---|---|---|---|
| Runway | Runway Affiliate | 20% | Placeholder URL in seed script |
| ElevenLabs | ElevenLabs Affiliate | 22% | Placeholder URL in seed script |
| HeyGen | HeyGen Affiliate | 25% | Placeholder URL in seed script |
| Synthesia | Synthesia Affiliate | 20% | Placeholder URL in seed script |
| KeyShot | keyshot.com/partners | unknown | Not applied |
| Claid AI | claid.ai/affiliates | unknown | Not applied |
| Figma | Figma Referral | unknown | Not applied |
| Adobe | adobe.com/affiliates | unknown | Not applied |
| Descript | descript.com/affiliates | unknown | Not applied |
| PhotoRoom | photoroom.com/affiliates | unknown | Not applied |

---

## Monetization (unchanged)

- Free: Daily briefing, 1 vertical, 7-day archive, limited signals
- Pro ($19/mo): All 3 verticals, all 10 dimensions, leaderboard, templates, full archive
- Studio ($99/mo): Multi-user, API, team settings, Slack integration
- Enterprise ($499+/mo): White-label, custom sources, priority support

---

## Things Still Open / Unsure

- Whether fashion designers self-identify as separate from "product photographers (apparel)" — determines if Fashion becomes vertical 4 or stays part of Product Photography
- Legal exposure of leaderboard before opt-out exists — get a 30-min legal check before going public
- Whether the embeddable Score badge creates conflict if vendors dispute their score — need a score dispute mechanism before scaling badges
- Exact timing on press pickup — CineD and No Film School are best first targets, but editorial calendars unknown
- Accent colors for deferred verticals (cyan / blue / pink) — need design pass before activating
- Reddit as a posting platform — requires careful tone management, not MVP
- Buffer vs direct API for social posting — reasonable to use Buffer at early stage to reduce maintenance burden
- `genlens.app` year-two renewal pricing — confirm with registrar before buying
