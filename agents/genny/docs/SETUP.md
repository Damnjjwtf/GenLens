# Setup

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`.

## Exa Semantic Discovery

Exa is an optional discovery lane for finding recent articles that configured
RSS feeds miss. It is not an authority layer and its results do not bypass the
GenLens quality gate. Keep the key only in the Hermes profile environment:

```dotenv
EXA_API_KEY=...
GENLENS_EXA_ENABLED=1
GENLENS_EXA_MODE=missing
GENLENS_EXA_MAX_QUERIES=4
```

`missing` searches only verticals without qualified feed candidates. Use
`all` only for a deliberate source audit because it makes one Exa request per
selected vertical. A direct test run is:

```bash
GENLENS_EXA_ENABLED=1 \
GENLENS_EXA_MODE=missing \
python3 scripts/genlens_compose_brief.py \
  --mode expanded --lens genny --per-vertical 5 --rss-limit 12 \
  --include-exa --exa-max-queries 4 \
  --out state/exa_test_brief.md --ledger-out state/exa_test_ledger.json
```

The test reports candidates and rejections in the ledger. Homepages, generic
roundups, undated results, weak highlights, stale items, and Reddit results
without corroboration remain out of the briefing. Do not paste the Exa key
into GitHub, this repository, Discord, or chat.

## Hermes Profile Setup

Create or update a Hermes profile named `genny`, then copy:

```bash
cp AGENT.md ~/.hermes/profiles/genny/SOUL.md
cp docs/SOUL-compact.md ~/.hermes/profiles/genny/SOUL-compact.md
cp -R data ~/.hermes/profiles/genny/
cp -R prompts ~/.hermes/profiles/genny/
cp -R scripts ~/.hermes/profiles/genny/
```

Add secrets only to the Hermes profile `.env`, never to this repo.

## VPS Sync / Repair

If Genny is alive in Discord but still using old scripts, sync the profile from GitHub on the VPS:

```bash
curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash
```

What it does:

- downloads the latest `Damnjjwtf/GenLens` main branch if no local checkout is provided
- copies `agents/genny` into `/root/.hermes/profiles/genny`
- preserves `/root/.hermes/profiles/genny/.env`
- preserves `/root/.hermes/profiles/genny/state`
- updates `SOUL.md`, scripts, skills, prompts, data, and docs
- checks Python syntax before restart
- restarts `hermes-gateway-genny.service`

Dry run:

```bash
curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash -s -- --dry-run
```

## Suggested Cron

8am Pacific daily:

```cron
0 15 * * * /root/.hermes/profiles/genny/scripts/genlens_digest.py
```

Hourly retry:

```cron
15 * * * * /root/.hermes/profiles/genny/scripts/genlens_digest_retry.py
```

## NotebookLM

Registered NotebookLM sources are tracked in:

```text
data/notebooklm_sources.json
```

Then add `data/genlens_notebooklm_bundle.md` as a source after Google auth is complete.
