# Last30Days Research Integration

Last30Days is an external research skill from:

`https://github.com/mvanhorn/last30days-skill`

It researches recent public signals across Reddit, X, YouTube, Hacker News,
Polymarket, GitHub, web search, and optional social/search providers. It is most
useful to GenLens as a demand-signal and community-signal layer, not as a
primary source of truth.

## Current Install State

- Codex local install: available through the user-level Agent Skills install.
- Local checkout: `../last30days-skill` relative to the workspace root.
- Hermes VPS install: blocked by Hermes security scan with a `DANGEROUS`
  verdict. Do not bypass by copying executable upstream code into the live
  profile.

If Hermes later supports a reviewed or sandboxed install, install with:

```bash
hermes skills install mvanhorn/last30days-skill/skills/last30days --force
```

Only treat it as installed after Hermes completes the install and `last30days`
appears in the profile skill list.

## GenLens Use Cases

Use Last30Days when Jonathan asks:

- what people want or need from Genny, Marti, or GenLens;
- whether a product idea has current market demand;
- what creators, operators, or developers are struggling with this month;
- which companies appear to be hiring into a workflow;
- how a tool, company, or role is being discussed in the last month.

## Jobs And Role Intelligence

For jobs, use Last30Days as a discovery layer only.

Preferred query shape:

```bash
last30days "Listen Labs" --hiring-signals
last30days "AI creative production jobs" --hiring-signals
last30days "generative artist ComfyUI VFX" --hiring-signals
```

Outputs can suggest:

- role-title mutations;
- company hiring direction;
- tools appearing in public job language;
- communities complaining about skill gaps;
- proof-build ideas for GenLens Role Radar.

They do not replace direct job evidence. Promote a job signal only after it is
verified against a public company career page, public ATS posting, pasted job
text, or another authoritative source.

## Genny/Marti Boundary

Genny may use Last30Days to understand creative-production demand. Marti may use
it to understand marketing-technology and go-to-market demand. Unified
Genny-Marti output may use it to discover convergence candidates, but not to
claim causality.

Never publish Last30Days output verbatim as a GenLens card. Convert it into:

1. a research queue item;
2. a source lead;
3. a role/tool hypothesis;
4. a direct verification task; or
5. a proof-build opportunity.

## Safety Rules

- Do not bypass Hermes security scanning.
- Do not scrape login-only sites or private communities.
- Do not automate applications, bids, DMs, or outreach.
- Do not cite social chatter as final proof.
- Preserve source labels and uncertainty.
- If the upstream skill is unavailable, say so plainly and use existing
  GenLens source tools instead.
