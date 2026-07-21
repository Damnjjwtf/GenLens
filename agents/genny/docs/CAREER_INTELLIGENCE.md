# Career Intelligence Layer

Genny's career intelligence layer turns public hiring, workflow, and tool-stack signals into GenLens Role Radar.

## Purpose

Genny should help working creative technologists understand:

- which AI creative roles are real now;
- which roles are emerging from repeated workflow/tool patterns;
- which roles are 12-18 month forecasts;
- which tools and skills show up together;
- what proof-build someone should ship to become credible for the work.

## Inputs

- `data/career_sources.json`: public career/news/source queries.
- `data/career_signals.json`: durable scored career signal ledger.
- `data/role_signals.json`: seeded observed/emerging/forecast roles.
- `data/notebooklm_sources.json`: registered NotebookLM research sources, including `Job Site Info` for job-site strategy and role-signal extraction when authenticated or exported.
- pasted job posts, transcripts, or hiring snippets from Jonathan.

## Scripts

Scan public career sources:

```bash
python3 scripts/genlens_career_intel.py --limit 8
```

Ingest pasted job/source text:

```bash
python3 scripts/genlens_career_intel.py --input-file /path/to/job-posts.txt
```

Generate role/build/product reports:

```bash
python3 scripts/genlens_role_radar.py --mode all
```

## Signal Quality

A career signal is publishable when it has:

- a role, hiring, skill, tool, workflow, or market-demand pattern;
- a source or pasted evidence;
- a concrete link to AI creative production;
- enough specificity to map to tools, skills, verticals, or proof-builds.

Reject:

- generic job-market content;
- SEO listicles;
- course/affiliate content;
- login-only/private job sources;
- automated applications or outreach;
- forecasts presented as existing jobs.

NotebookLM links are memory/research sources, not direct scrape feeds. If a NotebookLM source is not authenticated, Genny must ask for exported source text/transcripts or continue from local GenLens files.

## Output Contract

Every accepted item should support at least three of:

- role pattern;
- tool stack;
- skill/workflow verb;
- vertical;
- company/source evidence;
- proof-build implication.

Every role must be labeled:

- `observed`: real job/source evidence;
- `emerging`: repeated pattern across signals;
- `forecast`: evidence-backed 12-18 month role, not yet stable;
- `market-demand`: user/source pain that suggests a need but does not yet form a role.
