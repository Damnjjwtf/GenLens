# GenLens

**Daily intelligence for creative technologists** working in AI-accelerated visual production: product photography, filmmaking, digital humans.

GenLens watches 130+ sources across 10 dimensions of intelligence and synthesizes daily briefings tailored to your craft. Stay ahead of what's changing.

## The 10 Dimensions

1. **Workflow Stage Signals** — What changed in your bottleneck (rendering, voice gen, animation, etc.)
2. **Product Category Deep Dive** — Hard goods, soft goods, film types — category-specific optimization
3. **Competitive Intelligence** — What other creatives are shipping. Trending projects, commercial wins.
4. **Workflow Templates** — Fastest proven methods from real creators. Time, cost, quality breakdown.
5. **Cost & Time Delta** — Quantified savings. How many hours faster? How much cheaper?
6. **Legal & Ethical** — SAG-AFTRA, copyright, deepfake legislation, disclosure requirements.
7. **Talent + Hiring** — Market rates, skills in demand, salary trends. Know your value.
8. **Integration + Compatibility** — Which tools play nicely together. Pipeline compatibility matrix.
9. **Cultural / Trend Signals** — What aesthetic is winning. Hyper-realistic vs. nostalgic vs. hybrid.
10. **Benchmark + Leaderboard** — See who's winning. Top creators, fastest workflows, trending templates.

## Three Verticals

Toggle between:
- **Product Photography** — Hard goods, soft goods, presale workflows (KeyShot, Claid, Figma Weave)
- **Filmmaking** — VFX, color grading, sound design (Runway, DaVinci Resolve, Unreal)
- **Digital Humans** — Synthetic actors, voice, animation (D-ID, ElevenLabs, HeyGen)

## Features

### Phase 1 — Foundation

✅ Live market-dashboard landing page, sign-in (NextAuth v5: Resend email magic links + GitHub OAuth), dark/light mode, user settings, base DB schema, editorial UI (IBM Plex Mono + Lora + Playfair Display).

### Phase 2 — Intelligence layer (current)

✅ **Scraper engine** — 75 active sources, RSS + HTML + GitHub Atom + arXiv, parallel `Promise.allSettled`, SHA-256 dedup, full per-source logs in `scrape_log`.
✅ **Taxonomy classifier** — Claude Haiku 4.5, batches of 10, classifies vertical / dimension / signal_type / tool_names / time-cost-quality deltas. Currently classifying ~500 signals per run.
✅ **Growth Agent** — Claude Sonnet 4.6 generates social drafts (X, LinkedIn, **Discord** per-signal vertical-routed), GEO blocks, signal pages, and comparison pages. All output queues for human review at `/admin/growth-agent`.
✅ **Discord posting layer** — webhook-routed by `vertical + signal_type`, no OAuth. Approving a `social_discord` queue item auto-posts and logs to `post_results`.
✅ **GenLens Score** — 0-100 composite per (tool, vertical), recomputed nightly. Speed (30%) + cost (30%) anchored to `baseline_workflows`, quality proxy (15%), adoption from `trending_score` (25%). Mirrored to `tools.current_score`.
✅ **Weekly Index** — top 10 tools per vertical, biggest movers up/down, new entries, notable exits, with Claude-generated headline + lede. Drafts to `index_snapshots`, human approves, page renders.
✅ **GEO infrastructure** — JSON-LD on every page (Organization, WebSite, SoftwareApplication, NewsArticle, BreadcrumbList, FAQPage, Dataset), dynamic `sitemap.xml`, `llms.txt` (per [llmstxt.org](https://llmstxt.org)), `robots.ts` explicitly allowing GPTBot, OAI-SearchBot, Google-Extended, ClaudeBot, PerplexityBot, CCBot, and a dozen more.
✅ **Email digests** — Resend-backed, dark-themed HTML + plaintext, sent via `scripts/send-digest.mts`.

### Phase 2 — Remaining

- Public `/index/[date]` page renders the snapshot
- Score badge component (sparkline + breakdown) on tool pages
- OG image route at `/api/og/signal/[id]`
- Comparison page renderer at `/compare/[slug]`
- GAPS #0 creator opt-out (legal blocker before leaderboard goes public)

## Stack

- **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS
- **Database:** Neon Postgres (serverless)
- **Auth:** NextAuth v5 with Resend (email magic links) and GitHub OAuth
- **AI:** Anthropic Claude API (`claude-haiku-4-5-20251001` for the classifier, `claude-sonnet-4-6` for the Growth Agent and Index editorial — managed via `lib/constants.ts`)
- **Deployment:** Vercel (with Cron)

## Local Setup

### 1. Prerequisites
- Node.js 24+ (comes with npm)
- Neon account (free tier works: https://neon.tech)
- Resend account (free tier works: https://resend.com)

### 2. Install dependencies
```bash
npm install
```

### 3. Set up database

Create a Neon project and grab the pooled connection string.

Run the schema migration:
```bash
psql "$DATABASE_URL" -f lib/db/schema.sql
```

### 4. Register a GitHub OAuth app

Create one at https://github.com/settings/developers (separate apps for dev and prod):

- **Homepage URL:** `http://localhost:3000` (or your prod domain)
- **Authorization callback URL:** `http://localhost:3000/api/auth/callback/github` (or your prod equivalent)

Save the Client ID and generate a client secret.

### 5. Configure `.env.local`

Copy from `.env.example` and fill in:

```bash
# Database (from Neon)
DATABASE_URL=postgres://user:pass@ep-xxx.neon.tech/genlens?sslmode=require

# Auth secrets
AUTH_SECRET=<run: openssl rand -base64 32>
NEXTAUTH_SECRET=<same as AUTH_SECRET>
AUTH_URL=http://localhost:3000
NEXTAUTH_URL=http://localhost:3000

# Email magic-link sender (from Resend)
RESEND_API_KEY=re_xxx
EMAIL_FROM=brief@yourdomain.com

# GitHub OAuth (from step 4)
GITHUB_ID=<Client ID>
GITHUB_SECRET=<Client secret>

# AI (from Anthropic)
ANTHROPIC_API_KEY=sk-ant-xxx

# Other
CRON_SECRET=<run: openssl rand -hex 32>
```

### 6. Run dev server
```bash
npm run dev
```

Visit **http://localhost:3000**

- **Public:** Landing page with the live market dashboard and a sign-in form
- **Authenticated:** Dashboard with briefing status (Phase 2+)
- **Sign in:** Homepage `#sign-in` form, either email magic link or "Continue with GitHub"

## Auth Flow

1. **Unauthenticated users** → Public landing page at `/`. Sign-in form is the single CTA.
2. **Email path** → enter email → Resend sends a 24-hour magic link → click → session created.
3. **GitHub path** → click "Continue with GitHub" → OAuth round-trip → session created.
4. **Hitting a protected route while signed out** → redirected to `/?next=<path>#sign-in`. After sign-in, returned to `next`.

The Postgres adapter writes to `users`, `accounts`, `sessions`, and `verification_token`. There is no invite-code gate; sign-up is open.

## Architecture

```
app/                          # Next.js App Router
├── page.tsx                  # Routes to Landing (public) or Dashboard (auth)
├── layout.tsx                # Root layout, theme provider
├── auth/
│   ├── signin/page.tsx       # Redirect to /#sign-in (preserves ?next)
│   └── verify/page.tsx       # "Check your email" page (post magic-link send)
├── settings/page.tsx         # User preferences (auth required)
└── api/
    ├── auth/[...nextauth]/   # NextAuth endpoints
    ├── invite/route.ts       # POST validate invite code
    ├── settings/route.ts     # GET/POST user prefs
    ├── waitlist/route.ts     # POST collect early emails
    └── cron/                 # Daily scrape + brief (Phase 2)

lib/
├── db.ts                     # Neon client + queries
├── db/schema.sql             # Migration file
├── auth.ts                   # NextAuth config
├── constants.ts              # Enums (verticals, dimensions, taxonomy)
├── theme.ts                  # Theme detection + persistence
└── [phase2+]/                # Scraper, synthesis, email (coming)

components/
├── Landing.tsx               # Public landing page
├── Dashboard.tsx             # Auth dashboard (Phase 2)
├── ThemeProvider.tsx         # Light/dark mode context
├── ThemeToggle.tsx           # Theme toggle button
└── [phase2+]/                # Signal cards, filters, etc.

auth.ts                       # NextAuth root config (v5 convention)
middleware.ts                 # Route protection
vercel.json                   # Cron schedule
```

## Roadmap

### Phase 1 (Done) — Foundation
- Next.js scaffold, auth, database, landing page, settings

### Phase 2 — Scraper Engine
- 130+ source orchestrator (RSS, API, HTML, GitHub)
- Deduplication (content hashing)
- Taxonomy classifier (verticals, dimensions, workflow stages)
- Vercel Cron: daily scrape, store signals in DB

### Phase 3 — Synthesis
- Claude API integration (daily briefing generation)
- Social media drafts (X/LinkedIn)
- Keynote talking points
- Template spotlight selection

### Phase 4 — Dashboard
- Signal feed (filterable by vertical + dimension)
- Vertical toggle
- Dimension filter
- Leaderboard pages (templates, creators)
- Cost/time savings visualization

### Phase 5 — Email & Admin
- Daily email briefing delivery
- Subscriber list management
- Admin panel (invite codes, analytics)
- Archive page (past briefings)

### Phase 6 — Polish
- Mobile optimization
- Error handling & monitoring
- Performance tuning
- White-label / API options

## Development

### Type checking
```bash
npx tsc --noEmit
```

### Build
```bash
npm run build
```

### Linting
```bash
npm run lint
```

## Debugging

- **Theme not switching?** Check browser console for errors. Theme preference is stored in localStorage.
- **Email signup not working?** Verify `RESEND_API_KEY` is set and database is connected.
- **Auth redirecting to invite?** Middleware is working. Make sure you have a valid invite code.
- **DATABASE_URL errors?** Check `.env.local` has a valid Neon connection string.

## Contributing

Found a bug? Have a feature idea? 

- Open an issue on [GitHub](https://github.com/Damnjjwtf/GenLens-)
- Or email feedback to your Resend sender address

## License

MIT (for now — GenLens is in early beta)

---

**Built with Claude Code.** Questions? Check the [spec docs](docs/) or open an issue.
