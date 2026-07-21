#!/usr/bin/env python3
"""Coordinate Genny's source, content, tool, role, and product curation."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(os.environ.get("GENLENS_PROFILE_DIR", "/root/.hermes/profiles/genny"))
if not PROFILE_DIR.exists():
    PROFILE_DIR = BASE_DIR
STATE_DIR = PROFILE_DIR / "state"
DATA_DIR = PROFILE_DIR / "data"
SCRIPT_DIR = PROFILE_DIR / "scripts"

BRIEF_PATH = STATE_DIR / "latest_brief.md"
AUDIT_PATH = STATE_DIR / "source_audit.md"
TOOL_REPORT_PATH = STATE_DIR / "tool_curator_report.md"
ROLE_RADAR_PATH = STATE_DIR / "genlens_role_radar.md"
CAREER_RADAR_PATH = STATE_DIR / "career_radar.md"
PREFLIGHT_PATH = STATE_DIR / "editorial_preflight.md"
TOOL_CANDIDATES_PATH = DATA_DIR / "tool_candidates.json"
SENT_HISTORY_PATH = STATE_DIR / "sent_brief_history.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def import_email_parser():
    path = SCRIPT_DIR / "genlens_send_email.py"
    spec = importlib.util.spec_from_file_location("genlens_send_email", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def analyze_brief(brief_path: Path = BRIEF_PATH) -> dict[str, object]:
    parser = import_email_parser()
    text = brief_path.read_text(errors="replace") if brief_path.exists() else ""
    if hasattr(parser, "public_briefing_items"):
        items = parser.public_briefing_items(text)
    else:
        items = parser.parse_briefing_items(text)
    housekeeping = {
        "no qualified feed signals",
        "no qualified signals",
        "source check needed",
        "watch-only sources",
        "additional watchlist",
    }
    publishable = [
        item for item in items
        if item.get("url") or str(item.get("vertical")) == "GenLens"
    ]
    publishable = [
        item for item in publishable
        if str(item.get("title", "")).strip().lower() not in housekeeping
    ]
    linked = [item for item in publishable if item.get("url")]
    verticals = sorted({str(item.get("vertical")) for item in publishable})
    signal_verticals = sorted({str(item.get("vertical")) for item in linked})
    source_counts: dict[str, int] = {}
    duplicate_titles: dict[str, int] = {}
    urls: list[str] = []
    for item in linked:
        source = str(item.get("source") or "internal")
        source_counts[source] = source_counts.get(source, 0) + 1
        url = str(item.get("url") or "").split("#", 1)[0].rstrip("/")
        if url:
            urls.append(url)
        title = re.sub(r"[^a-z0-9]+", " ", str(item.get("title", "")).lower()).strip()
        if title:
            duplicate_titles[title] = duplicate_titles.get(title, 0) + 1
    duplicates = {title: count for title, count in duplicate_titles.items() if count > 1}
    url_fingerprint = hashlib.sha256("\n".join(sorted(set(urls))).encode("utf-8")).hexdigest()
    return {
        "cards": len(publishable),
        "linked_cards": len(linked),
        "verticals": verticals,
        "vertical_count": len(verticals),
        "signal_verticals": signal_verticals,
        "signal_vertical_count": len(signal_verticals),
        "source_counts": source_counts,
        "duplicates": duplicates,
        "urls": sorted(set(urls)),
        "url_fingerprint": url_fingerprint,
    }


def load_sent_history() -> list[dict[str, object]]:
    if not SENT_HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(SENT_HISTORY_PATH.read_text())
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


def repeat_analysis(analysis: dict[str, object]) -> dict[str, object]:
    history = load_sent_history()[-14:]
    urls = set(str(url) for url in analysis.get("urls", []) if str(url))
    recent_urls = {
        str(url)
        for row in history
        for url in row.get("urls", [])
        if str(url)
    }
    fingerprint = str(analysis.get("url_fingerprint") or "")
    exact_repeat = bool(fingerprint and any(row.get("url_fingerprint") == fingerprint for row in history))
    new_urls = sorted(urls - recent_urls)
    return {
        "exact_repeat": exact_repeat,
        "new_link_count": len(new_urls),
        "new_links": new_urls,
    }


def record_sent(analysis: dict[str, object], resend: dict[str, object] | None = None, brief_path: Path = BRIEF_PATH) -> None:
    history = load_sent_history()
    history.append({
        "sent_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "brief": str(brief_path),
        "url_fingerprint": analysis.get("url_fingerprint"),
        "urls": analysis.get("urls", []),
        "resend": resend or {},
    })
    SENT_HISTORY_PATH.write_text(json.dumps(history[-30:], indent=2, sort_keys=True) + "\n")


def render_preflight(
    analysis: dict[str, object],
    send_ready: bool,
    reason: str,
    brief_path: Path = BRIEF_PATH,
    audit_path: Path = AUDIT_PATH,
    tool_report_path: Path = TOOL_REPORT_PATH,
    role_radar_path: Path = ROLE_RADAR_PATH,
    career_radar_path: Path = CAREER_RADAR_PATH,
) -> str:
    lines = [
        "# GenLens Editorial Preflight",
        "",
        f"Status: {'ready' if send_ready else 'hold'}",
        f"Reason: {reason}",
        "",
        "## Counts",
        "",
        f"- Cards: {analysis['cards']}",
        f"- Linked cards: {analysis['linked_cards']}",
        f"- Verticals represented: {analysis['vertical_count']}",
        f"- Signal verticals represented: {analysis['signal_vertical_count']}",
        "",
        "## Verticals",
        "",
    ]
    for vertical in analysis["verticals"]:
        lines.append(f"- {vertical}")
    lines.extend(["", "## Source Counts", ""])
    for source, count in sorted(dict(analysis["source_counts"]).items(), key=lambda item: (-item[1], item[0]))[:20]:
        lines.append(f"- {source}: {count}")
    duplicates = dict(analysis["duplicates"])
    lines.extend(["", "## Duplicate Titles", ""])
    if duplicates:
        for title, count in sorted(duplicates.items(), key=lambda item: (-item[1], item[0]))[:20]:
            lines.append(f"- {title}: {count}")
    else:
        lines.append("- No exact duplicate titles parsed.")
    if "new_link_count" in analysis:
        lines.extend([
            "",
            "## Repeat Check",
            "",
            f"- Exact recent repeat: {analysis.get('exact_repeat')}",
            f"- New links vs recent sends: {analysis.get('new_link_count')}",
            f"- URL fingerprint: `{analysis.get('url_fingerprint')}`",
        ])
    lines.extend([
        "",
        "## Generated Artifacts",
        "",
        f"- Brief: `{brief_path}`",
        f"- Source audit: `{audit_path}`",
        f"- Tool curator report: `{tool_report_path}`",
        f"- Career radar: `{career_radar_path}`",
        f"- Role radar: `{role_radar_path}`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["active", "expanded"], default="expanded")
    parser.add_argument("--lens", choices=["genny", "marti", "unified"], default="genny")
    parser.add_argument("--per-vertical", type=int, default=5)
    parser.add_argument("--rss-limit", type=int, default=12)
    parser.add_argument("--min-cards", type=int, default=None)
    parser.add_argument("--min-verticals", type=int, default=None)
    parser.add_argument("--min-new-links", type=int, default=3)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--force-send", action="store_true")
    parser.add_argument("--allow-repeat", action="store_true")
    parser.add_argument("--to", default=os.environ.get("GENLENS_EMAIL_TO", "jj@damnjj.wtf"))
    parser.add_argument("--subject", default="GenLens updated intelligence briefing")
    args = parser.parse_args()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    suffix = "" if args.lens == "genny" else f"_{args.lens}"
    brief_path = STATE_DIR / f"latest{suffix}_brief.md"
    audit_path = STATE_DIR / f"source_audit{suffix}.md"
    tool_report_path = STATE_DIR / f"tool_curator_report{suffix}.md"
    role_radar_path = ROLE_RADAR_PATH
    career_radar_path = CAREER_RADAR_PATH
    preflight_path = STATE_DIR / f"editorial_preflight{suffix}.md"
    tool_candidates_path = DATA_DIR / f"tool_candidates{suffix}.json"
    min_cards = args.min_cards if args.min_cards is not None else {"genny": 12, "marti": 6, "unified": 12}[args.lens]
    min_verticals = args.min_verticals if args.min_verticals is not None else {"genny": 5, "marti": 3, "unified": 6}[args.lens]

    run(["python3", str(SCRIPT_DIR / "genlens_audit_sources.py"), "--lens", args.lens, "--limit", "8", "--out", str(audit_path)])
    run([
        "python3", str(SCRIPT_DIR / "genlens_compose_brief.py"),
        "--mode", args.mode,
        "--lens", args.lens,
        "--per-vertical", str(args.per_vertical),
        "--rss-limit", str(args.rss_limit),
        "--out", str(brief_path),
    ])
    run([
        "python3", str(SCRIPT_DIR / "genlens_curate_tools.py"),
        "--brief", str(brief_path),
        "--out", str(tool_candidates_path),
        "--markdown", str(tool_report_path),
    ])
    if args.lens in {"genny", "unified"}:
        run(["python3", str(SCRIPT_DIR / "genlens_career_intel.py"), "--limit", "8", "--out-md", str(career_radar_path)])
        run(["python3", str(SCRIPT_DIR / "genlens_role_radar.py"), "--mode", "all", "--out", str(role_radar_path)])

    analysis = analyze_brief(brief_path)
    cards = int(analysis["cards"])
    signal_vertical_count = int(analysis["signal_vertical_count"])
    duplicate_count = len(dict(analysis["duplicates"]))
    linked_cards = int(analysis["linked_cards"])
    repeat = repeat_analysis(analysis)
    new_link_count = int(repeat["new_link_count"])
    exact_repeat = bool(repeat["exact_repeat"])
    analysis["new_link_count"] = new_link_count
    analysis["exact_repeat"] = exact_repeat
    send_ready = linked_cards >= min_cards and signal_vertical_count >= min_verticals and duplicate_count == 0
    reason = "passed editorial gate" if send_ready else f"needs curation: linked_cards={linked_cards}/{min_cards}, signal_verticals={signal_vertical_count}/{min_verticals}, duplicate_titles={duplicate_count}"
    if send_ready and not args.allow_repeat and not args.force_send:
        if exact_repeat:
            send_ready = False
            reason = "hold: exact URL set was already sent recently"
        elif new_link_count < args.min_new_links:
            send_ready = False
            reason = f"hold: only {new_link_count}/{args.min_new_links} new links versus recent sent briefings"
    preflight_path.write_text(render_preflight(analysis, send_ready, reason, brief_path, audit_path, tool_report_path, role_radar_path, career_radar_path))

    result: dict[str, object] = {
        "ready": send_ready,
        "reason": reason,
        "lens": args.lens,
        "brief": str(brief_path),
        "preflight": str(preflight_path),
        "analysis": analysis,
        "repeat": repeat,
    }
    if args.send and (send_ready or args.force_send):
        send = run([
            "python3", str(SCRIPT_DIR / "genlens_send_email.py"),
            "--to", args.to,
            "--subject", args.subject,
            "--text-file", str(brief_path),
            "--template", "genlens-briefing",
        ])
        try:
            resend_result = json.loads(send.stdout)
            result["resend"] = resend_result
        except Exception:
            resend_result = {}
            result["resend_stdout"] = send.stdout.strip()
        record_sent(analysis, resend_result, brief_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if send_ready or not args.send else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
