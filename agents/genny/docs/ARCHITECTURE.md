# Architecture

Genny is a Hermes profile with four layers and two editorial lenses:

1. Persona and operating rules
2. Local source and memory files
3. Source scanning and briefing scripts
4. Delivery integrations

The `genny` lens covers generative creative production. The `marti` lens covers
marketing technology and distribution. `unified` runs both registries through
the same curation pipeline and may produce explicitly labeled convergence
candidates. The lenses share code but keep separate source taxonomies and
runtime artifacts.

## Persona Layer

`AGENT.md` defines voice, coverage modes, safety rules, source rules, and how to interpret Jonathan's requests. `docs/SOUL-compact.md` is the small prompt version.

## Data Layer

`data/genny_sources.json` is the source registry. Sources are grouped by
vertical and should be treated as leads until verified. Search-discovery
sources declare `trusted_domains`, while first-party domains are separately
declared in `primary_domains`; see `docs/GENNY_QUALITY_GATE.md`.

`data/marti_sources.json` is Marti's separate source registry, grouped by stack
layer. `data/marti_signal_schema.md` defines its admission and confidence rules.

`data/genlens_signal_record.schema.json` is the versioned contract for the
runtime signal ledger. The ledger preserves accepted and rejected observations
with stable source-derived IDs; see `docs/SIGNAL_LEDGER.md`.

`data/genlens_decision_queue.schema.json` is the versioned contract for the
runtime decision queue. It links explicit actor-attributed actions to verified
signal IDs; see `docs/DECISION_QUEUE.md`.

`data/genlens_convergence.schema.json` is the versioned contract for structured
Genny–Marti candidate pairs. Candidate generation and human review are separate
from the decision queue; see `docs/CONVERGENCE.md`.

`data/genlens_promotion_log.schema.json` is the versioned contract for dated
lens evaluations and attributed accepted-card reviews; see
`docs/PROMOTION_GOVERNANCE.md`.

`data/genlens_tools_manifest.md` is the canonical tool taxonomy.

`data/genlens_vertical_backlog.md` tracks verticals that are on deck but not part of default daily coverage.

`data/jonathan_feedback.md` stores persistent product feedback from this chat.

`data/genlens_notebooklm_bundle.md` is the seed document for NotebookLM.

## Script Layer

`scripts/genlens_compose_brief.py` builds source-backed Markdown briefings from
the local registry and records candidate reviews in the lens-specific signal
ledger. Genny applies a mandatory production-vertical, AI-mechanism,
concrete-event, confirmation, and publisher-trust gate before scoring.

`scripts/genlens_signal_ledger.py` canonicalizes evidence URLs, assigns stable
signal IDs, merges repeated observations, and writes the versioned ledger
atomically.

The composer accepts `--lens genny|marti|unified`. Marti and unified runs write
separate state files so they cannot overwrite Genny's latest briefing.

Runtime ledgers live at `state/signal_ledger.json`,
`state/signal_ledger_marti.json`, and `state/signal_ledger_unified.json`. They are
preserved across deployment and excluded from Git.

### Storage Boundary

The Hermes profile is an edge runtime, not the long-term product database.
Append-only JSON files under `state/` remain the durable local cache and audit
trail for a single Genny deployment. The GenLens web platform uses **Neon
Postgres** as its planned hosted system of record for users, signals, attributed
reviews, convergence decisions, and decision actions.

There is no implicit dual-write today. A future ingestion service must validate
the same versioned schemas, preserve stable signal and event IDs, and use
idempotency keys before copying runtime records into Postgres. Until that
service exists, local state remains authoritative for the VPS run that produced
it and must never be discarded during deployment.

`scripts/genlens_decision_brief.py` reads the validated current-run ledger and
renders evidence-bound operator recommendations into lens-specific
`state/decision_brief*.md` artifacts. It never writes queue events or claims
WVDA; see `docs/DECISION_BRIEF.md`.

`scripts/genlens_decision_queue.py` records explicit actions against
non-rejected signals, keeps an append-only event history, applies idempotent
mutations, manages queue state, and reports Weekly Verified Decision Actions.
Its runtime artifact is `state/decision_queue.json`, which is also preserved
across deployment and excluded from Git. The editorial pipeline does not create
decision events automatically.

`scripts/genlens_convergence.py` reads only the current published Genny and
Marti records in a validated unified ledger. It creates cross-lens hypotheses
from shared structured dimensions, maintains append-only attributed review
events, and appends only human-verified conclusions to a unified brief.

`scripts/genlens_promotion.py` records append-only issue evidence and human card
reviews, validates idempotency and chronology, and reports Marti promotion
status. The editorial send path fails closed when Marti evidence is absent or
incomplete; unified delivery additionally requires Marti promotion.

`scripts/genlens_send_email.py` sends visual Resend emails. It contains the GenLens briefing email template.

`scripts/genlens_digest.py` tries the GenLens API first. If the API fails, it falls back to the local source watcher.

`scripts/genlens_digest_retry.py` retries without spamming Discord unless the digest recovers.

## Delivery Layer

Genny currently supports:

- Discord through Hermes gateway
- Email through Resend
- Optional NotebookLM MCP after Google auth

## Known Constraints

- `https://genlens.app/api/digest/today` had a TLS hostname mismatch during setup, so Genny must not bypass TLS verification.
- NotebookLM cannot be fully automated without a Google login session.
- Source scanning is heuristic unless backed by a scraper service such as Apify, Firecrawl, or a custom ingestion pipeline.
