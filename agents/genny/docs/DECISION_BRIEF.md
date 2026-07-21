# GenLens Decision Brief

The decision brief is the evidence-bound recommendation layer between the
signal ledger and the user-attributed decision queue.

## Runtime Artifacts

- Genny: `state/decision_brief.md`
- Marti: `state/decision_brief_marti.md`
- Unified: `state/decision_brief_unified.md`
- Generator: `scripts/genlens_decision_brief.py`

The coordinated editorial flow generates the correct lens-specific brief after
writing and validating the signal ledger. Runtime artifacts remain excluded
from Git and are preserved by VPS sync.

## Recommendation Contract

GenLens may recommend one controlled action for a published signal:

- `migrate` for an explicit shutdown, deprecation, or migration;
- `budget` for an explicit pricing, fee, duties, billing, or commercial-model
  change;
- `brief` for an explicit policy, disclosure, rights, consent, compliance,
  labeling, copyright, lawsuit, or governance change;
- `test` for an explicit measurement, reporting, API, integration, workflow,
  agent, or newly available product capability;
- `watch` when the source proves a change but not a stronger operator action.

Each recommendation carries the stable signal ID, source link, confidence,
controlled mechanism, bounded operator use case, and potential impact area.
The generator does not invent quantitative outcomes or promote rejected
candidates.

Every rendered recommendation also includes:

- an action-specific operator next step;
- an explicit decision condition or stop/go boundary;
- an evidence boundary distinguishing a verified ecosystem change from an
  unproven local ROI, cost, or performance outcome;
- a stricter corroboration warning for single-source reporting.

`test` recommendations are layer-aware. Agentic marketing tests require a
least-privilege sandbox and human approval for external actions; paid-media
tests require capped spend and a frozen baseline; lifecycle tests require
non-production data, permissions, auditability, and reversibility; SEO/AEO
tests compare reporting coverage and latency on one bounded property.

## WVDA Boundary

A recommendation is not a user decision and never counts toward Weekly
Verified Decision Actions. It does not mutate `state/decision_queue.json`.
Only a named user's explicit confirmation, attribution note, channel, and
idempotency key may create a decision event.

## Command

```bash
python3 scripts/genlens_decision_brief.py \
  --ledger state/signal_ledger_marti.json \
  --out state/decision_brief_marti.md
```

If the current run has no published signals, the brief says so and recommends
improving source coverage instead of manufacturing an action.
