#!/usr/bin/env python3
"""Preview or deliver a promotion-gated Marti briefing to Discord."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import genlens_promotion as promotion
import genlens_signal_ledger as signal_ledger


PROFILE_DIR = Path(os.environ.get("GENLENS_PROFILE_DIR", "/root/.hermes/profiles/genny"))
DEFAULT_LEDGER = PROFILE_DIR / "state" / "signal_ledger_marti.json"
DEFAULT_PROMOTION_LOG = PROFILE_DIR / "state" / "lens_evaluations.json"
DEFAULT_HISTORY = PROFILE_DIR / "state" / "discord_delivery_history.json"
DEFAULT_ENV_PATH = PROFILE_DIR / ".env"
DEFAULT_WEBHOOK_ENV = "MARTI_DISCORD_WEBHOOK_URL"
HISTORY_VERSION = "1.0.0"
MAX_CARDS = 6
DISCORD_HOSTS = {"discord.com", "discordapp.com", "canary.discord.com", "ptb.discord.com"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def truncate(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"


def valid_discord_webhook(url: str) -> bool:
    parsed = urllib.parse.urlparse(str(url or "").strip())
    return bool(
        parsed.scheme == "https"
        and (parsed.hostname or "").lower() in DISCORD_HOSTS
        and re.fullmatch(r"/api(?:/v\d+)?/webhooks/\d+/[^/]+/?", parsed.path)
    )


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def load_env(path: Path = DEFAULT_ENV_PATH) -> None:
    """Load simple KEY=VALUE entries without replacing exported variables."""
    if not path.exists():
        return
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        raise ValueError(f"Cannot read environment file: {path}") from exc
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def current_published_records(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    signal_ledger.validate_signal_ledger(ledger)
    current_ids = set(ledger["latest_run"]["observed_signal_ids"])
    return [
        record
        for record in ledger["records"]
        if record.get("id") in current_ids and record.get("status") == "published"
    ]


def delivery_readiness(status: dict[str, Any], *, test: bool = False) -> tuple[bool, str]:
    if test:
        return True, "Discord connection test"
    if status.get("promoted") is True:
        return True, "passed Marti promotion gate"
    return False, str(status.get("reason") or "hold: Marti promotion evidence unavailable")


def connection_test_payload() -> dict[str, Any]:
    return {
        "username": "Marti • GenLens",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "Marti feed connected",
            "description": (
                "The Discord connection works. Source-backed Marti briefings will remain "
                "locked until the promotion gate passes."
            ),
            "color": 0x8B5CF6,
            "footer": {"text": "GenLens • AI-native marketing intelligence"},
            "timestamp": utc_now(),
        }],
    }


def briefing_payload(
    ledger: dict[str, Any],
    status: dict[str, Any],
    *,
    max_cards: int = MAX_CARDS,
) -> dict[str, Any]:
    records = current_published_records(ledger)
    records.sort(key=lambda row: (-int(row.get("score") or 0), str(row.get("title") or "")))
    selected = records[: max(1, min(max_cards, 10))]
    observed_at = str(ledger["latest_run"].get("observed_at") or utc_now())
    date = observed_at[:10]
    layers = sorted({layer for row in records for layer in row.get("verticals", [])})
    fields: list[dict[str, Any]] = []
    for record in selected:
        title = truncate(str(record.get("title") or "Untitled signal"), 256)
        summary = truncate(str(record.get("summary") or "Verified source-backed change."), 460)
        url = str(record.get("canonical_url") or "").strip()
        source = str(record.get("source", {}).get("name") or "Source")
        confidence = str(record.get("confidence") or "source-backed")
        link = f"[Open source]({url})" if url.startswith("https://") else "Source URL unavailable"
        fields.append({
            "name": title,
            "value": f"{summary}\n{link} • {source} • {confidence}",
            "inline": False,
        })
    omitted = max(0, len(records) - len(selected))
    description = (
        f"{len(records)} verified signals across {len(layers)} Marti layers. "
        "Every item links to its evidence source."
    )
    if omitted:
        description += f" Showing the top {len(selected)}; {omitted} remain in the full VPS brief."
    return {
        "username": "Marti • GenLens",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": f"Marti Intelligence — {date}",
            "description": description,
            "color": 0x8B5CF6,
            "fields": fields,
            "footer": {
                "text": (
                    "GenLens • Promotion verified • "
                    f"{status.get('reviewed_card_occurrences', 0)} reviewed card occurrences"
                )
            },
            "timestamp": observed_at,
        }],
    }


def payload_fingerprint(payload: dict[str, Any]) -> str:
    stable = json.loads(json.dumps(payload))
    for embed in stable.get("embeds", []):
        embed.pop("timestamp", None)
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def empty_history() -> dict[str, Any]:
    return {"version": HISTORY_VERSION, "updated_at": utc_now(), "deliveries": []}


def load_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_history()
    history = load_json(path, "Discord delivery history")
    if set(history) != {"version", "updated_at", "deliveries"}:
        raise ValueError("Discord delivery history fields do not match the versioned contract")
    if history.get("version") != HISTORY_VERSION or not isinstance(history.get("deliveries"), list):
        raise ValueError("Discord delivery history is invalid or unsupported")
    for row in history["deliveries"]:
        if not isinstance(row, dict) or not str(row.get("fingerprint") or ""):
            raise ValueError("Discord delivery history contains an invalid delivery")
    return history


def write_history(path: Path, history: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        json.dump(history, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def append_delivery(
    history: dict[str, Any],
    *,
    fingerprint: str,
    kind: str,
    message_id: str,
) -> None:
    history["deliveries"].append({
        "fingerprint": fingerprint,
        "kind": kind,
        "message_id": message_id,
        "delivered_at": utc_now(),
    })
    history["deliveries"] = history["deliveries"][-100:]
    history["updated_at"] = utc_now()


def post_webhook(url: str, payload: dict[str, Any]) -> dict[str, str]:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("wait", "true"))
    target = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))
    request = urllib.request.Request(
        target,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "GenLensMartiDiscord/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8", "replace") or "{}")
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ValueError(f"Discord delivery failed: {type(exc).__name__}") from exc
    return {
        "message_id": str(body.get("id") or ""),
        "channel_id": str(body.get("channel_id") or ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--promotion-log", default=str(DEFAULT_PROMOTION_LOG))
    parser.add_argument("--history", default=str(DEFAULT_HISTORY))
    parser.add_argument("--webhook-env", default=DEFAULT_WEBHOOK_ENV)
    parser.add_argument("--max-cards", type=int, default=MAX_CARDS)
    parser.add_argument("--test", action="store_true", help="Use a connection-only message")
    parser.add_argument("--send", action="store_true", help="Actually post; otherwise print a preview")
    args = parser.parse_args()

    load_env()

    if args.test:
        status = {"promoted": False, "reason": "connection test"}
        payload = connection_test_payload()
    else:
        ledger = load_json(Path(args.ledger), "Marti signal ledger")
        status = promotion.promotion_status(
            promotion.load_log(Path(args.promotion_log)),
            "marti",
        )
        payload = briefing_payload(ledger, status, max_cards=args.max_cards)

    ready, reason = delivery_readiness(status, test=args.test)
    fingerprint = payload_fingerprint(payload)
    result: dict[str, Any] = {
        "ready": ready,
        "reason": reason,
        "test": bool(args.test),
        "send_requested": bool(args.send),
        "fingerprint": fingerprint,
    }
    if not args.send:
        result["payload"] = payload
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if not ready:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    webhook = os.environ.get(args.webhook_env, "").strip()
    if not valid_discord_webhook(webhook):
        result.update({"ready": False, "reason": f"missing or invalid {args.webhook_env}"})
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    history_path = Path(args.history)
    history = load_history(history_path)
    if any(row.get("fingerprint") == fingerprint for row in history["deliveries"]):
        result.update({"sent": False, "reason": "hold: exact Discord payload was already delivered"})
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    response = post_webhook(webhook, payload)
    append_delivery(
        history,
        fingerprint=fingerprint,
        kind="test" if args.test else "marti-brief",
        message_id=response["message_id"],
    )
    write_history(history_path, history)
    result.update({"sent": True, **response})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
