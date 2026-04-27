# Next Steps for GenLens Development

**Last updated:** 2026-04-27  
**Current branch:** `claude/check-project-status-RRBad`  
**PR:** https://github.com/Damnjjwtf/GenLens/pull/1 (Draft)

---

## ✅ What Was Just Completed (This Session)

**Tool Taxonomy — Gap #3 Implementation (Phases 1-4)**

### Phase 1: Database Schema
- Added `tools` table with:
  - `slug` (unique), `canonical_name`, `aliases[]`, `verticals[]`, `categories[]`, `workflow_stages[]`
  - `vendor_name`, `website_url`, `pricing_tier`, `logo_url`
  - `affiliate_url`, `affiliate_program`, `affiliate_commission_pct` (affiliate revenue layer)
  - `is_public`, `is_featured`, `created_at`, `updated_at`
- Added `tool_ids INT[]` column to `signals` table (alongside `tool_names TEXT[]` for display)
- Created indexes on slug, verticals, aliases

**File:** `lib/db/schema.sql`

### Phase 2: Normalization Engine
- Created `lib/tools/normalize.ts`:
  - `normalizeToolNames(toolNames: string[])` — maps freeform names to tool IDs
  - `resolveToolIds(toolNames: string[])` — returns high-confidence tool_ids only
  - Exact matching on canonical names + aliases
  - Fuzzy matching fallback (Levenshtein distance, >0.75 threshold)
  - Singleton in-memory alias index with cache invalidation
- Zero new dependencies (uses native JS levenshtein implementation)

**File:** `lib/tools/normalize.ts`

### Phase 3: Signal Integration
- Updated `Classification` type to include `tool_ids: number[] | null`
- Classifier (`lib/scraper/classify.ts`):
  - `normalize()` function now async
  - Populates `tool_ids` via `resolveToolIds(tool_names)` post-classification
  - Logs warnings if tool normalization fails; doesn't block signal insert
- Orchestrator (`lib/scraper/orchestrator.ts`):
  - `insertSignal()` now inserts both `tool_names` (display) and `tool_ids` (FK reference)

**Files:** `lib/scraper/types.ts`, `lib/scraper/classify.ts`, `lib/scraper/orchestrator.ts`

### Phase 4: Batch Normalization (Manual Trigger First)
- CLI script: `scripts/normalize-signals.ts`
  - Usage: `npx tsx scripts/normalize-signals.ts [--limit 1000] [--dry-run] [--invalid-cache]`
  - Fetches signals with `tool_names` but no `tool_ids`
  - Processes in batches, logs progress every 50
  - Supports dry-run for validation
  - Can be run manually or scheduled

- Admin API: `POST /api/admin/normalize-tools`
  - Admin-only endpoint for manual trigger
  - Request: `{ limit: 500, dryRun: false, invalidateCache: false }`
  - Response: `{ normalized, skipped, errors, failedSignals }`
  - Capped at 5000 signals per request

**Files:** `scripts/normalize-signals.ts`, `app/api/admin/normalize-tools/route.ts`

### Commits
```
09cf483 feat(tools): batch normalization script + admin API trigger
c8b1b20 feat(tools): tool taxonomy schema + normalization engine
837f6a7 chore: update dependencies via npm install
```

---

## ⚠️ Blockers for Next Session

### Critical
- [ ] **DATABASE_URL environment variable**
  - Needed for: seeding tools, scraper tests, batch normalization
  - Format: `postgresql://user:password@host.neon.tech/dbname?sslmode=require`
  - Store in: `.env.local` (git-ignored, not in repo)
  - Source: Your Neon dashboard → Connection String
  - **Per-Device Setup:** Each device needs its own `.env.local` (not synced via git)
    ```bash
    echo 'DATABASE_URL="postgresql://..."' > .env.local
    ```

- [ ] **Schema migration applied to Neon database**
  - If not done yet: `psql $DATABASE_URL -f lib/db/schema.sql`
  - Verify `tools` table exists: `SELECT COUNT(*) FROM tools;` (should be 0 until seeding)

---

## 🚀 Next Actions (In Order)

### 1. Prepare Environment (if not already done)
```bash
# In repo root, create .env.local
echo 'DATABASE_URL="postgresql://..."' > .env.local

# Verify connection
psql $DATABASE_URL -c "SELECT version();"

# Apply schema if not already done
psql $DATABASE_URL -f lib/db/schema.sql
```

### 2. Seed Tools Table (27 canonical tools)
```bash
npx tsx scripts/seed-tools.ts
```

**Expected output:**
```
Seeding 27 tools...
  ✓ Inserted: KeyShot
  ✓ Inserted: Runway
  → Updated: ElevenLabs (if already exists)
  ...
Done. 27 inserted, 0 updated.

Tools with affiliate URLs:
  Runway: Runway Affiliate (~20% commission)
  ElevenLabs: ElevenLabs Affiliate (~22% commission)
  HeyGen: HeyGen Affiliate (~25% commission)
  Synthesia: Synthesia Affiliate (~20% commission)
  Adobe Firefly: Adobe Referral
  Figma Weave: Figma Referral

Tools needing affiliate programs (check their websites):
  KeyShot: https://www.keyshot.com
  Claid AI: https://claid.ai
  ...
```

### 3. Test End-to-End: Run Scraper on 1 Source
```bash
# Start dev server if needed
npm run dev

# Trigger scraper via cron endpoint
curl -X GET http://localhost:3000/api/cron/scrape \
  -H "Authorization: Bearer $CRON_SECRET"
```

**Verify:**
```sql
SELECT id, tool_names, tool_ids, created_at FROM signals 
WHERE tool_names IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 5;
```

Expected: `tool_ids` populated with numbers like `{42, 15, 8}` (not NULL)

### 4. Test Batch Normalization (on existing signals without tool_ids)
```bash
# Dry-run first (no database changes)
npx tsx scripts/normalize-signals.ts --limit 100 --dry-run

# If output looks good, run for real
npx tsx scripts/normalize-signals.ts --limit 500
```

**Or via admin API:**
```bash
curl -X POST http://localhost:3000/api/admin/normalize-tools \
  -H "Content-Type: application/json" \
  -d '{"limit": 500, "dryRun": true}'
```

### 5. Merge PR #1
Once verified:
```bash
git push origin claude/check-project-status-RRBad
# Then merge PR #1 on GitHub
```

---

## 📋 Gap Status

| Gap | Status | Blocker | Notes |
|-----|--------|---------|-------|
| #0: Creator Opt-Out | TODO | Blocks public leaderboard | Legal + trust requirement |
| #1: User Workflow Logging | TODO | Blocks Score personalization | 3-4 days effort |
| #2: Baseline Workflows | TODO | Blocks Score formula | 2-3 days effort |
| **#3: Tool Taxonomy** | **DONE** ✅ | **Unblocks Score/Index** | **This session** |
| #4: Cross-Vertical Signal Handling | TODO | Medium-high UX debt | 2-3 days |
| #5: Onboarding Flow | TODO | Affects retention | 2-3 days |
| #7: Semantic Deduplication | TODO | Blocks daily feed quality | 3-4 days effort |
| #8: Source Health Monitoring | TODO | Blocks reliable daily cron | 2 days effort |
| #9: Signal Feedback Loop | TODO | Improves signal quality | 2-3 days |

**Critical path to Score/Index launch:**
1. ✅ #3 Tool Taxonomy — DONE
2. → #2 Baseline Workflows (2-3 days)
3. → #1 User Workflow Logging (3-4 days)
4. → Score formula implementation (2-3 days)
5. → Index publication logic (2-3 days)

---

## 🔄 Deferred Phases (Can Schedule Later)

### Phase 5: Tools Leaderboard API (Optional for MVP)
Not started. Can defer until Score/Index working.
- `GET /api/tools/index` — top N tools by signal count
- Tools detail page enhancement

---

## 📝 Notes for Next Session

- Tool normalization is **non-blocking** — if it fails, signal still inserts with `tool_names` only. Batch job can catch up later.
- Seed script only inserts 27 tools. TOOLS_MANIFEST has 130+ — can extract those in a separate bootstrap script if needed.
- Affiliate URLs are seeded but mostly TODOs. Each vendor has different program URLs.
- Fuzzy matching threshold (0.75) is conservative. Adjust if needed after testing.
- Cache invalidation via `invalidateCache()` if tools table changes mid-session.

---

## Questions for Next Session

- Should we extract + seed all 130+ tools from TOOLS_MANIFEST.md now, or stick with 27 + manual curation?
- After seeding tools, what's the priority: Baseline Workflows (#2) or User Workflow Logging (#1) first?
- Should the normalization batch job run as daily cron at 03:00 UTC (after scraper), or manual-trigger only for now?

---

**Created:** 2026-04-27  
**Branch:** `claude/check-project-status-RRBad`  
**Status:** Ready for testing on next device
