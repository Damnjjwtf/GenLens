---
description: Sync, report state, and surface anything that needs attention before starting work
---

You are starting a new coding session. Run the checks below in parallel where safe, then give a tight report.

## 1. Sync the repo

- `git fetch origin --prune` (do not pull or merge yet)
- Read the current branch, ahead/behind count vs `origin/<branch>`, and any uncommitted or untracked files

## 2. Surface what's new

- New commits on `origin/main` not yet in local: `git log HEAD..origin/main --oneline`
- Open PRs against `main`: `gh pr list --state open --json number,title,headRefName,isDraft,reviewDecision,updatedAt --jq '.[] | "#\(.number) [\(.headRefName)] \(.title) — \(.reviewDecision // "no review")"'`
- PRs the user authored that have unaddressed review comments: `gh pr list --author @me --state open --search "review:changes-requested OR review:required"`

## 3. Surface what's pending

- First 3 unchecked items from BACKLOG.md (the deferred-features punchlist)
- First 3 unchecked items from GAPS.md (the launch blockers)
- Any commits with `WIP`, `TODO`, or `FIXME` in the message in the last 7 days: `git log --since='7 days ago' --grep='WIP\|TODO\|FIXME' --oneline`

## 4. Recommend the next move

Based on what you found, recommend ONE of:

- **Pull** — if behind and the working tree is clean: suggest `git pull origin <branch>` (don't run it; let me confirm)
- **Resolve divergence** — if both ahead and behind: explain what happened and offer rebase vs merge vs branch+PR
- **Resume in-flight work** — if there are uncommitted changes or unpushed commits: summarize what's there
- **Pick something new** — if everything is clean: surface the top BACKLOG/GAPS item and ask what I want to tackle

Do NOT auto-pull, auto-merge, auto-push, or run any destructive git command. Report and recommend only.

Keep the report under 25 lines. Be specific (file paths, branch names, PR numbers), not generic.
