# GenLens Spine: System-of-Record and Unification Decision

Status: adopted
Owner: Jonathan
Adopted: 2026-07-23
Governed by: `agents/genny/docs/GENLENS_NORTH_STAR.md` (canonical direction, 2026-07-20)

This document answers one question: GenLens currently has two signal stores
and two pipelines. Which one is the product, and how do they become one system?

---

## The Problem

Two halves of GenLens grew in parallel:

| | Web product | Genny/Marti agent |
|---|---|---|
| Runtime | Next.js on Vercel | Python on VPS (Hermes profile) |
| Storage | Neon Postgres (`signals`, `tools`, `tool_scores`) | Append-only JSON (`state/signal_ledger*.json`) |
| Ingestion | Scraper crons, 75+ sources | Source scan + quality gate |
| Verification | Claude classifier, SHA-256 dedup | Admission contract + attributed human review |
| Delivery | Dashboard, /tools, /markets | Discord, Resend email briefs |

They share a brand and a philosophy but no code and no data. Left alone, they
diverge into two competing sources of truth.

## The Decision

1. **Neon Postgres is the system of record.** Everything GenLens claims
   publicly must eventually resolve to a row in Neon. The north star's
   "queryable record of what changed" is the Neon database, full stop.

2. **The VPS JSON ledgers are edge runtime caches and audit trails.** They
   remain authoritative for the run that produced them, are never discarded
   during deployment, and are never the long-term product database. (This
   restates the storage boundary in `agents/genny/docs/ARCHITECTURE.md`.)

3. **Unification is contract-first, not code-first.** Neither side gets
   rewritten. The versioned schemas under `agents/genny/data/`
   (`genlens_signal_record.schema.json`, `genlens_decision_queue.schema.json`,
   `genlens_convergence.schema.json`) are the shared contract. The web side
   adopts the north star's 8-field decision-ready signal standard (change,
   mechanism, use case, impact, evidence, lens, decision, confidence) as
   columns, not as a rewrite of the Python pipeline.

4. **Data flows one way: edge to record.** A future run of Genny or Marti
   pushes its validated ledger records to the web app's ingestion endpoint.
   The web app never writes into VPS state. There is no dual-write and no
   sync-conflict surface.

## The Bridge (build order)

### Phase 1: Ingestion endpoint
- `POST /api/ingest/signals` on the web app.
- Validates payloads against `genlens_signal_record.schema.json`.
- Preserves stable signal IDs and event IDs from the ledger.
- Requires an idempotency key per record; replays are no-ops.
- Authenticated with a bearer token that lives only in the VPS `.env`
  (`GENLENS_INGEST_TOKEN`), never in the repo.
- New Neon table `ledger_signals` (separate from the scraper's `signals`
  table) so verified agent records and raw scraped signals never blur.

### Phase 2: Push script on the Genny side
- `agents/genny/scripts/genlens_push_ledger.py`: reads the validated local
  ledger, posts new records to the ingestion endpoint, records what was
  acknowledged. Failure leaves local state untouched and retries later.
- Runs after a successful compose, never during one.

### Phase 3: Web renders the verified record
- `/signals` and `/markets` progressively read from `ledger_signals`
  (verified, human-reviewed cards) in preference to raw scraper output.
- Every rendered claim links to its evidence URL and shows its lens and
  confidence, exactly as the ledger recorded them.

### Phase 4: Decisions come home
- The decision queue gains a web surface: a signed-in user records
  test/adopt/avoid/watch actions against verified signals.
- WVDA becomes measurable in the product instead of proxied by chat.
  (North star Milestone 3.)

### Later, explicitly not now
- Converging the web scraper's classifier with Genny's quality gate.
- Two-way tooling, dashboards for ledger admin, convergence surfaces.

## What This Decision Does NOT Change

- Genny's admission contract, publisher-trust gate, and human-review
  boundaries. The bridge copies verified records; it never verifies.
- Marti's promotion gate. Unpromoted lenses do not gain a web audience by
  side door.
- The append-only rules. The bridge never mutates or deletes ledger history,
  local or hosted.
- The model runtime handoff (`agents/genny/docs/MODEL_RUNTIME_HANDOFF.md`).
  That track proceeds independently.

## Focus Rule: NOW / NEXT / PARKED

One track in flight at a time. A track leaves NOW only when its acceptance
checklist passes or it is explicitly parked with a revisit trigger.

**NOW**
1. Security cleanup + model runtime Phases A/B (in flight, blocking, small).

**NEXT (in order)**
2. Spine Phase 1: ingestion endpoint + `ledger_signals` table.
3. Spine Phase 2: push script from the Genny side.
4. Spine Phase 3: web renders verified cards.
5. Role Radar web surface (`/roles`): public page rendering the career
   intelligence layer (observed / emerging / 12-18-month forecast roles from
   `agents/genny/data/role_signals.json` and the Career Radar pipeline, see
   `agents/genny/docs/CAREER_INTELLIGENCE.md`). Rides the same ledger-to-Neon
   bridge as Phase 3; do not build a separate pipeline for it. Trigger:
   start only after Phase 3 ships. Marti's martech-displacement coverage
   joins this surface only after her promotion gate passes.

**PARKED (with revisit triggers, per the BACKLOG.md convention)**
- Growth Agent social posting (X/LinkedIn): revisit when one delivery loop
  shows repeatable WVDA proxy evidence.
- Score/Index feature investment: keep the crons running, add nothing until
  Spine Phase 3 renders verified cards. Revisit: first external Score citation
  or 50 active users.
- Career radar expansion, NotebookLM automation, new verticals: unchanged
  BACKLOG.md triggers.
- Creator leaderboard: still hard-blocked by GAPS #0 (opt-out mechanism).

## Governance

If a proposed change adds a new surface, store, or pipeline that is not on
this list, it needs an explicit decision recorded here first. CLAUDE.md
directs all agent sessions to this file and the north star before building.
