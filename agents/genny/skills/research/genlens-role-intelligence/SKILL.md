---
name: genlens-role-intelligence
description: Analyze creative AI job posts, transcripts, and hiring signals to extract emerging roles, skills, tools, and 18-month GenLens job forecasts.
required_tools:
  - terminal
---

# GenLens Role Intelligence

Use this skill when Jonathan asks about jobs, new roles, career paths, role arbitrage, hiring signals, job scraping, future jobs, or how people can become emerging GenLens roles.

## Core Files

- Role memo: `/root/.hermes/profiles/genny/data/genlens_role_intelligence.md`
- Structured signals: `/root/.hermes/profiles/genny/data/role_signals.json`
- Career sources: `/root/.hermes/profiles/genny/data/career_sources.json`
- Career signal ledger: `/root/.hermes/profiles/genny/data/career_signals.json`
- Tools manifest: `/root/.hermes/profiles/genny/data/genlens_tools_manifest.md`
- Sources registry: `/root/.hermes/profiles/genny/data/genny_sources.json`

## First Command

For career intelligence, run the scanner before summarizing:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_career_intel.py --limit 8
```

Always read the `Job Source Quality` section in the generated Career Radar before answering. If sources are weak, say which source types need replacement or promotion instead of pretending the job market is fully covered.

If Jonathan provides job posts, transcripts, or snippets, save them to a temporary text file and ingest them:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_career_intel.py --input-file /tmp/job-posts.txt
```

## Output Modes

### Triage Existing Jobs

For real job posts, extract:

- Company
- Role title
- Location / remote / hybrid
- Salary or rate
- Direct job URL, publisher URL, and source domain
- Vertical
- Required tools
- Required skills
- Workflow verbs
- Seniority
- Signal strength
- Whether the role is truly new or a traditional title absorbing AI

### Arbitrage Current Gaps

Find mismatches:

- Companies need a workflow, but the market has no clean job title yet.
- Traditional artists can become competitive by adding a specific AI stack.
- Tool clusters imply a new role.

Example:

- `ComfyUI + ShotGrid + Nuke + LoRA + editorial QC` -> Generative Media Pipeline Operator.

### Forecast 18-Month Roles

Forecasts must be labeled clearly:

- `observed`: real job post / transcript / source.
- `emerging`: repeated pattern across multiple sources.
- `forecast`: evidence-backed prediction, not yet a stable role.

Do not present forecasts as existing jobs.

## Job Scraping Policy

Allowed:

- Company career pages.
- Public ATS boards: Greenhouse, Lever, Ashby, Workable.
- Studio/company job pages.
- Public search feeds for tightly scoped role queries.
- Pasted job posts/transcripts from Jonathan.

Prefer direct ATS/company URLs. If a result only has a Google News/search wrapper URL, label it as a lead and verify the original posting before making salary, location, or tool-stack claims.

Avoid:

- No login bypass.
- No LinkedIn scraping unless Jonathan provides an allowed export/API route.
- No mass collection of personal data.
- No automated job applications or outreach.
- Respect robots, rate limits, and terms where available.

## Genny Rule

Job posts are market intelligence. They reveal future creative-production workflows before the industry has stable job titles.

Evidence tiers:

- `primary`: public company careers, public ATS postings, pasted source text. Can support observed roles.
- `secondary`: articles/trade publications/search feeds. Use for emerging signals unless role facts are specific.
- `discovery`: social/community screenshots. Verify before publishing.
- `demand`: freelance/community requests. Use for market demand and proof-builds, not stable role titles.
- `manual`: watchlist sources requiring review.

Use role intelligence to make GenLens stronger:

- Add tools to the tool graph.
- Add sources for companies repeatedly hiring these roles.
- Build skill maps and learning paths.
- Explain how a Gen AD can move toward an emerging role.
