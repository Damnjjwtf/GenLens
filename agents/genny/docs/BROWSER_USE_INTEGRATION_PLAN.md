# Browser Use Integration Plan

Status: design approved, implementation not yet enabled in production.

Reference checkout: `../browser-use`

Upstream: [browser-use/browser-use](https://github.com/browser-use/browser-use)

## Decision

Use Browser Use as Genny and Marti's **fallback browser research worker**, not as
their primary search engine and not as a direct publishing agent.

The research order should be:

1. First-party RSS, Atom, sitemaps, and official release pages.
2. Exa semantic discovery for recent article candidates.
3. Browser Use for dynamic pages, blocked feeds, job boards, Reddit threads,
   newsletters, and source verification that the first two layers cannot handle.
4. The existing GenLens quality gate, ledger, deduplication, and delivery rules.

This keeps browser automation expensive and harder to reason about while still
giving Genny a way to read the web when a normal HTTP fetch is insufficient.

## What Browser Use Adds

- Browser navigation for JavaScript-heavy pages.
- Structured extraction from pages that do not expose useful RSS.
- Reusable browser sessions and profiles for approved, non-sensitive research.
- Domain restrictions and task-level browser configuration.
- A Python library, CLI, and MCP integration surface.
- Optional hosted browsers for isolation, proxying, and persistent profiles.

The upstream project currently requires Python 3.11 or newer. Its hosted
browser mode requires a Browser Use API key and usage credits; local mode still
requires a browser runtime and a compatible model provider.

## Proposed Architecture

```text
source registry
      |
      +--> RSS / sitemap fetchers
      +--> Exa semantic discovery
      +--> Browser Use research queue
                                |
                                v
                    structured candidate JSON
                                |
                     article/job verifier
                                |
                       quality + freshness gate
                                |
                 signal ledger -> brief / Discord / email
```

Browser Use should return evidence, not prose cards. Each result should contain:

- `url`
- `title`
- `published_at` or `date_unverified`
- `source_domain`
- `source_kind`
- `vertical` or Marti layer
- `evidence_excerpt`
- `claims_supported`
- `browser_task_id`
- `verification_status`
- `retrieved_at`

The worker must never mark a result `published`. Only the existing editorial
pipeline can promote it.

## Genny Jobs

Start with three read-only browser jobs:

### 1. Dynamic Source Reader

Use when an allowlisted source has no usable feed or its feed is stale. Read the
latest article/update pages, extract the article date and concrete change, and
return source-backed evidence.

### 2. Career Page Verifier

Use for public company career pages and public ATS pages. Extract role title,
location, compensation when shown, responsibilities, tools, and posting date.
Never apply, log in, message a recruiter, or submit a form.

### 3. Community Signal Scout

Use for Reddit and other community pages to find workflow pain, tool adoption,
job-title language, and requests. Community results are discovery evidence only
and require first-party or trade corroboration before they become a GenLens
claim.

## Marti Jobs

Give Marti a separate lens and separate task prompts for:

- Marketing platform changelogs and documentation.
- Public campaign, CRM, attribution, and automation case studies.
- Operator discussions about workflow pain and stack replacement.

Do not share Genny's browser profile with Marti. The two agents can share the
worker code and safety policy, but not cookies, local storage, or logged-in
sessions.

## Security Boundaries

- Run Browser Use in a dedicated virtual environment, separate from Hermes and
  the GenLens application dependencies.
- Prefer a hosted Browser Use browser or an isolated headless local browser.
- Start with public pages only; do not import personal Chrome profiles.
- Maintain an explicit domain allowlist per job.
- Block form submission, file upload, downloads, payments, account changes,
  email, Discord posting, and credential entry in the research worker.
- Never give the browser worker `RESEND_API_KEY`, Discord tokens, model keys, or
  the Hermes profile `.env`.
- Store browser artifacts outside the Git repository and expire them.
- Keep a hard task timeout, concurrency limit, URL limit, and monthly spend cap.
- Log URLs, task outcomes, and rejection reasons, but never page contents that
  contain credentials or private account data.

## Rollout Stages

### Stage 0: Isolated smoke test

- Install Browser Use in `/root/.hermes/profiles/genny/.venv-browser-use`.
- Run one public, non-authenticated task against a fixed allowlist.
- Verify the worker can return structured JSON and stop cleanly.
- Do not connect it to cron, Discord, email, or the live signal ledger yet.

### Stage 1: Manual research command

Add a Genny script such as `genlens_browser_research.py` with:

- `--vertical` or `--lens`;
- `--url` or a named allowlisted source;
- `--task-type dynamic-source|career|community`;
- JSON output and a Markdown evidence view;
- dry-run and timeout controls.

Evaluate 10 tasks against known pages. A task must produce a usable URL,
date/status, and evidence excerpt or be marked failed.

### Stage 2: Coverage-gap fallback

Call Browser Use only when RSS/sitemap and Exa fail to produce enough qualified
coverage for a vertical. Start with at most two browser tasks per run and one
task at a time. Save results as candidates for the normal quality gate.

### Stage 3: Scheduled source maintenance

Run a separate, low-frequency source-health job that proposes new feeds,
replacements, and allowlist changes. It may write an audit artifact, but it
must not silently change the canonical source registry.

### Stage 4: Promotion

Promote Browser Use to a regular daily fallback only after two weeks of metrics:

- qualified-candidate rate;
- direct-source resolution rate;
- date extraction rate;
- duplicate rate;
- source corroboration rate;
- average task duration;
- cost per accepted signal;
- browser failure and block rate.

## First Implementation Slice

The first code change should be small:

1. Add the dedicated Browser Use virtual-environment setup and health check.
2. Add a read-only `genlens_browser_research.py` wrapper.
3. Support one public dynamic-source task with structured JSON output.
4. Add unit tests for allowlists, timeouts, missing dates, and blocked actions.
5. Run a manual smoke test against one official source.

Only after that works should we add career and Reddit task templates, then wire
the worker into Exa/RSS coverage gaps.

## Recommendation

Proceed with Stage 0 and Stage 1. Do not install Browser Use directly into the
Hermes runtime or let it publish to Discord/email. Exa is already the right
semantic discovery layer; Browser Use should fill the browser-only gaps and
provide better evidence, especially for jobs, Reddit, and dynamic source pages.
