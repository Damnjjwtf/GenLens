#!/usr/bin/env python3
"""Generate GenLens role radar, proof-build, and product flywheel notes.

This script is intentionally deterministic. It does not invent fresh market
facts; it formats the role intelligence and product strategy files that Genny
has already been given.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("GENLENS_DATA_DIR", "/root/.hermes/profiles/genny/data"))
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR / "data"

OUT_PATH = Path(os.environ.get("GENLENS_ROLE_RADAR_OUT", "/root/.hermes/profiles/genny/state/genlens_role_radar.md"))

ROLE_SIGNALS_PATH = DATA_DIR / "role_signals.json"
STRATEGY_PATH = DATA_DIR / "genlens_product_strategy.md"
MODES_PATH = DATA_DIR / "genlens_operating_modes.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def role_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("roles", [])
    return [row for row in rows if isinstance(row, dict)]


def list_value(row: dict[str, Any], key: str) -> list[str]:
    value = row.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value:
        return [str(value)]
    return []


def role_name(row: dict[str, Any]) -> str:
    return str(row.get("role") or row.get("title") or "Untitled role")


def role_status(row: dict[str, Any]) -> str:
    return str(row.get("status") or row.get("evidence_level") or "observed")


def line_join(items: list[str], fallback: str = "Not specified") -> str:
    return ", ".join(items) if items else fallback


def render_roles(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Role Radar", ""]
    status_order = {"observed": 0, "emerging": 1, "forecast": 2}
    rows = sorted(rows, key=lambda row: (status_order.get(role_status(row).lower(), 9), role_name(row).lower()))
    for row in rows:
        status = role_status(row)
        vertical = row.get("vertical", "Cross-Vertical")
        lines.append(f"### {role_name(row)}")
        lines.append("")
        lines.append(f"- Status: {status}")
        lines.append(f"- Vertical: {vertical}")
        if row.get("company"):
            lines.append(f"- Company signal: {row['company']}")
        if row.get("salary"):
            lines.append(f"- Salary/rate signal: {row['salary']}")
        if row.get("location"):
            lines.append(f"- Location signal: {row['location']}")
        lines.append(f"- Tools: {line_join(list_value(row, 'tools'))}")
        lines.append(f"- Skills: {line_join(list_value(row, 'skills'))}")
        lines.append(f"- Workflow verbs: {line_join(list_value(row, 'workflow_verbs'))}")
        if row.get("why_it_matters"):
            lines.append(f"- Why it matters: {row['why_it_matters']}")
        elif row.get("notes"):
            lines.append(f"- Why it matters: {row['notes']}")
        lines.append("")
    return lines


def proof_build_for_role(row: dict[str, Any]) -> tuple[str, list[str]]:
    name = role_name(row)
    tools = list_value(row, "tools")
    vertical = str(row.get("vertical", "Cross-Vertical"))
    lower = f"{name} {vertical} {' '.join(tools)}".lower()

    if "game" in lower or "gameplay" in lower:
        title = "Generative gameplay prototype sprint"
        bullets = [
            "Build three playable graybox variants for one mechanic using Unreal or Unity plus AI-assisted asset variation.",
            "Document find-the-fun decisions, iteration time, discarded variants, and final gameplay clip.",
            "Ship a short screen recording, repo, and one-page production note.",
        ]
    elif "inference" in lower or "cuda" in lower or "gpu" in lower:
        title = "Creative inference ops dashboard"
        bullets = [
            "Run one image or video model through a repeatable API workflow and log latency, cost, failure modes, and output quality.",
            "Create a small dashboard or Markdown report comparing two model/provider settings.",
            "Ship the runner, sample outputs, and a clear production-readiness checklist.",
        ]
    elif "digital human" in lower or "voice" in lower or "avatar" in lower:
        title = "Synthetic presenter pipeline"
        bullets = [
            "Create a 60-second synthetic presenter workflow from script to voice to avatar video to captioned edit.",
            "Track cost, turnaround time, revision points, and rights/compliance notes.",
            "Ship the final video, process diagram, and tool-stack notes.",
        ]
    elif "product" in lower or "photography" in lower or "commerce" in lower:
        title = "Presale product visualization pipeline"
        bullets = [
            "Turn a product reference or CAD/mockup into three campaign-ready product images.",
            "Show background generation, lighting/material decisions, retouching, and ecommerce-ready variants.",
            "Ship before/after panels, prompt/node notes, cost estimate, and repeatability notes.",
        ]
    elif "vfx" in lower or "film" in lower or "nuke" in lower or "comfyui" in lower:
        title = "AI shot pipeline proof"
        bullets = [
            "Build one shot workflow from plate/reference to AI-assisted variant to composited final.",
            "Include ComfyUI or equivalent graph, Nuke/AE/Resolve handoff, and QC notes.",
            "Ship the final shot, node graph screenshot, and a time/cost delta.",
        ]
    else:
        title = "AI creative workflow proof"
        bullets = [
            "Pick one real creative workflow and rebuild it as a repeatable AI-assisted pipeline.",
            "Show inputs, tool stack, outputs, failure cases, and revision controls.",
            "Ship a live artifact plus a one-page breakdown with time/cost delta.",
        ]
    return title, bullets


def render_builds(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["## Build This", ""]
    for row in rows:
        title, bullets = proof_build_for_role(row)
        lines.append(f"### {role_name(row)} -> {title}")
        lines.append("")
        lines.append(f"- Suggested stack: {line_join(list_value(row, 'tools'))}")
        for bullet in bullets:
            lines.append(f"- {bullet}")
        lines.append("")
    return lines


def render_map(rows: list[dict[str, Any]]) -> list[str]:
    tool_counts: Counter[str] = Counter()
    company_counts: Counter[str] = Counter()
    vertical_counts: Counter[str] = Counter()
    clusters: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        vertical = str(row.get("vertical", "Cross-Vertical"))
        vertical_counts[vertical] += 1
        if row.get("company"):
            company_counts[str(row["company"])] += 1
        for tool in list_value(row, "tools"):
            tool_counts[tool] += 1
            clusters[vertical].add(tool)

    lines = ["## Market Map", ""]
    lines.append("### Role Signals By Vertical")
    lines.extend(f"- {vertical}: {count}" for vertical, count in vertical_counts.most_common())
    lines.append("")
    lines.append("### Repeating Tools")
    lines.extend(f"- {tool}: {count}" for tool, count in tool_counts.most_common(20))
    lines.append("")
    lines.append("### Company Signals")
    if company_counts:
        lines.extend(f"- {company}: {count}" for company, count in company_counts.most_common(20))
    else:
        lines.append("- No company signals captured yet.")
    lines.append("")
    lines.append("### Tool Clusters By Vertical")
    for vertical, tools in sorted(clusters.items()):
        lines.append(f"- {vertical}: {line_join(sorted(tools))}")
    lines.append("")
    return lines


def render_products() -> list[str]:
    lines = ["## Product Lab", ""]
    products = [
        ("This Week's Emerging Creative AI Roles", "Recurring briefing with observed roles, tool stacks, salary/location evidence, and a proof build for each role."),
        ("GenLens Role Maps", "Maps traditional creative roles to AI-native role mutations."),
        ("Tool Stack Blueprints", "Practical role-specific stack guides for AI Filmmaking, Product Photography, Digital Humans, Games, ArchViz, and Audio."),
        ("Proof-Build Generator", "Weekend-scoped portfolio projects tied to target roles and tools."),
        ("Hiring Briefs", "Company-facing briefs that explain the role they actually need and how to evaluate candidates."),
        ("Source Quality Dashboard", "Shows which sources produce real signal and which are stale, generic, broken, or watch-only."),
        ("Role Arbitrage Reports", "Paid research reports on 12-18 month creative AI labor-market shifts."),
    ]
    for name, description in products:
        lines.append(f"### {name}")
        lines.append("")
        lines.append(description)
        lines.append("")
    return lines


def render_header(mode: str) -> list[str]:
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return [
        "# GenLens Market Intelligence",
        f"Generated: {generated}",
        f"Mode: {mode}",
        "",
        "Genny treats creative AI job posts, source signals, and tool mentions as evidence of where AI-native production work is going.",
        "",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "roles", "builds", "map", "products"], default="all")
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args()

    data = load_json(ROLE_SIGNALS_PATH)
    rows = role_rows(data)

    lines = render_header(args.mode)
    if args.mode in {"all", "roles"}:
        lines.extend(render_roles(rows))
    if args.mode in {"all", "builds"}:
        lines.extend(render_builds(rows))
    if args.mode in {"all", "map"}:
        lines.extend(render_map(rows))
    if args.mode in {"all", "products"}:
        lines.extend(render_products())

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
