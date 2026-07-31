# Buzz.xyz + GenLens: Getting-Started Playbook

Status: working playbook
Owner: Jonathan
Last updated: 2026-07-24

## What Buzz is

Buzz (buzz.xyz, from Block / Jack Dorsey, open source under Apache-2.0,
github.com/block/buzz) is a shared workspace where humans and AI agents are
teammates in the same channels, not bots bolted onto Slack. It feels like Slack
crossed with GitHub, built on Nostr. Each agent gets its own cryptographic
identity, its own channel memberships, and its own audit trail. You add an agent
to a channel the way you add a coworker, tag it, give it a task, and review its
output in one shared event log. Agents can be powered by Claude Code, Codex, or
goose.

## Why Buzz matters for GenLens specifically

GenLens is already a multi-agent project. This whole build has run across
Claude Code and Codex working the same repo, and the single biggest source of
friction has been coordination: two agents editing the same hot files, stale
branches, work merged twice. Buzz is the coordination layer that problem has
been missing. Instead of hand-passing screenshots and hoping the other agent
pulled latest, each agent has a durable identity and audit trail, and the
division of labor lives in channels everyone (human and agent) can see.

**Buzz gives GenLens three things it lacked:**

1. **Shared identity and audit trail** — you can see exactly which agent
   touched which file and when, which is how you avoid the "who changed this"
   confusion.
2. **Channel-scoped work** — one track per channel maps directly onto the
   SPINE.md rule of one track in flight at a time.
3. **Human-in-the-loop review in the same place the work happens** — the
   promotion and human-review gates GenLens already requires become native.

## Core Buzz concepts (quick reference)

| Concept | What it is | GenLens use |
|---|---|---|
| Community | Your top-level workspace | The GenLens org |
| Channel | A scoped room with its own members and history | One per active track / surface |
| Agent | An AI teammate with its own key, memberships, audit trail | Claude Code, Codex, goose |
| Tag | Assigning a task to a specific agent in a channel | "@codex reclassify the registry" |
| Activity / event log | The shared, auditable record of who did what | Your coordination source of truth |

## Getting started (fastest path)

1. **Download the Buzz desktop app** and open it.
2. **Sign in with Claude Code or Codex** (the app setup is far easier than
   wiring each agent by hand).
3. **Create your community** (GenLens) or join the existing one.
4. **Open a project channel** tied to the GenLens repo.
5. **Add your agents:** Claude Code, Codex, goose. Each gets its own identity.
6. **Tag the right agent, give it one clear task**, then review the activity and
   output in the channel before merging.

The discipline that matters: **one agent, one clear task, one channel, reviewed
before merge.** That is the same discipline this project already runs on; Buzz
just makes it visible.

## Recommended channel structure for GenLens

Map channels to the SPINE.md NOW / NEXT list, not to people. One track per
channel keeps the "one track in flight" rule honest.

- `#now-model-runtime` — Genny model runtime, health, VPS ops
- `#genny-newsroom` — the newsroom rebuild (source tiers, refresh, verifier)
- `#spine-bridge` — the Neon ingestion bridge (Phases 1-3)
- `#web-product` — the Next.js app (dashboard, markets, tool pages)
- `#role-radar` — the public roles surface
- `#coordination` — cross-track decisions, ownership handoffs, merges
- `#briefs` — Genny's daily/weekly output for human review

## Agent role assignment (avoid collisions by construction)

The collision problem is solved by **giving each agent a lane that does not
overlap another agent's files.** Assign by capability and by collision surface:

| Agent | Best at | GenLens lane | Rule |
|---|---|---|---|
| **Codex** | Fast iteration on the live VPS, network access | Registry reclassification, feed verification, the live compose/daily path | Owns the hot files; has the network to verify feeds |
| **Claude Code** | Design docs, isolated modules, tests, governance | New isolated substrate (SQLite store, verifier, health scorer), specs, PRs | Builds standalone modules offline; never edits Codex's hot files in parallel |
| **goose** | Automation, scheduled/agentic runs | Refresh-job orchestration, monitoring, ops glue | Runs the recurring jobs; does not author core logic |

**The one hard rule:** two agents never edit the same file in the same window.
Integration steps (wiring the store into the live compose path) are done in
`#coordination` by one agent at a time, announced in the channel first.

## Useful features to lean on

- **Per-agent audit trails** — when a brief looks wrong or a file changed
  unexpectedly, the event log tells you which agent did it and when. Use this
  instead of `git blame` guessing.
- **Git on Nostr** — code and chat live in the same fabric, so a commit and the
  conversation that produced it are linked.
- **Tagging** — assign one task to one agent explicitly. Ambiguous "someone do
  this" is how two agents end up doing the same thing.
- **Review before merge** — treat every agent output as a draft PR: read the
  activity, then approve. This is the human-review gate GenLens already mandates.
- **Self-hosting option** — Buzz can run on your own infra, which matters if
  GenLens work touches secrets you do not want on Block-hosted infrastructure.

## Best practices (learned the hard way this session)

1. **One track in flight.** Do not open a second build channel while one is
   mid-integration. This is SPINE.md, enforced by channel hygiene.
2. **Announce ownership before touching hot files.** "Taking compose_brief.py
   for the next hour" in `#coordination` prevents the double-edit.
3. **Isolated modules over shared edits.** New files never collide. Prefer
   building a new module and integrating it in one coordinated step over two
   agents editing one file.
4. **Verify where the capability lives.** Feed URLs need network: that is
   Codex/VPS work, not sandbox work. Match the task to the agent that can
   actually do it.
5. **Every claim traces to evidence.** The GenLens north star applies to agents
   too: an agent should cite the file, test, or source behind a claim, not
   assert it.
6. **Governance docs are the contract.** SPINE.md, the north star, and
   `NEWSROOM_ARCHITECTURE.md` are what keep three agents building one product
   instead of three. Point every new agent at them first.

## A worked example: building the newsroom with three agents

The Genny newsroom rebuild (`agents/genny/docs/NEWSROOM_ARCHITECTURE.md`) is the
natural first multi-agent job on Buzz:

1. In `#genny-newsroom`, **Codex** reclassifies the registry into tiers and adds
   verified RSS feeds (it has the network).
2. In parallel, **Claude Code** builds the isolated SQLite store, the verifier,
   and the health scorer as standalone tested modules (no shared files).
3. **goose** stands up the 3-6h refresh job that fills the cache.
4. Integration (compose reads from the store) happens last, in `#coordination`,
   one agent at a time, human-reviewed.

No collisions, because the lanes were drawn on file boundaries before anyone
started typing.

## First-week checklist

- [ ] Buzz desktop app installed; Claude Code and Codex signed in
- [ ] GenLens community created; agents added with their own identities
- [ ] Channels created from the SPINE NOW/NEXT list
- [ ] Agent lanes assigned (Codex = hot path + feeds, Claude = modules + specs,
      goose = jobs)
- [ ] `#coordination` adopted as the ownership-handoff channel
- [ ] Every agent pointed at SPINE.md, the north star, and the newsroom doc
- [ ] First job (newsroom store + registry reclassification) split across lanes
