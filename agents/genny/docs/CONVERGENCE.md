# Verified Genny–Marti Convergence

Convergence is GenLens's premium cross-lens output. It is an editorial
conclusion to prove, not a keyword-overlap card, a quota, or a causal inference.

## Runtime Artifacts

- Unified signal ledger: `state/signal_ledger_unified.json`
- Structured candidate set: `state/convergence_candidates.json`
- Human review view: `state/convergence_brief.md`
- Append-only review events: `state/convergence_reviews.json`
- Generator and review CLI: `scripts/genlens_convergence.py`
- Contract: `data/genlens_convergence.schema.json`

All runtime artifacts remain excluded from Git and are preserved across VPS
sync. The review log must not be reconstructed from chat memory.

## Candidate Gate

A candidate can exist only when the current validated unified ledger contains:

1. one published Genny signal;
2. one different published Marti signal;
3. at least one shared production/marketing workflow;
4. at least one shared mechanism or named entity; and
5. either a shared named entity or a concrete bridge consequence such as cost,
   scale, rights, measurement, stack change, or conversion; and
6. overlap across at least two structured dimensions.

The dimensions are mechanism, workflow, named company/tool, and operator or
economic consequence. Every candidate stores stable IDs and exact evidence for
both signals. Its generated text is explicitly a hypothesis and says that no
causal relationship is asserted.

## Verification Boundary

Generated candidates have `status: candidate` and `confidence: hypothesis`.
They are written to the separate research artifact and never enter the unified
briefing.

A candidate becomes publishable only after an append-only review event records:

- `status: verified`;
- a named `actor_id`;
- a substantive conclusion;
- a verification note explaining what both sources support;
- a unique idempotency key; and
- a timestamp.

A reviewer may reject a candidate with the same attribution requirements.
Rejected and unreviewed candidates are never appended to the unified briefing.
Only verified conclusions render under `Verified Convergence`.

Editorial verification is not a Verified Decision Action. It does not mutate
the decision queue and does not count toward WVDA.

## Commands

Generate or refresh candidates from the current unified ledger:

```bash
python3 scripts/genlens_convergence.py generate \
  --ledger state/signal_ledger_unified.json \
  --reviews state/convergence_reviews.json \
  --out-json state/convergence_candidates.json \
  --out-md state/convergence_brief.md \
  --brief state/latest_unified_brief.md
```

Record a verified conclusion after manually checking both sources:

```bash
python3 scripts/genlens_convergence.py review \
  --candidates state/convergence_candidates.json \
  --reviews state/convergence_reviews.json \
  --candidate-id conv_0123456789abcdefabcd \
  --status verified \
  --actor-id jonathan \
  --note "Both sources support the same workflow handoff; no causal lift is claimed." \
  --conclusion "Generative video editing is moving into paid-media creative operations." \
  --idempotency-key review-message-123
```

Run `generate` again to apply the review event and append the verified
conclusion idempotently to the unified brief.

## Product Promotion Gate

Unified delivery must not become the default until:

- Marti passes its independent promotion gate;
- at least three convergence conclusions survive human verification; and
- human review confirms that the conclusions are useful and non-causal unless
  both sources directly support causality.

The coordinated editorial flow enforces the three-verification minimum and
still holds unified delivery until an operator deliberately supplies
`--allow-unified-delivery`. Ordinary card and vertical counts cannot bypass
this promotion gate. `--force-send` remains an explicit emergency override and
must not be used to simulate promotion evidence.

## July 21, 2026 Isolated Evaluation

An expanded unified no-send run produced 12 linked cards across eight distinct
Genny and Marti layers. The old general editorial counts would have marked that
edition ready. The structured review initially surfaced one broad “new video
capability” pair; the specific-bridge rule rejected it because the sources did
not share a named entity or a concrete cost, scale, rights, measurement, stack,
or conversion consequence.

The final artifact therefore contained zero candidates and zero verified
conclusions. No convergence text appeared in the unified brief, and the unified
promotion gate holds delivery at `0/3` human-verified conclusions. No email was
sent and no review event was fabricated.

Repeated verified patterns may later support benchmarks or market maps. This
artifact does not itself claim those products exist.
