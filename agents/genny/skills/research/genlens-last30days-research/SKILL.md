---
name: genlens-last30days-research
description: Use Last30Days as an optional recent-signal discovery layer for GenLens, Genny, Marti, jobs, market demand, and community research.
---

# GenLens Last30Days Research

Use this skill when Jonathan asks for recent market demand, community sentiment,
"does anyone want this", creative AI job-market signals, Genny/Marti research,
or a last-30-days view of a company, tool, role, or product category.

## Source

External repo:

`https://github.com/mvanhorn/last30days-skill`

GenLens integration notes:

`docs/LAST30DAYS_RESEARCH.md`

## Availability Check

Before claiming Last30Days is available inside Hermes, verify it:

```bash
command -v last30days || true
find /root/.hermes/skills /root/.hermes/profiles/genny/skills -maxdepth 4 -iname "SKILL.md" 2>/dev/null | grep -i last30days || true
```

If unavailable, say that the upstream Hermes install is blocked by the security
scanner and use GenLens native source tools instead.

## How To Use It

Treat Last30Days as discovery and demand intelligence. It can help find what
people recently discussed, complained about, shared, hired for, or bet on. It is
not itself authoritative evidence for a GenLens card.

For jobs and role intelligence, prefer:

```bash
last30days "AI creative production jobs" --hiring-signals
last30days "generative artist ComfyUI VFX" --hiring-signals
last30days "creative technologist AI video" --hiring-signals
```

For Genny demand:

```bash
last30days "AI creative production intelligence"
last30days "AI filmmaking workflow pain"
last30days "ComfyUI production workflow"
```

For Marti demand:

```bash
last30days "AI marketing agents"
last30days "marketing orchestration AI"
last30days "AEO citation tracking"
```

## Promotion Rules

Allowed:

- Add discovered companies, tools, roles, communities, and questions to a
  research queue.
- Turn repeated complaints into proof-build ideas.
- Use hiring-signals output to update Role Radar hypotheses.
- Use source leads to improve `genny_sources.json`, `marti_sources.json`, or
  `career_sources.json` after verifying the source quality.

Not allowed:

- Do not publish social chatter as a final signal.
- Do not cite Last30Days output as primary proof.
- Do not scrape private Discords, login-only job boards, or application flows.
- Do not bypass the Hermes security scanner by copying upstream executable code
  into the live profile.

## Output Shape

When summarizing a Last30Days run for GenLens, report:

- topic queried;
- usable source families returned;
- strongest demand/job/community signals;
- weak or missing coverage;
- direct verification tasks for Genny or Marti.

Keep the conclusion grounded: "discovery signal", "market-demand lead", or
"verification task" unless a direct authoritative source has been checked.
