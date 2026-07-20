# Setup

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`.

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

Register the notebook:

```text
Name: Creative Autonomy
URL: https://notebooklm.google.com/notebook/7509454e-8872-477f-b67e-0e001ae91280
```

Then add `data/genlens_notebooklm_bundle.md` as a source after Google auth is complete.
