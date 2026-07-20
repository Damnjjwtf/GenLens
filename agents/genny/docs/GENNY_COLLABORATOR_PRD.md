# Genny: Product and Collaboration Brief

Last updated: July 20, 2026

Use this document to onboard an AI collaborator, engineer, researcher, designer, or product partner to Genny. It combines product intent, operating knowledge, technical boundaries, and contribution instructions. Treat the repository as canonical and verify live behavior before claiming a deployment succeeded.

## One-sentence definition

Genny is the Hermes-powered intelligence agent behind GenLens: she turns verified changes in AI-assisted creative production into useful briefings, role intelligence, proof-build ideas, and product opportunities for working creative technologists.

## Product thesis

Creative professionals do not need another AI-news link feed. They need an editor that can distinguish a real production shift from noise and explain what changed, how it works, who can use it, and what it changes in cost, time, quality, rights, or labor.

Genny should become a compounding market-intelligence system:

1. Sources produce leads.
2. Verified leads become structured signals.
3. Repeated tool and workflow signals reveal changing roles.
4. Role clusters suggest small proof builds.
5. Repeated pain and proof builds reveal GenLens product opportunities.
6. Jonathan's feedback updates the system's editorial judgment.

The output is not “AI news.” The output is a decision advantage for people building and directing AI-accelerated creative work.

## Owner and audience

- Product owner: Jonathan James
- Product: GenLens, `https://genlens.app`
- Primary operator: Jonathan
- Primary audience: Gen ADs and creative technologists
- Core users: product photographers, VFX/CGI artists, AI filmmakers, digital-human directors, creative production leads, and adjacent emerging roles
- Default delivery: designed email through Resend, with a short Discord confirmation through Hermes

## Jobs to be done

Genny should help a user answer:

- What changed in AI creative production that is worth my attention?
- How does the capability enter a real production workflow?
- Does it reduce cost or time, increase iteration, improve control, or change legal risk?
- Which tools and vendors are becoming strategically important?
- Which creative roles are appearing or changing?
- What can I build this weekend to prove a new capability?
- Which repeated signals could become a GenLens product?

## Operating modes

### Signal Brief

A source-backed daily or requested briefing. This is the main publishing mode.

### Role Radar

Maps observed, emerging, and forecast roles from job posts, tool clusters, and workflow changes. Forecast roles must never be presented as existing jobs.

### Build This

Produces weekend-sized proof builds connected to a role, workflow, and tool stack. A proof build should create evidence, not merely a concept deck.

### Market Map

Connects companies, tools, sources, verticals, roles, and workflow clusters.

### Product Lab

Turns repeated user pain, source gaps, tool clusters, and proof-build patterns into GenLens product opportunities.

## Coverage model

Default daily coverage:

- Product Photography
- AI Filmmaking
- Digital Humans / Synthetic Actors

Expanded coverage may also include:

- Advertising / Brand Content
- ArchViz
- AI Design / Motion Graphics
- Music Production / Audio
- Fashion / Apparel / Textile
- Podcast / Long-Form Audio
- Education / E-Learning Content
- Social / Short-Form Video
- Game Development / Real-Time 3D
- Cross-Vertical Watchlist

Do not permanently promote an expanded vertical into default daily coverage without Jonathan's explicit approval.

## What qualifies as a signal

A publishable item should support at least three of these five fields:

1. Platform or technology
2. Core technical or workflow dynamic
3. Concrete production use case
4. Strategic impact
5. Verifiable source link

Prefer:

- releases, changelogs, papers, and meaningful model updates
- production case studies and workflow breakdowns
- changes in production economics, iteration speed, quality control, or rights
- APIs, SDKs, integrations, node graphs, automation layers, and pipeline changes
- job posts that reveal tool stacks, workflow verbs, and role changes

Reject or hold:

- product homepages and generic landing pages
- pricing pages without an actual pricing change
- stale listicles and generic how-to articles
- celebrity, entertainment, funding, or culture news without production relevance
- affiliate pages, coupons, generic “top tools” articles, and weak aggregators
- unsupported claims from community chatter
- an item that cannot connect to a concrete creative workflow

RSS, news searches, and community posts are discovery leads. Prefer primary sources for final verification.

## Editorial standards

- Default maximum item age: 45 days.
- Daily generation is feed-first.
- Manual vendor pages are normally watch-only or verification sources.
- Expanded briefings target five items per vertical when the evidence supports it.
- Never pad a weak vertical to hit volume.
- A missing vertical becomes a source-coverage gap, not a fake card.
- “No qualified feed signals” and other housekeeping notes must never render as public email cards.
- Do not send an exact recent URL fingerprint again.
- Require at least three new links versus recent send history unless Jonathan explicitly allows a repeat.
- Limit concentration by source, domain, and topic cluster.
- Do not use preview images. Use strong linked titles and visible source buttons.
- Never claim delivery without a Resend response ID.

## Voice

Warm, expert, direct, and useful. Never corporate. Never hype without evidence. Prefer a concrete production consequence over an adjective.

Good:

> Runway added controllable frame editing that lets a VFX artist revise generated plates before the Resolve conform.

Weak:

> Runway announced an exciting new update that will transform creativity.

## System architecture

```text
Source registry + feeds + searches
                |
                v
       source audit and scan
                |
                v
     quality, recency, URL, and
       false-positive filters
                |
                v
        Markdown brief composer
          /       |        \
         v        v         v
  tool curator  role radar  source-gap report
          \       |        /
                v
        editorial preflight
     cards / verticals / repeats
                |
       hold -----+----- send
                         |
                         v
                Resend HTML email
                         |
                         v
             sent-history record
```

Genny runs as the Hermes profile at `/root/.hermes/profiles/genny`. The systemd service is `hermes-gateway-genny.service`. GitHub `Damnjjwtf/GenLens`, directory `agents/genny`, is the durable source of truth. The VPS profile is a deployment target.

## Key files

| File | Responsibility |
|---|---|
| `AGENT.md` | Full persona, routing rules, editorial behavior, and safety constraints |
| `docs/SOUL-compact.md` | Compact Hermes prompt |
| `data/genny_sources.json` | Source registry grouped by vertical |
| `data/genlens_preferences.json` | Jonathan's persistent output and product preferences |
| `data/genlens_signal_schema.md` | Acceptance standard for publishable signals |
| `data/genlens_tools_manifest.md` | Canonical tool taxonomy |
| `data/role_signals.json` | Observed, emerging, and forecast role inputs |
| `data/genlens_product_strategy.md` | Product and market-intelligence direction |
| `data/jonathan_feedback.md` | Durable feedback from Jonathan |
| `scripts/genlens_compose_brief.py` | Fetches, filters, ranks, deduplicates, and composes briefs |
| `scripts/genlens_editorial_ops.py` | Runs the coordinated pipeline and enforces the send gate |
| `scripts/genlens_send_email.py` | Parses public cards, renders email, and calls Resend |
| `scripts/genlens_audit_sources.py` | Classifies source health and usefulness |
| `scripts/genlens_curate_tools.py` | Extracts and normalizes tool candidates |
| `scripts/genlens_role_radar.py` | Generates role, build, map, and product artifacts |
| `scripts/sync_to_hermes_profile.sh` | Deploys repository files to the VPS while preserving secrets and state |
| `scripts/genny_workspace_sync.sh` | Pulls or publishes Genny work across devices |

## State and secrets

These belong only on the live profile and must never be committed:

- `.env`
- `state/`
- `logs/`
- API keys, bot tokens, credentials, cookies, and auth material
- generated caches

Important runtime state includes:

- `state/latest_brief.md`
- `state/editorial_preflight.md`
- `state/sent_brief_history.json`
- `state/source_audit.md`
- `state/tool_curator_report.md`
- `state/genlens_role_radar.md`

## Primary commands

Run the coordinated editorial pipeline on the VPS:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_editorial_ops.py \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12 \
  --send
```

Run without `--send` to produce and inspect artifacts without delivering email.

Deploy the latest merged `main` to the VPS:

```bash
curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash
```

Check the live service:

```bash
systemctl status hermes-gateway-genny.service --no-pager
```

Pull Genny changes on a laptop or desktop:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh pull
```

Validate, commit, and push Genny changes:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh publish "Describe the Genny change"
```

## Send gate

The editorial coordinator defaults to:

- minimum 12 public cards
- minimum 5 represented signal verticals
- minimum 3 new links compared with recent sends
- no exact duplicate titles
- no exact recent URL fingerprint

`--force-send` may override the quality gate. `--allow-repeat` may override repeat protection. An AI collaborator must not use either flag unless Jonathan explicitly asks.

## Definition of done

A requested briefing is done only when:

1. Sources were fetched or audited.
2. Every public card passed the signal-quality rules.
3. The editorial preflight passed, or Jonathan explicitly approved an override.
4. The designed email was accepted by Resend.
5. The Resend response ID was reported.
6. A concise Discord confirmation was produced when appropriate.

A code or configuration change is done only when:

1. Repository instructions were followed.
2. Python and shell syntax checks passed.
3. Secrets and runtime state stayed untracked.
4. The change was pushed to GitHub for cross-device continuity.
5. The desired commit reached `main` before VPS deployment.
6. The service was verified as active after deployment.

## Current state as of July 20, 2026

- The GenLens email repeat bug has been fixed.
- Empty “No qualified feed signals” notes no longer render as cards.
- Sent URL fingerprint history is active.
- The default recency window is 45 days.
- False-positive filters have been tightened.
- Source feeds and searches have been improved.
- Last known successful Resend ID supplied by Jonathan: `a922f250-0826-420f-9652-7fbd11ad0e88`.
- The live `hermes-gateway-genny.service` was verified active after the July 20 repository sync.
- NotebookLM remains optional and requires a valid Google login session before use.
- Marti now exists as an MVP lens on the shared editorial pipeline.
- Marti has a separate source registry and signal schema, lens-specific state
  artifacts, email identity, source audit, quality gate, and no-send execution
  path.
- Unified mode can run both source registries and emit labeled convergence
  candidates for editorial verification.
- Marti's first expanded live-feed evaluation produced three qualified cards
  across Paid Media, Commerce, and SEO/AEO. The preflight correctly held the
  issue below the six-card threshold. Marti is operational but its source pool
  is not yet strong enough for default scheduled delivery.

## Known constraints

- The GenLens digest API previously showed a TLS hostname mismatch. Never bypass TLS verification.
- Source scanning is heuristic and depends on the quality and availability of external feeds.
- Manual vendor pages are often blocked, stale, or unsuitable as news sources.
- NotebookLM is not a source of truth and cannot be assumed authenticated.
- Desktop SSH to the VPS may be unavailable even when the Hermes service is healthy; use Spaceship Starlight's browser command line when needed.
- The live VPS may have an Ubuntu kernel update pending. Do not reboot casually during active repair work.

## Collaboration protocol for another AI

### Before changing anything

1. Read this document, `AGENT.md`, `AGENTS.md`, and the relevant implementation files.
2. Run `genny_workspace_sync.sh pull` if the working tree is clean.
3. Inspect Git status and preserve unrelated work.
4. State the intended change and the user-visible outcome.

### While working

- Prefer small changes tied to a measurable editorial or operational failure.
- Keep source registry edits separate from rendering changes when practical.
- Add tests or deterministic fixtures when changing parsing, filtering, repeat protection, or send gates.
- Do not weaken quality thresholds merely to increase card count.
- Do not introduce a new service, paid dependency, or secret without Jonathan's approval.
- Do not edit the live VPS as the only copy of a change.

### Before handoff

1. Compile all Python scripts.
2. Validate all shell scripts with `bash -n`.
3. Run the relevant pipeline without sending email.
4. Review generated cards for source quality, duplicates, stale dates, and housekeeping leakage.
5. Publish the Genny-only diff to GitHub.
6. Report the branch, commit, tests, deployment status, and any remaining risk.

## Suggested collaboration tasks

High-value work:

- deterministic tests for Markdown parsing and public-card filtering
- fixtures for stale, undated, duplicate, and false-positive signals
- normalized URL handling for tracking parameters and aliases
- better source-health scoring and replacement recommendations
- structured provenance from source lead through final email card
- a review queue for uncertain signals rather than silent rejection
- metrics for source yield, send quality, repeat rate, and vertical coverage
- role-signal extraction from real job posts
- proof-build scoring tied to evidence and user demand

Avoid starting with:

- a broad rewrite
- a new UI disconnected from the editorial pipeline
- higher briefing volume without better evidence
- autonomous sending without the current preflight gate
- scraping systems that ignore terms, robots policies, rate limits, or source rights

## Copy/paste prompt for an AI collaborator

```text
You are collaborating on Genny, the Hermes-powered GenLens intelligence agent.

Start by reading:
- agents/genny/docs/GENNY_COLLABORATOR_PRD.md
- agents/genny/AGENT.md
- agents/genny/AGENTS.md
- the implementation files relevant to the task

GitHub is the source of truth. The VPS profile is a deployment target. Never commit .env, state/, logs, tokens, credentials, or caches. Never weaken editorial gates, force-send, bypass TLS, or claim delivery without explicit evidence.

Before work, inspect Git status and pull safely. During work, preserve unrelated changes and tie each edit to a user-visible outcome. Before handoff, validate Python and shell syntax, run the relevant no-send path, review the diff, and push only Genny-related files. Report the branch, commit, checks, and whether the VPS was actually deployed.

Product standard: Genny is not a link aggregator. A publishable signal must explain what changed, how it works, who uses it, what production outcome it affects, and where the source proves it. If evidence is weak, keep researching instead of padding the briefing.
```

## Success metrics

Near-term operational metrics:

- zero repeated-email incidents
- zero housekeeping cards in public delivery
- zero unverified delivery claims
- increasing percentage of cards backed by primary sources
- decreasing stale-link and generic-landing-page rejection rate
- useful coverage across at least five verticals in expanded mode
- visible new-link count before every send

Longer-term product metrics:

- briefing open and click-through rate
- percentage of signals saved, shared, or acted on
- proof builds started from Genny recommendations
- tool and role hypotheses later confirmed by multiple sources
- GenLens products derived from repeated evidence rather than one-off ideation

## Non-goals

Genny is not:

- a general-purpose chatbot
- an indiscriminate AI-news scraper
- an affiliate tool directory
- a system that sends on schedule regardless of quality
- a replacement for source verification or human editorial judgment
- authorized to expose secrets, bypass security controls, or silently deploy unreviewed code
