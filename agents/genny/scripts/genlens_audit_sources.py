#!/usr/bin/env python3
"""Audit GenLens source quality.

This does not write a briefing. It classifies configured sources so Genny can
explain why a source should or should not feed the daily email.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from genlens_compose_brief import (
    SOURCE_PATH,
    fetch_manual_links,
    fetch_rss,
    is_discovery_source,
)


def load_sources() -> dict[str, Any]:
    return json.loads(Path(os.environ.get("GENLENS_SOURCE_PATH", str(SOURCE_PATH))).read_text())


def source_class(source: dict[str, Any]) -> str:
    if source.get("rss"):
        return "briefable-feed"
    if is_discovery_source(source):
        return "briefable-manual"
    return "watch-only"


def audit(limit: int, deep_manual: bool = False) -> str:
    data = load_sources()
    lines = [
        "# GenLens Source Quality Audit",
        "",
        "Classification:",
        "",
        "- `briefable-feed`: RSS/Atom source that can produce candidate briefing items.",
        "- `briefable-manual`: article/blog/news page that can be crawled for candidate links.",
        "- `watch-only`: product docs/homepages/source-of-truth pages. Useful for verification, not news cards.",
        "- `quiet-feed`: valid feed/source, but no publishable signals in this audit window.",
        "- `needs-replacement`: broken, blocked, or consistently low-value source that should be replaced.",
        "",
    ]
    totals = {"briefable-feed": 0, "briefable-manual": 0, "watch-only": 0, "quiet-feed": 0, "needs-replacement": 0}
    for vertical, sources in data.get("verticals", {}).items():
        lines.append(f"## {vertical}")
        for source in sources:
            klass = source_class(source)
            totals[klass] += 1
            qualified = 0
            error = ""
            try:
                if source.get("rss"):
                    qualified = len(fetch_rss(source, vertical, limit))
                elif deep_manual and is_discovery_source(source):
                    qualified = len(fetch_manual_links(source, vertical, limit))
            except Exception as exc:
                error = str(exc)
            watch = ", ".join(source.get("watch_for", [])[:4])
            status = klass
            if klass == "briefable-manual" and not deep_manual:
                suffix = " - manual source; skipped in fast audit"
            elif error and klass != "watch-only":
                status = "needs-replacement"
                totals[status] += 1
                suffix = f" - publishable leads: {qualified}"
            elif klass != "watch-only" and qualified == 0:
                status = "quiet-feed"
                totals[status] += 1
                suffix = f" - publishable leads: {qualified}"
            else:
                suffix = f" - publishable leads: {qualified}" if klass != "watch-only" else ""
            if error:
                suffix += f" - error: {error}"
            lines.append(
                f"- **{source.get('name', 'Source')}** — `{status}`{suffix}. {source.get('url', '')}"
            )
            if watch:
                lines.append(f"  Watch for: {watch}")
        lines.append("")
    lines.insert(
        1,
        f"Summary: {totals['briefable-feed']} feeds, {totals['briefable-manual']} manual article sources, {totals['watch-only']} watch-only sources, {totals['quiet-feed']} quiet feeds, {totals['needs-replacement']} sources needing replacement.",
    )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--out", default="")
    parser.add_argument("--deep-manual", action="store_true", help="Crawl manual blog/news pages. Slower; use for source tuning.")
    args = parser.parse_args()
    text = audit(max(1, min(args.limit, 20)), args.deep_manual)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(str(out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
