# Genny Production-Signal Quality Gate

Status: implemented and regression-tested; latest isolated live run held for
coverage rather than padding

## Purpose

Genny tracks verified changes in generative-AI production. It is not a general
creative-technology feed. Keyword overlap, a high score, or appearance in a
Google News query is insufficient for publication.

## Admission Contract

A Genny card must satisfy every requirement below:

1. **Substantive evidence:** a non-empty source summary with enough detail to
   support a decision-ready interpretation.
2. **Production relevance:** explicit evidence for the named production
   vertical, such as filmmaking, product photography, digital humans, music,
   design, fashion, games, or another configured workflow.
3. **AI mechanism:** explicit generative-AI language or a recognized
   AI-production model or product. Generic renderer, engine, infrastructure,
   or 3D releases do not qualify.
   Game-development items must additionally name a generated or edited
   production artifact (for example an asset, prop, level, scene, UI, NPC, or
   gameplay system); an AI agent merely controlling an engine is insufficient.
4. **Concrete change:** a release, launch, update, acquisition, partnership,
   legal or policy event, deprecation, or equivalent ecosystem change. Static
   explainers, tutorials, analysis, and event promotions do not qualify.
5. **Confirmation:** the source must not explicitly say that the claimed
   feature or partnership is unconfirmed.
6. **Source trust:** search-discovered articles must resolve to a publisher in
   that search source's explicit `trusted_domains` list. Direct vendor domains
   are separately identified in `primary_domains` so confidence reflects the
   evidence publisher rather than the discovery channel.
7. **Recency and concentration:** the existing 45-day, exact-URL,
   cross-source near-duplicate, per-source, per-domain, and topic-concentration
   controls still apply. When two publishers describe the same launch, Genny
   keeps the stronger, newer source rather than inflating coverage.

## First-Party Discovery Contract

RSS remains the preferred discovery transport, but several production vendors
publish structured update pages without feeds. Genny may discover those updates
through a registry-approved `official_sitemap` only when all of these controls
are present:

- the registry points to a leaf URL-set sitemap, never an unbounded sitemap
  index;
- the sitemap and update page use the same first-party domain;
- `include_patterns` constrain discovery to the vendor's article or release
  namespace;
- the article exposes a publication date and is no older than 45 days;
- page title and evidence come from article metadata, JSON-LD, or coherent body
  copy and still pass the full production-signal admission contract;
- page reads are capped per source, with normal source/domain concentration
  limits applied afterward.

Ordinary vendor homepages remain watch-only. A sitemap is a discovery aid, not
an authority shortcut: generic articles, tutorials, stale pages, and weak AI or
vertical evidence are still rejected and recorded in the candidate ledger.

Rejected candidates remain in the signal ledger with a machine-readable reason.
The gate must surface a coverage gap instead of manufacturing breadth.

## Recommendation Contract

Decision enrichment remains conservative:

- explicit pricing or commercial-model changes become `budget`;
- policy, labeling, copyright, or lawsuit changes become `brief`;
- releases and workflow capabilities become `test`;
- shutdowns and deprecations become `migrate`;
- verified changes without a stronger operator action remain `watch`.

Page chrome such as a navigation link labeled “Enterprise Pricing” does not
turn an unrelated product release into a budget recommendation.

## July 21, 2026 Isolated Evaluation

Command shape (run from an isolated profile; no `--send`):

```bash
python3 scripts/genlens_editorial_ops.py \
  --lens genny \
  --mode expanded \
  --per-vertical 5 \
  --rss-limit 12
```

The release-candidate evaluation retained nine linked signals across six
production verticals and rejected 286 candidates. Bounded first-party sitemap
discovery added current, dated official updates without weakening the gate. The
surviving set covered:

- two Photoroom product-imagery updates;
- Runway/Aleph in Figma Weave (collapsed to one cross-source signal);
- two Reallusion digital-human product releases;
- Lionsgate's expanded Runway relationship and equity stake;
- Articulate's Q2 AI-assisted course-production update;
- the AI-music labeling program;
- the Suno training-data lawsuit.

The editorial preflight correctly returned `hold`: breadth passed at 6 of the 5
required signal verticals, but depth remained only 9 of the 12 required linked
cards. Duplicate titles were zero. No email was sent. The Unity CLI was rejected
because engine control alone is not generative game production; older Unity 3D
Object and UI Generator releases were correctly classified as production
signals and then rejected by the 45-day recency gate. A second Figma/Runway
article about the same Aleph launch was rejected as a cross-source near
duplicate. Generic Godot and V-Ray releases, broad NVIDIA infrastructure, weak
aggregators, press-release mills, unconfirmed CapCut claims, tutorials, weekly
roundups, and conference promotions also did not survive the final gate.

## Promotion Boundary

This gate repairs admission quality; it does not prove Genny's ongoing source
coverage target. Scheduled delivery still requires the normal preflight and
human review. Lowering the card or vertical threshold to make a sparse issue
pass would violate the GenLens north star.
