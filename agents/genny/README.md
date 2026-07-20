# Genny - GenLens Intelligence Agent

Genny is the Hermes profile behind GenLens: a source-grounded intelligence agent for creative technologists working in AI-accelerated visual production.

Her job is to monitor AI creative production signals, compose GenLens briefings, and send polished email digests. The active GenLens verticals are Product Photography, AI Filmmaking, and Digital Humans. Expanded briefings also use on-deck verticals such as Advertising / Brand Content, ArchViz, Motion Graphics, Music Production, and Fashion / Apparel.

## What Is In This Project

- `AGENT.md` - Genny's operating persona and rules.
- `data/` - source registry, tools manifest, preferences, backlog, NotebookLM seed bundle, and Jonathan feedback.
- `scripts/` - source scan, briefing composition, daily digest, retry digest, and Resend email delivery.
- `prompts/` - reusable prompt specs for signal scoring, briefing format, and delta extraction.
- `docs/` - setup and architecture notes.

No API keys, bot tokens, Google credentials, or Resend secrets are stored here.

## Core Commands

Compose an expanded briefing:

```bash
python3 scripts/genlens_compose_brief.py --mode expanded --per-vertical 5 --rss-limit 12 --out state/latest_brief.md
```

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
