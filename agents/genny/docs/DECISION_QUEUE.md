# GenLens Decision Queue

The decision queue is the first durable action layer above the structured
signal ledger. It records what a named actor explicitly decided to do with a
non-rejected GenLens signal and reports the north-star metric, Weekly Verified
Decision Actions (WVDA).

## Runtime Artifacts

- Queue state and event history: `state/decision_queue.json`
- Versioned contract: `data/genlens_decision_queue.schema.json`
- CLI and validation logic: `scripts/genlens_decision_queue.py`

The runtime file is intentionally excluded from Git and preserved by the VPS
sync script. Queue writes are atomic. If the existing file is malformed or uses
an unsupported version, the CLI stops instead of overwriting history.

## What Counts As WVDA

An event counts only when all of these are true:

1. It references a real, non-rejected signal in a validated signal ledger.
2. Its event type is `decision_action`.
3. Its actor type is `user`, with a stable nonempty actor ID.
4. It has a nonempty attribution note stating what the user decided.
5. Its action is one of `test`, `adopt`, `avoid`, `migrate`, `brief`, `budget`,
   `plan`, or `watch`.

WVDA deduplicates by `(actor_id, signal_id, action)` within each UTC week.
Repeated confirmations remain in the audit history but add only one WVDA.

Opens, clicks, email delivery, agent recommendations, system activity, inferred
intent, and queue state transitions do not count. Adding a verified signal to a
watch queue counts only when a user explicitly asks for it.

## Queue States

- `queued`: accepted for later attention.
- `in_progress`: a test, brief, migration, budget, or plan is underway.
- `completed`: an adopt or avoid decision is complete, or the user explicitly
  completes an item.
- `dismissed`: the user explicitly removes the item from active consideration.

State transitions are auditable events. They never add WVDA on their own.

## Examples

Record an explicit user action:

```bash
python3 scripts/genlens_decision_queue.py \
  --ledger state/signal_ledger_marti.json \
  record-action \
  --signal-id sig_0123456789abcdefabcd \
  --action test \
  --actor-id jonathan \
  --channel discord \
  --note "Test this workflow with the growth team." \
  --idempotency-key discord-message-123-test
```

Each mutation requires an idempotency key. Replaying the same event returns the
existing result; reusing the key with a different payload fails.

Move an existing item without increasing WVDA:

```bash
python3 scripts/genlens_decision_queue.py transition \
  --item-id dq_0123456789abcdefabcd \
  --status completed \
  --actor-id jonathan \
  --note "Sandbox test finished." \
  --idempotency-key decision-complete-123
```

Report the metric for a UTC week that starts on Monday:

```bash
python3 scripts/genlens_decision_queue.py report --week-start 2026-07-20
```

Validate the stored queue:

```bash
python3 scripts/genlens_decision_queue.py validate
```

## Operational Rule

Genny and Marti may suggest actions, but they must not record a user-qualified
event until the user explicitly confirms the action. Preserve the user’s words
in the attribution note where practical. Never manufacture activity to improve
the metric.
