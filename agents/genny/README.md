# Genny - GenLens Intelligence Agent

GenLens is the intelligence system for the generative AI economy. Genny is its
production-intelligence lens for creative technologists working in
AI-accelerated visual production; Marti is its AI-native marketing and MarTech
lens. Both use one source-grounded editorial spine while remaining distinct
specialist voices.

Her job is to monitor AI creative production signals, compose GenLens briefings, and send polished email digests. The active GenLens verticals are Product Photography, AI Filmmaking, and Digital Humans. Expanded briefings also use on-deck verticals such as Advertising / Brand Content, ArchViz, Motion Graphics, Music Production, and Fashion / Apparel.

## What Is In This Project

- `AGENT.md` - Genny's operating persona and rules.
- `data/` - source registry, signal-record schema, tools manifest, preferences, backlog, NotebookLM seed bundle, and Jonathan feedback.
- `scripts/` - source scan, career intelligence, briefing composition, structured signal ledger, daily digest, retry digest, and Resend email delivery.
- `prompts/` - reusable prompt specs for signal scoring, briefing format, and delta extraction.
- `docs/` - setup and architecture notes.

For AI or human collaborators, start with
[`docs/GENNY_COLLABORATOR_PRD.md`](docs/GENNY_COLLABORATOR_PRD.md).
For the canonical product hierarchy, positioning, north-star metric, and
milestones, see [`docs/GENLENS_NORTH_STAR.md`](docs/GENLENS_NORTH_STAR.md).
For Marti's current evidence and promotion gate, see
[`docs/MARTI_MVP_EVALUATION.md`](docs/MARTI_MVP_EVALUATION.md).
For stable signal IDs, accepted/rejected review history, and runtime artifacts,
see [`docs/SIGNAL_LEDGER.md`](docs/SIGNAL_LEDGER.md).

No API keys, bot tokens, Google credentials, or Resend secrets are stored here.

## Core Commands

Compose an expanded briefing:

```bash
python3 scripts/genlens_compose_brief.py --mode expanded --per-vertical 5 --rss-limit 12 --out state/latest_brief.md
```

The composer also writes `state/signal_ledger.json`. Marti and unified runs use
their own suffixed ledger files.

Send a visual email:

```bash
python3 scripts/genlens_send_email.py \
  --to jj@example.com \
  --subject "GenLens briefing" \
  --text-file state/latest_brief.md \
  --template genlens-briefing
```

Run the daily digest fallback flow:

```bash
python3 scripts/genlens_digest.py
```

Scan career intelligence signals:

```bash
python3 scripts/genlens_career_intel.py \
  --limit 8 \
  --out-json data/career_signals.json \
  --out-md state/career_radar.md
```

Ingest a pasted job post or transcript:

```bash
python3 scripts/genlens_career_intel.py \
  --input-file /path/to/job-posts.txt \
  --out-json data/career_signals.json \
  --out-md state/career_radar.md
```

Run Marti without sending email:

```bash
python3 scripts/genlens_editorial_ops.py \
  --lens marti \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12
```

Run the unified lens without sending email:

```bash
python3 scripts/genlens_editorial_ops.py --lens unified --mode expanded
```

Marti and unified runs use separate brief, audit, preflight, and tool-candidate
artifacts. The existing Genny files are not overwritten. Add `--send` only after
the preflight reports `ready`.

## Sync The Live Hermes Profile

On the VPS, run this when the repo has updates but Genny is still using old behavior:

```bash
curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash
```

That command downloads the latest GenLens `main`, copies `agents/genny` into `/root/.hermes/profiles/genny`, preserves the live `.env` and `state/`, checks Python syntax, installs any declared Python requirements, and restarts `hermes-gateway-genny.service`.

If the repo is already cloned on the VPS:

```bash
bash agents/genny/scripts/sync_to_hermes_profile.sh --repo-dir /path/to/GenLens
```

## Work Across Mobile And Desktop

GitHub is Genny's source of truth. At the start of a session, update the local
checkout:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh pull
```

At the end of a session, validate, commit, and push only Genny files:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh publish "Describe the Genny change"
```

Repository instructions in `AGENTS.md` tell Codex to follow this handoff workflow
whenever it works inside `agents/genny`.

## Environment

Copy `.env.example` to `.env` and fill in your own values.

```bash
cp .env.example .env
```

Required for email:

- `RESEND_API_KEY`
- `GENLENS_EMAIL_FROM`

Optional for Hermes/OpenRouter:

- `OPENROUTER_API_KEY`
- `DISCORD_BOT_TOKEN`

## NotebookLM Status

NotebookLM is optional. Genny has a local NotebookLM source bundle at `data/genlens_notebooklm_bundle.md`, but NotebookLM itself still requires a human Google login session before it can be queried through the MCP.
