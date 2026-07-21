#!/usr/bin/env python3
"""Persist versioned GenLens signal observations with stable identities."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
MAX_HISTORY_PER_SIGNAL = 50
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "oc",
    "ref",
    "source",
}
STATUS_PRIORITY = {"rejected": 0, "qualified": 1, "published": 2}
CONFIDENCE_PRIORITY = {
    "hypothesis": 0,
    "single-source": 1,
    "corroborated": 2,
    "primary-source": 3,
}
PRIMARY_SOURCE_TYPES = {"official_updates", "release_notes", "github_releases"}

VERTICAL_IMPACT_CONTEXT = {
    "Agentic Marketing Workflows": "marketing workflow automation and operator leverage",
    "Paid Media / Creative Performance": "campaign control, creative performance, and media operations",
    "Stack Consolidation / Displacement": "stack continuity, replacement timing, and migration effort",
    "Lifecycle / Retention": "segmentation, engagement, and retention operations",
    "Measurement / Attribution": "measurement coverage and attribution decisions",
    "Commerce / Conversion": "conversion, merchandising, and commercial economics",
    "SEO / AEO / Content Systems": "search visibility, content discovery, and reporting",
    "Sales / Marketing Convergence": "revenue workflow coordination and pipeline operations",
    "Marketing Data / Identity": "customer-data quality, identity, and governance",
    "Product Photography": "production speed, asset control, and commercial image quality",
    "AI Filmmaking": "production speed, editorial control, and video pipeline economics",
    "Digital Humans": "performance control, localization, and synthetic-media operations",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonicalize_url(url: str) -> str:
    """Normalize a source URL while retaining query parameters with meaning."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return raw.split("#", 1)[0].rstrip("/")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query_rows = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS:
            continue
        query_rows.append((key, value))
    query = urllib.parse.urlencode(sorted(query_rows))
    return urllib.parse.urlunsplit(("https", host, path, query, ""))


def stable_signal_id(url: str, title: str) -> str:
    canonical = canonicalize_url(url)
    fallback = re.sub(r"[^a-z0-9]+", " ", str(title or "").lower()).strip()
    material = canonical or fallback
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"sig_{digest}"


def reason_code(reason: str) -> str:
    code = re.sub(r"[^a-z0-9]+", "-", str(reason or "").lower()).strip("-")
    return code or "unspecified"


def confidence_for_source(source_type: str, status: str, authoritative: bool = False) -> str:
    if status == "rejected":
        return "hypothesis"
    if authoritative or source_type in PRIMARY_SOURCE_TYPES:
        return "primary-source"
    return "single-source"


def make_candidate_review(
    *,
    lens: str,
    vertical: str,
    source_name: str,
    source_url: str = "",
    source_type: str,
    source_priority: str,
    title: str,
    summary: str,
    url: str,
    published_at: str,
    status: str,
    score: int,
    reason: str,
) -> dict[str, Any]:
    if status not in STATUS_PRIORITY:
        raise ValueError(f"Unsupported signal status: {status}")
    canonical_url = canonicalize_url(url)
    canonical_source_url = canonicalize_url(source_url)
    candidate_host = urllib.parse.urlsplit(canonical_url).netloc
    source_host = urllib.parse.urlsplit(canonical_source_url).netloc
    authoritative = bool(
        source_type in PRIMARY_SOURCE_TYPES
        or (
            candidate_host
            and source_host
            and (
                candidate_host == source_host
                or candidate_host.endswith(f".{source_host}")
            )
        )
    )
    signal_id = stable_signal_id(canonical_url, title)
    normalized_source = re.sub(r"[^a-z0-9]+", "-", str(source_name or "source").lower()).strip("-")
    review_material = f"{lens}|{vertical}|{signal_id}|{normalized_source}"
    review_id = "rev_" + hashlib.sha256(review_material.encode("utf-8")).hexdigest()[:20]
    return {
        "review_id": review_id,
        "signal_id": signal_id,
        "lens": lens,
        "vertical": vertical,
        "source_name": source_name or "Source",
        "source_url": canonical_source_url,
        "source_type": source_type or "unknown",
        "source_priority": source_priority or "medium",
        "title": str(title or "").strip(),
        "summary": str(summary or "").strip(),
        "url": str(url or "").strip(),
        "canonical_url": canonical_url,
        "published_at": str(published_at or "").strip() or None,
        "status": status,
        "score": int(score),
        "quality_reason": str(reason or "unspecified"),
        "quality_reason_code": reason_code(reason),
        "reason": str(reason or "unspecified"),
        "reason_code": reason_code(reason),
        "authoritative": authoritative,
        "confidence": confidence_for_source(source_type, status, authoritative),
    }


def update_review_status(
    reviews: list[dict[str, Any]],
    review_id: str,
    status: str,
    reason: str,
) -> None:
    for review in reviews:
        if review.get("review_id") != review_id:
            continue
        review["status"] = status
        review["reason"] = reason
        review["reason_code"] = reason_code(reason)
        review["confidence"] = confidence_for_source(
            str(review.get("source_type") or "unknown"),
            status,
            bool(review.get("authoritative")),
        )
        return


def unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def public_review(review: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "review_id",
        "lens",
        "vertical",
        "status",
        "score",
        "quality_reason",
        "quality_reason_code",
        "reason",
        "reason_code",
        "confidence",
        "source_name",
        "source_url",
        "source_type",
        "source_priority",
        "authoritative",
    )
    return {key: review.get(key) for key in keys}


def decision_enrichment(
    *,
    status: str,
    title: str,
    summary: str,
    verticals: list[str],
) -> dict[str, str | None]:
    """Derive a conservative operator recommendation from explicit source text.

    The output uses a controlled vocabulary and never records a user decision.
    Rejected candidates remain intentionally unenriched.
    """
    if status not in {"published", "qualified"}:
        return {
            "mechanism": None,
            "use_case": None,
            "impact": None,
            "recommended_action": None,
        }

    text = f"{title} {summary}".lower()
    if re.search(r"\b(shut(?:ting)? down|sunset|deprecat(?:e[ds]?|ing)?|end of life|migration|migrate)\b", text):
        action = "migrate"
        mechanism = "service shutdown, deprecation, or migration"
    elif re.search(r"\b(pricing|price change|duties|fees?|costs?|billing|commercial terms)\b", text):
        action = "budget"
        mechanism = "pricing, fee, or commercial-model change"
    elif re.search(r"\b(disclosure|transparency|policy|license|rights|consent|compliance|governance)\b", text):
        action = "brief"
        mechanism = "policy, disclosure, rights, or governance change"
    elif re.search(r"\b(measurement|attribution|report(?:s|ing)?|search console|track(?:s|ing)?|analytics|incrementality)\b", text):
        action = "test"
        mechanism = "measurement or reporting capability"
    elif re.search(r"\b(api|sdk|mcp|integration|automation|agent(?:ic)?|workflow|orchestration)\b", text):
        action = "test"
        mechanism = "API, integration, agent, or workflow capability"
    elif re.search(r"\b(launch(?:es|ed|ing)?|releas(?:e[ds]?|ing)?|introduc(?:e[ds]?|ing)|add(?:s|ed|ing)?|new (?:feature|tool|capability|control|property)|now available|available globally|can now)\b", text):
        action = "test"
        mechanism = "new or expanded product capability"
    else:
        action = "watch"
        mechanism = "verified ecosystem change"

    vertical = verticals[0] if verticals else "the affected workflow"
    context = VERTICAL_IMPACT_CONTEXT.get(vertical, f"the {vertical} workflow")
    use_case = {
        "migrate": f"Assess replacement and transition requirements in {vertical}.",
        "budget": f"Review budget and commercial assumptions for {vertical}.",
        "brief": f"Brief affected operators and update guidance for {vertical}.",
        "test": f"Run a bounded evaluation in {vertical} before adoption.",
        "watch": f"Monitor follow-on evidence for {vertical}.",
    }[action]
    return {
        "mechanism": mechanism,
        "use_case": use_case,
        "impact": f"Potential impact on {context}.",
        "recommended_action": action,
    }


def build_run_records(
    reviews: list[dict[str, Any]],
    *,
    run_lens: str,
    mode: str,
    observed_at: str | None = None,
) -> list[dict[str, Any]]:
    del run_lens, mode  # Recorded at the run level by write_signal_ledger.
    observed = observed_at or utc_now()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for review in reviews:
        signal_id = str(review.get("signal_id") or "")
        if signal_id:
            grouped.setdefault(signal_id, []).append(review)

    records: list[dict[str, Any]] = []
    for signal_id, signal_reviews in grouped.items():
        ranked = sorted(
            signal_reviews,
            key=lambda row: (
                STATUS_PRIORITY.get(str(row.get("status")), -1),
                int(row.get("score") or 0),
            ),
            reverse=True,
        )
        best = ranked[0]
        status = str(best.get("status") or "rejected")
        membership_reviews = (
            [row for row in signal_reviews if row.get("status") != "rejected"]
            if status != "rejected"
            else signal_reviews
        )
        evidence = []
        evidence_seen: set[tuple[str, str]] = set()
        for review in sorted(
            membership_reviews,
            key=lambda row: int(row.get("score") or 0),
            reverse=True,
        ):
            evidence_key = (
                str(review.get("canonical_url") or ""),
                str(review.get("source_name") or "Source"),
            )
            if not evidence_key[0] or evidence_key in evidence_seen:
                continue
            evidence_seen.add(evidence_key)
            evidence.append({
                "url": evidence_key[0],
                "source_name": evidence_key[1],
                "source_url": review.get("source_url") or "",
                "source_type": review.get("source_type") or "unknown",
                "authoritative": bool(review.get("authoritative")),
                "published_at": review.get("published_at"),
            })
        confidence = max(
            (str(row.get("confidence") or "hypothesis") for row in ranked),
            key=lambda value: CONFIDENCE_PRIORITY.get(value, -1),
        )
        reviews_public = [public_review(row) for row in signal_reviews]
        lenses = unique_strings([str(row.get("lens") or "") for row in membership_reviews])
        verticals = unique_strings([str(row.get("vertical") or "") for row in membership_reviews])
        enrichment = decision_enrichment(
            status=status,
            title=str(best.get("title") or ""),
            summary=str(best.get("summary") or ""),
            verticals=verticals,
        )
        record = {
            "id": signal_id,
            "status": status,
            "lenses": lenses,
            "verticals": verticals,
            "title": best.get("title") or "Untitled signal",
            "summary": best.get("summary") or "",
            "canonical_url": best.get("canonical_url") or "",
            "source": {
                "name": best.get("source_name") or "Source",
                "url": best.get("source_url") or "",
                "type": best.get("source_type") or "unknown",
                "priority": best.get("source_priority") or "medium",
                "authoritative": bool(best.get("authoritative")),
            },
            "evidence": evidence,
            "change": best.get("title") or "Untitled signal",
            "mechanism": enrichment["mechanism"],
            "use_case": enrichment["use_case"],
            "impact": enrichment["impact"],
            "recommended_action": enrichment["recommended_action"],
            "confidence": confidence,
            "score": max(int(row.get("score") or 0) for row in signal_reviews),
            "rejection_reason": best.get("reason_code") if status == "rejected" else None,
            "first_observed_at": observed,
            "last_observed_at": observed,
            "observation_count": 1,
            "reviews": reviews_public,
            "history": [{
                "observed_at": observed,
                "status": status,
                "review_count": len(reviews_public),
                "reason_codes": unique_strings([
                    str(row.get("reason_code") or "") for row in reviews_public
                ]),
            }],
        }
        records.append(record)
    return sorted(records, key=lambda row: str(row["id"]))


def load_existing_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read existing signal ledger without risking history loss: {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("records", []), list):
        raise ValueError(f"Existing signal ledger has an invalid structure: {path}")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"Existing signal ledger schema {data.get('schema_version')!r} is not supported; expected {SCHEMA_VERSION}"
        )
    return data


def validate_signal_ledger(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Signal ledger schema version mismatch")
    latest_run = payload.get("latest_run")
    if not isinstance(latest_run, dict):
        raise ValueError("Signal ledger is missing latest_run")
    if latest_run.get("lens") not in {"genny", "marti", "unified"}:
        raise ValueError("Signal ledger has an invalid run lens")
    if latest_run.get("mode") not in {"active", "expanded"}:
        raise ValueError("Signal ledger has an invalid run mode")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Signal ledger records must be a list")
    ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Signal ledger record must be an object")
        signal_id = str(record.get("id") or "")
        if not re.fullmatch(r"sig_[a-f0-9]{20}", signal_id):
            raise ValueError(f"Invalid signal ID: {signal_id!r}")
        if signal_id in ids:
            raise ValueError(f"Duplicate signal ID: {signal_id}")
        ids.add(signal_id)
        status = record.get("status")
        if status not in STATUS_PRIORITY:
            raise ValueError(f"Invalid signal status for {signal_id}: {status!r}")
        if not record.get("lenses") or not record.get("verticals"):
            raise ValueError(f"Signal {signal_id} is missing lens or vertical membership")
        if status == "rejected":
            if record.get("recommended_action") is not None or not record.get("rejection_reason"):
                raise ValueError(f"Rejected signal {signal_id} has inconsistent decision fields")
        elif record.get("recommended_action") not in {"test", "adopt", "avoid", "migrate", "brief", "budget", "plan", "watch"}:
            raise ValueError(f"Qualified signal {signal_id} is missing a supported action")
        if status == "published" and not record.get("evidence"):
            raise ValueError(f"Published signal {signal_id} has no evidence")
        history = record.get("history")
        if not isinstance(history, list) or not history or len(history) > MAX_HISTORY_PER_SIGNAL:
            raise ValueError(f"Signal {signal_id} has invalid observation history")
        for observation in history:
            if not isinstance(observation, dict):
                raise ValueError(f"Signal {signal_id} has a malformed history entry")
            if observation.get("status") not in STATUS_PRIORITY:
                raise ValueError(f"Signal {signal_id} has an invalid historical status")
            if int(observation.get("review_count") or 0) < 1:
                raise ValueError(f"Signal {signal_id} has an invalid historical review count")
            reason_codes = observation.get("reason_codes")
            if not isinstance(reason_codes, list) or not reason_codes:
                raise ValueError(f"Signal {signal_id} has no historical reason codes")
        if int(record.get("observation_count") or 0) < len(history):
            raise ValueError(f"Signal {signal_id} observation count is inconsistent")


def write_signal_ledger(
    path: Path,
    reviews: list[dict[str, Any]],
    *,
    run_lens: str,
    mode: str,
    observed_at: str | None = None,
) -> dict[str, Any]:
    observed = observed_at or utc_now()
    current_records = build_run_records(
        reviews,
        run_lens=run_lens,
        mode=mode,
        observed_at=observed,
    )
    existing = load_existing_ledger(path)
    merged = {
        str(row.get("id")): row
        for row in existing.get("records", [])
        if isinstance(row, dict) and row.get("id")
    }
    for current in current_records:
        signal_id = str(current["id"])
        previous = merged.get(signal_id)
        if previous:
            current["first_observed_at"] = previous.get("first_observed_at") or observed
            current["observation_count"] = int(previous.get("observation_count") or 0) + 1
            history = [
                row for row in previous.get("history", [])
                if isinstance(row, dict)
            ] + current["history"]
            current["history"] = history[-MAX_HISTORY_PER_SIGNAL:]
        merged[signal_id] = current

    counts = {"published": 0, "qualified": 0, "rejected": 0}
    for record in current_records:
        status = str(record.get("status") or "rejected")
        counts[status] = counts.get(status, 0) + 1
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": observed,
        "latest_run": {
            "lens": run_lens,
            "mode": mode,
            "observed_at": observed,
            "review_count": len(reviews),
            "signal_count": len(current_records),
            "counts": counts,
            "observed_signal_ids": [str(row["id"]) for row in current_records],
        },
        "records": sorted(merged.values(), key=lambda row: str(row.get("id") or "")),
    }
    validate_signal_ledger(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
    return payload
