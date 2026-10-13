#!/usr/bin/env python3
"""Push reviewed ledger observations to GenLens without losing audit history.

Run only after a successful Genny/Marti composition. Never run this during
source discovery. This script does not publish signals or bypass promotion.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from genlens_signal_ledger import validate_signal_ledger

SCHEMA_VERSION = "1.0.0"


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Never forward the ingestion bearer token across HTTP redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def event_for(actor: str, record: dict[str, Any]) -> dict[str, Any]:
    """Stable event identity for identical actor + ledger snapshot."""
    serialized = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256((actor + "\x00" + serialized).encode("utf-8")).hexdigest()
    event_id = "evt_" + digest[:24]
    return {
        "schema_version": SCHEMA_VERSION,
        "actor_id": actor,
        "event_id": event_id,
        "idempotency_key": event_id,
        "record": record,
    }


def event_batch(ledger: dict[str, Any], include_history: bool = False) -> list[dict[str, Any]]:
    validate_signal_ledger(ledger)
    run = ledger["latest_run"]
    observed = set(run["observed_signal_ids"])
    records = [
        row for row in ledger["records"]
        if include_history or row["id"] in observed
    ]
    return [event_for(run["lens"], row) for row in sorted(records, key=lambda r: r["id"])]


def read_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "acknowledged": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Cannot safely load the existing push checkpoint") from exc
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("acknowledged"), dict):
        raise ValueError("Existing push checkpoint has an unknown structure")
    return data


def write_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=".genlens-push-", suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            json.dump(data, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def validate_endpoint(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"} and not parsed.username and not parsed.password:
        return
    raise ValueError("Ingestion URL must be HTTPS, or HTTP on localhost for development")


def send_event(url: str, token: str, event: dict[str, Any], timeout: float = 20.0) -> dict[str, Any]:
    payload = json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.build_opener(RejectRedirects).open(request, timeout=timeout) as response:
            status = response.status
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print secrets, response body, or exception headers.
        raise RuntimeError("Ingestion returned HTTP " + str(exc.code)) from None
    except urllib.error.URLError:
        raise RuntimeError("Ingestion endpoint could not be reached") from None
    if status not in (200, 201) or not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError("Ingestion returned an unexpected acknowledgement")
    if result.get("event_id") != event["event_id"] or result.get("signal_id") != event["record"]["id"]:
        raise RuntimeError("Ingestion acknowledgement did not match the submitted event")
    return result


def push(
    events: list[dict[str, Any]], checkpoint_path: Path, *,
    url: str | None, token: str | None, dry_run: bool = False, max_records: int = 50
) -> dict[str, int]:
    if max_records < 1:
        raise ValueError("max_records must be positive")
    state = read_checkpoint(checkpoint_path)
    remaining = [e for e in events if e["event_id"] not in state["acknowledged"]][:max_records]
    report = {"seen": len(events), "pending": len(remaining), "acked": 0, "skipped": len(events) - len(remaining)}
    if dry_run:
        return report
    if not url or not token or len(token) < 32:
        raise ValueError("Set GENLENS_INGEST_URL and a sufficiently long GENLENS_INGEST_TOKEN")
    validate_endpoint(url)
    for event in remaining:
        send_event(url, token, event)
        state["acknowledged"][event["event_id"]] = {
            "signal_id": event["record"]["id"],
            "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        write_checkpoint(checkpoint_path, state)
        report["acked"] += 1
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Idempotently push GenLens ledger observations")
    parser.add_argument("--ledger", required=True, type=Path, help="Path to the validated Genny/Marti ledger JSON")
    parser.add_argument("--checkpoint", type=Path, help="Optional persistent acknowledgement file")
    parser.add_argument("--include-history", action="store_true", help="Explicit one-time backfill of old observations")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-records", type=int, default=50)
    args = parser.parse_args(argv)

    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        events = event_batch(ledger, include_history=args.include_history)
        checkpoint = args.checkpoint or args.ledger.parent / "genlens_push_acks.json"
        report = push(
            events, checkpoint,
            url=os.environ.get("GENLENS_INGEST_URL"),
            token=os.environ.get("GENLENS_INGEST_TOKEN"),
            dry_run=args.dry_run, max_records=args.max_records,
        )
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print("GenLens ledger push failed: " + str(exc), file=sys.stderr)
        return 1

    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
