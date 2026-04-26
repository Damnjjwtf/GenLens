# GenLens Product Gaps

Comprehensive inventory of missing pieces. Organized by criticality and blocker status.

**Last reviewed:** April 26, 2026

---

## CRITICAL GAPS (block core features)

These must be addressed before launching Score, Index, or personalized briefings.

### 1. User Workflow Logging System

**What's missing:**
- `user_workflows` table (user_id, tool_stack[], workflow_stage, product_category, time_hours, cost_dollars, quality_notes, created_at)
- POST `/api/workflows` endpoint for users to log completed work
- UI for "/workflows/add" — simple form: "What did you just finish? Tools used? How long? What stage?"
- Workflow history view (user dashboard tab showing their logged workflows)
- Personal Score computation (user's Score vs. leader Score in their vertical)

**Why critical:**
- Score becomes meaningless without user workflows (can't show "you're 10 hours slower than leader")
- Arbitrage depends entirely on user knowing their current stack
- Growth loop (share-card artifact) assumes users have logged at least one workflow
- Better benchmarks depend on user contributions

**Blocks:** Score personalization, Arbitrage, growth loop
**Severity:** High
**Effort estimate:** 3-4 days (schema + API + UI)

**Revisit trigger:** Before launching GenLens Score publicly. Can ship Score in private beta without this, but personalization doesn't work.

---

### 2. Baseline Workflows Table

**What's missing:**
- `baseline_workflows` table (workflow_stage, vertical, product_category, traditional_time_hours, traditional_cost_dollars, ai_accelerated_time_hours, ai_accelerated_cost_dollars, baseline_year, source)
- Seed data: "Traditional hard goods rendering = 14 hours, $1,200 in farm costs"
- Tool Score formula must anchor against baselines, not just raw deltas

**Example baseline:**
```
stage: rendering
vertical: product_photography
category: hard_goods
traditional: 14 hours, $1,200 (outsourced farm)
ai_accelerated: 4 hours, $100 (KeyShot 2026 license)
source: GENLENS_SPEC_v2
```

**Why critical:**
- Score formula needs: `(baseline_time - signal_time) / baseline_time * 100` to be defensible
- Without baselines, "KeyShot saves 10 hours" is meaningless (10 hours vs. what?)
- Score comparability across tools breaks without shared baselines

**Blocks:** GenLens Score calculation
**Severity:** High
**Effort estimate:** 2-3 days (schema + seed data + formula validation)

**Revisit trigger:** Before writing the Score computation formula (which happens in Claude Code kickoff).

---

### 3. Tool Taxonomy & Master Tool List

**What's missing:**
- `tools` table (id, canonical_name, aliases[], category, vendor_name, website, pricing_tier, logo_url, created_at, updated_at)
- Deduplication mapping ("elevenlabs" → "ElevenLabs" → "Eleven Labs" all map to tool_id: 42)
- Tool scraper: extract tools from signals, normalize names, update tool table
- FK constraint: signals.tool_names should reference tools.id, not free-text

**Example entry:**
```
id: 42
canonical_name: "ElevenLabs"
aliases: ["elevenlabs", "eleven labs", "el"]
category: "voice_synthesis"
vendor: "Eleven Labs Inc."
website: "https://elevenlabs.io"
pricing_tier: "freemium"
logo_url: "https://..."
```

**Why critical:**
- Score entity must reference stable tool IDs, not free-text strings
- Templates reference tools by name; need canonical linking
- Leaderboard aggregates by tool; without dedup, one tool appears 5 times
- Index ("top 10 tools this week") needs to count unique tools correctly

**Blocks:** Score entity stability, template taxonomy, leaderboard accuracy, Index calculation
**Severity:** High
**Effort estimate:** 4-5 days (schema + dedup logic + batch normalization job)

**Revisit trigger:** Before Score/Index computation. Critical path item.

---

### 4. Cross-Vertical Signal Handling

**What's missing:**
- UI for multi-vertical users (currently assumes toggle = one vertical at a time)
- Settings: allow users to select multiple active verticals
- Dashboard layout: show signals from all active verticals, with vertical badges
- Filter: "show me signals that affect all 3 verticals I'm active in"
- Index: GLI-ALL (cross-vertical index, shows tools/signals that apply to all)

**Why critical:**
- Many users work across verticals (filmmaker who also does product work)
- Some signals affect all verticals (Claude API price, NVIDIA GPU, copyright lawsuit)
- Current single-vertical toggle forces artificial friction

**Blocks:** Usability for multi-vertical users, comprehensive Index
**Severity:** Medium-High (not launch blocker but UX debt)
**Effort estimate:** 2-3 days (UI refactor + query changes)

**Revisit trigger:** When you onboard a user who says "I do both Product Photography and Filmmaking". Probably within first 50 users.

---

## UX GAPS (confusing for new users)

### 5. Onboarding / Initial Setup Flow

**What's missing:**
- `/onboarding` route that runs after first login
- Step 1: "Which verticals do you work in?" (single or multi-select)
- Step 2: "What's your biggest bottleneck?" (vertical-specific workflow stage selector)
- Step 3: "Which tools do you already use?" (checkboxes from tools table)
- Step 4: "How often do you want briefings?" (daily/weekly, time, timezone)
- Stores all this in user_preferences, then redirects to dashboard

**Why it matters:**
- Without this, new user lands on dashboard with no context
- First briefing is generic, not personalized
- User doesn't understand the vertical toggle and filters exist

**Blocks:** Good onboarding UX, retention (new user confusion = churn)
**Severity:** Medium (doesn't block launch but matters for retention)
**Effort estimate:** 2-3 days (flow design + UI + preference storage)

**Revisit trigger:** After your first 10 beta users. If >30% don't complete setup or set wrong preferences, revisit immediately.

---

### 6. Tool/Dimension/Workflow Stage Explainer

**What's missing:**
- Inline help (? icons on dashboard, briefing sections)
- Glossary: what is "Dimension 5: Cost & Time Delta" in plain English
- Tool browser: users can browse all tracked tools, see their category, current signals
- Workflow stage definitions per vertical (e.g., "Rendering = process where 3D models become 2D images")

**Why it matters:**
- Domain expertise bias: you understand "rendering" and "voice_gen" but new users don't
- Without context, briefing sections feel opaque

**Blocks:** Accessibility for non-experts
**Severity:** Low (nice-to-have, not critical)
**Effort estimate:** 1-2 days (docs + UI help system)

**Revisit trigger:** When a beta user says "What does this section mean?" or stops reading signals.

---

## DATA QUALITY GAPS

### 7. Semantic Deduplication

**What's missing:**
- Current approach: SHA-256 of (title + source_url) — good for exact duplicates
- Missing: semantic similarity for near-duplicates
  - Same news story published on 3 different blogs (different titles, different URLs, same content)
  - YouTube tutorial about KeyShot vs. KeyShot official announcement (different but related)
- Solution: Claude embeddings + similarity threshold (>0.85 = duplicate, merge into one signal)

**Why it matters:**
- Without it, users see the same story 3 times per day
- Feed becomes noisy, diminishing returns on reading
- Trending score gets inflated (one story counted as 3 signals)

**Blocks:** Feed quality, trending accuracy
**Severity:** Medium (launch blocker for daily feeds)
**Effort estimate:** 3-4 days (embedding logic + merge strategy + dedup pipeline)

**Revisit trigger:** After first week of scraping. If >20% of feed is obvious duplicates, implement immediately.

---

### 8. Source Health Monitoring

**What's missing:**
- `source_health` table (source_name, last_successful_scrape, error_count, last_error, status: active|failing|stale)
- Dashboard: which 130+ sources are actually returning signals (admin view)
- Alert: if >10 sources fail for >24 hours, flag them
- Stale detection: if a source hasn't updated in 7 days, mark stale
- Automatic rotation: disable sources that are consistently failing

**Why it matters:**
- Blind spot: you won't know if 30 sources are silently broken
- False negatives: if RSS scrapers all fail, users think "nothing happened today" (false)
- Admin can't debug without visibility

**Blocks:** Data quality confidence, admin operations
**Severity:** Medium (important for reliability)
**Effort estimate:** 2 days (monitoring logic + dashboard)

**Revisit trigger:** Before running daily Vercel Cron. Essential for production reliability.

---

### 9. Signal Feedback Loop

**What's missing:**
- `signal_feedback` table (signal_id, user_id, feedback_type: helpful|misleading|outdated|duplicate, comment, created_at)
- UI: thumbs up/down on each signal card with optional note
- Analysis: "which signals do users mark as unhelpful" → improve scraping/taxonomy
- User contribution: "this signal doesn't apply to my workflow" → helps personalization
- Dispute mechanism: "KeyShot doesn't save me 10 hours" → collects contrary data

**Why it matters:**
- Without feedback, you're guessing what's useful
- Conflicting data points (user says KeyShot saves 4 hours, signal claims 10) won't be surfaced
- No mechanism for users to contribute ground truth

**Blocks:** Signal quality improvement, user engagement
**Severity:** Low (launch v1 without this, add after)
**Effort estimate:** 2-3 days (schema + UI + analysis views)

**Revisit trigger:** After 2 weeks of daily briefings. If you're not getting engagement signals, revisit immediately. If high engagement without feedback, defer.

---

### 10. Deduplication Strategy (Sources to Signal)

**What's missing:**
- Edge case handling: same story from 3 sources
  - Option A: Keep all 3, mark as "corroborated" (strong signal)
  - Option B: Keep best source, discard others (cleaner feed)
  - Option C: Merge into one signal with source attribution to all 3
- Recommendation: Option C (merge + multi-source attribution)
- Implementation: After semantic dedup detects near-duplicates, merge signals, update source list

**Why it matters:**
- Affects feed quality and trending score calculation
- If you keep all 3, a story about "KeyShot released" counts as 3x signal strength
- If you keep 1, you lose signal confidence (3 sources corroborate = stronger than 1)

**Blocks:** Trending score accuracy
**Severity:** Medium
**Effort estimate:** 3-4 days (merge logic + source attribution + trendscore recalc)

**Revisit trigger:** When you notice the same story appearing 3 times in one briefing.

---

## FUTURE SURFACES (deferred, but plan for it)

### 11. Search & Archive

**What's missing:**
- `/archive` route showing past briefings (searchable, filterable)
- `/signals` feed (view all individual signals, not just briefing digest)
- Search endpoints:
  - By tool name ("all signals about KeyShot")
  - By dimension (1-10)
  - By workflow stage
  - By vertical
  - By date range
  - By trending score threshold
- Full-text search on signal titles + descriptions

**Why it matters:**
- "When did ElevenLabs release emotional prosody?" — users will ask this
- "Show me all rendering-stage signals from March" — researchers, studios
- Archive becomes a knowledge base, not just email history

**Blocks:** User reference utility, researcher use cases
**Severity:** Low (ship v1, add before Series A)
**Effort estimate:** 3-4 days (UI + search API + indexing)

**Revisit trigger:** After 4 weeks of daily briefings. If users ask "can I search past briefings," build it.

---

### 12. Mobile Experience / PWA

**What's missing:**
- Responsive design (dark mode already planned, but mobile layout not detailed)
- PWA manifest (installable on home screen)
- Offline access to last N briefings
- Push notifications for breaking signals
- Mobile-optimized signal card (smaller UI, swipe navigation)

**Why it matters:**
- Creatives are mobile-first (on set, in studio, between meetings)
- Notification "KeyShot just dropped, upgrade now" is valuable real-time signal
- PWA makes it feel like a native app

**Blocks:** Mobile user base, engagement
**Severity:** Low (ship responsive web first, PWA as v1.1)
**Effort estimate:** 4-5 days (responsive design + PWA setup + notification service worker)

**Revisit trigger:** When mobile users hit 15% of traffic and request offline access.

---

### 13. API / Webhooks for Studios

**What's missing:**
- `/api/v1/signals` endpoint (GET with filters, pagination)
- API key generation in user settings
- Rate limiting (free: 100/day, Pro: 1000/day, Studio: unlimited)
- Webhook support: subscribe to "notify me when tool X releases an update"
- API docs (OpenAPI/Swagger spec)

**Why it matters:**
- Monetization: Studio tier ($99/mo) includes API access
- Integration: studios want to ingest GenLens signals into their tools
- Programmatic access: agencies can run reports on their team's trends

**Blocks:** B2B sales, API monetization
**Severity:** Low (launch v1 without, add for Studio tier v1.1)
**Effort estimate:** 5-7 days (API scaffold + auth + docs)

**Revisit trigger:** When a studio customer asks "do you have an API?"

---

### 14. Admin Dashboard Observability

**What's missing:**
- `/admin/scraper-health` — real-time view of which sources are running, failing, stale
- `/admin/signals-log` — last 100 signals ingested, with source + classification
- `/admin/user-analytics` — DAU, open rate, click-through on signals, retention cohorts
- `/admin/churn-analysis` — users who haven't opened email in 7 days
- `/admin/engagement` — which signals/dimensions get the most interaction
- `/admin/source-performance` — signals per source, error rate per source, trending_score distribution

**Why it matters:**
- Without visibility, you can't diagnose product issues
- "Why did briefing volume drop 40%?" — needs data
- "Which signals drive most retention?" — need engagement logs
- "Which sources are worth keeping?" — need performance metrics

**Blocks:** Operations, product insight
**Severity:** Medium (important for reliability + iteration)
**Effort estimate:** 4-5 days (analytics logging + dashboard UI)

**Revisit trigger:** After first 2 weeks of daily scrapes + sends. Essential for debugging and product decisions.

---

### 15. Sub-indices by Category

**What's missing:**
- GLI-PP (Product Photography) can split into:
  - GLI-PP-HardGoods (KeyShot, CAD tools)
  - GLI-PP-SoftGoods (CLO3D, Marvelous Designer)
  - GLI-PP-Lifestyle (compositing, background gen)
- GLI-FM (Filmmaking) can split into:
  - GLI-FM-Commercial (30-sec to 2-min ads)
  - GLI-FM-MusicVideo
  - GLI-FM-Feature (long-form narrative)
- GLI-DH (Digital Humans) can split into:
  - GLI-DH-TalkingHead (single person, static camera)
  - GLI-DH-FullAnimation (avatar, full body)
  - GLI-DH-Deepfake (ethical use, disclosure)

**Why it matters:**
- User doing hard goods rendering doesn't care about CLO3D releases
- Filmmaker doesn't care about hard goods tools
- More targeted intelligence = higher engagement

**Blocks:** User satisfaction, niche use cases
**Severity:** Low (ship GLI-PP/FM/DH first, sub-indices as v2)
**Effort estimate:** 2-3 days (filtering + index computation)

**Revisit trigger:** When you have 200+ active users per vertical. Premature optimization before then.

---

### 16. Creator Portfolio Integration

**What's missing:**
- Link leaderboard creators to their portfolios (Behance, ArtStation, Instagram)
- Show portfolio stats (follower count, engagement, recent projects)
- Creator-specific signal feed ("what's the leader in your niche working with right now?")
- Attribution: when a template is trending, attribute to the creator who popularized it

**Why it matters:**
- Leaderboard becomes a discovery tool for hiring, collaboration
- Creators see themselves ranked, creates network effect (want to improve rank)
- Follower can learn by following leader's toolkit updates

**Blocks:** Leaderboard virality, network effects
**Severity:** Low (v1 just shows names/tools, v2 adds portfolio)
**Effort estimate:** 3-4 days (portfolio linking + stats aggregation)

**Revisit trigger:** When a creator asks "how can I get on the leaderboard?"

---

### 17. Historical Trend Analysis

**What's missing:**
- `scores_history` table (tool_id, score, week_start_date, movers_rank_up, movers_rank_down)
- `trends_history` table (aesthetic_description, vertical, week_start_date, rank)
- Weekly snapshot compute job (every Monday, store historical state)
- "Biggest movers" calculation (compare this week's scores to last week's)
- Trend velocity charts ("rendering got X% faster per month in Q1 2026")

**Why it matters:**
- Index needs "biggest movers" — that's a week-over-week comparison
- Briefings can show "trajectory" not just "snapshot"
- Users want to know: "is rendering getting faster or slower?"
- Pattern recognition: "every March, digital humans tools release updates"

**Blocks:** Index "movers" section, historical trend analysis, pattern forecasting
**Severity:** Medium (ship Index without history first, add week 2)
**Effort estimate:** 2-3 days (schema + weekly snapshot job)

**Revisit trigger:** After first 2 weeks of Index publication. Compute week 1 vs. week 2 changes.

---

### 18. Competitive Benchmarking (Studio vs. Studio)

**What's missing:**
- `studio_profiles` table (studio_name, team_size, tool_stack, specialization, contact, opted_in)
- Comparative view: "Your rendering stage is 18 hours. Industry average: 12 hours. Top studios: 6 hours."
- Anonymized benchmarking: "You're in the bottom 40th percentile for Product Photography speed"
- Privacy: studios can opt-in to benchmarking leaderboard
- Hiring pressure signal: "studios using KeyShot 2026 are hiring 3x more Gen ADs"

**Why it matters:**
- Monetization: Studio tier can see "how do we compare to competitors"
- Hiring data: talent can see "studios doing X tool are paying premium rates"
- Competitive tension: studios want to close the gap to the leader

**Blocks:** Studio tier value prop
**Severity:** Low (v1 doesn't have this, add for Series A pitch)
**Effort estimate:** 5-7 days (schema + aggregation logic + privacy controls)

**Revisit trigger:** When Studio tier launch is planned.

---

## REVISIT SCHEDULE

- **Quarterly review:** Check this file, mark items resolved, add new gaps
- **Milestone-triggered:** When hitting user counts (50, 100, 500 users)
- **User-requested:** When beta user explicitly asks for a gap item
- **Data-triggered:** When analytics show usage pattern that reveals a gap

---

## Summary: Minimum Viable Checklist for Phase 2 Launch

To ship Score + Index + public beta responsibly:

**Must have (blocks launch):**
- [ ] User workflow logging system (#1)
- [ ] Baseline workflows (#2)
- [ ] Tool taxonomy (#3)
- [ ] Source health monitoring (#8)
- [ ] Semantic deduplication (#7)

**Should have (UX debt otherwise):**
- [ ] Onboarding flow (#5)
- [ ] Signal feedback loop (#9)
- [ ] Historical trend analysis (#17)
- [ ] Admin observability (#14)
- [ ] Cross-vertical signal handling (#4)

**Nice to have (v1.1 or v2):**
- [ ] Search & archive (#11)
- [ ] Mobile/PWA (#12)
- [ ] API/webhooks (#13)
- [ ] Sub-indices (#15)
- [ ] Creator portfolio integration (#16)
- [ ] Competitive benchmarking (#18)

---

**Last updated:** April 26, 2026  
**Maintained by:** Claude Code agent + human review
