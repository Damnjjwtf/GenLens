#!/usr/bin/env python3
"""Render evidence-bound decision recommendations from a GenLens signal ledger."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any

import genlens_signal_ledger as signal_ledger

ACTION_ORDER = {
    "migrate": 0,
    "budget": 1,
    "brief": 2,
    "test": 3,
    "adopt": 4,
    "avoid": 5,
    "plan": 6,
    "watch": 7,
}


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read signal ledger: {path}") from exc
    signal_ledger.validate_signal_ledger(payload)
    return payload


def current_published_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    latest_run = payload.get("latest_run", {})
    current_ids = set(str(value) for value in latest_run.get("observed_signal_ids", []))
    records = [
        row
        for row in payload.get("records", [])
        if isinstance(row, dict)
        and row.get("status") == "published"
        and str(row.get("id")) in current_ids
    ]
    return sorted(
        records,
        key=lambda row: (
            ACTION_ORDER.get(str(row.get("recommended_action") or "watch"), 99),
            -int(row.get("score") or 0),
            str(row.get("title") or ""),
        ),
    )


def evidence_link(record: dict[str, Any]) -> str:
    evidence = next(
        (row for row in record.get("evidence", []) if isinstance(row, dict) and row.get("url")),
        {},
    )
    url = str(evidence.get("url") or record.get("canonical_url") or "")
    source = str(evidence.get("source_name") or record.get("source", {}).get("name") or "Source")
    published_at = str(evidence.get("published_at") or "")
    label = f"{source}, {published_at}" if published_at else source
    return f"[{label}]({url})" if url else label


def render_decision_brief(payload: dict[str, Any], limit: int = 12) -> str:
    latest_run = payload["latest_run"]
    lens = str(latest_run.get("lens") or "genlens")
    observed_at = str(latest_run.get("observed_at") or "")
    all_published = current_published_records(payload)
    records = all_published[: max(1, limit)]
    authoritative = sum(
        1
        for row in records
        if row.get("confidence") == "primary-source" or row.get("source", {}).get("authoritative")
    )
    rejected = [
        row
        for row in payload.get("records", [])
        if isinstance(row, dict)
        and row.get("status") == "rejected"
        and str(row.get("id")) in set(latest_run.get("observed_signal_ids", []))
    ]
    rejection_counts = collections.Counter(
        str(row.get("rejection_reason") or "unspecified") for row in rejected
    )

    lines = [
        f"# GenLens Decision Brief — {lens.title()}",
        "",
        f"Generated from validated signal ledger `{payload.get('schema_version')}` at `{observed_at}`.",
        "",
        "These are evidence-bound GenLens recommendations, not recorded user decisions. They do not count toward Weekly Verified Decision Actions. A named user must explicitly confirm an action before it enters the decision queue.",
        "",
        "## Decision Readiness",
        "",
        f"- Published signals in this run: {len(all_published)}",
        f"- Recommendations rendered: {len(records)}",
        f"- Primary or authoritative rendered signals: {authoritative}/{len(records)}" if records else "- Primary or authoritative rendered signals: 0/0",
        f"- Rejected candidates retained for audit: {len(rejected)}",
        "",
        "## Recommended Decisions",
        "",
    ]
    if not records:
        lines.extend([
            "- No current published signal supports an operator recommendation. Improve source coverage; do not manufacture a decision.",
            "",
        ])
    for record in records:
        action = str(record.get("recommended_action") or "watch")
        title = str(record.get("title") or "Untitled signal")
        url = str(record.get("canonical_url") or "")
        title_link = f"[{title}]({url})" if url else title
        lines.extend([
            f"### {action.title()} — {title_link}",
            "",
            f"- Signal ID: `{record.get('id')}`",
            f"- Lens / layer: {', '.join(record.get('lenses', []))} / {', '.join(record.get('verticals', []))}",
            f"- Evidence-backed change: {record.get('summary') or record.get('change')}",
            f"- Mechanism: {record.get('mechanism') or 'Not yet established'}",
            f"- Operator use case: {record.get('use_case') or 'Not yet established'}",
            f"- Expected impact: {record.get('impact') or 'Not yet established'}",
            f"- Confidence: `{record.get('confidence')}`",
            f"- Evidence: {evidence_link(record)}",
            f"- Confirmation needed: a named user must explicitly choose `{action}` (or another supported action) with an attribution note.",
            "",
        ])

    lines.extend(["## Rejection Audit", ""])
    if rejection_counts:
        for reason, count in rejection_counts.most_common(8):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- No rejected candidates in the current run.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    payload = load_ledger(Path(args.ledger))
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_decision_brief(payload, args.limit))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
