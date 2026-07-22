#!/usr/bin/env python3
"""Persist lens evaluation evidence and report fail-closed promotion status."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

import genlens_editorial_ops as editorial_ops
import genlens_signal_ledger as signal_ledger

LOG_VERSION = "1.0.0"
LENSES = {"genny", "marti", "unified"}
REVIEW_VERDICTS = {"accepted", "false_positive"}
REVIEW_ISSUES = {"layer", "relevance", "source", "evidence", "duplicate", "other"}
CHANNELS = {"cli", "discord", "email", "web", "api", "other"}
MARTI_REQUIRED_RUNS = 3
MARTI_REVIEW_TARGET = 20
MARTI_MAX_FALSE_POSITIVES = 1
MARTI_MIN_AUTHORITY_RATIO = 0.60


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalize_timestamp(value: str) -> str:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def deterministic_id(prefix: str, idempotency_key: str) -> str:
    key = str(idempotency_key or "").strip()
    if not key:
        raise ValueError("An explicit idempotency key is required")
    return prefix + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def empty_log() -> dict[str, Any]:
    return {
        "log_version": LOG_VERSION,
        "generated_at": utc_now(),
        "runs": [],
        "reviews": [],
    }


def validate_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(row, str) or not row for row in value):
        raise ValueError(f"{label} must be a list of nonempty strings")


def validate_log(payload: dict[str, Any]) -> None:
    if set(payload) != {"log_version", "generated_at", "runs", "reviews"}:
        raise ValueError("Promotion log fields do not match the versioned contract")
    if payload.get("log_version") != LOG_VERSION:
        raise ValueError("Promotion log version mismatch")
    normalize_timestamp(str(payload.get("generated_at") or ""))
    if not isinstance(payload.get("runs"), list) or not isinstance(payload.get("reviews"), list):
        raise ValueError("Promotion runs and reviews must be lists")

    run_fields = {
        "id", "idempotency_key", "lens", "evaluation_date", "recorded_at",
        "ledger_observed_at", "brief_fingerprint", "url_fingerprint",
        "signal_ids", "linked_cards", "signal_vertical_count",
        "duplicate_titles", "primary_or_authoritative_cards",
        "source_authority_ratio", "exact_repeat", "new_link_count",
        "min_cards", "min_verticals", "min_authority_ratio",
        "issue_gate_passed", "recorded_by",
    }
    run_ids: set[str] = set()
    run_keys: set[str] = set()
    runs_by_id: dict[str, dict[str, Any]] = {}
    for run in payload["runs"]:
        if not isinstance(run, dict) or set(run) != run_fields:
            raise ValueError("Promotion run fields do not match the versioned contract")
        run_id = str(run.get("id") or "")
        key = str(run.get("idempotency_key") or "")
        if not re.fullmatch(r"evalrun_[a-f0-9]{20}", run_id) or run_id in run_ids or key in run_keys:
            raise ValueError("Invalid or duplicate promotion run identity")
        if run_id != deterministic_id("evalrun_", key):
            raise ValueError("Promotion run ID does not match its idempotency key")
        if run.get("lens") not in LENSES:
            raise ValueError("Invalid promotion run lens")
        recorded_at = normalize_timestamp(str(run.get("recorded_at") or ""))
        ledger_observed = normalize_timestamp(str(run.get("ledger_observed_at") or ""))
        if run.get("evaluation_date") != ledger_observed[:10]:
            raise ValueError("Promotion evaluation date must match the ledger observation date")
        if not re.fullmatch(r"[a-f0-9]{64}", str(run.get("brief_fingerprint") or "")):
            raise ValueError("Invalid promotion brief fingerprint")
        if not re.fullmatch(r"[a-f0-9]{64}", str(run.get("url_fingerprint") or "")):
            raise ValueError("Invalid promotion URL fingerprint")
        validate_string_list(run.get("signal_ids"), "Promotion signal IDs")
        if any(not re.fullmatch(r"sig_[a-f0-9]{20}", value) for value in run["signal_ids"]):
            raise ValueError("Promotion run contains an invalid signal ID")
        integer_fields = (
            "linked_cards", "signal_vertical_count", "duplicate_titles",
            "primary_or_authoritative_cards", "new_link_count", "min_cards", "min_verticals",
        )
        if any(not isinstance(run.get(field), int) or int(run[field]) < 0 for field in integer_fields):
            raise ValueError("Promotion run count fields must be nonnegative integers")
        ratio = run.get("source_authority_ratio")
        minimum = run.get("min_authority_ratio")
        if not isinstance(ratio, (int, float)) or not 0 <= float(ratio) <= 1:
            raise ValueError("Invalid promotion source-authority ratio")
        if not isinstance(minimum, (int, float)) or not 0 <= float(minimum) <= 1:
            raise ValueError("Invalid promotion minimum authority ratio")
        expected_pass = bool(
            run["linked_cards"] >= run["min_cards"]
            and run["signal_vertical_count"] >= run["min_verticals"]
            and run["duplicate_titles"] == 0
            and float(ratio) >= float(minimum)
            and not run["exact_repeat"]
        )
        if bool(run.get("issue_gate_passed")) != expected_pass:
            raise ValueError("Promotion run pass state does not match its evidence")
        if not str(run.get("recorded_by") or "").strip() or recorded_at < ledger_observed:
            raise ValueError("Invalid promotion run attribution or chronology")
        run_ids.add(run_id)
        run_keys.add(key)
        runs_by_id[run_id] = run

    review_fields = {
        "id", "idempotency_key", "run_id", "signal_id", "verdict",
        "issue_type", "actor_id", "channel", "note", "occurred_at",
    }
    review_ids: set[str] = set()
    review_keys: set[str] = set()
    for review in payload["reviews"]:
        if not isinstance(review, dict) or set(review) != review_fields:
            raise ValueError("Promotion review fields do not match the versioned contract")
        review_id = str(review.get("id") or "")
        key = str(review.get("idempotency_key") or "")
        if not re.fullmatch(r"evalrev_[a-f0-9]{20}", review_id) or review_id in review_ids or key in review_keys:
            raise ValueError("Invalid or duplicate promotion review identity")
        if review_id != deterministic_id("evalrev_", key):
            raise ValueError("Promotion review ID does not match its idempotency key")
        run = runs_by_id.get(str(review.get("run_id") or ""))
        if run is None or review.get("signal_id") not in run["signal_ids"]:
            raise ValueError("Promotion review does not reference an accepted card occurrence")
        if review.get("verdict") not in REVIEW_VERDICTS:
            raise ValueError("Invalid promotion review verdict")
        issue = review.get("issue_type")
        if review["verdict"] == "accepted" and issue is not None:
            raise ValueError("Accepted review cannot carry a false-positive issue")
        if review["verdict"] == "false_positive" and issue not in REVIEW_ISSUES:
            raise ValueError("False-positive review requires a controlled issue type")
        if review.get("channel") not in CHANNELS:
            raise ValueError("Invalid promotion review channel")
        if not str(review.get("actor_id") or "").strip() or not str(review.get("note") or "").strip():
            raise ValueError("Promotion review requires human attribution and a note")
        normalize_timestamp(str(review.get("occurred_at") or ""))
        review_ids.add(review_id)
        review_keys.add(key)


def load_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_log()
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read promotion log without risking history loss: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Promotion log has an invalid structure: {path}")
    validate_log(payload)
    return payload


def write_log(path: Path, payload: dict[str, Any]) -> None:
    validate_log(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    temp_path.replace(path)


def current_published_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    current_ids = set(str(value) for value in payload.get("latest_run", {}).get("observed_signal_ids", []))
    return [
        row for row in payload.get("records", [])
        if isinstance(row, dict)
        and row.get("status") == "published"
        and str(row.get("id") or "") in current_ids
    ]


def record_run(
    *,
    log_path: Path,
    ledger_path: Path,
    brief_path: Path,
    idempotency_key: str,
    min_cards: int,
    min_verticals: int,
    exact_repeat: bool = False,
    new_link_count: int = 0,
    min_authority_ratio: float = MARTI_MIN_AUTHORITY_RATIO,
    recorded_by: str = "editorial-ops",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    try:
        ledger = json.loads(ledger_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read evaluation ledger: {ledger_path}") from exc
    signal_ledger.validate_signal_ledger(ledger)
    analysis = editorial_ops.analyze_brief(brief_path)
    latest = ledger["latest_run"]
    lens = str(latest.get("lens") or "")
    if lens not in LENSES:
        raise ValueError("Evaluation ledger has an unsupported lens")
    ledger_observed_at = normalize_timestamp(str(latest.get("observed_at") or ""))
    published = current_published_records(ledger)
    signal_ids = [str(row["id"]) for row in published]
    authoritative = sum(
        1 for row in published
        if row.get("confidence") == "primary-source" or row.get("source", {}).get("authoritative")
    )
    linked_cards = int(analysis["linked_cards"])
    ratio = authoritative / linked_cards if linked_cards else 0.0
    duplicate_titles = len(dict(analysis["duplicates"]))
    key = str(idempotency_key or "").strip()
    event = {
        "id": deterministic_id("evalrun_", key),
        "idempotency_key": key,
        "lens": lens,
        "evaluation_date": ledger_observed_at[:10],
        "recorded_at": normalize_timestamp(recorded_at or utc_now()),
        "ledger_observed_at": ledger_observed_at,
        "brief_fingerprint": hashlib.sha256(brief_path.read_bytes()).hexdigest(),
        "url_fingerprint": str(analysis["url_fingerprint"]),
        "signal_ids": signal_ids,
        "linked_cards": linked_cards,
        "signal_vertical_count": int(analysis["signal_vertical_count"]),
        "duplicate_titles": duplicate_titles,
        "primary_or_authoritative_cards": authoritative,
        "source_authority_ratio": round(ratio, 6),
        "exact_repeat": bool(exact_repeat),
        "new_link_count": max(0, int(new_link_count)),
        "min_cards": max(1, int(min_cards)),
        "min_verticals": max(1, int(min_verticals)),
        "min_authority_ratio": float(min_authority_ratio),
        "issue_gate_passed": bool(
            linked_cards >= min_cards
            and int(analysis["signal_vertical_count"]) >= min_verticals
            and duplicate_titles == 0
            and ratio >= min_authority_ratio
            and not exact_repeat
        ),
        "recorded_by": str(recorded_by or "editorial-ops").strip(),
    }
    log = load_log(log_path)
    existing = next((row for row in log["runs"] if row.get("id") == event["id"]), None)
    if existing:
        comparable = {key: value for key, value in event.items() if key != "recorded_at"}
        if any(existing.get(key) != value for key, value in comparable.items()):
            raise ValueError("Run idempotency key was already used for different evaluation evidence")
        return {"created": False, "run": existing, "status": promotion_status(log, lens)}
    log["runs"].append(event)
    log["generated_at"] = event["recorded_at"]
    write_log(log_path, log)
    return {"created": True, "run": event, "status": promotion_status(log, lens)}


def record_review(
    *,
    log_path: Path,
    run_id: str,
    signal_id: str,
    verdict: str,
    actor_id: str,
    channel: str,
    note: str,
    idempotency_key: str,
    issue_type: str | None = None,
    occurred_at: str | None = None,
) -> dict[str, Any]:
    log = load_log(log_path)
    run = next((row for row in log["runs"] if row.get("id") == run_id), None)
    if run is None or signal_id not in run["signal_ids"]:
        raise ValueError("Review must reference an accepted signal occurrence in a recorded run")
    if verdict not in REVIEW_VERDICTS:
        raise ValueError("Unsupported review verdict")
    if verdict == "accepted":
        issue_type = None
    elif issue_type not in REVIEW_ISSUES:
        raise ValueError("False-positive review requires a controlled issue type")
    if channel not in CHANNELS or not actor_id.strip() or not note.strip():
        raise ValueError("Review requires actor, channel, and note")
    key = str(idempotency_key or "").strip()
    event = {
        "id": deterministic_id("evalrev_", key),
        "idempotency_key": key,
        "run_id": run_id,
        "signal_id": signal_id,
        "verdict": verdict,
        "issue_type": issue_type,
        "actor_id": actor_id.strip(),
        "channel": channel,
        "note": note.strip(),
        "occurred_at": normalize_timestamp(occurred_at or utc_now()),
    }
    existing = next((row for row in log["reviews"] if row.get("id") == event["id"]), None)
    if existing:
        if existing != event:
            raise ValueError("Review idempotency key was already used for a different review")
        return {"created": False, "review": existing, "status": promotion_status(log, str(run["lens"]))}
    log["reviews"].append(event)
    log["generated_at"] = event["occurred_at"]
    write_log(log_path, log)
    return {"created": True, "review": event, "status": promotion_status(log, str(run["lens"]))}


def promotion_status(log: dict[str, Any], lens: str = "marti") -> dict[str, Any]:
    validate_log(log)
    lens_runs = [row for row in log["runs"] if row.get("lens") == lens]
    latest_by_date: dict[str, dict[str, Any]] = {}
    for run in lens_runs:
        latest_by_date[str(run["evaluation_date"])] = run
    dated_runs = [latest_by_date[key] for key in sorted(latest_by_date)]
    streak = 0
    for run in reversed(dated_runs):
        if not run["issue_gate_passed"]:
            break
        streak += 1

    occurrences: list[tuple[str, str]] = []
    for run in reversed(dated_runs):
        for signal_id in run["signal_ids"]:
            occurrence = (str(run["id"]), str(signal_id))
            if occurrence not in occurrences:
                occurrences.append(occurrence)
            if len(occurrences) >= MARTI_REVIEW_TARGET:
                break
        if len(occurrences) >= MARTI_REVIEW_TARGET:
            break
    latest_reviews: dict[tuple[str, str], dict[str, Any]] = {}
    target_set = set(occurrences)
    for review in log["reviews"]:
        key = (str(review["run_id"]), str(review["signal_id"]))
        if key in target_set:
            latest_reviews[key] = review
    reviewed = len(latest_reviews)
    false_positives = sum(row["verdict"] == "false_positive" for row in latest_reviews.values())
    run_gate = streak >= MARTI_REQUIRED_RUNS
    review_gate = bool(
        len(occurrences) >= MARTI_REVIEW_TARGET
        and reviewed >= MARTI_REVIEW_TARGET
        and false_positives <= MARTI_MAX_FALSE_POSITIVES
    )
    promoted = bool(lens == "marti" and run_gate and review_gate)
    if promoted:
        reason = "passed Marti promotion gate"
    elif not run_gate:
        reason = f"hold: Marti clean dated run streak={streak}/{MARTI_REQUIRED_RUNS}"
    elif len(occurrences) < MARTI_REVIEW_TARGET:
        reason = f"hold: Marti accepted-card occurrences={len(occurrences)}/{MARTI_REVIEW_TARGET}"
    elif reviewed < MARTI_REVIEW_TARGET:
        reason = f"hold: Marti human reviews={reviewed}/{MARTI_REVIEW_TARGET}"
    else:
        reason = f"hold: Marti false positives={false_positives}/{MARTI_MAX_FALSE_POSITIVES} allowed"
    return {
        "lens": lens,
        "promoted": promoted,
        "reason": reason,
        "clean_dated_run_streak": streak,
        "required_clean_runs": MARTI_REQUIRED_RUNS,
        "accepted_card_occurrences": len(occurrences),
        "reviewed_card_occurrences": reviewed,
        "review_target": MARTI_REVIEW_TARGET,
        "false_positives": false_positives,
        "max_false_positives": MARTI_MAX_FALSE_POSITIVES,
        "latest_evaluation_date": dated_runs[-1]["evaluation_date"] if dated_runs else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record-run")
    record.add_argument("--log", required=True)
    record.add_argument("--ledger", required=True)
    record.add_argument("--brief", required=True)
    record.add_argument("--idempotency-key", required=True)
    record.add_argument("--min-cards", type=int, required=True)
    record.add_argument("--min-verticals", type=int, required=True)
    record.add_argument("--min-authority-ratio", type=float, default=MARTI_MIN_AUTHORITY_RATIO)
    record.add_argument("--new-link-count", type=int, default=0)
    record.add_argument("--exact-repeat", action="store_true")
    record.add_argument("--recorded-by", default="editorial-ops")

    review = subparsers.add_parser("record-review")
    review.add_argument("--log", required=True)
    review.add_argument("--run-id", required=True)
    review.add_argument("--signal-id", required=True)
    review.add_argument("--verdict", choices=sorted(REVIEW_VERDICTS), required=True)
    review.add_argument("--issue-type", choices=sorted(REVIEW_ISSUES))
    review.add_argument("--actor-id", required=True)
    review.add_argument("--channel", choices=sorted(CHANNELS), default="cli")
    review.add_argument("--note", required=True)
    review.add_argument("--idempotency-key", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--log", required=True)
    status.add_argument("--lens", choices=sorted(LENSES), default="marti")

    validate = subparsers.add_parser("validate")
    validate.add_argument("--log", required=True)

    args = parser.parse_args()
    log_path = Path(args.log)
    if args.command == "record-run":
        result = record_run(
            log_path=log_path,
            ledger_path=Path(args.ledger),
            brief_path=Path(args.brief),
            idempotency_key=args.idempotency_key,
            min_cards=args.min_cards,
            min_verticals=args.min_verticals,
            exact_repeat=args.exact_repeat,
            new_link_count=args.new_link_count,
            min_authority_ratio=args.min_authority_ratio,
            recorded_by=args.recorded_by,
        )
    elif args.command == "record-review":
        result = record_review(
            log_path=log_path,
            run_id=args.run_id,
            signal_id=args.signal_id,
            verdict=args.verdict,
            issue_type=args.issue_type,
            actor_id=args.actor_id,
            channel=args.channel,
            note=args.note,
            idempotency_key=args.idempotency_key,
        )
    elif args.command == "status":
        result = promotion_status(load_log(log_path), args.lens)
    else:
        payload = load_log(log_path)
        result = {"valid": True, "runs": len(payload["runs"]), "reviews": len(payload["reviews"])}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
