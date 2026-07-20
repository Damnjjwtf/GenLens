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

`data/genny_sources.json` is the source registry. Sources are grouped by vertical and should be treated as leads until verified.

`data/marti_sources.json` is Marti's separate source registry, grouped by stack
layer. `data/marti_signal_schema.md` defines its admission and confidence rules.

`data/genlens_tools_manifest.md` is the canonical tool taxonomy.

`data/genlens_vertical_backlog.md` tracks verticals that are on deck but not part of default daily coverage.

`data/jonathan_feedback.md` stores persistent product feedback from this chat.

`data/genlens_notebooklm_bundle.md` is the seed document for NotebookLM.

## Script Layer

`scripts/genlens_compose_brief.py` builds source-backed Markdown briefings from the local registry.

The composer accepts `--lens genny|marti|unified`. Marti and unified runs write
separate state files so they cannot overwrite Genny's latest briefing.

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
