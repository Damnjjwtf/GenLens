# GenLens Lens Promotion Governance

Marti and unified delivery fail closed until durable evidence proves the
documented promotion gates. A passing issue is necessary but not sufficient for
scheduled delivery.

## Runtime artifacts

- Append-only evidence log: `state/lens_evaluations.json`
- Versioned contract: `data/genlens_promotion_log.schema.json`
- Recorder, reviewer, validator, and status report:
  `scripts/genlens_promotion.py`

The runtime log is excluded from Git, preserved by VPS sync, and written
atomically. Invalid or unsupported history stops the operation instead of being
overwritten.

## Run evidence

Each recorded evaluation binds one validated signal ledger to one rendered
brief and stores:

- the lens and ledger observation date;
- stable signal IDs and brief/URL fingerprints;
- linked-card and represented-layer counts;
- duplicate-title count;
- primary/authoritative source count and ratio;
- exact-repeat state and number of new links;
- the thresholds used and the resulting issue-gate verdict.

An idempotency key is mandatory. Multiple executions on the same UTC date are
auditable, but only the latest run for that lens/date counts toward the dated
streak. Re-running one feed snapshot three times cannot simulate three days of
reliability. A failed or exact-repeat run resets the clean streak.

## Human card review

Every review references a specific `(run_id, signal_id)` occurrence. It requires
a named actor, channel, note, verdict, and idempotency key. Verdicts are:

- `accepted`
- `false_positive`, with one controlled issue: `layer`, `relevance`, `source`,
  `evidence`, `duplicate`, or `other`

Reviews are never inferred from opens, clicks, model output, or agent judgment.
The latest review of each accepted-card occurrence is used in the status report.

## Marti promotion gate

Marti is promotion-ready only when all conditions hold:

1. Three clean evaluation dates in an uninterrupted streak.
2. Each counted run has at least 6 linked cards across 3 Marti layers.
3. Each counted run has zero duplicate titles and at least 60% primary or
   authoritative cards.
4. Exact-repeat protection passes.
5. The latest 20 accepted-card occurrences all have attributed human reviews.
6. No more than one of those 20 is a layer/relevance false positive.

Marti sends consult this status and hold when the log is missing or incomplete.
Unified sends require Marti promotion in addition to three human-verified
convergence conclusions and explicit unified-delivery approval. `--force-send`
remains an explicit emergency override and does not create promotion evidence.

## Commands

Record a no-send editorial evaluation:

```bash
python3 scripts/genlens_editorial_ops.py \
  --lens marti \
  --mode expanded \
  --record-evaluation \
  --evaluation-idempotency-key marti-2026-07-22-daily
```

Review one accepted card occurrence:

```bash
python3 scripts/genlens_promotion.py record-review \
  --log state/lens_evaluations.json \
  --run-id evalrun_0123456789abcdefabcd \
  --signal-id sig_0123456789abcdefabcd \
  --verdict accepted \
  --actor-id jonathan \
  --channel cli \
  --note "Verified the layer, change, evidence, and relevance." \
  --idempotency-key marti-review-message-123
```

Inspect or validate readiness:

```bash
python3 scripts/genlens_promotion.py status \
  --log state/lens_evaluations.json \
  --lens marti

python3 scripts/genlens_promotion.py validate \
  --log state/lens_evaluations.json
```

Recording a run does not send an email and does not promote a lens by itself.
