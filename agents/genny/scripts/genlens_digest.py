#!/usr/bin/env python3
"""Fetch and format the GenLens daily digest for Discord.

This script is deliberately deterministic: it formats only API-provided signals
and never asks an LLM to fill gaps.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DIGEST_URL = os.environ.get("GENLENS_DIGEST_URL", "https://genlens.app/api/digest/today")
STATE_PATH = Path(os.environ.get("GENLENS_STATE_PATH", "/root/.hermes/profiles/genny/state/digest_state.json"))
SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_SCAN_SCRIPT = Path(os.environ.get("GENLENS_SOURCE_SCAN_SCRIPT", str(SCRIPT_DIR / "genlens_source_scan.py")))
DISCORD_CHAR_LIMIT = int(os.environ.get("GENLENS_DISCORD_CHAR_LIMIT", "1800"))
ACTIVE_VERTICALS = ["Product Photography", "AI Filmmaking", "Digital Humans"]
ALIASES = {
    "product_photography": "Product Photography",
    "product-photography": "Product Photography",
    "product photography": "Product Photography",
    "ai_filmmaking": "AI Filmmaking",
    "ai-filmmaking": "AI Filmmaking",
    "ai filmmaking": "AI Filmmaking",
    "commercial_filmmaking": "AI Filmmaking",
    "commercial-filmmaking": "AI Filmmaking",
    "commercial filmmaking": "AI Filmmaking",
    "Commercial Filmmaking": "AI Filmmaking",
    "digital_humans": "Digital Humans",
    "digital-humans": "Digital Humans",
    "digital humans": "Digital Humans",
}


def pacific_today() -> str:
    try:
        from zoneinfo import ZoneInfo

        return dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:
        return (dt.datetime.utcnow() - dt.timedelta(hours=8)).date().isoformat()


def load_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def normalize_vertical(value: Any) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    key = raw.lower().replace("_", " ").replace("-", " ")
    return ALIASES.get(raw.lower()) or ALIASES.get(key) or (raw if raw in ACTIVE_VERTICALS else None)


def fetch_digest() -> Any:
    req = urllib.request.Request(DIGEST_URL, headers={"User-Agent": "Genny/1.0 (+genlens.app)"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=25, context=ctx) as response:
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}")
        ctype = response.headers.get("content-type", "")
        body = response.read(2_000_000)
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        preview = body[:160].decode("utf-8", "replace")
        raise RuntimeError(f"Digest returned non-JSON content ({ctype}): {preview}") from exc


def as_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("signals", "items", "digest", "entries", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            nested = as_list(value)
            if nested:
                return nested
    verticals = data.get("verticals")
    if isinstance(verticals, dict):
        out: list[dict[str, Any]] = []
        for vertical, items in verticals.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        out.append({"vertical": vertical, **item})
        return out
    return []


def first(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def chips(item: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("time_delta", "timeDelta", "time", "cost_delta", "costDelta", "cost", "delta"):
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in values:
            values.append(text)
    if not values:
        return ""
    return " " + " ".join(f"`{v}`" for v in values[:3])


def link_for(item: dict[str, Any]) -> str:
    return first(item, "url", "target_url", "targetUrl", "link", "source_url", "sourceUrl")


def format_digest(data: Any) -> str:
    items = as_list(data)
    grouped: dict[str, list[dict[str, Any]]] = {v: [] for v in ACTIVE_VERTICALS}
    for item in items:
        vertical = normalize_vertical(first(item, "vertical", "category", "section"))
        if vertical in grouped:
            grouped[vertical].append(item)

    if not any(grouped.values()):
        raise RuntimeError("Digest returned no signals for active GenLens verticals.")

    date = first(data, "date", "published_at", "publishedAt") if isinstance(data, dict) else ""
    header = "**GenLens Daily Briefing**"
    if date:
        header += f" - {date}"
    lines = [header, ""]
    for vertical in ACTIVE_VERTICALS:
        signals = grouped[vertical]
        if not signals:
            continue
        lines.append(f"**{vertical}**")
        for item in signals[:8]:
            title = first(item, "signal_title", "signalTitle", "title", "headline", "name") or "Untitled signal"
            summary = first(item, "one_line_summary", "oneLineSummary", "summary", "description", "content")
            url = link_for(item)
            tail = chips(item)
            if url:
                lines.append(f"- [{title}]({url}){tail}")
            else:
                lines.append(f"- {title}{tail}")
            if summary:
                lines.append(f"  {summary}")
        lines.append("")
    return "\n".join(lines).strip()


def unavailable_message(reason: str) -> str:
    return (
        "**GenLens Daily Briefing unavailable**\n"
        f"Genny could not fetch `genlens.app/api/digest/today`: {reason}\n"
        "No signals were fabricated. I will try again in one hour."
    )


def trim_for_discord(message: str, limit: int = DISCORD_CHAR_LIMIT) -> str:
    if len(message) <= limit:
        return message
    suffix = "\n\n_Source-watch fallback truncated. Ask Genny for `source_scan` to see the full queue._"
    return message[: max(0, limit - len(suffix))].rstrip() + suffix


def clean_source_scan(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith("# GenLens Source Scan") or line.startswith("Generated:"):
            continue
        if not line.strip() and (not lines or not lines[-1].strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def source_watch_fallback(reason: str) -> str:
    sections: list[str] = []
    for vertical in ACTIVE_VERTICALS:
        try:
            result = subprocess.run(
                [str(SOURCE_SCAN_SCRIPT), "--vertical", vertical, "--limit", "1"],
                check=False,
                text=True,
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            sections.append(f"## {vertical}\n- Source scan failed: {exc}")
            continue
        output = clean_source_scan(result.stdout or result.stderr or "")
        if output:
            sections.append(output)
        else:
            sections.append(f"## {vertical}\n- No source leads returned by local scanner.")

    message = (
        "**GenLens Daily Source Watch**\n"
        f"Primary API unavailable: `{reason}`\n"
        "No signals were fabricated. These are source leads for manual verification.\n\n"
        + "\n\n".join(sections)
    )
    return trim_for_discord(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-only", action="store_true", help="Only run if today previously failed and has not succeeded.")
    args = parser.parse_args()

    today = pacific_today()
    state = load_state()
    today_state = state.get(today, {}) if isinstance(state.get(today, {}), dict) else {}
    if args.retry_only and today_state.get("status") != "failed":
        return 0

    try:
        message = format_digest(fetch_digest())
    except urllib.error.HTTPError as exc:
        reason = f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
    except Exception as exc:
        reason = str(exc)
    else:
        now_utc = dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        state[today] = {"status": "sent", "last_attempt_utc": now_utc}
        save_state(state)
        print(message)
        return 0

    fallback_message = source_watch_fallback(reason)
    attempts = int(today_state.get("attempts", 0)) + 1
    now_utc = dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    state[today] = {
        "status": "fallback_sent",
        "attempts": attempts,
        "last_error": reason,
        "last_attempt_utc": now_utc,
    }
    save_state(state)
    if not args.retry_only:
        print(fallback_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
