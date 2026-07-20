# Genny cross-device workflow

GitHub is the source of truth for Genny. The live Hermes profile is a deployment
target, not a place to make durable edits.

## Start every Genny work session

1. Inspect the working tree before changing files.
2. Pull the current branch with fast-forward-only semantics when the tree is clean.
3. If the pull cannot fast-forward or local Genny changes already exist, stop and
   explain the conflict instead of overwriting work.

The helper command is:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh pull
```

## Finish every Genny work session

1. Never commit `.env`, `state/`, logs, credentials, tokens, or generated caches.
2. Validate all Python and shell files.
3. Commit only changes under `agents/genny`.
4. Push the current branch to GitHub so another device can continue from it.
5. Report the branch and commit SHA to Jonathan.

The helper command is:

```bash
bash agents/genny/scripts/genny_workspace_sync.sh publish "Describe the Genny change"
```

If publishing is not authorized or authentication is unavailable, leave the
validated changes uncommitted and give Jonathan the exact command to run.

## Deploying to Hermes

After the desired Genny commit is on `main`, deploy from the VPS with:

```bash
curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash
```

The deployment must preserve `/root/.hermes/profiles/genny/.env` and
`/root/.hermes/profiles/genny/state/`.
