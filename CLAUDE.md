# GenLens Phase 2 Instructions

## Overview
GenLens is daily intelligence briefings for creative technologists in AI-accelerated visual production. Phase 1 (foundation) is shipped. Phase 2 adds the core value: scraper engine, deduplication, taxonomy classification, and briefing synthesis.

## Target Audience
- Product photographers (KeyShot, Claid, Figma Weave)
- Filmmakers (Runway, DaVinci Resolve, Unreal)
- Digital humans creators (D-ID, ElevenLabs, HeyGen)

## Phase 2 Priorities (in order)

### 1. Scraper Engine (`lib/scraper/`)
Build orchestrator to ingest from 130+ sources:
- **RSS feeds** — industry blogs, tool release notes, news
- **APIs** — GitHub, YouTube, product updates
- **HTML scraping** — forums, job boards, pricing pages
- **Custom parsers** — specialized sources per vertical

Structure:
```
lib/scraper/
├── sources.ts          # Source definitions (URL, type, parser, vertical, dimension)
├── orchestrator.ts     # Main scraper coordinator
├── parsers/
│   ├── rss.ts
│   ├── html.ts
│   ├── api.ts
│   └── github.ts
├── dedup.ts            # Content hashing + similarity
└── error-handler.ts    # Retry logic, fallbacks
```

Key functions:
- `fetchAllSources()` — Run all 130+ sources daily
- `deduplicateSignals()` — Hash content, cluster similar pieces
- `normalizeSignal()` — Consistent format (title, url, source, date, vertical, dimension)

### 2. Taxonomy Classifier (`lib/classifier/`)
Route signals to the right dimensions and workflows:
```
lib/classifier/
├── verticals.ts        # Classify: product_photography | filmmaking | digital_humans
├── dimensions.ts       # Classify: workflow_signals, competitive_intel, cost_deltas, etc.
├── workflows.ts        # Extract: rendering, voice_gen, animation, color_grading, etc.
└── sentiment.ts        # Classify: positive, negative, neutral (for trending)
```

Use Claude API to classify if needed (cost: ~$0.001 per signal, acceptable for daily run).

### 3. Database Inserts (`lib/db.ts`)
Extend queries:
- `insertSignals(signals[])` — Batch insert deduplicated signals
- `updateSignalStats(dimension)` — Track trending dimension this week
- `insertBriefing(user_id, signals[])` — Save daily briefing

### 4. Briefing Synthesis (`lib/synthesis/`)
Generate daily briefing per user:
```
lib/synthesis/
├── briefing-generator.ts   # Claude API calls
├── templates.ts            # Briefing structure
└── social-drafts.ts        # X/LinkedIn snippets (Phase 2+)
```

For each user:
1. Fetch signals matching their verticals + dimension preferences
2. Call Claude to synthesize into narrative briefing (~500 words)
3. Generate 3 social media drafts
4. Save to briefings table
5. Queue for email delivery (Phase 3)

**Prompt structure** (sketch):
```
You are a briefing editor for {vertical} creators. 
Synthesize these 20 signals into a 500-word daily briefing:
{signals}

Format:
- Opening insight (1 sentence)
- Three key takeaways (with links)
- Trending this week
- Action item (what to do today)
```

### 5. Cron Scheduler (`app/api/cron/`)
Set up Vercel Cron to run daily:
- **11:00 UTC** — Scraper + dedup + classify → store signals
- **13:00 UTC** — Synthesis + email queue
- Adjust times based on user timezones in Phase 4

Structure:
```
app/api/cron/
├── scrape/route.ts    # Trigger orchestrator.ts
└── synthesize/route.ts # Trigger briefing-generator.ts
```

vercel.json already has schedule defined.

## Code Conventions
- **Use TypeScript** — strict mode, no `any`
- **Error handling** — wrap external API calls in try/catch, log to console + DB
- **Database** — use parameterized queries (already in lib/db.ts)
- **Claude API** — use `claude-sonnet-4-20250514` (fast + cheap for batch synthesis)
- **Rate limiting** — respect source rate limits, implement exponential backoff
- **Testing** — test scraper with 5 sample sources before scaling to 130

## Files Reference
- **Spec docs** — `/docs/GENLENS_*.md`
- **README** — `/README.md` (setup, auth flow, phases)
- **Database schema** — `/lib/db/schema.sql`
- **Constants** — `/lib/constants.ts` (verticals, dimensions, sources)

## Success Metrics (Phase 2)
- Scraper ingests 100+ signals/day without errors
- Dedup achieves 60%+ reduction (removes near-duplicates)
- Synthesis runs in <5 sec per user via Claude API
- Daily cron completes in <30 min for all users

## Next Steps
1. Start with scraper (`lib/scraper/`) — skeleton 10 sources first
2. Integrate dedup (test hash collision rates)
3. Add classifier (mock or Claude-based)
4. Build synthesis flow
5. Test end-to-end with Vercel Cron

## Questions?
Refer to spec docs or ask in chat.
