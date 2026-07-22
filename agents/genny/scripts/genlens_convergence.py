#!/usr/bin/env python3
"""Generate and human-verify cross-lens GenLens convergence candidates."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import genlens_signal_ledger as signal_ledger

SCHEMA_VERSION = "1.0.0"
REVIEW_STATUSES = {"verified", "rejected"}
BRIDGE_CONSEQUENCES = {
    "cost-economics",
    "speed-scale",
    "rights-risk",
    "measurement",
    "stack-change",
    "revenue-conversion",
}
BRIEF_START = "<!-- genlens-verified-convergence:start -->"
BRIEF_END = "<!-- genlens-verified-convergence:end -->"

MECHANISM_PATTERNS = {
    "agentic-automation": re.compile(r"\b(agent(?:ic)?|automation|orchestration|workflow)\b", re.I),
    "api-integration": re.compile(r"\b(api|sdk|integration|plugin|connector)\b", re.I),
    "product-capability": re.compile(r"\b(launch|release|new (?:feature|tool|model|capability)|now available|product capability)\b", re.I),
    "pricing-commercial-model": re.compile(r"\b(pricing|price|fees?|billing|duties|commercial model|cost per)\b", re.I),
    "policy-rights-governance": re.compile(r"\b(policy|rights|copyright|consent|disclosure|labeling|compliance|governance|lawsuit)\b", re.I),
    "measurement-reporting": re.compile(r"\b(measurement|attribution|analytics|reporting|tracking|incrementality)\b", re.I),
    "market-consolidation": re.compile(r"\b(acquisition|acquires?|equity stake|partnership|consolidation|shutdown|migration)\b", re.I),
}

WORKFLOW_PATTERNS = {
    "creative-assets": re.compile(r"\b(creative assets?|creative production|design workflow|brand content|campaign creative)\b", re.I),
    "video-production": re.compile(r"\b(video|film(?:making)?|vfx|footage|short-form|reels?|tiktok|post-production)\b", re.I),
    "image-production": re.compile(r"\b(product photography|product images?|image generation|catalog|retouch|packshot)\b", re.I),
    "audio-production": re.compile(r"\b(music|audio|voice|podcast|songs?|tracks?|dubbing|mastering)\b", re.I),
    "commerce-conversion": re.compile(r"\b(commerce|shopify|checkout|storefront|merchant|conversion|merchandising)\b", re.I),
    "paid-media": re.compile(r"\b(ads?|advertising|campaign|roas|cpm|bidding|paid media)\b", re.I),
    "content-search": re.compile(r"\b(content systems?|seo|aeo|search console|search terms|publishing)\b", re.I),
    "customer-lifecycle": re.compile(r"\b(lifecycle|retention|crm|email|sms|journey|customer engagement)\b", re.I),
    "data-measurement": re.compile(r"\b(customer data|identity|cdp|attribution|measurement|analytics|reporting)\b", re.I),
    "real-time-3d": re.compile(r"\b(real-time 3d|game development|unity|unreal|godot|digital human|avatar|character)\b", re.I),
}

CONSEQUENCE_PATTERNS = {
    "cost-economics": re.compile(r"\b(cost|pricing|price|fees?|budget|economics|commercial)\b", re.I),
    "speed-scale": re.compile(r"\b(speed|faster|scale|volume|throughput|automation|time)\b", re.I),
    "quality-control": re.compile(r"\b(quality|control|consistency|accuracy|editing|governance)\b", re.I),
    "rights-risk": re.compile(r"\b(rights|copyright|consent|policy|disclosure|compliance|lawsuit|risk)\b", re.I),
    "measurement": re.compile(r"\b(measurement|attribution|analytics|reporting|tracking)\b", re.I),
    "stack-change": re.compile(r"\b(migration|replacement|shutdown|deprecation|consolidation|stack displacement)\b", re.I),
    "revenue-conversion": re.compile(r"\b(revenue|conversion|retention|roas|sales|commerce)\b", re.I),
}

ENTITY_PATTERNS = {
    "Adobe": re.compile(r"\badobe\b", re.I),
    "Canva": re.compile(r"\bcanva\b", re.I),
    "CapCut": re.compile(r"\bcapcut\b", re.I),
    "ElevenLabs": re.compile(r"\belevenlabs\b", re.I),
    "Figma": re.compile(r"\bfigma\b", re.I),
    "Google": re.compile(r"\bgoogle\b", re.I),
    "HubSpot": re.compile(r"\bhubspot\b", re.I),
    "Meta": re.compile(r"\bmeta\b", re.I),
    "n8n": re.compile(r"\bn8n\b", re.I),
    "OpenAI": re.compile(r"\bopenai\b", re.I),
    "Reallusion": re.compile(r"\breallusion\b", re.I),
    "Runway": re.compile(r"\brunway\b", re.I),
    "Salesforce": re.compile(r"\bsalesforce\b", re.I),
    "Shopify": re.compile(r"\bshopify\b", re.I),
    "Slack": re.compile(r"\bslack(?:bot)?\b", re.I),
    "Suno": re.compile(r"\bsuno\b", re.I),
    "Zapier": re.compile(r"\bzapier\b", re.I),
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temp_path, path)


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read convergence ledger: {path}") from exc
    signal_ledger.validate_signal_ledger(payload)
    if payload.get("latest_run", {}).get("lens") != "unified":
        raise ValueError("Convergence requires a unified signal-ledger run")
    return payload


def current_published(payload: dict[str, Any], lens: str) -> list[dict[str, Any]]:
    current_ids = set(str(value) for value in payload.get("latest_run", {}).get("observed_signal_ids", []))
    return [
        row
        for row in payload.get("records", [])
        if isinstance(row, dict)
        and row.get("status") == "published"
        and str(row.get("id")) in current_ids
        and lens in row.get("lenses", [])
    ]


def record_text(record: dict[str, Any]) -> str:
    return " ".join(
        [
            str(record.get("title") or ""),
            str(record.get("summary") or ""),
            str(record.get("mechanism") or ""),
            str(record.get("use_case") or ""),
            str(record.get("impact") or ""),
            " ".join(str(value) for value in record.get("verticals", [])),
        ]
    )


def tags(text: str, patterns: dict[str, re.Pattern[str]]) -> set[str]:
    return {name for name, pattern in patterns.items() if pattern.search(text)}


def candidate_id(genny_id: str, marti_id: str) -> str:
    material = f"{genny_id}|{marti_id}"
    return "conv_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def evidence_row(record: dict[str, Any], lens: str) -> dict[str, Any]:
    evidence = next(
        (row for row in record.get("evidence", []) if isinstance(row, dict) and row.get("url")),
        {},
    )
    return {
        "lens": lens,
        "signal_id": record.get("id"),
        "title": record.get("title"),
        "url": evidence.get("url") or record.get("canonical_url"),
        "source_name": evidence.get("source_name") or record.get("source", {}).get("name") or "Source",
        "published_at": evidence.get("published_at"),
        "confidence": record.get("confidence") or "single-source",
    }


def build_candidates(payload: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    genny_records = current_published(payload, "genny")
    marti_records = current_published(payload, "marti")
    rows: list[tuple[int, dict[str, Any]]] = []
    for genny in genny_records:
        genny_text = record_text(genny)
        genny_dimensions = {
            "mechanisms": tags(genny_text, MECHANISM_PATTERNS),
            "workflows": tags(genny_text, WORKFLOW_PATTERNS),
            "entities": tags(genny_text, ENTITY_PATTERNS),
            "consequences": tags(genny_text, CONSEQUENCE_PATTERNS),
        }
        for marti in marti_records:
            if genny.get("id") == marti.get("id"):
                continue
            marti_text = record_text(marti)
            shared = {
                "mechanisms": sorted(genny_dimensions["mechanisms"] & tags(marti_text, MECHANISM_PATTERNS)),
                "workflows": sorted(genny_dimensions["workflows"] & tags(marti_text, WORKFLOW_PATTERNS)),
                "entities": sorted(genny_dimensions["entities"] & tags(marti_text, ENTITY_PATTERNS)),
                "consequences": sorted(genny_dimensions["consequences"] & tags(marti_text, CONSEQUENCE_PATTERNS)),
            }
            dimension_count = sum(bool(values) for values in shared.values())
            if not shared["workflows"] or not (shared["mechanisms"] or shared["entities"]):
                continue
            if dimension_count < 2:
                continue
            # Broad pairs such as “new video tool” + “new video campaign
            # feature” are not useful convergence. Require a named shared
            # entity or a concrete economic/operator bridge beyond generic
            # quality-control language.
            if not shared["entities"] and not (set(shared["consequences"]) & BRIDGE_CONSEQUENCES):
                continue
            score = dimension_count * 10 + sum(min(2, len(values)) for values in shared.values())
            shared_labels = shared["workflows"] + shared["mechanisms"] + shared["entities"] + shared["consequences"]
            hypothesis = (
                f"Potential shared {shared['workflows'][0]} change: Genny records “{genny.get('title')}” while "
                f"Marti records “{marti.get('title')}”. Shared evidence tags: {', '.join(shared_labels)}. "
                "Verify whether the production change materially alters the marketing workflow or economics; "
                "no causal relationship is asserted."
            )
            row = {
                "id": candidate_id(str(genny.get("id")), str(marti.get("id"))),
                "status": "candidate",
                "confidence": "hypothesis",
                "score": score,
                "genny_signal_id": genny.get("id"),
                "marti_signal_id": marti.get("id"),
                "shared": shared,
                "hypothesis": hypothesis,
                "conclusion": None,
                "verification": None,
                "evidence": [evidence_row(genny, "genny"), evidence_row(marti, "marti")],
            }
            rows.append((score, row))
    rows.sort(key=lambda item: (-item[0], str(item[1]["id"])))
    return [row for _score, row in rows[: max(1, limit)]]


def empty_reviews() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "events": []}


def load_reviews(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_reviews()
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read convergence reviews without risking history loss: {path}") from exc
    validate_reviews(payload)
    return payload


def validate_reviews(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("events"), list):
        raise ValueError("Invalid convergence review log")
    event_ids: set[str] = set()
    idempotency_keys: set[str] = set()
    for event in payload["events"]:
        if not isinstance(event, dict) or event.get("status") not in REVIEW_STATUSES:
            raise ValueError("Invalid convergence review event")
        if not re.fullmatch(r"convr_[a-f0-9]{20}", str(event.get("id") or "")):
            raise ValueError("Invalid convergence review event ID")
        if event["id"] in event_ids or event.get("idempotency_key") in idempotency_keys:
            raise ValueError("Duplicate convergence review event")
        if not re.fullmatch(r"conv_[a-f0-9]{20}", str(event.get("candidate_id") or "")):
            raise ValueError("Convergence review event has an invalid candidate ID")
        if not event.get("actor_id") or not event.get("note") or not event.get("idempotency_key") or not event.get("recorded_at"):
            raise ValueError("Convergence review event lacks attribution")
        if event["status"] == "verified" and not event.get("conclusion"):
            raise ValueError("Verified convergence event lacks a conclusion")
        event_ids.add(event["id"])
        idempotency_keys.add(str(event.get("idempotency_key") or ""))


def apply_reviews(candidates: list[dict[str, Any]], reviews: dict[str, Any]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in reviews.get("events", []):
        latest[str(event.get("candidate_id"))] = event
    for candidate in candidates:
        event = latest.get(str(candidate["id"]))
        if not event:
            continue
        candidate["status"] = event["status"]
        candidate["confidence"] = "human-verified" if event["status"] == "verified" else "rejected"
        candidate["conclusion"] = event.get("conclusion") if event["status"] == "verified" else None
        candidate["verification"] = event
    return candidates


def build_artifact(payload: dict[str, Any], reviews: dict[str, Any], limit: int = 12) -> dict[str, Any]:
    candidates = apply_reviews(build_candidates(payload, limit), reviews)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "ledger_schema_version": payload.get("schema_version"),
        "latest_run_observed_at": payload.get("latest_run", {}).get("observed_at"),
        "candidate_count": sum(row["status"] == "candidate" for row in candidates),
        "verified_count": sum(row["status"] == "verified" for row in candidates),
        "rejected_count": sum(row["status"] == "rejected" for row in candidates),
        "records": candidates,
    }


def validate_artifact(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION or not isinstance(payload.get("records"), list):
        raise ValueError("Invalid convergence artifact")
    ids: set[str] = set()
    for record in payload["records"]:
        if not re.fullmatch(r"conv_[a-f0-9]{20}", str(record.get("id") or "")):
            raise ValueError("Invalid convergence candidate ID")
        if record["id"] in ids or record.get("status") not in {"candidate", "verified", "rejected"}:
            raise ValueError("Invalid or duplicate convergence candidate")
        if len(record.get("evidence", [])) != 2 or {row.get("lens") for row in record["evidence"]} != {"genny", "marti"}:
            raise ValueError("Convergence candidate must retain one signal from each lens")
        if not record.get("shared", {}).get("workflows"):
            raise ValueError("Convergence candidate lacks a shared workflow")
        if record["status"] == "verified" and (not record.get("conclusion") or not record.get("verification")):
            raise ValueError("Verified convergence candidate lacks human verification")
        ids.add(record["id"])
    expected_counts = {
        "candidate_count": sum(row.get("status") == "candidate" for row in payload["records"]),
        "verified_count": sum(row.get("status") == "verified" for row in payload["records"]),
        "rejected_count": sum(row.get("status") == "rejected" for row in payload["records"]),
    }
    if any(payload.get(key) != value for key, value in expected_counts.items()):
        raise ValueError("Convergence artifact counts do not match records")


def evidence_link(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "Signal")
    url = str(row.get("url") or "")
    return f"[{title}]({url})" if url else title


def render_artifact(payload: dict[str, Any]) -> str:
    lines = [
        "# GenLens Convergence Review",
        "",
        "This artifact connects Genny production signals with Marti marketing signals for human verification. Candidate hypotheses are not publishable conclusions and assert no causality.",
        "",
        "## Counts",
        "",
        f"- Candidate: {payload.get('candidate_count', 0)}",
        f"- Human verified: {payload.get('verified_count', 0)}",
        f"- Human rejected: {payload.get('rejected_count', 0)}",
        "",
        "## Verified Convergence",
        "",
    ]
    verified = [row for row in payload["records"] if row["status"] == "verified"]
    if not verified:
        lines.extend(["- No cross-lens conclusion has been human verified.", ""])
    for row in verified:
        actor = row["verification"]["actor_id"]
        lines.extend([
            f"### {row['conclusion']}",
            "",
            f"- Candidate ID: `{row['id']}`",
            f"- Verified by: `{actor}` at `{row['verification']['recorded_at']}`",
            f"- Genny evidence: {evidence_link(row['evidence'][0])}",
            f"- Marti evidence: {evidence_link(row['evidence'][1])}",
            f"- Verification note: {row['verification']['note']}",
            "",
        ])
    lines.extend(["## Candidate Research Queue", ""])
    candidates = [row for row in payload["records"] if row["status"] == "candidate"]
    if not candidates:
        lines.extend(["- No unreviewed convergence candidate met the structured overlap gate.", ""])
    for row in candidates:
        lines.extend([
            f"### Candidate — `{row['id']}`",
            "",
            f"- Hypothesis: {row['hypothesis']}",
            f"- Genny evidence: {evidence_link(row['evidence'][0])}",
            f"- Marti evidence: {evidence_link(row['evidence'][1])}",
            "- Required review: verify the shared mechanism or workflow, document the operator consequence, and reject any implied causal claim not supported by both sources.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def verified_brief_section(payload: dict[str, Any]) -> str:
    verified = [row for row in payload["records"] if row["status"] == "verified"]
    if not verified:
        return ""
    lines = [BRIEF_START, "## Verified Convergence", "", "_Each conclusion below was explicitly verified by a named human against one Genny and one Marti signal._", ""]
    for row in verified:
        lines.append(f"- **{row['conclusion']}** — Genny: {evidence_link(row['evidence'][0])}. Marti: {evidence_link(row['evidence'][1])}. `human verified`")
    lines.extend(["", BRIEF_END])
    return "\n".join(lines)


def update_brief(path: Path, payload: dict[str, Any]) -> None:
    text = path.read_text() if path.exists() else ""
    text = re.sub(
        rf"\n?{re.escape(BRIEF_START)}.*?{re.escape(BRIEF_END)}\n?",
        "\n",
        text,
        flags=re.S,
    ).rstrip()
    section = verified_brief_section(payload)
    path.write_text(text + ("\n\n" + section if section else "") + "\n")


def record_review(
    *,
    candidates_path: Path,
    reviews_path: Path,
    candidate_id_value: str,
    status: str,
    actor_id: str,
    note: str,
    conclusion: str,
    idempotency_key: str,
    recorded_at: str | None = None,
) -> tuple[dict[str, Any], bool]:
    artifact = json.loads(candidates_path.read_text())
    validate_artifact(artifact)
    if status not in REVIEW_STATUSES:
        raise ValueError(f"Unsupported convergence review status: {status}")
    if not actor_id.strip() or not note.strip() or not idempotency_key.strip():
        raise ValueError("Convergence review requires actor, note, and idempotency key")
    if status == "verified" and len(conclusion.strip()) < 20:
        raise ValueError("Verified convergence requires a substantive conclusion")
    if candidate_id_value not in {str(row["id"]) for row in artifact["records"]}:
        raise ValueError(f"Unknown convergence candidate: {candidate_id_value}")
    reviews = load_reviews(reviews_path)
    existing = next((row for row in reviews["events"] if row.get("idempotency_key") == idempotency_key), None)
    if existing:
        same = all(
            existing.get(key) == value
            for key, value in {
                "candidate_id": candidate_id_value,
                "status": status,
                "actor_id": actor_id.strip(),
                "note": note.strip(),
                "conclusion": conclusion.strip() or None,
            }.items()
        )
        if not same:
            raise ValueError("Idempotency key already used for a different convergence review")
        return existing, False
    timestamp = recorded_at or utc_now()
    material = f"{candidate_id_value}|{idempotency_key}"
    event = {
        "id": "convr_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:20],
        "candidate_id": candidate_id_value,
        "status": status,
        "actor_id": actor_id.strip(),
        "note": note.strip(),
        "conclusion": conclusion.strip() or None,
        "idempotency_key": idempotency_key.strip(),
        "recorded_at": timestamp,
    }
    reviews["events"].append(event)
    validate_reviews(reviews)
    atomic_write_json(reviews_path, reviews)
    return event, True


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--ledger", required=True)
    generate.add_argument("--reviews", required=True)
    generate.add_argument("--out-json", required=True)
    generate.add_argument("--out-md", required=True)
    generate.add_argument("--brief")
    generate.add_argument("--limit", type=int, default=12)

    review = subparsers.add_parser("review")
    review.add_argument("--candidates", required=True)
    review.add_argument("--reviews", required=True)
    review.add_argument("--candidate-id", required=True)
    review.add_argument("--status", choices=sorted(REVIEW_STATUSES), required=True)
    review.add_argument("--actor-id", required=True)
    review.add_argument("--note", required=True)
    review.add_argument("--conclusion", default="")
    review.add_argument("--idempotency-key", required=True)

    args = parser.parse_args()
    if args.command == "review":
        event, created = record_review(
            candidates_path=Path(args.candidates),
            reviews_path=Path(args.reviews),
            candidate_id_value=args.candidate_id,
            status=args.status,
            actor_id=args.actor_id,
            note=args.note,
            conclusion=args.conclusion,
            idempotency_key=args.idempotency_key,
        )
        print(json.dumps({"created": created, "event": event}, indent=2, sort_keys=True))
        return 0

    ledger = load_ledger(Path(args.ledger))
    reviews = load_reviews(Path(args.reviews))
    artifact = build_artifact(ledger, reviews, args.limit)
    validate_artifact(artifact)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    atomic_write_json(out_json, artifact)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_artifact(artifact))
    if args.brief:
        update_brief(Path(args.brief), artifact)
    print(json.dumps({
        "artifact": str(out_json),
        "brief": str(out_md),
        "candidate_count": artifact["candidate_count"],
        "verified_count": artifact["verified_count"],
        "rejected_count": artifact["rejected_count"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
