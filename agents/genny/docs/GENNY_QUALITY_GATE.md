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
4. **Concrete change:** a release, launch, update, acquisition, partnership,
   legal or policy event, deprecation, or equivalent ecosystem change. Static
   explainers, tutorials, analysis, and event promotions do not qualify.
5. **Confirmation:** the source must not explicitly say that the claimed
   feature or partnership is unconfirmed.
6. **Source trust:** search-discovered articles must resolve to a publisher in
   that search source's explicit `trusted_domains` list. Direct vendor domains
   are separately identified in `primary_domains` so confidence reflects the
   evidence publisher rather than the discovery channel.
7. **Recency and concentration:** the existing 45-day, dedupe, per-source,
   per-domain, and topic-concentration controls still apply.

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

The final evaluation retained seven linked signals across four production
verticals and rejected 278 candidates. The surviving set covered:

- Runway/Aleph in Figma Weave;
- two Reallusion digital-human product releases;
- Netflix's acquisition of an AI-filmmaking company;
- Lionsgate's expanded Runway relationship and equity stake;
- the AI-music labeling program;
- the Suno training-data lawsuit.

The editorial preflight correctly returned `hold`: Genny had only 7 of the 12
required linked cards and 4 of the 5 required signal verticals. No email was
sent. Generic Godot and V-Ray releases, broad NVIDIA infrastructure, weak
aggregators, press-release mills, unconfirmed CapCut claims, tutorials, and
conference promotions did not survive the final gate.

## Promotion Boundary

This gate repairs admission quality; it does not prove Genny's ongoing source
coverage target. Scheduled delivery still requires the normal preflight and
human review. Lowering the card or vertical threshold to make a sparse issue
pass would violate the GenLens north star.
