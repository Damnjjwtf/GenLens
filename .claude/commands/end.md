---
description: Wrap up the session — flag uncommitted work, unpushed commits, and dangling PRs
---

You are wrapping up a coding session. Run the checks below and give a tight close-out report.

## 1. Local state

- Uncommitted changes: `git status -sb`
- Untracked files — flag anything that looks accidental (`.env`, `.env.local`, secrets, build artifacts in `.next/`, large binaries, OS junk like `.DS_Store`)
- Unpushed commits on the current branch: `git log @{upstream}..HEAD --oneline` (or `origin/main..HEAD` if no upstream)

## 2. Remote state

- Open PRs the user authored: `gh pr list --author @me --state open --json number,title,reviewDecision,mergeable --jq '.[] | "#\(.number) \(.title) — review:\(.reviewDecision // "none") merge:\(.mergeable)"'`
- Any of those marked `MERGEABLE` and approved? Surface them as ready to merge.
- Any with `CHANGES_REQUESTED`? Surface them as needing my attention next session.

## 3. Recommend the next move

Based on what you found, do ONE of:

- **All clean** — branch matches origin, no uncommitted changes, no open PRs awaiting action: confirm with one line and exit.
- **Uncommitted work** — list what's modified, propose a commit message (conventional-commits style, scope from the affected files), and ASK before committing or pushing. Never push automatically.
- **Unpushed commits** — list them and ask whether to push. Note if pushing requires opening a PR vs landing on `main`.
- **Trailing follow-ups** — if the session leaves something incomplete (a half-finished migration, a TODO comment, an env var not yet wired), suggest whether it should land in BACKLOG.md, GAPS.md, or a new GitHub issue.

## 4. Memory hygiene

- Did anything come up this session that should be saved to user/project memory? (e.g. a workflow preference, a non-obvious project fact, a new external resource). If yes, propose the memory write. If no, skip this section.

Do NOT auto-commit, auto-push, or modify memory without asking. Report and recommend only.

Keep the report under 25 lines.
