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

## Source Channel Strategy

Use the `Job Site Info` NotebookLM transcript as source strategy, not as direct evidence unless exported text is available. It identifies the places where AI creative roles surface first:

- Company career pages: preferred primary evidence for observed roles, salary bands, locations, and tool stacks.
- X/social screenshots: discovery hints for role-title mutations and community reaction. Verify elsewhere before publishing.
- Discord/private communities: manual-only. Never scrape private servers; use pasted snippets as market-demand signals unless independently verified.
- Upwork/freelance marketplaces: demand signals for workflow pain, web scraping, data extraction, automation, and proof-build opportunities. Do not automate applications or logged-in scraping.
- Industry publications: secondary verification for agency staffing shifts, account reviews, and budget movement.

Priority companies from the Source 5 transcript:

- Adobe, Sphere, Paramount Tech, Lightricks, Amazon Prime Video / Amazon MGM, Netflix, Epic Games.

Secondary watchlist from the job-site notebook:

- Twilio Segment, Jasper, Vantage Point, BBD Boom, Ad Age, public clipping-shop discussions, and freelance automation demand.

## Evidence Tiers

Every job source must carry an evidence tier:

- `primary`: public company career pages, public ATS postings, or pasted source text. These can support `observed` roles.
- `secondary`: public articles, trade publications, and search feeds. These support `emerging` signals; only use them for `observed` roles when the role facts are specific and source-backed.
- `discovery`: social/community mentions and screenshots. Use as leads only.
- `demand`: freelance marketplace and community work requests. Use for market-demand and proof-build ideas, not stable full-time role titles.
- `manual`: watchlist sources requiring human/agent review.

Genny should prefer sources that repeatedly produce accepted signals and demote sources that repeatedly produce generic or rejected items.

## Refinement Loop

Each Career Radar scan now outputs `Job Source Quality`.

Use that section to:

- keep sources with multiple accepted signals or strong average scores;
- tune or replace sources with repeated checked items and zero accepted signals;
- leave manual/watchlist sources out of automatic claims;
- add new primary sources when a company repeatedly appears in accepted signals;
- turn noisy channels into discovery-only inputs instead of briefing evidence.

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
- unverified social screenshots presented as fact;
- freelance marketplace tasks presented as full-time roles.

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
