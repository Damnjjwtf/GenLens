#!/usr/bin/env python3
"""Extract and curate tool candidates from GenLens source output.

This creates a lightweight review queue. It does not auto-add tools to the
manifest; it separates known tools from candidates that need human/Genny review.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(os.environ.get("GENLENS_TOOLS_MANIFEST", "/root/.hermes/profiles/genny/data/genlens_tools_manifest.md"))
if not MANIFEST_PATH.exists():
    MANIFEST_PATH = BASE_DIR / "data" / "genlens_tools_manifest.md"
BRIEF_PATH = Path(os.environ.get("GENLENS_BRIEF_PATH", "/root/.hermes/profiles/genny/state/latest_brief.md"))
if not BRIEF_PATH.exists():
    BRIEF_PATH = BASE_DIR / "state" / "latest_brief.md"
OUT_PATH = Path(os.environ.get("GENLENS_TOOL_CANDIDATES", "/root/.hermes/profiles/genny/data/tool_candidates.json"))

TOOL_HINTS = re.compile(
    r"\b(comfyui|figma|weave|weavy|fal(?:\.ai)?|runway|sora|veo|kling|luma|flux|blender|unreal|unity|godot|v-ray|vray|resolve|houdini|photoshop|firefly|synthesia|heygen|elevenlabs|elevencreative|grok imagine|geforce now|nvidia|blackmagic|davinci|corona|enscape|replicate|n8n|hubspot|shopify|posthog|rudderstack|mautic|salesforce|agentforce|klaviyo|braze|google ads|performance max|meta ads|advantage\+)\b",
    re.I,
)

STOPWORDS = {
    "Additional Watchlist",
    "AI Filmmaking",
    "AI Design",
    "ArchViz",
    "Candidate",
    "Cross Vertical Watchlist",
    "Daily",
    "Digital Humans",
    "Education",
    "Feed",
    "Fashion",
    "Game Development",
    "Manual",
    "Music Production",
    "Podcast",
    "Product Photography",
    "Release",
    "Social",
    "Source",
    "The Interline",
}

STOPWORD_LOWER = {word.lower() for word in STOPWORDS}
GENERIC_NAME_PATTERNS = re.compile(
    r"\b(accelerate|additional|ai-driven|ai-native|asia|candidate|coverage gaps?|daily|design|drag-and-drop|feed|forbidden|future|head|http error|manual|phase|release|raises?|source|watchlist|blog|news search|briefing|signals?)\b",
    re.I,
)
SOURCE_NAME_PATTERNS = re.compile(
    r"\b(news search|blog|magazine|newsletter|feed|source|musictech|motionographer|interline|replicate blog|nvidia blog|godot news)\b",
    re.I,
)
TRACKED_TOOLS = {
    "ComfyUI",
    "fal",
    "fal.ai",
    "ElevenCreative",
    "Figma Weave",
    "Weavy",
    "Runway Aleph",
    "Veo",
    "Sora",
    "Kling",
    "Luma",
    "n8n",
    "HubSpot",
    "Shopify",
    "PostHog",
    "RudderStack",
    "Mautic",
    "Salesforce",
}
ALIASES = {
    "weavy": "Figma Weave",
    "fal.ai": "fal",
}


def normalize(value: str) -> str:
    value = re.sub(r"[`*_()\[\]{}]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -:.,")
    return value


def load_known_tools() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()
    text = MANIFEST_PATH.read_text(errors="replace")
    tools: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"\s*-\s+(?:\*\*)?([^*(\n]+?)(?:\*\*)?\s*(?:\(|$)", line)
        if match:
            name = normalize(match.group(1))
            if 2 <= len(name) <= 60:
                tools.add(name)
    return tools | TRACKED_TOOLS


def extract_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    patterns = [
        r"\b(?:[A-Z][A-Za-z0-9.+-]+|[a-z]+\.ai)(?:\s+(?:[A-Z][A-Za-z0-9.+-]+|AI|3D|SDK|API|v\d+(?:\.\d+)*))*\b",
        r"\b(?:fal\.ai|ComfyUI|Figma Weave|Weavy|V-Ray|DaVinci Resolve|Blackmagic Design|Runway Aleph|Google Veo|OpenAI Sora)\b",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            name = normalize(match.group(0))
            if name in STOPWORDS or name.lower() in STOPWORD_LOWER or len(name) < 3 or len(name) > 70:
                continue
            if name.lower() in {"the", "and", "with", "from", "today", "source"}:
                continue
            if GENERIC_NAME_PATTERNS.search(name) or SOURCE_NAME_PATTERNS.search(name):
                continue
            if TOOL_HINTS.search(name) or len(name.split()) <= 4:
                candidates.append(name)
    return candidates


def context_for(text: str, name: str) -> str:
    idx = text.lower().find(name.lower())
    if idx < 0:
        return ""
    start = max(0, idx - 140)
    end = min(len(text), idx + len(name) + 220)
    return normalize(text[start:end])


def curate(text: str) -> dict[str, Any]:
    known_tools = load_known_tools()
    known_lookup = {tool.lower(): tool for tool in known_tools}
    counts = Counter(extract_candidates(text))
    known_hits: dict[str, dict[str, Any]] = {}
    review_queue: dict[str, dict[str, Any]] = {}

    for name, count in counts.most_common():
        key = name.lower()
        canonical = ALIASES.get(key)
        if canonical:
            key = canonical.lower()
            name = canonical
        substring_known = next((tool for tool in known_tools if tool.lower() in key and len(tool) >= 4), None)
        if substring_known:
            key = substring_known.lower()
            name = substring_known
        record = {
            "name": known_lookup.get(key, name),
            "mentions": count,
            "context": context_for(text, name),
        }
        if key in known_lookup:
            known_hits[known_lookup[key]] = record
        elif count >= 1 and TOOL_HINTS.search(name):
            review_queue[name] = {
                **record,
                "status": "review",
                "reason": "Mentioned in source-backed brief output but not found in canonical tools manifest.",
            }

    vertical_mentions: dict[str, list[str]] = defaultdict(list)
    current_vertical = "Unassigned"
    for line in text.splitlines():
        if line.startswith("## "):
            current_vertical = line.removeprefix("## ").strip()
        line_tools = []
        for tool in known_tools:
            if tool.lower() in line.lower():
                line_tools.append(tool)
        for tool in line_tools[:8]:
            if tool not in vertical_mentions[current_vertical]:
                vertical_mentions[current_vertical].append(tool)

    return {
        "known_tools_seen": sorted(known_hits.values(), key=lambda item: (-item["mentions"], item["name"].lower())),
        "review_queue": sorted(review_queue.values(), key=lambda item: (-item["mentions"], item["name"].lower())),
        "vertical_mentions": dict(sorted(vertical_mentions.items())),
        "manifest_path": str(MANIFEST_PATH),
        "source_path": str(BRIEF_PATH),
    }


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# GenLens Tool Curator Report",
        "",
        f"Known tools seen: {len(data['known_tools_seen'])}",
        f"Review candidates: {len(data['review_queue'])}",
        "",
        "## Review Queue",
    ]
    if data["review_queue"]:
        for item in data["review_queue"][:20]:
            lines.append(f"- **{item['name']}** — {item['mentions']} mention(s). {item['reason']}")
    else:
        lines.append("- No new tool candidates found.")
    lines.extend(["", "## Known Tools Seen"])
    for item in data["known_tools_seen"][:25]:
        lines.append(f"- **{item['name']}** — {item['mentions']} mention(s).")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", default=str(BRIEF_PATH))
    parser.add_argument("--out", default=str(OUT_PATH))
    parser.add_argument("--markdown", default="")
    args = parser.parse_args()

    brief_path = Path(args.brief)
    text = brief_path.read_text(errors="replace") if brief_path.exists() else ""
    data = curate(text)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(data))
    else:
        print(render_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
