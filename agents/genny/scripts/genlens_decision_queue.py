#!/usr/bin/env python3
"""Record explicit user decisions attributed to verified GenLens signals."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import genlens_signal_ledger as signal_ledger

QUEUE_VERSION = "1.0.0"
ACTIONS = {"test", "adopt", "avoid", "migrate", "brief", "budget", "plan", "watch"}
ITEM_STATUSES = {"queued", "in_progress", "completed", "dismissed"}
ACTOR_TYPES = {"user", "agent", "system"}
CHANNELS = {"cli", "discord", "email", "web", "api", "other"}
ACTION_STATUS = {
    "watch": "queued",
    "test": "in_progress",
    "migrate": "in_progress",
    "brief": "in_progress",
    "budget": "in_progress",
    "plan": "in_progress",
    "adopt": "completed",
    "avoid": "completed",
}

BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(os.environ.get("GENLENS_PROFILE_DIR", "/root/.hermes/profiles/genny"))
if not PROFILE_DIR.exists():
    PROFILE_DIR = BASE_DIR
DEFAULT_QUEUE_PATH = PROFILE_DIR / "state" / "decision_queue.json"
DEFAULT_LEDGER_PATH = PROFILE_DIR / "state" / "signal_ledger.json"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalize_timestamp(value: str | None) -> str:
    if not value:
        return utc_now()
    if not isinstance(value, str):
        raise ValueError(f"Invalid ISO timestamp: {value!r}")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def event_id(idempotency_key: str) -> str:
    key = str(idempotency_key or "").strip()
    if not key:
        raise ValueError("An explicit idempotency key is required")
    return "evt_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def item_id(signal_id: str) -> str:
    return "dq_" + hashlib.sha256(signal_id.encode("utf-8")).hexdigest()[:20]


def empty_queue(generated_at: str | None = None) -> dict[str, Any]:
    return {
        "queue_version": QUEUE_VERSION,
        "generated_at": generated_at or utc_now(),
        "items": [],
        "events": [],
    }


def validate_identity(actor_id: str, actor_type: str, channel: str, note: str) -> None:
    if not str(actor_id or "").strip():
        raise ValueError("actor_id is required")
    if actor_type not in ACTOR_TYPES:
        raise ValueError(f"Unsupported actor_type: {actor_type}")
    if channel not in CHANNELS:
        raise ValueError(f"Unsupported channel: {channel}")
    if not str(note or "").strip():
        raise ValueError("A nonempty attribution note is required")


def validate_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(row, str) for row in value):
        raise ValueError(f"{label} must be a list of strings")


def validate_queue(payload: dict[str, Any]) -> None:
    if set(payload) != {"queue_version", "generated_at", "items", "events"}:
        raise ValueError("Decision queue fields do not match the versioned contract")
    if payload.get("queue_version") != QUEUE_VERSION:
        raise ValueError("Decision queue version mismatch")
    if not payload.get("generated_at"):
        raise ValueError("Decision queue generated_at is required")
    normalize_timestamp(payload.get("generated_at"))
    items = payload.get("items")
    events = payload.get("events")
    if not isinstance(items, list) or not isinstance(events, list):
        raise ValueError("Decision queue items and events must be lists")

    item_ids: set[str] = set()
    signal_ids: set[str] = set()
    items_by_id: dict[str, dict[str, Any]] = {}
    item_fields = {
        "id", "signal_id", "title", "canonical_url", "lenses", "verticals",
        "status", "current_action", "created_at", "updated_at",
        "last_actor_id", "last_note",
    }
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Decision queue item must be an object")
        if set(item) != item_fields:
            raise ValueError("Decision queue item fields do not match the versioned contract")
        current_item_id = str(item.get("id") or "")
        signal_id = str(item.get("signal_id") or "")
        if not re.fullmatch(r"dq_[a-f0-9]{20}", current_item_id):
            raise ValueError(f"Invalid decision queue item ID: {current_item_id!r}")
        if current_item_id != item_id(signal_id):
            raise ValueError(f"Decision queue item ID does not match signal ID: {current_item_id}")
        if current_item_id in item_ids or signal_id in signal_ids:
            raise ValueError("Decision queue contains duplicate item or signal IDs")
        if not re.fullmatch(r"sig_[a-f0-9]{20}", signal_id):
            raise ValueError(f"Invalid signal ID in decision queue: {signal_id!r}")
        if item.get("status") not in ITEM_STATUSES:
            raise ValueError(f"Invalid queue status for {current_item_id}")
        if item.get("current_action") not in ACTIONS:
            raise ValueError(f"Invalid current action for {current_item_id}")
        if not isinstance(item.get("title"), str) or not item.get("title"):
            raise ValueError(f"Missing title for {current_item_id}")
        if not isinstance(item.get("canonical_url"), str):
            raise ValueError(f"Invalid canonical URL for {current_item_id}")
        validate_string_list(item.get("lenses"), f"Lenses for {current_item_id}")
        validate_string_list(item.get("verticals"), f"Verticals for {current_item_id}")
        normalize_timestamp(item.get("created_at"))
        normalize_timestamp(item.get("updated_at"))
        if not str(item.get("last_actor_id") or "").strip() or not str(item.get("last_note") or "").strip():
            raise ValueError(f"Missing last-action attribution for {current_item_id}")
        item_ids.add(current_item_id)
        signal_ids.add(signal_id)
        items_by_id[current_item_id] = item

    event_ids: set[str] = set()
    event_fields = {
        "id", "event_type", "item_id", "signal_id", "action", "from_status",
        "to_status", "actor_id", "actor_type", "channel", "note",
        "occurred_at", "qualifies_wvda", "lenses", "verticals",
    }
    state_by_item: dict[str, str] = {}
    first_event_by_item: dict[str, dict[str, Any]] = {}
    last_event_by_item: dict[str, dict[str, Any]] = {}
    last_action_by_item: dict[str, str] = {}
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Decision event must be an object")
        if set(event) != event_fields:
            raise ValueError("Decision event fields do not match the versioned contract")
        current_event_id = str(event.get("id") or "")
        if not re.fullmatch(r"evt_[a-f0-9]{20}", current_event_id) or current_event_id in event_ids:
            raise ValueError(f"Invalid or duplicate decision event ID: {current_event_id!r}")
        current_item_id = str(event.get("item_id") or "")
        item = items_by_id.get(current_item_id)
        if item is None:
            raise ValueError(f"Decision event {current_event_id} references an unknown item")
        if event.get("signal_id") != item.get("signal_id"):
            raise ValueError(f"Decision event {current_event_id} references the wrong signal")
        if event.get("event_type") not in {"decision_action", "state_transition"}:
            raise ValueError(f"Invalid event type for {current_event_id}")
        if event.get("actor_type") not in ACTOR_TYPES or event.get("channel") not in CHANNELS:
            raise ValueError(f"Invalid attribution metadata for {current_event_id}")
        if not str(event.get("actor_id") or "").strip() or not str(event.get("note") or "").strip():
            raise ValueError(f"Incomplete attribution metadata for {current_event_id}")
        normalize_timestamp(event.get("occurred_at"))
        validate_string_list(event.get("lenses"), f"Lenses for {current_event_id}")
        validate_string_list(event.get("verticals"), f"Verticals for {current_event_id}")
        previous_status = state_by_item.get(current_item_id)
        if event.get("from_status") != previous_status:
            raise ValueError(f"Decision event {current_event_id} breaks queue state history")
        if event.get("to_status") not in ITEM_STATUSES:
            raise ValueError(f"Invalid target status for {current_event_id}")
        if event.get("event_type") == "decision_action":
            action = event.get("action")
            if action not in ACTIONS or event.get("to_status") != ACTION_STATUS[action]:
                raise ValueError(f"Invalid decision action transition for {current_event_id}")
            last_action_by_item[current_item_id] = action
        elif event.get("action") is not None:
            raise ValueError(f"State transition {current_event_id} cannot contain an action")
        expected_wvda = bool(
            event.get("event_type") == "decision_action"
            and event.get("actor_type") == "user"
            and event.get("action") in ACTIONS
            and str(event.get("note") or "").strip()
        )
        if bool(event.get("qualifies_wvda")) != expected_wvda:
            raise ValueError(f"WVDA qualification invariant failed for {current_event_id}")
        state_by_item[current_item_id] = str(event["to_status"])
        first_event_by_item.setdefault(current_item_id, event)
        last_event_by_item[current_item_id] = event
        event_ids.add(current_event_id)

    for current_item_id, item in items_by_id.items():
        first = first_event_by_item.get(current_item_id)
        last = last_event_by_item.get(current_item_id)
        if first is None or last is None or first.get("event_type") != "decision_action":
            raise ValueError(f"Decision queue item {current_item_id} has no originating action")
        if item.get("created_at") != first.get("occurred_at"):
            raise ValueError(f"Decision queue item {current_item_id} has invalid creation history")
        if (
            item.get("status") != last.get("to_status")
            or item.get("current_action") != last_action_by_item.get(current_item_id)
            or item.get("updated_at") != last.get("occurred_at")
            or item.get("last_actor_id") != last.get("actor_id")
            or item.get("last_note") != last.get("note")
        ):
            raise ValueError(f"Decision queue item {current_item_id} does not match its event history")

    if events and payload.get("generated_at") != events[-1].get("occurred_at"):
        raise ValueError("Decision queue generated_at does not match the latest appended event")


def load_queue(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_queue()
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read existing decision queue without risking decision-history loss: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Existing decision queue has an invalid structure: {path}")
    validate_queue(payload)
    return payload


def write_queue(path: Path, payload: dict[str, Any]) -> None:
    validate_queue(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def load_signal(ledger_path: Path, signal_id: str) -> dict[str, Any]:
    try:
        payload = json.loads(ledger_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read signal ledger: {ledger_path}") from exc
    signal_ledger.validate_signal_ledger(payload)
    signal = next(
        (row for row in payload.get("records", []) if row.get("id") == signal_id),
        None,
    )
    if signal is None:
        raise ValueError(f"Signal {signal_id} is not present in the signal ledger")
    if signal.get("status") == "rejected":
        raise ValueError(f"Signal {signal_id} is rejected and cannot enter the decision queue")
    return signal


def idempotent_result(
    queue: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any] | None:
    existing = next((row for row in queue["events"] if row.get("id") == expected["id"]), None)
    if existing is None:
        return None
    comparison_keys = (
        "event_type",
        "item_id",
        "signal_id",
        "action",
        "to_status",
        "actor_id",
        "actor_type",
        "channel",
        "note",
        "occurred_at",
    )
    if any(existing.get(key) != expected.get(key) for key in comparison_keys):
        raise ValueError("Idempotency key was already used for a different decision event")
    item = next(row for row in queue["items"] if row.get("id") == existing.get("item_id"))
    return {"deduplicated": True, "item": item, "event": existing}


def record_action(
    *,
    queue_path: Path,
    ledger_path: Path,
    signal_id: str,
    action: str,
    actor_id: str,
    note: str,
    idempotency_key: str,
    actor_type: str = "user",
    channel: str = "cli",
    occurred_at: str | None = None,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise ValueError(f"Unsupported decision action: {action}")
    validate_identity(actor_id, actor_type, channel, note)
    occurred = normalize_timestamp(occurred_at)
    signal = load_signal(ledger_path, signal_id)
    queue = load_queue(queue_path)
    current_item_id = item_id(signal_id)
    existing_item = next((row for row in queue["items"] if row.get("id") == current_item_id), None)
    from_status = existing_item.get("status") if existing_item else None
    to_status = ACTION_STATUS[action]
    current_event = {
        "id": event_id(idempotency_key),
        "event_type": "decision_action",
        "item_id": current_item_id,
        "signal_id": signal_id,
        "action": action,
        "from_status": from_status,
        "to_status": to_status,
        "actor_id": actor_id.strip(),
        "actor_type": actor_type,
        "channel": channel,
        "note": note.strip(),
        "occurred_at": occurred,
        "qualifies_wvda": actor_type == "user",
        "lenses": list(signal.get("lenses") or []),
        "verticals": list(signal.get("verticals") or []),
    }
    duplicate = idempotent_result(queue, current_event)
    if duplicate is not None:
        return duplicate

    if existing_item is None:
        existing_item = {
            "id": current_item_id,
            "signal_id": signal_id,
            "title": signal.get("title") or "Untitled signal",
            "canonical_url": signal.get("canonical_url") or "",
            "lenses": list(signal.get("lenses") or []),
            "verticals": list(signal.get("verticals") or []),
            "status": to_status,
            "current_action": action,
            "created_at": occurred,
            "updated_at": occurred,
            "last_actor_id": actor_id.strip(),
            "last_note": note.strip(),
        }
        queue["items"].append(existing_item)
    else:
        existing_item.update({
            "title": signal.get("title") or existing_item.get("title") or "Untitled signal",
            "canonical_url": signal.get("canonical_url") or existing_item.get("canonical_url") or "",
            "lenses": list(signal.get("lenses") or existing_item.get("lenses") or []),
            "verticals": list(signal.get("verticals") or existing_item.get("verticals") or []),
            "status": to_status,
            "current_action": action,
            "updated_at": occurred,
            "last_actor_id": actor_id.strip(),
            "last_note": note.strip(),
        })
    queue["events"].append(current_event)
    queue["generated_at"] = occurred
    write_queue(queue_path, queue)
    return {"deduplicated": False, "item": existing_item, "event": current_event}


def transition_item(
    *,
    queue_path: Path,
    item_id: str,
    status: str,
    actor_id: str,
    note: str,
    idempotency_key: str,
    actor_type: str = "user",
    channel: str = "cli",
    occurred_at: str | None = None,
) -> dict[str, Any]:
    if status not in ITEM_STATUSES:
        raise ValueError(f"Unsupported queue status: {status}")
    validate_identity(actor_id, actor_type, channel, note)
    occurred = normalize_timestamp(occurred_at)
    queue = load_queue(queue_path)
    item = next((row for row in queue["items"] if row.get("id") == item_id), None)
    if item is None:
        raise ValueError(f"Decision queue item not found: {item_id}")
    current_event = {
        "id": event_id(idempotency_key),
        "event_type": "state_transition",
        "item_id": item_id,
        "signal_id": item["signal_id"],
        "action": None,
        "from_status": item["status"],
        "to_status": status,
        "actor_id": actor_id.strip(),
        "actor_type": actor_type,
        "channel": channel,
        "note": note.strip(),
        "occurred_at": occurred,
        "qualifies_wvda": False,
        "lenses": list(item.get("lenses") or []),
        "verticals": list(item.get("verticals") or []),
    }
    duplicate = idempotent_result(queue, current_event)
    if duplicate is not None:
        return duplicate
    item.update({
        "status": status,
        "updated_at": occurred,
        "last_actor_id": actor_id.strip(),
        "last_note": note.strip(),
    })
    queue["events"].append(current_event)
    queue["generated_at"] = occurred
    write_queue(queue_path, queue)
    return {"deduplicated": False, "item": item, "event": current_event}


def week_bounds(week_start: str | None = None) -> tuple[dt.datetime, dt.datetime]:
    if week_start:
        try:
            start_date = dt.date.fromisoformat(week_start)
        except ValueError as exc:
            raise ValueError(f"Invalid week-start date: {week_start}") from exc
    else:
        today = dt.datetime.now(dt.timezone.utc).date()
        start_date = today - dt.timedelta(days=today.weekday())
    if start_date.weekday() != 0:
        raise ValueError("week_start must be a Monday")
    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=dt.timezone.utc)
    return start, start + dt.timedelta(days=7)


def wvda_report(
    queue_path: Path,
    *,
    week_start: str | None = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    queue = load_queue(queue_path)
    start, end = week_bounds(week_start)
    qualifying = []
    for event in queue["events"]:
        if not event.get("qualifies_wvda"):
            continue
        occurred = dt.datetime.fromisoformat(str(event["occurred_at"]).replace("Z", "+00:00"))
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=dt.timezone.utc)
        occurred = occurred.astimezone(dt.timezone.utc)
        if not (start <= occurred < end):
            continue
        if actor_id and event.get("actor_id") != actor_id:
            continue
        qualifying.append(event)

    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in sorted(qualifying, key=lambda row: str(row.get("occurred_at") or "")):
        key = (
            str(event.get("actor_id") or ""),
            str(event.get("signal_id") or ""),
            str(event.get("action") or ""),
        )
        unique.setdefault(key, event)
    decisions = list(unique.values())

    def counts_for(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in decisions:
            value = str(event.get(key) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    by_lens: dict[str, int] = {}
    for event in decisions:
        for lens in event.get("lenses", []) or ["unknown"]:
            by_lens[str(lens)] = by_lens.get(str(lens), 0) + 1
    return {
        "metric": "Weekly Verified Decision Actions",
        "definition": "Unique user-attributed signal actions per actor, signal, and action type during the UTC week.",
        "week_start": start.date().isoformat(),
        "week_end_exclusive": end.date().isoformat(),
        "actor_filter": actor_id,
        "weekly_verified_decision_actions": len(decisions),
        "qualifying_event_count": len(qualifying),
        "unique_signals": len({str(event.get("signal_id")) for event in decisions}),
        "by_action": counts_for("action"),
        "by_actor": counts_for("actor_id"),
        "by_lens": dict(sorted(by_lens.items())),
        "decision_event_ids": [str(event.get("id")) for event in decisions],
    }


def list_items(queue_path: Path, status: str | None = None) -> list[dict[str, Any]]:
    queue = load_queue(queue_path)
    rows = queue["items"]
    if status:
        if status not in ITEM_STATUSES:
            raise ValueError(f"Unsupported queue status: {status}")
        rows = [row for row in rows if row.get("status") == status]
    return sorted(rows, key=lambda row: str(row.get("updated_at") or ""), reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record and report user-attributed GenLens decisions.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE_PATH))
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER_PATH))
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record-action")
    record.add_argument("--signal-id", required=True)
    record.add_argument("--action", choices=sorted(ACTIONS), required=True)
    record.add_argument("--actor-id", required=True)
    record.add_argument("--actor-type", choices=sorted(ACTOR_TYPES), default="user")
    record.add_argument("--channel", choices=sorted(CHANNELS), default="cli")
    record.add_argument("--note", required=True)
    record.add_argument("--occurred-at")
    record.add_argument("--idempotency-key", required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("--item-id", required=True)
    transition.add_argument("--status", choices=sorted(ITEM_STATUSES), required=True)
    transition.add_argument("--actor-id", required=True)
    transition.add_argument("--actor-type", choices=sorted(ACTOR_TYPES), default="user")
    transition.add_argument("--channel", choices=sorted(CHANNELS), default="cli")
    transition.add_argument("--note", required=True)
    transition.add_argument("--occurred-at")
    transition.add_argument("--idempotency-key", required=True)

    report = subparsers.add_parser("report")
    report.add_argument("--week-start")
    report.add_argument("--actor-id")

    listing = subparsers.add_parser("list")
    listing.add_argument("--status", choices=sorted(ITEM_STATUSES))

    subparsers.add_parser("validate")
    args = parser.parse_args()
    queue_path = Path(args.queue)
    ledger_path = Path(args.ledger)

    if args.command == "record-action":
        result = record_action(
            queue_path=queue_path,
            ledger_path=ledger_path,
            signal_id=args.signal_id,
            action=args.action,
            actor_id=args.actor_id,
            actor_type=args.actor_type,
            channel=args.channel,
            note=args.note,
            occurred_at=args.occurred_at,
            idempotency_key=args.idempotency_key,
        )
    elif args.command == "transition":
        result = transition_item(
            queue_path=queue_path,
            item_id=args.item_id,
            status=args.status,
            actor_id=args.actor_id,
            actor_type=args.actor_type,
            channel=args.channel,
            note=args.note,
            occurred_at=args.occurred_at,
            idempotency_key=args.idempotency_key,
        )
    elif args.command == "report":
        result = wvda_report(queue_path, week_start=args.week_start, actor_id=args.actor_id)
    elif args.command == "list":
        result = {"items": list_items(queue_path, args.status)}
    else:
        queue = load_queue(queue_path)
        validate_queue(queue)
        result = {
            "valid": True,
            "queue_version": queue["queue_version"],
            "items": len(queue["items"]),
            "events": len(queue["events"]),
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
