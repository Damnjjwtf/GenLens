# Marti Signal Schema

Status: MVP operating schema

Last updated: July 20, 2026

Marti tracks changes in marketing technology, distribution, measurement, and stack economics. A publishable item must support at least three of the fields below and must include a verifiable link.

## Required fields

- Platform or technology
- Core mechanism: agent, API, integration, data flow, pricing model, or automation
- Stack layer
- Concrete operator use case
- Displacement implication, when supported
- Strategic impact: cost, ROAS, CAC, CPM, retention, time-to-launch, or stack complexity
- Verification link

## Source hierarchy

1. Official release notes, changelogs, API documentation, pricing-change evidence, and repositories
2. Operator case studies with disclosed stack, spend, or outcome data
3. Trade reporting with concrete mechanism or economic detail
4. Search and aggregator feeds for discovery only

## Reject

- Vendor positioning without a mechanism or number
- Sponsored listicles and tool roundups
- Analyst badges without accessible methodology
- Generic growth advice
- Pricing pages without evidence of a pricing change
- Replacement claims without migration cost and capability-loss analysis

## Confidence labels

- `primary-source`: supported by an authoritative first-party source
- `corroborated`: supported by two credible sources
- `single-source`: credible but not yet independently corroborated
- `hypothesis`: useful research lead; not publishable as fact

Confidence and completeness are separate. A primary release note can be authoritative even when it does not establish a commercial outcome; that outcome remains a hypothesis until evidence supports it.

## Decision-ready archive fields

When Marti signals become persisted structured records, each record should add:

- a stable ID;
- lens value `marti`;
- a recommended decision: `test`, `adopt`, `avoid`, `migrate`, `brief`,
  `budget`, or `watch`;
- the confidence label above;
- source type plus published and observed dates;
- a mechanism, operator use case, impact, and exact evidence URL.

For cross-lens output, `convergence` may replace `marti` only after a human
verifies the shared mechanism, workflow, or economic consequence. This is the
target archive schema, not a claim that stable signal storage already exists.
