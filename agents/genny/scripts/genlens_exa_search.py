#!/usr/bin/env python3
"""Small, dependency-free adapter for Exa semantic web search.

Exa is intentionally treated as a discovery provider. It returns candidate
articles and extractive highlights; the GenLens composer still owns freshness,
URL, relevance, duplication, and editorial acceptance.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any, Callable

API_URL = "https://api.exa.ai/search"
DEFAULT_TIMEOUT = 12
DEFAULT_RESULT_LIMIT = 6


class ExaSearchError(RuntimeError):
    """Raised when Exa cannot return a usable search response."""


def _as_date(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10] if len(raw) >= 10 else ""


def _highlight_text(result: dict[str, Any]) -> str:
    highlights = result.get("highlights")
    if isinstance(highlights, list):
        values = [str(value).strip() for value in highlights if str(value).strip()]
        if values:
            return " ".join(values)[:900]
    text = str(result.get("text") or result.get("summary") or "").strip()
    return text[:900]


def build_query(vertical: str, watch_for: list[str] | None = None, lens: str = "genny") -> str:
    terms = ", ".join(str(term).strip() for term in (watch_for or [])[:8] if str(term).strip())
    if lens == "marti":
        intent = "marketing technology releases, agent workflows, APIs, measurement, or operator case studies"
    else:
        intent = "generative AI production releases, workflow changes, tools, case studies, or rights updates"
    suffix = f" Relevant terms: {terms}." if terms else ""
    return (
        f"{vertical}: find recent, substantive editorial or first-party reporting about {intent}. "
        "Prefer a concrete change, mechanism, launch, policy, measured outcome, or production use. "
        "Exclude product homepages, generic tool roundups, tutorials, and promotional landing pages."
        f"{suffix}"
    )


def search(
    query: str,
    *,
    api_key: str | None = None,
    result_limit: int = DEFAULT_RESULT_LIMIT,
    max_age_days: int = 45,
    search_type: str = "auto",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    opener: Callable[..., Any] | None = None,
) -> list[dict[str, str]]:
    key = (api_key if api_key is not None else os.environ.get("EXA_API_KEY", "")).strip()
    if not key:
        raise ExaSearchError("EXA_API_KEY is not configured")
    if not query.strip():
        raise ExaSearchError("Exa query is empty")

    today = dt.datetime.now(dt.timezone.utc).date()
    payload: dict[str, Any] = {
        "query": query.strip(),
        "type": search_type or "auto",
        "numResults": max(1, min(int(result_limit), 20)),
        "startPublishedDate": (today - dt.timedelta(days=max(1, int(max_age_days)))).isoformat(),
        "endPublishedDate": (today + dt.timedelta(days=1)).isoformat(),
        "contents": {
            "highlights": {
                "query": query.strip(),
                "maxCharacters": 900,
            }
        },
    }
    if include_domains:
        payload["includeDomains"] = [str(value).strip() for value in include_domains if str(value).strip()]
    if exclude_domains:
        payload["excludeDomains"] = [str(value).strip() for value in exclude_domains if str(value).strip()]

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": key,
            "User-Agent": "GenLensExaDiscovery/1.0",
        },
        method="POST",
    )
    opener = opener or urllib.request.urlopen
    try:
        with opener(request, timeout=timeout, context=ssl.create_default_context()) as response:
            body = response.read(2_000_000)
    except urllib.error.HTTPError as exc:
        raise ExaSearchError(f"HTTP {exc.code} from Exa") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ExaSearchError(f"Exa request failed: {exc}") from exc
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExaSearchError("Exa returned invalid JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ExaSearchError("Exa response did not contain a results list")

    candidates: list[dict[str, str]] = []
    for result in data["results"]:
        if not isinstance(result, dict):
            continue
        url = str(result.get("url") or "").strip()
        title = str(result.get("title") or "").strip()
        date = _as_date(str(result.get("publishedDate") or ""))
        summary = _highlight_text(result)
        if not url or not title or not date or not summary:
            continue
        candidates.append({
            "title": title,
            "url": url,
            "date": date,
            "summary": summary,
            "exa_id": str(result.get("id") or "").strip(),
        })
    return candidates
