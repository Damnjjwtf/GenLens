# Genny Newsroom Architecture

Status: adopted blueprint (2026-07-24)
Owner: Jonathan
Supersedes: the "scan every homepage in the registry" intake model

## The reframe

Genny needs a **newsroom wire service, not a larger web scraper**. The old
registry held too many manual homepage URLs that produce slow, repetitive,
low-value results. The daily email held below the quality gate not because the
news was thin but because the intake was feedless and undifferentiated.

The wrong question: "What websites can I scrape?"
The right question: "Which sources repeatedly produce new, verifiable changes
that matter to working creative professionals?"

The fix is to separate **discovery**, **verification**, and **publishing**, and
to let editorial output improve the source list instead of treating every
source equally.

## 1. Source portfolio (four tiers)

Every source carries a `tier`. Tier governs trust and whether it can be direct
evidence or lead-only.

- **Tier 1: First-party changes.** Official release notes, changelogs, product
  announcements, API updates, pricing, licensing, policy pages. Highest trust;
  can be direct evidence.
- **Tier 2: Independent trade reporting.** CG Channel, FXGuide, VP Land, No
  Film School, 80.lv, Motionographer, Creative Bloq, and similar specialist
  publications. CG Channel is especially high-value: it spans VFX, games,
  motion design, ArchViz, software releases, and production breakdowns. Can be
  direct evidence and is the preferred second key (see the two-key rule).
- **Tier 3: Curated newsletters.** The Producers' Lowdown, TOOOLS, School of
  Motion's Motion Mondays, VP Land's newsletter, selected AI/creative
  newsletters. Useful for finding stories and workflow trends; NOT automatically
  trusted as final evidence. Lead-generating, resolve to a Tier 1/2 article
  before publishing.
- **Tier 4: Discovery only.** X, Reddit, Google News, YouTube, Last30Days,
  community submissions. Generate leads only, never become briefing cards
  without a real article or official source.

ComfyUI's dated archive (blog.comfy.org/archive) is the model source shape:
dated posts tied to actual model support, workflow changes, releases, and
production capabilities.

## 2. Source-refresh layer (decouple gathering from delivery)

The 8am email must NOT crawl the internet. A separate refresh job runs every
3 to 6 hours and stores candidates:

- RSS and Atom feeds
- XML sitemaps
- Newsletter inbox parser
- Apify captures for the remaining high-value feedless sites (fallback, not the
  main strategy)
- Last30Days discovery queries
- Official changelog / API checks

The daily email reads only **verified cached candidates**, so delivery is fast
and predictable. Apify is the fallback for feedless sites, not the backbone.

### Exa as the discovery + content engine (adopted 2026-07-24)

Exa (exa.ai) is a neural search API that returns clean article text instead of
raw HTML, priced pay-per-request (roughly $7 per 1,000 searches with contents
for the first results bundled in; cheap at Genny's volume). It directly attacks
the feedless-scraping problem: instead of scraping 58 feedless homepages, the
refresh job asks Exa semantic queries and gets back dated, clean article
content. Use it two ways:

- **Scout / discovery:** semantic and keyword queries ("AI filmmaking release",
  "ComfyUI production workflow", "generative artist hired") surface fresh
  articles the registry never listed. Feeds the source-proposal loop (section 6).
- **Harvester / content extraction:** Exa `contents` returns clean text for a
  known URL, replacing slow HTML scraping and reducing Apify dependence to the
  genuinely un-fetchable long tail.

Key lives only in the VPS profile `.env` as `EXA_API_KEY` (or
`GENLENS_EXA_API_KEY`), never in the repo. Exa is discovery-and-extraction
grade: results still pass the full verifier (section 3) and the two-key rule
(section 4) before publishing. It is a faster, cleaner intake, not a bypass of
the gate.

## 3. Verification (the admission contract, per candidate)

Every candidate must answer:

- What changed?
- What product, model, workflow, or policy is involved?
- Which GenLens vertical does it affect?
- What can a professional do differently?
- Is there a measurable time, cost, quality, rights, or hiring implication?
- Is this an article, or merely a homepage, tutorial, event promo, or ad?

A candidate FAILS if it is: a product homepage, a generic "best tools" article,
a tutorial without a new development, a press-release rewrite with no
operational detail, older than the freshness window, a duplicate of a story
already sent, or missing a specific production mechanism.

This extends the existing `GENNY_QUALITY_GATE.md` contract; it does not replace
it. The gate is not loosened.

## 4. Two-key publication rule

For important claims, prefer two independent keys:

- One official source proving the change exists (Tier 1).
- One independent source explaining the practical consequence (Tier 2).

Example: a Runway announcement proves a feature exists; FXGuide or CG Channel
explains how it changes a real VFX workflow. If only one source exists, the
card is labeled `single-source` rather than presented as fully corroborated.

## 5. Fixed editorial slots per vertical

Stop trying to fill five cards per vertical. Give each vertical two meaningful
slots:

- **Change slot:** release, model, API, pricing, rights, or policy shift.
- **Workflow slot:** case study, production breakdown, job signal, or
  measurable use case.

A vertical with no qualified story gets no card, only a short internal coverage
note, never a visible failure card.

## 6. Source health scoring

Every source accumulates: fetch success rate, qualified-candidate rate,
article-to-homepage ratio, duplicate rate, average freshness, vertical
relevance, last meaningful signal, last failure reason. Sources that repeatedly
produce weak results lose priority automatically; consistent producers rise.
Editorial output thereby improves the source list.

## 7. Five cooperating roles

- **Scout:** discovers new feeds, newsletters, publications, job sources.
  Powered by Last30Days. Never the final editor.
- **Harvester:** collects RSS, newsletter, sitemap, and Apify candidates.
- **Verifier:** reads and scores the actual articles against section 3.
- **Clusterer:** removes duplicates and recurring versions of one story.
- **Editor:** selects final cards and writes the briefing.

These are roles, not necessarily separate processes at first; they can start as
functions and split into jobs as load grows.

## 8. Storage: SQLite operational layer

The append-only JSON ledger is becoming too large to reason about. Move the
operational layer to a small SQLite database. Tables:

- `sources` — the portfolio (tier, vertical, feed URL, priority, health fields)
- `source_runs` — one row per source per refresh (fetch outcome, counts)
- `candidates` — harvested items awaiting or past verification
- `signal_reviews` — verifier verdicts with reasons (accepted/rejected)
- `story_clusters` — dedup groups of the same story across sources
- `deliveries` — what was sent, when, to whom
- `rejections` — negative memory, so a killed story does not resurface

Keep Markdown exports for Genny and human review. The JSON signal ledger stays
as the durable audit cache per `SPINE.md`; SQLite is the operational working
set, not a replacement system of record. The web product's system of record
remains Neon (SPINE.md).

## 9. Reddit community intelligence layer

Reddit is a **core input, but as community intelligence, not unquestioned
news**. It sits inside Tier 4 (discovery) with extra structure. The value split:

- Official sources tell Genny what launched.
- Trade publications explain what changed.
- Reddit reveals what broke, what professionals actually use, what workflows
  are emerging, and what people are asking for.

Powered by the existing Last30Days checkout, which already has Reddit RSS /
listing discovery, subreddit targeting, relevance scoring, and comment
enrichment (`last30days-skill/.../lib/reddit_keyless.py`). Last30Days powers the
Reddit Scout; it is never the final editor.

### Lanes

1. **Targeted subreddit watchlists**, curated per vertical: AI image and
   ComfyUI workflows; VFX, filmmaking, motion design, 3D; digital humans, voice,
   mocap; game development and Unreal; product photography and ecommerce;
   freelance and creative-technology careers.
2. **Keyword discovery:** `tool + workflow`, `tool + broken`, `tool +
   production`, `AI pipeline`, `creative technologist`, `ComfyUI + client`,
   `AI filmmaking + commercial`, `generative artist + job`.
3. **Comment intelligence:** the title is often weak; the signal is in the
   comments ("I tried this on a real production", "this breaks when", "the
   workaround is", "our studio replaced", "I was hired to").
4. **Community trend detection:** when multiple unrelated threads discuss the
   same tool, failure, workflow, or job title, Genny emits a `community_signal`
   that is NOT treated as verified fact until an official or independent source
   confirms it.

### Signal types

`workflow_proof`, `pain_point`, `tool_adoption`, `emerging_role`,
`pricing_complaint`, `rights_or_policy_concern`, `rumor`, `request_for_tool`.
Only the first five normally enter editorial review. `rumor` stays in a watch
queue; `request_for_tool` and `pricing_complaint` feed the source/product
feedback loop.

### Feedback loop into the source system

- If Reddit repeatedly discusses a tool absent from the manifest, Genny
  proposes: add it to the watchlist, find its official changelog, find
  independent coverage, identify the vertical, track future releases and job
  mentions.
- If Reddit repeatedly complains a source is stale or promotional, that source
  loses priority automatically (feeds section 6 health scoring).

### Guardrail (non-negotiable)

Reddit can prove people are experiencing a workflow, pain point, or adoption
pattern. It CANNOT independently prove a company's product claim, salary
number, benchmark, or legal position. Those require verification against an
official or authoritative source. Reddit's Data API terms require proper
OAuth/access and impose usage restrictions, including possible separate
agreements for commercial or high-volume use; the keyless RSS/listing path is
discovery-grade, not a licensed data pipeline.

### Roles (extend section 7)

- **Reddit Scout:** discovers posts, subreddits, comment threads.
- **Reddit Extractor:** saves permalink, date, subreddit, score, comments,
  relevant excerpts.
- **Community Clusterer:** groups repeated discussions into one trend.
- **Source Verifier:** finds the official or trade source behind the claim.
- **Genny Editor:** uses Reddit only when it adds workflow evidence or market
  context, never as sole proof of a claim.

Reddit refreshes every few hours into the cache (section 2); the daily email
reads cached, already-ranked community signals, so Reddit rate limits never
break the 8am job. `community_signal` rows live in `candidates` with
`source_tier = 4` and a `signal_type`; unconfirmed rumors and watch-queue items
are held, not published.

## Rollout (sequenced)

1. Reclassify the registry: tag every source with a tier; remove homepage URLs
   from daily intake (keep them for audit only).
2. Add 10 to 15 high-quality RSS/Atom sources across the active verticals, and
   wire Exa as the discovery + content engine for the feedless long tail.
3. Add a newsletter inbox and newsletter parser.
4. Add Apify only for the remaining high-value feedless sources.
5. Build the verifier queue and the negative-memory rejection store.
6. Move daily composition to cached verified signals.
7. Add the source-health dashboard and weekly source audit.

## Governance and coordination

Per `SPINE.md`, this is a new pipeline and one track at a time. Because Genny's
daily path is under active edit in another session, build order must avoid
collisions: new isolated modules (the SQLite store, the verifier, the health
scorer) can be built standalone and tested offline; the integration steps that
touch the live compose/daily path (rollout 1, 6) are coordinated, not done in
parallel. Feed-URL additions require network verification and are done where
that network exists (the VPS), not blind.
