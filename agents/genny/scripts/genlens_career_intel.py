#!/usr/bin/env python3
"""Scan public career/workflow signals for GenLens Role Radar.

This is a source-quality layer, not a job-application bot. It fetches public
RSS/search feeds and optional pasted job/source text, scores candidates, and
writes a durable career signal ledger for Genny.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("GENLENS_DATA_DIR", "/root/.hermes/profiles/genny/data"))
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR / "data"
STATE_DIR = Path(os.environ.get("GENLENS_STATE_DIR", "/root/.hermes/profiles/genny/state"))
if not STATE_DIR.exists():
    STATE_DIR = BASE_DIR / "state"

CAREER_SOURCES_PATH = DATA_DIR / "career_sources.json"
ROLE_SIGNALS_PATH = DATA_DIR / "role_signals.json"
OUT_JSON_PATH = Path(os.environ.get("GENLENS_CAREER_SIGNALS", str(DATA_DIR / "career_signals.json")))
OUT_MD_PATH = Path(os.environ.get("GENLENS_CAREER_RADAR", str(STATE_DIR / "career_radar.md")))

ROLE_PATTERNS = {
    "Creative Technologist": r"\bcreative technologist\b",
    "Generative Artist": r"\bgenerative artist\b|\bAI artist\b",
    "AI Pipeline Engineer": r"\bAI pipeline engineer\b|\bpipeline engineer\b",
    "Synthetic Production TD": r"\btechnical director\b|\bTD\b|\bsynthetic production\b",
    "Inference Ops Specialist": r"\binference specialist\b|\binference ops\b|\bGPU (?:engineer|operator|operations?|infrastructure)\b|\binference (?:engineer|operator|operations?|infrastructure)\b",
    "AI Workflow Producer": r"\bworkflow producer\b|\bAI producer\b|\bproduction workflow\b",
    "AI Game Tools Engineer": r"\bgame tools\b|\btools programmer\b|\bAI workflows\b",
    "Digital Human Producer": r"\bdigital human\b|\bsynthetic actor\b|\bavatar\b",
}

TOOL_PATTERNS = {
    "ComfyUI": r"\bcomfyui\b",
    "fal": r"\bfal(?:\.ai)?\b",
    "Runway": r"\brunway\b",
    "Kling": r"\bkling\b",
    "Veo": r"\bveo\b",
    "Luma": r"\bluma\b",
    "Nuke": r"\bnuke\b",
    "After Effects": r"\bafter effects\b",
    "Maya": r"\bmaya\b",
    "Houdini": r"\bhoudini\b",
    "Blender": r"\bblender\b",
    "Unreal Engine": r"\bunreal\b",
    "Unity": r"\bunity\b",
    "LoRA": r"\blora\b",
    "ControlNet": r"\bcontrolnet\b",
    "PyTorch": r"\bpytorch\b",
    "CUDA": r"\bcuda\b",
    "ElevenLabs": r"\belevenlabs\b",
    "Synthesia": r"\bsynthesia\b",
    "HeyGen": r"\bheygen\b",
    "Adobe Firefly": r"\bfirefly\b",
}

SKILL_PATTERNS = {
    "pipeline engineering": r"\bpipeline\b",
    "AI/ML production": r"\bAI/ML\b|\bmachine learning\b|\bML\b",
    "creative coding": r"\bcreative coding\b|\bprototype\b|\bAPI\b",
    "model routing": r"\bmodel routing\b|\borchestration\b",
    "GPU operations": r"\bGPU\b|\bCUDA\b|\binference\b|\blatency\b",
    "VFX compositing": r"\bVFX\b|\bcompositing\b|\bNuke\b",
    "workflow design": r"\bworkflow\b|\bprocess\b|\bhandoff\b",
    "rights/provenance": r"\bright(?:s)?\b|\bprovenance\b|\bconsent\b|\bSAG-AFTRA\b",
}

VERTICAL_PATTERNS = {
    "AI Filmmaking": r"\bfilm\b|\bfilmmaking\b|\bvideo\b|\bVFX\b|\bshot\b",
    "Digital Humans": r"\bdigital human\b|\bsynthetic actor\b|\bavatar\b|\bvoice\b|\blip sync\b",
    "AI Design / Motion Graphics": r"\bdesign\b|\bmotion graphics\b|\bfigma\b|\bafter effects\b",
    "Game Development / Real-Time 3D": r"\bgame\b|\bunreal\b|\bunity\b|\bNPC\b|\blevel\b",
    "Product Photography": r"\bproduct photography\b|\becommerce\b|\bcommerce\b|\bSKU\b",
    "Infrastructure": r"\binference\b|\bGPU\b|\bCUDA\b|\bAPI\b|\borchestration\b",
}

COMPANY_PATTERNS = {
    "Adobe": r"\badobe\b|\bfirefly\b",
    "Sphere": r"\bsphere\b",
    "Paramount": r"\bparamount\b",
    "Lightricks": r"\blightricks\b|\bltx\b",
    "Amazon Prime Video": r"\bamazon prime video\b|\bprime video\b|\bamazon mgm\b",
    "Netflix": r"\bnetflix\b",
    "Epic Games": r"\bepic games\b|\bunreal engine\b",
    "OpusClip": r"\bopusclip\b",
    "Twilio Segment": r"\btwilio segment\b|\bsegment\b",
    "Jasper": r"\bjasper\b",
    "Vantage Point": r"\bvantage point\b",
    "BBD Boom": r"\bbbd boom\b",
}

LOCATION_PATTERNS = {
    "Los Angeles": r"\blos angeles\b|\bLA\b",
    "Culver City": r"\bculver city\b",
    "San Francisco": r"\bsan francisco\b",
    "New York City": r"\bnew york\b|\bNYC\b",
    "Las Vegas": r"\blas vegas\b",
    "Los Gatos": r"\blos gatos\b",
    "Vancouver": r"\bvancouver\b",
    "Toronto": r"\btoronto\b",
    "Montreal": r"\bmontreal\b|\bmontr[eé]al\b",
    "Remote": r"\bremote\b",
    "Hybrid": r"\bhybrid\b",
}

POSITIVE_PATTERNS = re.compile(
    r"\b(job|jobs|career|careers|hiring|role|roles|salary|skills?|workflow|pipeline|production|studio|artist|engineer|technologist|director|producer|VFX|ComfyUI|inference|GPU|generative AI|AI video|creative AI)\b",
    re.I,
)
SALARY_PATTERN = re.compile(
    r"(\$\s?\d{2,3}(?:,\d{3})?(?:k|K)?(?:\s?[-–]\s?\$?\s?\d{2,3}(?:,\d{3})?(?:k|K)?)?|\$\s?\d+\s?(?:per hour|/hour|\/hr|hr))",
    re.I,
)
NEGATIVE_PATTERNS = re.compile(
    r"\b(best \d+|best tools?|top \d+|serverless GPU clouds?|cost-effective GPUs?|jobgether|coupon|pricing|login|signup|subscribe|privacy|terms|course discount|affiliate|stock picks?|crypto)\b",
    re.I,
)
ATS_DOMAINS = {"boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "jobs.workable.com", "workable.com"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


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


def child_source(node: ET.Element) -> tuple[str, str]:
    for child in list(node):
        local = child.tag.split("}", 1)[-1].lower()
        if local == "source":
            return strip_text(child.text), child.attrib.get("url", "").strip()
    return "", ""


def source_domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.removeprefix("www.").lower()
    except Exception:
        return ""


def is_google_news_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return "news.google." in parsed.netloc


def resolved_google_news_url(url: str, publisher_url: str = "") -> str:
    parsed = urllib.parse.urlparse(url)
    if not is_google_news_url(url):
        return url
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("url", "q"):
        value = query.get(key, [""])[0]
        if value.startswith("http"):
            return value
    if publisher_url.startswith("http"):
        return publisher_url
    return url


def fetch_rss(url: str, limit: int) -> list[dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "GenLensCareerIntel/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=18, context=ctx) as response:
        body = response.read(1_500_000)
    root = ET.fromstring(body)
    nodes = [n for n in root.iter() if n.tag.split("}", 1)[-1].lower() in {"item", "entry"}]
    items: list[dict[str, str]] = []
    for node in nodes[:limit]:
        title = child_text(node, ("title",))
        publisher, publisher_url = child_source(node)
        raw_link = child_link(node)
        link = resolved_google_news_url(raw_link, publisher_url)
        published = child_text(node, ("pubdate", "published", "updated", "date"))
        summary = child_text(node, ("description", "summary", "content", "encoded"))
        if title:
            items.append({
                "title": title,
                "url": link,
                "raw_url": raw_link,
                "publisher": publisher,
                "publisher_url": publisher_url,
                "domain": source_domain(link),
                "date": parse_date(published),
                "summary": summary[:500],
            })
    return items


def matches(patterns: dict[str, str], text: str) -> list[str]:
    found = []
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.I):
            found.append(label)
    return found


def first_salary(text: str) -> str:
    match = SALARY_PATTERN.search(text)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def verification_status(source: dict[str, Any], url: str, raw_url: str, publisher_url: str, text: str) -> str:
    tier = str(source.get("evidence_tier") or "secondary").lower()
    domain = source_domain(url)
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/")
    has_direct_job_path = bool(path) and path not in {"jobs", "careers", "search", "job-board"}
    if tier == "primary" and domain in ATS_DOMAINS and has_direct_job_path:
        return "verified-direct-posting"
    if tier == "primary" and domain in ATS_DOMAINS:
        return "lead-needs-direct-url"
    if publisher_url and is_google_news_url(raw_url):
        return "publisher-domain-lead"
    if tier in {"demand", "discovery"}:
        return "demand-lead"
    if re.search(r"\b(salary|compensation|location|remote|hybrid|requirements?|responsibilities)\b", text, re.I):
        return "secondary-specific"
    return "needs-verification"


def fingerprint(title: str, url: str) -> str:
    basis = (url or title).strip().lower()
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def int_value(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, list):
            return int_value(value[0], default) if value else default
        return int(value)
    except Exception:
        return default


def score_candidate(title: str, summary: str, source: dict[str, Any]) -> tuple[int, list[str]]:
    text = f"{title} {summary}"
    reasons: list[str] = []
    score = 0
    if POSITIVE_PATTERNS.search(text):
        score += 25
        reasons.append("career/workflow language")
    roles = matches(ROLE_PATTERNS, text)
    if roles:
        score += min(25, 10 + 5 * len(roles))
        reasons.append("role title/pattern")
    tools = matches(TOOL_PATTERNS, text)
    if tools:
        score += min(20, 8 + 3 * len(tools))
        reasons.append("tool stack")
    skills = matches(SKILL_PATTERNS, text)
    if skills:
        score += min(15, 5 + 3 * len(skills))
        reasons.append("skills/workflow verbs")
    if source.get("trust") == "high":
        score += 10
        reasons.append("high-trust source")
    elif source.get("trust") == "medium":
        score += 5
        reasons.append("medium-trust source")
    if NEGATIVE_PATTERNS.search(text):
        score -= 30
        reasons.append("noise pattern")
    return max(0, min(100, score)), reasons


def status_for(score: int, roles: list[str], title: str) -> str:
    lowered = title.lower()
    if "forecast" in lowered or "future" in lowered:
        return "forecast"
    if roles and score >= 45 and re.search(r"\b(role|career|job|hiring|artist|technologist|engineer|producer|director)\b", lowered):
        return "observed"
    if roles and score >= 50:
        return "emerging"
    if score >= 50:
        return "emerging"
    return "market-demand"


def status_for_tier(base_status: str, score: int, roles: list[str], source: dict[str, Any]) -> str:
    tier = str(source.get("evidence_tier") or "").lower()
    if tier in {"demand", "discovery"}:
        return "market-demand"
    if tier == "secondary" and base_status == "observed" and score < 60:
        return "emerging" if roles else "market-demand"
    return base_status


def accepted_for_tier(score: int, roles: list[str], tools: list[str], skills: list[str], source: dict[str, Any], noisy: bool) -> bool:
    if noisy:
        return False
    tier = str(source.get("evidence_tier") or "secondary").lower()
    if tier == "primary":
        return score >= 55 or (roles and score >= 45) or (tools and skills and score >= 40)
    if tier == "secondary":
        return score >= 60 or (roles and score >= 50) or (tools and skills and score >= 45)
    if tier in {"demand", "discovery"}:
        return score >= 60 or (tools and skills and score >= 50)
    return score >= 55 or (roles and score >= 45) or (tools and skills and score >= 40)


def candidate_from_item(item: dict[str, str], source: dict[str, Any]) -> dict[str, Any]:
    title = strip_text(item.get("title", ""))
    summary = strip_text(item.get("summary", ""))
    text = f"{title} {summary}"
    roles = matches(ROLE_PATTERNS, text)
    tools = matches(TOOL_PATTERNS, text)
    skills = matches(SKILL_PATTERNS, text)
    companies = matches(COMPANY_PATTERNS, text)
    locations = matches(LOCATION_PATTERNS, text)
    salary = first_salary(text)
    verticals = matches(VERTICAL_PATTERNS, text) or list(source.get("verticals", [])) or ["Cross-Vertical Watchlist"]
    score, reasons = score_candidate(title, summary, source)
    noisy = bool(NEGATIVE_PATTERNS.search(text))
    base_status = status_for(score, roles, title)
    status = status_for_tier(base_status, score, roles, source)
    accepted = accepted_for_tier(score, roles, tools, skills, source, noisy)
    return {
        "id": fingerprint(title, item.get("url", "")),
        "title": title,
        "url": item.get("url", ""),
        "raw_url": item.get("raw_url", ""),
        "publisher": item.get("publisher", ""),
        "publisher_url": item.get("publisher_url", ""),
        "domain": item.get("domain", source_domain(item.get("url", ""))),
        "source": source.get("name", "Unknown source"),
        "source_type": source.get("type", "unknown"),
        "evidence_tier": source.get("evidence_tier", "secondary"),
        "date": item.get("date", ""),
        "summary": summary,
        "score": score,
        "status": status,
        "verification_status": verification_status(source, item.get("url", ""), item.get("raw_url", ""), item.get("publisher_url", ""), text),
        "companies": companies,
        "locations": locations,
        "salary": salary,
        "roles": roles,
        "tools": tools,
        "skills": skills,
        "verticals": verticals,
        "reasons": reasons,
        "accepted": accepted,
    }


def load_sources() -> dict[str, Any]:
    return json.loads(CAREER_SOURCES_PATH.read_text())


def load_existing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"signals": []}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {"signals": []}


def pasted_items(text: str) -> list[dict[str, str]]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    items = []
    for chunk in chunks:
        lines = chunk.splitlines()
        title = strip_text(lines[0])[:180]
        summary = strip_text(" ".join(lines[1:]) or chunk)
        url_match = re.search(r"https?://\S+", chunk)
        items.append({
            "title": title,
            "summary": summary[:500],
            "url": url_match.group(0).rstrip(").,") if url_match else "",
            "date": dt.date.today().isoformat(),
        })
    return items


def empty_source_stat(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": source.get("name", "Unknown source"),
        "type": source.get("type", "unknown"),
        "evidence_tier": source.get("evidence_tier", "secondary"),
        "trust": source.get("trust", "unknown"),
        "checked": 0,
        "accepted": 0,
        "rejected": 0,
        "avg_score": 0,
        "error": "",
    }


def summarize_source_stat(stat: dict[str, Any]) -> dict[str, Any]:
    checked = int_value(stat.get("checked"))
    accepted = int_value(stat.get("accepted"))
    rejected = int_value(stat.get("rejected"))
    avg_score = int_value(stat.get("avg_score"))
    error = str(stat.get("error") or "")
    source_type = str(stat.get("type") or "")
    network_error = bool(re.search(r"\b(nodename|name or service|temporary failure|timed out|network|dns)\b", error, re.I))
    if source_type == "manual":
        action = "manual-review"
    elif network_error and checked == 0:
        action = "check-runtime-network"
    elif error and checked == 0:
        action = "needs-replacement"
    elif checked == 0:
        action = "quiet"
    elif accepted >= 2 or avg_score >= 60:
        action = "keep"
    elif accepted == 0 and rejected >= 3:
        action = "tune-or-replace"
    else:
        action = "watch"
    stat["action"] = action
    return stat


def collect(limit: int, input_file: str = "") -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    data = load_sources()
    signals: list[dict[str, Any]] = []
    notes: list[str] = []
    source_stats: list[dict[str, Any]] = []
    for source in data.get("sources", []):
        source_type = source.get("type")
        stat = empty_source_stat(source)
        if source_type == "rss":
            try:
                items = fetch_rss(str(source.get("url")), limit)
            except urllib.error.URLError as exc:
                reason = f"fetch failed - {exc.reason}"
                notes.append(f"{source.get('name')}: {reason}")
                stat["error"] = reason
                source_stats.append(summarize_source_stat(stat))
                continue
            except Exception as exc:
                reason = f"parse failed - {exc}"
                notes.append(f"{source.get('name')}: {reason}")
                stat["error"] = reason
                source_stats.append(summarize_source_stat(stat))
                continue
            source_candidates = [candidate_from_item(item, source) for item in items]
            stat["checked"] = len(source_candidates)
            stat["accepted"] = sum(1 for candidate in source_candidates if candidate.get("accepted"))
            stat["rejected"] = stat["checked"] - stat["accepted"]
            if source_candidates:
                stat["avg_score"] = round(sum(int_value(candidate.get("score")) for candidate in source_candidates) / len(source_candidates))
            signals.extend(source_candidates)
            source_stats.append(summarize_source_stat(stat))
        elif source_type == "manual":
            notes.append(f"{source.get('name')}: manual watchlist only")
            source_stats.append(summarize_source_stat(stat))

    if input_file:
        path = Path(input_file)
        source = {
            "name": f"Pasted source: {path.name}",
            "type": "pasted",
            "verticals": ["Cross-Vertical Watchlist"],
            "trust": "high",
        }
        for item in pasted_items(path.read_text()):
            signals.append(candidate_from_item(item, source))
    return signals, notes, source_stats


def merge_signals(existing: list[dict[str, Any]], fresh: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for signal in existing + fresh:
        sid = str(signal.get("id") or fingerprint(str(signal.get("title", "")), str(signal.get("url", ""))))
        previous = by_id.get(sid)
        if not previous or int(signal.get("score", 0)) >= int(previous.get("score", 0)):
            signal["id"] = sid
            by_id[sid] = signal
    return sorted(by_id.values(), key=lambda row: (int(bool(row.get("accepted", False))), int_value(row.get("score", 0))), reverse=True)


def render_markdown(signals: list[dict[str, Any]], notes: list[str], source_stats: list[dict[str, Any]], limit: int) -> str:
    accepted = [row for row in signals if row.get("accepted")]
    rejected = [row for row in signals if not row.get("accepted")]
    role_counts = Counter(role for row in accepted for role in row.get("roles", []))
    tool_counts = Counter(tool for row in accepted for tool in row.get("tools", []))
    vertical_counts = Counter(vertical for row in accepted for vertical in row.get("verticals", []))

    lines = [
        "# GenLens Career Radar",
        f"Generated: {now_iso()}",
        "",
        "Career Radar treats public job, hiring, workflow, and tool-stack mentions as signals of where AI creative production work is going.",
        "",
        "## Summary",
        "",
        f"- Accepted signals: {len(accepted)}",
        f"- Rejected / watch-only signals: {len(rejected)}",
    ]
    if role_counts:
        lines.append(f"- Top role patterns: {', '.join(f'{k} ({v})' for k, v in role_counts.most_common(6))}")
    if tool_counts:
        lines.append(f"- Top tools: {', '.join(f'{k} ({v})' for k, v in tool_counts.most_common(8))}")
    if vertical_counts:
        lines.append(f"- Top verticals: {', '.join(f'{k} ({v})' for k, v in vertical_counts.most_common(6))}")
    lines.append("")

    lines.extend(["## Accepted Signals", ""])
    if not accepted:
        lines.append("- No publishable career signals passed the score gate. Keep scanning; do not pad with generic job-market content.")
    for row in accepted[:limit]:
        url = f" [{row['url']}]({row['url']})" if row.get("url") else ""
        lines.extend([
            f"### {row.get('title')}{url}",
            "",
            f"- Score: {row.get('score')} / 100",
            f"- Status: {row.get('status')}",
            f"- Source: {row.get('source')}",
            f"- Evidence tier: {row.get('evidence_tier')}",
            f"- Verification: {row.get('verification_status')}",
            f"- Domain: {row.get('domain') or 'unknown'}",
            f"- Companies: {', '.join(row.get('companies', [])) or 'Unidentified'}",
            f"- Locations: {', '.join(row.get('locations', [])) or 'Unspecified'}",
            f"- Salary/rate: {row.get('salary') or 'Unspecified'}",
            f"- Verticals: {', '.join(row.get('verticals', [])) or 'Unassigned'}",
            f"- Roles: {', '.join(row.get('roles', [])) or 'Unclassified'}",
            f"- Tools: {', '.join(row.get('tools', [])) or 'None detected'}",
            f"- Skills: {', '.join(row.get('skills', [])) or 'None detected'}",
            f"- Why accepted: {', '.join(row.get('reasons', [])) or 'Score gate passed'}",
        ])
        if row.get("summary"):
            lines.append(f"- Summary: {row.get('summary')}")
        if row.get("publisher_url") and row.get("publisher_url") != row.get("url"):
            lines.append(f"- Publisher URL: {row.get('publisher_url')}")
        if row.get("raw_url") and is_google_news_url(str(row.get("raw_url"))) and row.get("raw_url") != row.get("url"):
            lines.append("- URL note: resolved from Google News wrapper.")
        lines.append("")

    lines.extend(["## Job Source Quality", ""])
    if source_stats:
        for stat in sorted(source_stats, key=lambda row: (str(row.get("action")) != "keep", str(row.get("action")), str(row.get("name")))):
            lines.append(
                f"- **{stat.get('name')}** — `{stat.get('action')}` / `{stat.get('evidence_tier')}`: "
                f"{stat.get('accepted')}/{stat.get('checked')} accepted, avg score {stat.get('avg_score')}. "
                f"Trust: {stat.get('trust')}."
            )
            if stat.get("error"):
                lines.append(f"  Error: {stat.get('error')}")
    else:
        lines.append("- No source statistics produced.")
    lines.append("")

    lines.extend(["## Source Notes", ""])
    if notes:
        lines.extend(f"- {note}" for note in notes[:30])
    else:
        lines.append("- No source errors.")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8, help="Items per RSS source.")
    parser.add_argument("--input-file", default="", help="Optional pasted job/source text to ingest.")
    parser.add_argument("--out-json", default=str(OUT_JSON_PATH))
    parser.add_argument("--out-md", default=str(OUT_MD_PATH))
    parser.add_argument("--max-report", type=int, default=20)
    args = parser.parse_args()

    fresh, notes, source_stats = collect(max(1, min(args.limit, 20)), args.input_file)
    existing = load_existing(Path(args.out_json)).get("signals", [])
    merged = merge_signals(existing, fresh)
    payload = {
        "updated": now_iso(),
        "schema": {
            "status": "observed | emerging | forecast | market-demand",
            "accepted": "true when score >= 55, or explicit role signals score >= 45, or tool+skill signals score >= 40, with no noise pattern detected",
            "score": "0-100 career-intelligence quality score",
        },
        "source_quality": source_stats,
        "signals": merged[:250],
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n")
    out_md.write_text(render_markdown(merged, notes, source_stats, max(1, args.max_report)))
    print(out_json)
    print(out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
