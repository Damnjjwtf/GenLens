# GenLens Signal Ledger

Status: Runtime contract v1.0.0

The signal ledger turns ephemeral feed reviews into durable, auditable GenLens
state. It is generated during briefing composition and does not change which
cards render in email or whether the editorial send gate passes.

## Artifacts

- Genny: `state/signal_ledger.json`
- Marti: `state/signal_ledger_marti.json`
- Unified: `state/signal_ledger_unified.json`
- Contract: `data/genlens_signal_record.schema.json`

The `state/` directory is runtime-only and must not be committed. VPS deployment
preserves it.

## Stable identity

Each signal receives a deterministic `sig_` ID derived from its canonical source
URL. URL fragments and common tracking parameters do not change the ID. If no
valid URL exists, the normalized title is the fallback identity input.

Repeated observations update one record:

- `first_observed_at` remains fixed;
- `last_observed_at` advances;
- `observation_count` increments;
- `history` retains compact status and reason-code summaries for the latest 50
  observations, while `reviews` keeps the latest full review detail.

The same source signal can carry reviews from more than one layer or lens while
remaining one record.

## Statuses

- `published`: selected for the public Markdown briefing.
- `qualified`: passed source quality but was not selected for the public set.
- `rejected`: failed quality, recency, relevance, dedupe, or concentration
  checks.

Every review keeps its original quality reason plus the final selection reason,
with normalized reason codes for analysis. A candidate can therefore show that
it passed quality but was withheld by dedupe or concentration. Examples include
`stale-item`, `duplicate-signal`, and `topic-concentration-limit`.

## Decision readiness

Every record stores change, evidence, source classification, confidence, lens,
layer, and a conservative recommended action. Newly qualified or published feed
signals default to `watch`.

`mechanism`, `use_case`, and `impact` remain `null` until a later enrichment step
can support them with evidence. The ledger must not invent those fields merely
to look complete.

This ledger is not the Weekly Verified Decision Actions log. WVDA requires a
separate user-attributed decision queue; opens and clicks are not decisions.

## Commands

Normal composition writes the ledger next to the Markdown output:

```bash
python3 scripts/genlens_compose_brief.py \
  --lens marti \
  --mode expanded \
  --out state/latest_marti_brief.md
```

Override the artifact path when needed:

```bash
python3 scripts/genlens_compose_brief.py \
  --lens genny \
  --ledger-out /tmp/genny-signal-ledger.json \
  --out /tmp/genny-brief.md
```

The coordinated `genlens_editorial_ops.py` flow always includes the correct
lens-specific ledger path in its JSON result and Markdown preflight.
