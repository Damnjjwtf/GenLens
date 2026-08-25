# The Solo Builder's Guide to Buzz

A getting-started and operations guide for one person who wants to run Buzz
(Block's Nostr-based agent workspace) as a primary development environment,
and possibly turn it into revenue.

---

## As of

- **Repo read:** `block/buzz`, default branch `main`, latest commit `4d47aa8`
  ("feat(desktop): improve agent activity header ui (#3321)"), dated
  **2026-07-30**. Roughly 18.3k GitHub stars at read time (up from ~125 the
  week of the July 21, 2026 launch).
- **How it was read:** files were fetched from `raw.githubusercontent.com`
  and the GitHub web UI, then extracted. A few exact literal strings (for
  example the canvas REST path) are documented, not byte, verified, and are
  flagged inline as such. Everything tagged [SHIPPED] is either in the
  README's "Works today" column or confirmed in a cited source file.
- **Tagging:** every claim is tagged **[SHIPPED]** (Works today column, or
  verified in code), **[PARTIAL]** (Being wired up, or shipped with
  documented gaps), or **[VISION]** (Strong opinions / a VISION doc). If a
  claim could not be placed, it was cut.

### Drift this guide resolves against the repo

The repo is the authority. Two items in circulation are wrong or stale:

1. **Search backend is Postgres FTS, not Typesense.** [SHIPPED]
   `ARCHITECTURE.md` states search runs over an `events.search_tsv`
   generated `tsvector` column with a GIN index (`idx_events_search_tsv`),
   and there is a dedicated `crates/buzz-search` crate for it (`Cargo.toml`).
   `docker-compose.yml` ships Postgres, Redis, MinIO, Keycloak, Adminer, and
   Prometheus, and **no Typesense service**. The `TYPESENSE_API_KEY` and
   `TYPESENSE_URL` entries still sitting in `.env.example` are vestigial:
   nothing in the compose stack or the crate graph serves them. Treat
   Typesense as dead config.

2. **Git hosting is in the "Works today" column now.** [SHIPPED] The
   README status table lists "git events, git hosting" under Works today,
   and `Cargo.toml` carries `crates/git-sign-nostr` and
   `crates/git-credential-nostr`. This moved from aspiration into shipped.

Unverified items from earlier briefs that do **not** appear in the repo, and
are therefore excluded: agent Lightning wallets (NIP-47/L402), FEDSTR
marketplaces, and a named "self-compacting context engine." No `lightning`,
`wallet`, `l402`, or `fedstr` crate exists in `Cargo.toml`. (Mesh compute
*does* exist and is covered below, tagged honestly.)

---

## 0. Two paths in, and which one to take first

**Take the packaged desktop build first.** [SHIPPED] You do not need to
compile anything to open Buzz. The README points at
`https://github.com/block/buzz/releases/latest` with builds for macOS
(`.dmg`), Linux (`.AppImage` / `.deb`), and Windows (`.exe`). Install it,
point it at a relay, and you have a working client. Do this before touching
Docker.

By default a fresh desktop build talks to Block's hosted relays. The
`Justfile` hardcodes the two hosted endpoints it can target:

- production: `wss://buzz.block.builderlab.xyz`
- staging: `wss://sprout-oss.stage.blox.sqprod.co`

Point the client elsewhere with `BUZZ_RELAY_URL` (see Section 1). Remember
the hosted relay is **not end-to-end encrypted** (Section 1, and
`SECURITY.md`), so it is fine for evaluation, not for client-confidential
work.

### The self-host path (from source)

This is the daily-driver path for a builder who wants their own relay.
Verified against the current `README.md` and `Justfile`:

```bash
git clone https://github.com/block/buzz.git && cd buzz
. ./bin/activate-hermit      # activates the Hermit-pinned toolchain
just setup && just build     # one time: docker up, migrate, deps, cargo build
just dev                     # daily: local relay + desktop app in dev mode
```

- `just setup` runs `bootstrap` (installs dev tools via Hermit, validates
  Docker, creates `.env` from `.env.example`) then `./scripts/dev-setup.sh`
  (starts Docker services, applies migrations, installs desktop deps).
  [SHIPPED] (`Justfile`)
- `just build` is `cargo build --workspace`. [SHIPPED] (`Justfile`)
- `just dev` validates ports, builds sidecar tools, health-checks the relay,
  then launches the local relay plus desktop app. It accepts a `mesh=1`
  flag to enable mesh-LLM features (Section 6 / Known Limitations).
  [SHIPPED] (`Justfile`)

**Toolchain requirements** [SHIPPED] (`README.md`): Docker plus Hermit, or a
manual toolchain of Rust 1.88+, Node 24+, pnpm 10+, and `just`. The default
local relay listens on `ws://localhost:3000` (`.env.example`:
`RELAY_URL=ws://localhost:3000`, `BUZZ_BIND_ADDR=0.0.0.0:3000`).

**Windows** [SHIPPED] (`README.md`): install Git for Windows so a Git Bash
is present. Optionally set `BUZZ_SHELL` to an alternative bash-compatible
shell path. `BUZZ_SHELL` is consumed by the dev MCP shell tool (Section 2),
not by the relay, and it is **not** present in `.env.example`, so treat it
as an environment override you set yourself, not a config-file key.

Useful adjacent recipes, all verified in `Justfile`: `just down` (stop
services, keep data), `just ps`, `just logs`, `just reset` (wipe dev state,
keep installed Buzz), `just migrate` (`cargo run -p buzz-admin -- migrate`
plus seed local community), `just relay` (run just the relay).

---

## 1. Identity and the relay

### secp256k1 keypairs as identity

Identity in Buzz is a secp256k1 (Nostr) keypair. There is no account server;
your public key (npub) *is* your identity, portable across any relay or
community that will admit it. [SHIPPED] (`VISION.md`: "Keypair-based
identity (secp256k1) portable across communities.")

Bootstrap one with the operator CLI:

```bash
buzz-admin generate-key
```

This prints a public key and a secret key, and tells you to
`Set BUZZ_PRIVATE_KEY to the secret key to use this identity.` [SHIPPED]
(`crates/buzz-admin/src/main.rs`, clap command `GenerateKey`: "Generate a
new Nostr keypair (for bootstrapping)".)

What portable identity actually buys you: the same npub can present itself
to a second community and repost a profile there. What it does **not** buy
you: shared state. Per `VISION_AGENT.md`, "no agent state is inherited
across hosts", your profile, presence, DMs, memories, jobs, channel
memberships, and audit trail are all scoped to the community behind a given
relay URL. Portability is of the *key*, not of the *history*. [SHIPPED]

### The agent-facing surface

Agents authenticate exactly like humans, with a keypair and Schnorr
signatures (NIP-42 over WebSocket, NIP-98 over REST). [SHIPPED]
(`SECURITY.md`.) Two env vars drive an agent identity:

- `BUZZ_PRIVATE_KEY` (required): 32-byte hex or `nsec1...`. [SHIPPED]
  (`.env.example`, marked REQUIRED under the ACP section.)
- `BUZZ_RELAY_URL`: which relay/community to join, default
  `ws://localhost:3000`. [SHIPPED] (`.env.example`.)

`buzz-cli` is the scriptable agent surface. [SHIPPED] It groups operations
into `messages`, `channels`, `canvas`, `reactions`, `dms`, `users`,
`workflows`, `repos`, `upload`, `mem`, `social`, `feed`, and `pack`
(persona packs). Example:

```bash
export BUZZ_PRIVATE_KEY="nsec1..."
export BUZZ_RELAY_URL="ws://localhost:3000"
buzz messages send --channel <uuid> --content "Hello"
buzz channels list
```

(Subcommand groups and examples from `crates/buzz-cli`. Output is JSON on
stdout, errors to stderr with exit codes.)

### Scoping by identity, not permission flags

This is the single most important mental model, and it is deliberately
minimal. **Channel membership is the sole access gate.** [SHIPPED]
(`SECURITY.md`: "Channel membership is the sole access gate. No role-based
ACLs or capability systems exist. Non-members cannot access private
channels.")

So you do not scope an agent by handing it a permission set. You scope it by
*which key it holds* and *which channels that key is a member of*. An agent
that should only see the `#triage` channel gets a keypair that is a member
of `#triage` and nothing else. There is no finer-grained capability layer
underneath that. The one role distinction that exists is at the relay
membership level: `buzz-admin add-member --pubkey <npub|hex> --role
<admin|member>` (`crates/buzz-admin/src/main.rs`). "admin" vs "member" is
relay-wide membership management, not per-channel capabilities.

Practical consequence for Section 5: your agent roster is a **key-and-
membership design**, not a permissions matrix. If you would not give a human
teammate a key to a room, do not give an agent one.

### The hash-chain audit log: what it does and does not guarantee

Every action is a signed Nostr event, and `buzz-audit` maintains a
SHA-256 hash-chained, tamper-**evident** log (10 audit actions, per-community
chains in multi-community mode). [SHIPPED] (`ARCHITECTURE.md`;
`crates/buzz-audit`.)

Be precise about the guarantee. Per `SECURITY.md`: the audit log is
"tamper-evident but not tamper-resistant (database attackers can rewrite
chains)." [SHIPPED] So:

- It **does** give you a cryptographically linked, signed record of who
  (which key) did what, in order, such that after-the-fact edits break the
  chain and are detectable *if you have an untampered reference point*.
- It **does not** stop someone with write access to the Postgres database
  from rewriting the chain wholesale. Tamper-evidence only helps if you
  externalize a checkpoint (export chain heads off-box) that an attacker
  cannot also rewrite. Nothing in the repo does that externalization for
  you. If you sell provenance (Section 7), this boundary is the whole game.

### Self-hosting the Rust relay

The real local stack, from `docker-compose.yml` [SHIPPED]:

| Service | Image | Role |
|---|---|---|
| postgres | `postgres:17-alpine` | System of record (events, channels, workflows, audit) |
| redis | `redis:7-alpine` | Pub/sub fan-out, presence, typing |
| minio | `minio/minio:latest` | S3-compatible media store (via Blossom / `buzz-media`) |
| minio-init | `minio/mc:latest` | Creates the media bucket, sets policy |
| keycloak | `quay.io/keycloak/keycloak:26.0` | Auth service (dev mode) |
| adminer | `adminer:latest` | Web DB admin |
| prometheus | `prom/prometheus:latest` | Metrics |

Note what is **not** here: no Typesense (search is Postgres FTS, above), and
no relay container. The relay is a Rust binary you run with `just relay`
(`cargo run -p buzz-relay`) or `just dev`, against the compose stack.
[SHIPPED] (`Justfile`.)

Media lives in S3/MinIO through the Blossom protocol (`crates/buzz-media`,
50 MB upload cap). [SHIPPED] Configuration keys in `.env.example`:
`BUZZ_S3_ENDPOINT`, `BUZZ_S3_ACCESS_KEY`, `BUZZ_S3_SECRET_KEY`,
`BUZZ_S3_BUCKET`, `BUZZ_S3_REGION`, `BUZZ_S3_ADDRESSING_STYLE`.

**Honest operational cost for a team of one.** This is six-plus moving
parts (Postgres 17, Redis 7, MinIO, Keycloak, Prometheus, the relay
process, plus a reverse proxy you must add for TLS). The relay itself does
not terminate TLS: per `SECURITY.md`, "TLS termination required at reverse
proxy or relay; relay itself doesn't enforce TLS." So a real deployment is:
provision a host, run the compose stack, run the relay, front it with
Caddy/nginx/Traefik for `wss://`, back up Postgres and the MinIO bucket, and
scrape Prometheus. None of that is exotic, but it is a standing service you
now operate. For a single builder, budget it like running your own small
SaaS backend, because that is what it is. This operational weight is exactly
the thing you can sell (Section 7).

### Multi-community mode

One relay URL selects one community by default; a hosted operator can serve
many communities on one deployment. [SHIPPED] (`VISION.md`: "Run your own
relay for one community, or let an operator host thousands on shared
infrastructure, same OSS codebase.") Isolation is real: profiles, DMs,
memories, and audit chains are per-community, and search queries are fenced
to their `community_id` via community-leading btree filters BitmapAnd-ed
with the GIN probe (`ARCHITECTURE.md`).

For a solo builder serving multiple clients off one box: this is your
tenancy model. One relay, one Postgres, N communities, each client's data
and audit chain isolated by `community_id`. That is the technical basis for
the deployment offering in Section 7, and it is why you can amortize one
hardened deployment across several paying clients.

### End-to-end encryption: there isn't any

State this plainly to any client. Per `SECURITY.md`: "No end-to-end
encryption. The relay stores events in plaintext. All encryption
responsibility rests with clients." [SHIPPED] This is not specific to the
hosted relay. **Nothing** is E2E today. Self-hosting does not add E2E; it
just means *you* hold the plaintext database instead of Block. For a
privacy-sensitive team the only lever is self-hosting plus disk/transport
encryption you add yourself, and even then your own DB admin can read
everything.

---

## 2. The swappable harness (ACP + MCP)

### buzz-acp: relay mentions to agent subprocesses

`buzz-acp` bridges relay `@mentions` to agent subprocesses over ACP
(Agent Communication Protocol, JSON-RPC). [SHIPPED] (`ARCHITECTURE.md`;
`crates/buzz-acp`.) Mechanics, verified:

- **Agent pool: 1 to 32 subprocesses**, default 1
  (`.env.example`: `BUZZ_ACP_AGENTS=1`; `ARCHITECTURE.md` confirms the 1-32
  range and a claim/return pool lifecycle). [SHIPPED]
- **Per-channel queuing:** at most one prompt is in flight per channel;
  queued events are batched into a single `session/prompt`. [SHIPPED]
  (`ARCHITECTURE.md`.)
- **Crash recovery:** a crashed agent subprocess is detected and respawned;
  no persistent state is kept between runs. [SHIPPED] (`ARCHITECTURE.md`.)

### Model-agnosticism in practice

The agent command is a swappable subprocess. `.env.example` defaults it to
goose (`BUZZ_ACP_AGENT_COMMAND=goose`, with `BUZZ_ACP_MODEL` for the model
ID). [SHIPPED] Because the harness speaks ACP to whatever binary you name,
you can point it at Claude Code, Codex, or goose per agent by changing that
command. The `Justfile` ships first-class goose recipes (`just goose`,
`just goose-bg`), which tells you goose is the best-trodden path today.

What survives a harness swap: the identity (the keypair), channel
memberships, the audit trail, and the relay-side queue and pool behavior are
all in Buzz, not in the agent. What does not survive: any in-agent memory or
context, since the harness keeps no persistent state between runs (above).
Buzz gives agents a durable memory surface of its own via `buzz mem`
(`ls/get/hash/set/patch/rm`), so cross-run state should live there, keyed to
the agent, rather than inside the harness process. [SHIPPED]
(`crates/buzz-cli`.)

### buzz-dev-mcp: the shell and file tools, and the safety boundary

This is the highest-stakes claim in the whole system, so read it carefully.

`buzz-dev-mcp` is an MCP server that gives an agent local tools. Registered
tools (from `crates/buzz-dev-mcp/src/lib.rs`) [SHIPPED]:

- `shell`: runs bash commands (or cmd/PowerShell via `BUZZ_SHELL`). Output
  is capped ~8 KB for the model, with full output up to 10 MB saved to an
  artifact.
- `read_file`: reads text files with line numbers, offset/limit windowing.
- `view_image`: loads images from file, HTTP(S), or data URL, resized to
  max 1568px.
- `str_replace`: atomic find-and-replace in files.
- `todo`, plus lifecycle hooks `_Stop` and `_PostCompact` (the latter
  persists todo state across the agent's context compaction).

**The sandbox boundary, stated plainly: there isn't one.** The code
resolves paths relative to a workdir that defaults to the server's current
directory, but enforces **no** working-directory confinement, **no** path
allowlist or denylist, and **no** command filtering. The only confined
behavior is `view_image`, which may not escape the workdir. `shell` executes
with the **full privileges of the user/process that launched the harness**.
The Windows `CREATE_NO_WINDOW` flag suppresses a console window; it is not a
security boundary.

The consequence for a solo builder: an agent wired to `buzz-dev-mcp` can run
any command your user account can run, read and edit any file that account
can reach, and reach the network. Buzz's identity scoping controls *which
channels an agent sees*; it does **not** contain what the agent's shell can
*do* to the host. If you need isolation, you must provide it at the OS
layer: run each harness as a dedicated low-privilege user, inside a
container, or on a throwaway VM, with the workdir pointed at a project
checkout and nothing sensitive reachable from that account. Do not run a
`buzz-dev-mcp`-backed agent as your own login user on a machine that holds
secrets. This is the load-bearing hardening item in Section 7.

---

## 3. Branch as room

The core idea: a feature branch becomes a channel, patches land as NIP-34
git events, CI results post into the room, and the merge decision lives
beside the evidence. [SHIPPED for the plumbing] (`VISION.md`: "Git repos
hosted on the relay; branches map to channels automatically. When the branch
merges, the channel archives into a permanent record of why that code
exists.")

### Git hosting and nostr-signed git

Git hosting and NIP-34 git events are in the Works today column
(`README.md`), backed by two crates you set up as git helpers [SHIPPED]:

- `git-sign-nostr` (`crates/git-sign-nostr`): signs git objects with your
  Nostr key, so commit/patch provenance ties to the same identity as
  everything else.
- `git-credential-nostr` (`crates/git-credential-nostr`): a git credential
  helper that authenticates git operations against the relay with your Nostr
  key.

Repo and branch operations are exposed through `buzz-cli`'s `repos` group:
`create`, `get`, `list`, and `protect` (branch protection), for example
[SHIPPED] (`crates/buzz-cli`):

```bash
buzz repos create --id my-service
buzz repos list
buzz repos protect set --id my-service --ref refs/heads/main --push admin
```

### Where this falls short of a GitHub replacement

Be blunt with yourself and clients. This is git *hosting and signing over
Nostr*, not a GitHub-equivalent product:

- **CI** is "results post into the room." Buzz does not ship a CI runner;
  something external must run the build and post back. The `Justfile` is
  your build surface, not a hosted CI. [PARTIAL / integrate-yourself]
- **Issues** have a forum-post kind (`KIND_FORUM_POST` 45001,
  `KIND_FORUM_COMMENT` 45003 in `ARCHITECTURE.md`) but there is no
  issue-tracker product with labels, milestones, and triage UI. [PARTIAL]
- **PR review ergonomics** (line comments, review states, required
  reviewers) are not a shipped GitHub-style flow. Branch protection exists
  at the `repos protect` level; a full review UI does not. [PARTIAL]

Treat Buzz git as "the room where the code conversation and signed patches
live," and keep GitHub/GitLab if you need the review and CI product surface.

### Parallel worktrees for one person, many agents

To run several agents on separate branches without collisions, use plain git
worktrees so each agent gets its own checkout on its own branch:

```bash
# from your main clone
git worktree add ../buzz-feature-a -b feature-a
git worktree add ../buzz-feature-b -b feature-b

# point each agent harness at its own workdir, e.g. run the ACP harness
# with cwd = ../buzz-feature-a for the agent on feature-a
git worktree list
git worktree remove ../buzz-feature-a   # when the branch is done
```

Each worktree is an independent working directory, so two agents editing
`feature-a` and `feature-b` never fight over the index or the checkout. Pair
this with the OS-level isolation from Section 2: one low-privilege user or
container per worktree keeps the unsandboxed `shell` tool boxed to that
branch's files.

---

## 4. Canvas, huddles, and workflows

### Canvas (kind 40100)

Canvas is a persistent, replaceable surface. `KIND_CANVAS = 40100` is a
`pub const` in `crates/buzz-core/src/kind.rs`. [SHIPPED] It is exposed
through `buzz-cli` as `buzz canvas get` / `buzz canvas set`
(`crates/buzz-cli`) [SHIPPED], and per the README/API is reachable over REST
at `/api/channels/{channel_id}/canvas` (documented path, not byte-verified
in this read).

The pattern to exploit: canvas is a per-channel durable document that
survives the chat scroll. Use it for the thing a channel keeps returning to,
a task board, a running diff, an architecture sketch, a decision log, so the
"current state" is one addressable surface rather than something you
reconstruct from message history.

### Huddles

Real-time voice lives inside `buzz-relay` (`src/audio/`), not a separate
service. [SHIPPED] (`ARCHITECTURE.md`.) Verified specifics:

- WebSocket Opus relay: endpoint `wss://.../huddle/{channel_id}/audio`,
  opaque Opus frames with an 8-byte header.
- NIP-42 challenge per participant; channel-membership check at admission.
- Soft cap ~25 peers (hard cap 255 via a `u8` peer index).
- **No external SFU:** peers relay frames through the relay itself.
- Lifecycle events (joined / left / ended) are emitted as Nostr events; last
  peer out archives the room atomically.

**Not built:** recording and per-track publishing. The kinds are reserved
but there is no producer. [PARTIAL] (`ARCHITECTURE.md` §9 item 4.) If a
client needs a recorded review session, you must capture it out-of-band.

### buzz-workflow (YAML automation)

`buzz-workflow` is a YAML-as-code automation engine (`crates/buzz-workflow`).
[SHIPPED for the engine, with stubs] Verified from `ARCHITECTURE.md`:

- **4 trigger types:** message, reaction, schedule, webhook.
- **7 actions**, executed with an `evalexpr` condition layer (100 ms
  timeout) and a Semaphore (100 permits).
- Webhook URLs are SSRF-protected against private/loopback ranges
  (`SECURITY.md`).

Flag the gaps clearly:

- **Approval gates are not wired end-to-end.** [PARTIAL] The executor
  returns `StepResult::Suspended`, and the relay has grant/deny endpoints
  with DB CRUD, but the engine intercepts before creating `WaitingApproval`
  rows, so a run that hits an approval gate is marked **Failed** (issue
  WF-08, `ARCHITECTURE.md` §9 item 5). A `buzz workflows approve`
  subcommand exists in the CLI, but the persistence path behind it is not
  complete. Do not design a workflow whose safety depends on an approval
  gate today.
- **Two actions are stubbed:** `send_dm` and `set_channel_topic` are in the
  schema but return `NotImplemented`; a run that reaches one fails at
  execution (issue WF-07, `ARCHITECTURE.md` §9 item 6). Verify any action
  you depend on actually executes before you build on it.

### buzz-persona (agent persona packs)

`buzz-persona` (`crates/buzz-persona`) is the closest thing to a supported
way to give an agent a stable role. [SHIPPED, as packs] Persona packs are
handled through `buzz-cli`'s `pack` group: `buzz pack validate` and
`buzz pack inspect` (`crates/buzz-cli`). Use packs to pin an agent's
role/definition as a versioned, inspectable artifact rather than ad-hoc
prompt text.

Honest limit of this read: the per-field pack schema (exact keys such as
system prompt, model, tool bindings, channel bindings) is not fully
enumerated in the files I could read, `crates/buzz-persona` has no README in
the tree. Treat "persona packs configure a stable agent role and are
validated/inspected via `buzz pack`" as [SHIPPED], and treat the exact field
list as **unverified**, confirm against `crates/buzz-persona` source before
you promise a client a specific field.

### Frame-anchored media comments

Comments can be pinned to specific points in a video. [SHIPPED]
(`README.md`: "Frame-anchored comments on video playback.") Noted here; it is
the concrete hook for the AI-filmmaker vertical in Section 7.

---

## 5. A solo builder's agent roster (a pattern, not product features)

This is the missing layer: the repo ships reference docs but no roster
patterns or scoping guidance. Below is a design *pattern* for one person
running a small portfolio. The role names are descriptive, not Buzz
built-ins. Each agent is a **keypair plus a channel-membership set** (there
is no finer permission layer, Section 1), and its "must not touch" list is
enforced by *omission*: if a key is not a member of a channel and not
launched with `buzz-dev-mcp`, it cannot reach that room or that shell.

Design rules that fall out of the architecture:

- Scope = key + memberships. Give each agent its **own** keypair
  (`buzz-admin generate-key`) and add it only to the channels it needs
  (`buzz-admin add-member` / `buzz channels join`).
- Only agents that must change files get `buzz-dev-mcp`. That tool is
  unsandboxed (Section 2), so every agent holding it needs an OS-level box
  (dedicated user / container / VM).
- Keep write-capable agents on their own worktree (Section 3).
- Prefer read/post-only agents; they cannot damage a host.

| Role | Harness | Channels (member of) | Tools / scope | Explicitly NOT allowed |
|---|---|---|---|---|
| **Reviewer** | Claude Code or goose via `buzz-acp` | the per-branch review rooms only | read repo + post review comments; `buzz repos get`, `messages send`; **no** `buzz-dev-mcp` write | no shell, no merge, not a member of any client's private ops channel |
| **Triager** | goose via `buzz-acp` | `#inbox` / `#triage` only | read new messages, label/route, open forum posts; `messages`, `reactions`, `feed` | no repo write, no shell, cannot post in delivery channels |
| **Release-notes writer** | any ACP agent | `#releases` + read access to merged branch rooms | read merged-branch history, write to canvas/`#releases`; `canvas set`, `messages send` | no shell, not in client-confidential channels, cannot trigger deploys |
| **Research agent** | ACP agent with web-enabled harness | `#research` only | read/post, fetch external sources, write findings to canvas | no `buzz-dev-mcp` shell, no repo write, no membership in any customer channel |
| **Build/CI runner** (only if you need file writes) | ACP agent **with** `buzz-dev-mcp` | one project's build room only | `shell` + `str_replace` in a single worktree, posts CI results | runs as a **dedicated low-priv user in a container**; no access to secrets, other projects, or your login user's home |

The deliverable form of this table (see Section 7) is exactly what you sell
as "agent roster design": for each agent, its key, its membership list, its
tool grant, and its written prohibitions, checked into a repo as the org's
source of truth.

---

## 6. Known limitations (required section)

Drawn from `ARCHITECTURE.md` §9 and my own reading. Everything here is a
real, current gap as of commit `4d47aa8`.

1. **Rate limiting is defined but not enforced.** [PARTIAL] The
   `RateLimiter` trait exists in `buzz-auth`, but the only implementation is
   `AlwaysAllowRateLimiter`, a test stub gated behind
   `#[cfg(any(test, feature = "test-utils"))]`. `RateLimitConfig` defines 4
   tiers (human, agent-standard, agent-elevated, agent-platform); none are
   enforced. A runaway or hostile client is not throttled by Buzz. (§9.2)
2. **Approval gates are not wired end-to-end.** [PARTIAL] Runs that hit an
   approval gate are marked Failed, not suspended (WF-08). Do not rely on
   them for safety. (§9.5)
3. **Two workflow actions are stubbed.** [PARTIAL] `send_dm` and
   `set_channel_topic` return `NotImplemented`. (§9.6)
4. **Huddle recording and per-track publishing are absent.** [PARTIAL]
   Kinds reserved, no producer. (§9.4)
5. **The dev MCP shell tool is unsandboxed.** [SHIPPED, and it is the risk]
   `buzz-dev-mcp` `shell` runs with full user privileges, no workdir
   confinement, no command filter (`crates/buzz-dev-mcp/src/lib.rs`,
   Section 2). Isolation is the operator's job.
6. **No end-to-end encryption anywhere.** [SHIPPED reality] The relay stores
   plaintext (`SECURITY.md`). Self-hosting relocates the plaintext to you;
   it does not encrypt it end-to-end.
7. **Audit log is tamper-evident, not tamper-resistant.** [SHIPPED] A DB
   writer can rewrite chains (`SECURITY.md`). Provenance claims need an
   external checkpoint you build yourself (Section 1).
8. **No compile-time query checking.** [PARTIAL] Uses runtime
   `sqlx::query()`, no `.sqlx/` offline cache (§9.1). A schema drift shows
   up at runtime, not at build.
9. **Authorization is membership-only.** [SHIPPED, by design] No RBAC or
   capability system beyond channel membership and relay-level admin/member
   (`SECURITY.md`). Fine-grained least-privilege must be expressed as key +
   membership design, not policy.
10. **Mesh compute is real but feature-flagged and not in "Works today".**
    [PARTIAL] `crates/buzz-relay-mesh` exists; `VISION.md` describes it as
    shipped ("Relay communities can pool opted-in member hardware into
    shared AI compute" via an OpenAI-compatible endpoint, membership-gated);
    the `Justfile` gates it behind `mesh=1` with dedicated e2e and
    hardware-inference recipes (`mesh-dev-fresh`, `mesh-e2e-hardware`,
    `mesh-e2e-confidence`). But it is **absent from the README Works-today
    table**, and `VISION_AGENT.md` frames the multi-community-on-shared-
    infra story as isolation rather than true peer compute. Treat mesh as
    experimental/opt-in, not a stable dependency. The transport specifics
    (for example QUIC) are **unverified** in this read.
11. **Mobile clients are in progress.** [PARTIAL] Flutter iOS/Android are in
    the "Being wired up" column (`README.md`). Desktop (Tauri + React) is
    shipped.
12. **Some polish features are planned only.** [VISION] Web-of-trust
    reputation, push notifications, and "culture" features (polls, kudos,
    knowledge crystallization) are in the "Strong opinions, pending code"
    column or marked planned in `VISION.md`.

### Adopt today, or watch?

**Position: adopt now as a *second* system for your agent fleet, if and only
if you can self-host and run the OS-level isolation. Do not adopt it as your
team's primary chat or as a GitHub replacement yet.**

The reasoning. The parts a solo builder actually needs are shipped and
coherent: keypair identity, per-agent audit trails, the ACP harness with a
1-32 pool and per-channel queuing, git hosting with nostr-signed commits,
canvas, huddles, and a real (if stub-dotted) workflow engine. That is a
genuinely differentiated substrate for running agents as first-class,
audited members. Nothing comparable ships this today.

But the gaps are not cosmetic for production: no enforced rate limiting, no
E2E encryption, an unsandboxed shell tool, approval gates that fail closed by
failing the run, and a tamper-evident-but-not-resistant audit log. Those are
survivable for *your own* development environment where you control the host
and the blast radius. They are not yet survivable as the sole system of
record for a paying client's confidential work unless you add the missing
controls yourself. Which is exactly the opening in Section 7.

Watch-only is the wrong call because the differentiator (agent identity plus
signed audit) is real and available now, and the switching-cost window is
finite. Full-primary-adoption is the wrong call because you would be betting
a client's compliance posture on controls that are documented as absent.
Second-system adoption captures the upside and contains the downside.

---

## 7. The commercial angle: selling this to businesses

### Lead with the trap

**Buzz is free and open source. Selling Buzz is reselling a free product,
and that is a race to zero.** The sellable thing is never the software. It is
the *outcome*: auditable agent work, stood up safely, with Buzz as an
implementation detail the client never has to think about. Price the
outcome, not the bits.

Ranked by how fast a one-person shop can close the first deal:

#### 1. Deployment and operations (fastest to first dollar)

This closes first because the pain is concrete and immediate: the
self-hosted stack is non-trivial and the security gaps are documented.
Scope a **fixed-fee "stand it up, harden it, hand it over"** engagement.

What "hardened" concretely means, given the documented gaps, each item ties
to a section above:

- **Isolate the shell tool.** Every `buzz-dev-mcp`-backed agent runs as a
  dedicated low-privilege user, in a container or throwaway VM, workdir
  scoped to one project checkout, no secrets reachable. This is the single
  most important control (Section 2 / limitation 5).
- **Put rate limiting in front.** Since Buzz enforces none (limitation 1),
  add reverse-proxy / gateway rate limits and connection caps at the edge.
- **Terminate TLS properly.** Caddy/nginx/Traefik in front of the relay for
  `wss://`, since the relay does not enforce TLS (Section 1).
- **Externalize audit checkpoints.** Periodically export per-community audit
  chain heads off-box so tamper-evidence has an anchor the DB admin cannot
  rewrite (Section 1 / limitation 7).
- **Encrypt at rest and in transit yourself.** No E2E exists (limitation 6);
  add disk encryption, locked-down Postgres/MinIO, and network policy.
- **Back up and monitor.** Postgres + MinIO backups, Prometheus alerts,
  restore drills.
- **Lock down membership.** `buzz-admin` roles, private channels by default,
  documented key custody.

Deliverable: a running, TLS-fronted, backed-up, monitored relay with an
isolation model for every agent, plus a runbook. This is a 1-3 week fixed-fee
job you can template and repeat. Multi-community mode (Section 1) lets you
host several small clients on one hardened deployment, which is where the
margin compounds.

#### 2. Agent roster design (durable, higher margin)

This is org design, not engineering, and it sells to **operations**, not
just to a lead developer. The durable question is: which agents should this
organization have, what is each one's key, which channels is it a member of,
what tools does it hold, and what is it explicitly forbidden to touch.

The deliverable is the Section 5 table, made specific to the client and
checked into a repo as the source of truth: for each agent, a generated
keypair identity, an exact channel-membership list, a tool grant
(read/post-only vs `buzz-dev-mcp`-enabled with its isolation profile), and a
written prohibition list. Because Buzz scopes by key-and-membership rather
than a permission engine, this document *is* the access-control policy;
there is no other layer to get wrong. That makes the artifact unusually
high-leverage and unusually easy to audit, which is exactly what an
operations buyer pays for. It is also recurring: rosters drift, new agents
get proposed, prohibitions need review.

#### 3. Provenance and conformance (the strongest thesis)

Every action, human or agent, is a signed Nostr event under its own keypair,
linked in a hash-chained audit log (`buzz-audit`, Section 1). That is a
**chain of custody for the production *process***, distinct from
asset-level provenance like C2PA (which attests the *artifact*). Buzz
attests *who or what touched the work, in what order, under which key*.

As disclosure regimes tighten (the EU AI Act's Article 50 transparency
obligations among them), "who or what touched this, and can you prove it"
becomes a procurement question, and Buzz's log is a credible technical
answer to the *process* half of it.

State honestly what the log **does** and **does not** evidence, because
overclaiming here is malpractice:

- **Evidences:** a cryptographically signed, ordered record that a
  particular key performed a particular action, tamper-*evident* so
  after-the-fact edits are detectable against an untampered reference.
- **Does not evidence:** it does not by itself prove *which human* controls
  a key (identity binding is your process, not the protocol's), it is not
  tamper-*resistant* against a DB admin (limitation 7), and it is not, on its
  own, legal or regulatory sufficiency. You are selling a defensible
  technical record and the process around it, **not** compliance advice, and
  you should say so in writing.

Now the two verticals.

**The AI filmmaker.** The concrete hook is frame-anchored media comments
(Section 4): notes pinned to specific moments in a cut, in a channel, as
signed events. Branch-as-room maps onto shot and version review, one
room per shot or per cut version, canvas plus huddle is the review session
with a durable record attached. Media assets themselves do not belong in git
(they live in MinIO/S3 via Blossom), but the *decisions* about them do: which
model produced which asset, which human approved which take, all as signed
events under distinct keys. The sellable output is a **defensible record of
which model produced which asset and which human approved it**, which is
increasingly a client- and broadcaster-delivery requirement. Caveat to
honor: huddle recording is not built (limitation 4), so if the review
session itself must be recorded, capture it out-of-band.

**The marketing team.** Campaign-as-channel, with agents for research,
variant generation, and brand review (a natural instance of the Section 5
roster). The acute, budgeted pain is **legal/compliance review in regulated
categories** (financial services, health, supplements), where proving a
human approved a specific claim *before* publication is a real bottleneck.
The workflow: a variant-generation agent posts drafts into the campaign
channel; a brand/legal reviewer (human) approves in-thread; the approval is a
signed event tied to that human's key, sitting immutably beside the claim it
approved. That gives you a queryable "who approved this claim, when" record.
Honest caveat: because approval-gate workflow automation is not wired
(limitation 2), enforce the approval as a **human posting a signed approval
event**, not as an automated gate that blocks publication. The record is
real; the automatic enforcement is not there yet, so keep the human in the
loop by design, not by hope.

### The counter-case, argued honestly

- **Switching costs on Slack are severe.** Do not sell Buzz as a Slack
  replacement; you will lose. Position it as a **second system where the
  agent fleet lives and is audited**, adjacent to the client's existing
  chat. Integrate, do not rip and replace.
- **Block controls the roadmap.** Block can absorb any service layer you
  build on top, ship hosting, hardening, or roster tooling as product, and
  erase your margin. You are renting a gap in their product, not owning an
  asset.
- **Incumbents may ship agent identity.** The differentiator (per-agent
  keypair identity plus signed audit) is exactly the kind of thing Slack,
  GitHub, or a cloud vendor could add, collapsing the distinction.

**The window.** This is a timing arbitrage, not a durable moat. My estimate:
**roughly 12 to 18 months.** The floor is set by how fast Block hardens the
documented gaps (rate limiting, approval gates, sandboxing), each closed gap
is one fewer thing you can charge to fix. The ceiling is set by when a major
incumbent ships credible agent-identity-plus-audit, at which point
provenance-as-a-service commoditizes. Inside that window, the
fastest-closing, highest-repeat work is deployment-and-hardening (offering
1), and the most defensible, relationship-deepening work is roster design and
provenance (offerings 2 and 3). Land with the first, retain with the others,
and treat every gap Block closes as a signal to move up the stack before the
arbitrage expires.

---

*Sources are cited inline by repository file path against `block/buzz` at
commit `4d47aa8` (2026-07-30). Where a specific could not be verified in the
files read, it is marked "unverified" rather than smoothed over.*
