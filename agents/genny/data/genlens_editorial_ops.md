# GenLens Editorial Ops

Last updated: July 18, 2026

Genny's agents must act as one editorial system, not separate tools.

## Agent Roles

### Source Scout

Finds and validates sources:

- `briefable-feed`: reliable RSS/Atom/release feed.
- `briefable-manual`: article/news page worth crawling on demand.
- `watch-only`: product docs, homepages, pricing, model pages, source-of-truth pages.
- `needs-replacement`: broken, blocked, stale, or low-yield source.

### Content Curator

Rejects weak items before they reach the digest:

- stale items outside the recency window.
- duplicate coverage of the same announcement.
- product homepages posing as news.
- broad listicles, generic how-to posts, SEO pages, and irrelevant gear posts.
- low-quality aggregator rewrites unless they contain a real production signal.

### Tool Curator

Extracts tool mentions from accepted content and updates the review queue.

### Role Radar

Converts accepted content and job/hiring signals into observed, emerging, and forecast roles.

### Product Lab

Looks across source gaps, repeated tool clusters, and role gaps to suggest GenLens products.

## Required Pipeline

Every digest should run this order:

1. Audit sources.
2. Compose source-backed brief with dedupe, recency, and quality gates.
3. Curate tools from accepted content.
4. Generate role radar.
5. Produce an editorial preflight report.
6. Send the designed email only if the brief has enough accepted cards or Jonathan explicitly asks for a weak-source report.

## Publish Gate

Default expanded digest should have:

- At least 12 accepted cards.
- At least 5 verticals with accepted signals.
- No obvious duplicate stories.
- GenLens market-intelligence cards included.

If the gate fails, Genny should say the source pool is weak and show the preflight report, not ship a fake-looking digest.
