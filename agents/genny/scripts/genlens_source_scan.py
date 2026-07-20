#!/usr/bin/env python3
"""Scan Genny's GenLens source list and print a compact source briefing."""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SOURCE_PATH = Path("/root/.hermes/profiles/genny/data/genny_sources.json")


def load_sources() -> dict[str, Any]:
    return json.loads(SOURCE_PATH.read_text())


def strip_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            return parsed.date().isoformat()
    except Exception:
        pass
    return strip_text(value)[:24]


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(node):
        local = child.tag.split("}", 1)[-1].lower()
        if local in names:
            return strip_text(child.text)
    return ""


def child_link(node: ET.Element) -> str:
    for child in list(node):
        local = child.tag.split("}", 1)[-1].lower()
        if local == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def fetch_rss(url: str, limit: int) -> list[dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "GennySourceScan/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=18, context=ctx) as response:
        body = response.read(1_500_000)
    root = ET.fromstring(body)
    nodes = [n for n in root.iter() if n.tag.split("}", 1)[-1].lower() in {"item", "entry"}]
    items: list[dict[str, str]] = []
    for node in nodes[:limit]:
        title = child_text(node, ("title",))
        link = child_link(node)
        published = child_text(node, ("pubdate", "published", "updated", "date"))
        summary = child_text(node, ("description", "summary", "content", "encoded"))
        if title:
            items.append({
                "title": title,
                "url": link,
                "date": parse_date(published),
                "summary": summary[:220],
            })
    return items


def source_matches(source: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    haystack = " ".join([
        str(source.get("name", "")),
        str(source.get("url", "")),
        " ".join(source.get("watch_for", [])),
    ]).lower()
    return query.lower() in haystack


def print_source_list(data: dict[str, Any]) -> None:
    registry = data.get("source_registry", {})
    print(f"# {registry.get('name', 'Genny Source List')}")
    if registry.get("updated"):
        print(f"Updated: {registry['updated']}")
    for note in registry.get("notes", []):
        print(f"- {note}")
    for vertical, sources in data.get("verticals", {}).items():
        print(f"\n## {vertical}")
        for source in sources:
            rss = source.get("rss") or "manual"
            priority = source.get("priority", "normal")
            cadence = source.get("cadence", "as needed")
            watch = ", ".join(source.get("watch_for", []))
            print(f"- {source.get('name')} - {source.get('url')} ({rss}; {priority}; {cadence})")
            if watch:
                print(f"  Watch for: {watch}")
            if source.get("notes"):
                print(f"  Notes: {source['notes']}")


def scan(data: dict[str, Any], vertical_filter: str, query: str, limit: int) -> int:
    print("# GenLens Source Scan")
    print(f"Generated: {dt.datetime.now(dt.UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}")
    found_any = False
    for vertical, sources in data.get("verticals", {}).items():
        if vertical_filter and vertical.lower() != vertical_filter.lower():
            continue
        section_lines: list[str] = []
        for source in sources:
            if not source_matches(source, query):
                continue
            rss = source.get("rss", "")
            name = source.get("name", "Unnamed source")
            if not rss:
                section_lines.append(f"- {name}: manual check required - {source.get('url')}")
                continue
            try:
                items = fetch_rss(rss, limit=limit)
            except urllib.error.URLError as exc:
                section_lines.append(f"- {name}: RSS unavailable - {exc.reason}")
                continue
            except Exception as exc:
                section_lines.append(f"- {name}: RSS parse failed - {exc}")
                continue
            if not items:
                section_lines.append(f"- {name}: no recent RSS items returned")
                continue
            section_lines.append(f"- {name}")
            for item in items:
                date = f" ({item['date']})" if item.get("date") else ""
                url = item.get("url", "")
                if url:
                    section_lines.append(f"  - {item['title']}{date} - {url}")
                else:
                    section_lines.append(f"  - {item['title']}{date}")
                if item.get("summary"):
                    section_lines.append(f"    {item['summary']}")
        if section_lines:
            found_any = True
            print(f"\n## {vertical}")
            print("\n".join(section_lines))
    if not found_any:
        print("\nNo configured sources matched that request.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="Print configured sources only.")
    parser.add_argument("--vertical", default="", help="Filter to one vertical.")
    parser.add_argument("--query", default="", help="Filter source names/watch terms.")
    parser.add_argument("--limit", type=int, default=3, help="RSS items per source.")
    args = parser.parse_args()

    data = load_sources()
    if args.list:
        print_source_list(data)
        return 0
    return scan(data, args.vertical, args.query, max(1, min(args.limit, 8)))


if __name__ == "__main__":
    raise SystemExit(main())
