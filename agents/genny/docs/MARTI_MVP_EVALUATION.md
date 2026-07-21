# Marti MVP Evaluation

Date: July 21, 2026
Status: Research MVP passes one evaluation run; not approved for scheduled sends

## What is live

- `--lens marti` and `--lens unified` execution paths
- separate Marti source registry and signal schema
- active and expanded Marti stack-layer taxonomies
- shared 45-day recency, URL, dedupe, concentration, and false-positive filters
- Marti-specific layer-admission rules
- separate Marti brief, audit, preflight, and tool-candidate artifacts
- Marti and unified email identities in the existing Resend renderer
- lens-aware daily email command
- convergence candidate detection requiring two theme terms in each lens
- deterministic regression tests for taxonomy, recency, housekeeping suppression, email identity, and convergence

## First live-feed results

The first expanded Marti evaluation produced three qualified public cards across:

- Paid Media / Creative Performance
- Commerce / Conversion
- SEO / AEO / Content Systems

The six-card, three-layer Marti gate held the issue. This is correct. The source
pool proves the pipeline but does not yet support a reliable standalone briefing.

The initial expanded pass produced nine cards before tighter layer rules. Manual
review found five clear category leaks, including enterprise infrastructure and
government stories. The stricter rules reduced the set to three stronger cards.
This is evidence that Marti needs narrower sources, not lower thresholds.

The first unified pass produced seven cards across both lenses. Its initial
convergence suggestion relied on broad creative language, so the detector was
tightened. Convergence remains a research prompt until a human verifies the
shared workflow or economic consequence.

## Source-expansion evaluation

Human review invalidated the July 20 source-expansion pass because a static
RudderStack explainer had been admitted as a change signal. The article page's
footer contained a separate product-update link, and the parser incorrectly
combined that footer language with the explainer title. That run does not count
toward promotion.

The repaired July 21 no-send evaluation produced seven linked cards across five
Marti layers, with no duplicate titles and seven links not present in the
isolated evaluation history:

- Paid Media / Creative Performance: 3
- Stack Consolidation / Displacement: 1
- Lifecycle / Retention: 1
- Commerce / Conversion: 1
- SEO / AEO / Content Systems: 1

Six of the seven cards resolve to official first-party sources. Zapier's Relay
shutdown notice is the one credible secondary source. The accepted set includes
official Google Ads campaign and disclosure changes, Meta's Creator Marketing
Hub announcement, a Salesforce/Slackbot workflow change, Shopify Managed
Markets pricing, and the new Search Console platform-property type.

The repair requires a concrete change or measured outcome, keeps the layer
mechanism and change evidence in the same title or summary, rejects static
how-to/comparison pages that borrow product-update language from page chrome,
and reads evidence-bearing article paragraphs when official feeds provide weak
summaries. Regression tests cover the RudderStack false positive and the late
Search Console article body.

This clean July 21 result counts as evaluation run 1 of the three consecutive
passing runs required for promotion. It does not authorize scheduled sends, and
no email was sent. Agentic Marketing Workflows remains the highest-priority
source gap.

## Reassessment of the Marti-Genny thesis

### Confirmed

- One technical spine can support two source taxonomies without duplicating the
  whole pipeline.
- Marti's stack-layer model is meaningfully different from Genny's production
  vertical model and deserves a separate lens.
- The arbitrage framing is more differentiated than a generic martech digest.
- Cross-lens analysis is technically possible and potentially valuable.

### Not yet proven

- Marti can sustain a high-quality standalone publishing cadence.
- Convergence candidates consistently reveal non-obvious, defensible insights.
- A Kill List can support credible savings deltas and migration-cost estimates.
- Readers want a unified default digest rather than separate specialist editions.
- A queryable signal graph, Ask Marti, forecast calibration, and born-asset data
  model do not exist yet.

## Promotion gate

Do not schedule or default-send Marti until all conditions hold:

1. At least six linked cards across three Marti layers.
2. The gate passes in three consecutive evaluation runs.
3. At least 60% of cards resolve to primary or authoritative first-party sources.
4. A human review of the last 20 accepted cards finds no more than one layer or
   relevance false positive.
5. Repeat protection and housekeeping suppression remain clean.

Do not make unified delivery the default until Marti passes its own promotion
gate and at least three convergence candidates have survived human verification.

## Recommended next build order

1. Repeat the live evaluation twice more and manually review the accepted-card
   set before considering scheduled delivery.
2. Improve the Agentic Marketing Workflows source pool without lowering the
   editorial gate.
3. Introduce structured signal records with stable IDs, source type, confidence,
   lens, layer, mechanism, use case, and impact fields.
4. Record rejected candidates with machine-readable rejection reasons.
5. Build the Kill List only after structured cost and migration assumptions exist.
6. Add Ask Marti only after the structured archive is large enough to answer
   useful questions without general model knowledge.

## Product recommendation

Keep Genny and Marti as distinct editorial lenses on one intelligence spine.
Do not collapse their voices or force a unified issue. Let each lens earn its own
cadence. Treat verified convergence as a premium output rather than a quota.
