#!/usr/bin/env python3
"""Render evidence-bound decision recommendations from a GenLens signal ledger."""
from __future__ import annotations

import argparse
import collections
import json
import re
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

MEASURED_IMPACT_PATTERN = re.compile(
    r"(?=.*\b(?:roi|roas|cac|cpm|conversion|retention|revenue|cost|time|hours?|days?|lift|increase|decrease|reduction|savings?)\b)"
    r"(?=.*(?:\$\s?\d|\b\d+(?:\.\d+)?\s?(?:%|x|hours?|days?|weeks?|months?)\b))",
    re.I,
)


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


def operator_next_step(record: dict[str, Any]) -> str:
    action = str(record.get("recommended_action") or "watch")
    vertical = str(next(iter(record.get("verticals", [])), "the affected workflow"))
    if action == "migrate":
        return (
            "Inventory affected workflows, owners, exports, integrations, and the shutdown deadline; "
            "then run a recovery and feature-parity check against replacement options."
        )
    if action == "budget":
        return (
            "Model the change against current volume, markets, margins, and contract terms; compare present "
            "and proposed total cost before changing a budget."
        )
    if action == "brief":
        return (
            "Map the change to active campaigns, assets, and review controls; confirm rollout scope and assign "
            "an owner to update the operating checklist."
        )
    if action == "test":
        if vertical == "Agentic Marketing Workflows":
            return (
                "Run one least-privilege sandbox workflow with human approval on every external action; measure "
                "operator time, task accuracy, error recovery, and approval escapes."
            )
        if vertical == "Paid Media / Creative Performance":
            return (
                "Choose one representative campaign, freeze its baseline, and test the new control with capped "
                "spend while measuring reach, frequency, cost, and operator effort."
            )
        if vertical == "Lifecycle / Retention":
            return (
                "Test one non-production segmentation or identity task on a representative sample; verify "
                "accuracy, auditability, permissions, and reversibility."
            )
        if vertical == "SEO / AEO / Content Systems":
            return (
                "Enable the capability on one bounded property and compare reporting coverage, latency, and "
                "decision usefulness with the existing baseline."
            )
        return (
            f"Run one bounded {vertical} workflow against a recorded baseline; measure quality, time, cost, "
            "permissions, and reversibility."
        )
    return (
        "Set a follow-up trigger—general availability, applicable pricing, independent operator evidence, or a "
        "second authoritative source—and assign a review date."
    )


def decision_condition(record: dict[str, Any]) -> str:
    action = str(record.get("recommended_action") or "watch")
    if action == "migrate":
        return "Approve a cutover only after export recovery, critical integration parity, security review, owner, and rollback plan are verified."
    if action == "budget":
        return "Change budget only when the terms apply to the account and the modeled economics clear an owner-defined threshold."
    if action == "brief":
        return "Change operating guidance only after the effective date, affected inventory, and required control are confirmed."
    if action == "test":
        return "Adopt only if a predefined metric improves without breaching cost, quality, permission, or reversibility guardrails."
    return "Take no implementation action until the named follow-up trigger occurs."


def evidence_boundary(record: dict[str, Any]) -> str:
    text = f"{record.get('title') or ''} {record.get('summary') or ''}"
    if MEASURED_IMPACT_PATTERN.search(text):
        return "The source includes a measured outcome; verify its denominator, time window, cohort, and applicability before using it as a forecast."
    if record.get("confidence") == "primary-source":
        return "The primary source verifies the change, not local ROI, cost, or performance impact; quantify those in the bounded next step."
    return "This is single-source evidence; corroborate the change and quantify local impact before any irreversible action."


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
            f"- Operator next step: {operator_next_step(record)}",
            f"- Decision condition: {decision_condition(record)}",
            f"- Evidence boundary: {evidence_boundary(record)}",
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
