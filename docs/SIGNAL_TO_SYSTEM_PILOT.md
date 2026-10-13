# GenLens v0.1: Signal to system

Status: private-pilot implementation, not yet deployed.
Canonical direction: SPINE.md and agents/genny/docs/GENLENS_NORTH_STAR.md.

## Product promise

**GenLens. Signal to system.**

Evidence-backed technology news and decision support for GTM engineers and
creative technologists. News is a permanent part of the product.

- Marti: GTM, data, marketing automation, distribution, conversion, economics.
- Genny: models, media production, creative APIs, workflows, quality, rights.
- Convergence: verified production/marketing overlaps, never invented.

User journey: source → verified signal → relevant workflow → decision → outcome.

## Implemented in this branch

- Migration 009 adds append-only ledger_signal_events and the queryable
  ledger_signals projection, separate from the raw scraper signals.
- POST /api/ingest/signals checks bearer authorization, payload size,
  schema fields, source evidence, actor/lens membership, and idempotency.
- Replays don't insert duplicate events. Older observations can't overwrite
  newer projections. The original JSON ledger remains untouched.
- agents/genny/scripts/genlens_push_ledger.py is a manual, checkpointed
  sender for the agent's validated ledger records. It can dry-run and resume.
- /admin/verified-signals is a private, database-admin-only evidence desk.
  It never publishes cards, triggers campaigns, or spends money.
- Automated tests cover validation, deterministic IDs and durable checkpoints.

Not shipped: automatic push cron, public verified feed, role personalization,
decision tracking, price/checkout, or production data synchronization.

## Safe activation steps (not yet performed)

1. On the intended authorized Neon database, execute:
   psql "$DATABASE_URL" -f lib/migrations/009_verified_signal_ingest.sql
2. Generate a strong random secret locally, e.g. openssl rand -hex 32.
   Configure the SAME GENLENS_INGEST_TOKEN in protected Vercel settings
   and the VPS profile. Never paste credentials into Git or this chat.
3. Set GENLENS_INGEST_URL on the VPS to the verified HTTPS deployment
   hostname with /api/ingest/signals. Never assume a domain or bypass TLS.
   Check Vercel deployment protection separately; the VPS may be denied.
4. After a successful Genny or Marti compose, from agents/genny run:
   python3 scripts/genlens_push_ledger.py --ledger state/signal_ledger.json --dry-run
   For Marti use state/signal_ledger_marti.json.
5. Review the dry run. Repeat without --dry-run only on approved records.
   An explicit historical backfill requires --include-history.
6. Open the private /admin/verified-signals page, replay the same push,
   and confirm idempotency. A newly composed run should add an immutable
   event and, when newer, update the projection.

## Local test commands

- npx tsc --noEmit
- npx tsx --test tests/verified-signal-validation.test.ts
- python3 -m unittest discover -s agents/genny/tests -p test_push_ledger.py -v
- npm run build

Run and inspect the checks before merging. This branch has not been rolled out.

## Human editorial boundary

An agent's status of published means selection for its own briefing, NOT
independent human approval.

Marti's separate promotion gate requires three clean dates, source authority,
twenty attributed human card reviews, and repeat protection. Unified outputs
also require verified convergence and explicit approval.

The ingestion endpoint ONLY stores records. This branch does not make the
ledger public. Research documents in Drive remain hypotheses until checked
against current sources. The old auto-generated spreadsheet is NOT a
publication feed.

## Two-lane pilot after engineering acceptance

Start with five GTM engineers and five creative technologists. Each identifies
the core tools they use and one costly workflow problem. Deliver three curated
editions with evidence, practical implications, and next-step recommendations.

Measure returning readers, actual tests, and user-attributed decisions.
Track Weekly Verified Decision Actions (WVDA), not opens or impressions.
Ask for an actual paid commitment before selecting a subscription price.

Next engineering milestone: signed-in role-aware Signal → Decision cards with
human Test / Adopt / Avoid / Watch and an observable outcome. Keep the public
homepage and pricing work out of this bridge pull request.
