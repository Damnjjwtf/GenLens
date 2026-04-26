# GenLens Growth Agent

The Growth Agent is the distribution engine for GenLens. It runs nightly after the scraper, reads classified signals, and produces five types of output — all queued for human review before anything publishes.

---

## What it produces

| Output type | Where it goes | When |
|---|---|---|
| `social_x` | X / Twitter — human posts after approval | Daily 9am |
| `social_linkedin` | LinkedIn — human posts after approval | Daily 10am |
| `geo_block` | `genlens.app/tools/[slug]` — Q&A blocks + FAQ schema | Nightly, per tool |
| `signal_page` | `genlens.app/signals/[id]` — public shareable URL | Nightly, top 5 signals |
| `index_post` | `genlens.app/index/[date]` — weekly Monday Index | Sundays |
| `comparison_page` | `genlens.app/compare/[a]-vs-[b]` | When tools co-appear in signals |

Nothing publishes without human approval. Everything queues in `growth_agent_queue`.

---

## Files

```
lib/agent/growth-agent.ts           Core agent pipeline
app/api/cron/growth-agent/route.ts  Vercel Cron + admin trigger endpoint
app/api/agent/queue/route.ts        Queue CRUD API (approve, reject, publish)
app/admin/growth-agent/page.tsx     Admin review UI
app/tools/[slug]/page.tsx           Public tool directory pages (GEO + affiliate)
app/signals/[id]/page.tsx           Public signal pages (freemium hook)
scripts/seed-tools.ts               Populates tools table from manifest
lib/migrations/004_growth_agent.sql DB migration — run this first
vercel.json                         Cron schedule config
```

---

## Setup

### 1. Run the migration
```bash
psql $DATABASE_URL -f lib/migrations/004_growth_agent.sql
```

### 2. Seed the tool directory
```bash
npx tsx scripts/seed-tools.ts
```

This creates 22 tool records. Add affiliate URLs in `scripts/seed-tools.ts` as you sign up for each program. Re-run the script after — it upserts.

### 3. Add environment variable
```
CRON_SECRET=your-secret-here   # Must match Vercel Cron auth header
```

### 4. Deploy to Vercel
`vercel.json` configures three cron jobs:
- `0 2 * * *` — scraper (existing)
- `0 3 * * *` — growth agent (new)
- `0 7 * * 1` — Monday Index post (new)

### 5. Access the admin panel
Navigate to `/admin/growth-agent`. Requires admin role on your user record:
```sql
UPDATE users SET role = 'admin' WHERE email = 'you@youremail.com';
```

---

## Running manually

From the admin panel, click **▸ run agent** to trigger an on-demand run.

Or via API:
```bash
curl -X POST https://genlens.app/api/cron/growth-agent \
  -H "Content-Type: application/json" \
  -H "Cookie: next-auth.session-token=..." \
  -d '{"runType": "on_demand"}'
```

For a weekly Index run:
```bash
# Same as above but with:
-d '{"runType": "weekly_index"}'
```

---

## Review workflow

1. Agent runs nightly → outputs land in `growth_agent_queue` with `status=draft`
2. Admin opens `/admin/growth-agent` → sees draft queue
3. For each item: read, optionally edit inline, then **Approve** or **Reject**
4. On approve:
   - GEO blocks → update `tools` table → live on tool page immediately
   - Signal pages → update `signals` table → live at `/signals/[id]`
   - Comparison pages → insert into `tool_comparisons` → live at `/compare/[slug]`
   - Social posts → marked approved + scheduled. Copy and post manually, or integrate with Buffer/Zapier
   - Index posts → approved → publishes Monday 8am

---

## GEO strategy

GEO = Generative Engine Optimization. Getting cited by ChatGPT, Perplexity, Gemini when users ask about tools.

The agent writes structured Q&A content with:
- Direct answers (no preamble)
- Confidence labels: (high), (medium), (low)
- Source attribution on every claim
- FAQ JSON-LD schema on every tool and comparison page
- Last-updated dates (AI engines weight recency)

Over time, every signal = one new GEO content block. Every night the scraper runs, the GEO surface grows. After 90 days: thousands of citable pages with zero manual content effort.

---

## Affiliate revenue

Tool directory pages earn affiliate commissions from day one — before any subscriber exists.

Current programs seeded:
| Tool | Program | ~Commission |
|---|---|---|
| Runway | Runway Affiliate | 20% |
| ElevenLabs | ElevenLabs Affiliate | 22% |
| HeyGen | HeyGen Affiliate | 25% |
| Synthesia | Synthesia Affiliate | 20% |

**TODO — apply for these programs:**
- KeyShot (keyshot.com/partners)
- Claid AI (claid.ai/affiliates)
- Figma (figma.com/referral)
- Adobe (adobe.com/affiliates)
- Descript (descript.com/affiliates)
- PhotoRoom (photoroom.com/affiliates)

Replace the placeholder `?ref=genlens` URLs in `scripts/seed-tools.ts` with real affiliate URLs. Re-run the seed script.

---

## Things still to build

- `app/api/og/signal/[id]/route.ts` — OG image generation per signal (use `@vercel/og`)
- `app/compare/[slug]/page.tsx` — public comparison page (mirrors tool page pattern)
- `app/index/[date]/page.tsx` — public weekly Index archive page
- Social API integration (Buffer, Zapier, or direct Twitter/LinkedIn API) for one-click posting from admin
- Quarterly Hiring Report PDF generator (pulls from Dimension 7 signals, 90-day window)
- Email notification to admin when agent queue has new drafts (so you don't miss the window)

---

## Growth tandems

The agent enables these compounding loops:

**Loop 1 (Vendor backlinks):** GEO block approved → tool page updates → vendor sees their Score/summary → embeds GenLens badge on their site → backlink → SEO

**Loop 2 (Creator citation):** Signal page approved → creator shares on X → audience clicks → freemium gate → signup

**Loop 3 (Press/Index):** Monday Index approved → posted → CineD or No Film School quotes it → organic authority

**Loop 4 (Affiliate):** Comparison page approved → AI engine cites it → creator lands on page → clicks affiliate link → commission
