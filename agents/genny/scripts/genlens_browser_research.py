#!/usr/bin/env python3
"""Read-only Browser Use worker for GenLens source-gap research.

This file intentionally does not import Browser Use at module import time. The
normal GenLens composer can therefore run without the large browser runtime;
the dedicated Browser Use virtualenv is invoked only for an explicit fallback
research task.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.parse
from pathlib import Path
from typing import Any


DISALLOWED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.google.internal.",
}
DISALLOWED_DOMAINS = {
    "accounts.google.com",
    "discord.com",
    "discordapp.com",
    "mail.google.com",
    "notebooklm.google.com",
}
NOISE_PATH = re.compile(
    r"(^/$|/pricing/?$|/features?/?$|/solutions?/?$|/customers?/?$|/products?/?$|"
    r"/platform/?$|/templates?/?$|/use-cases?/?$|/category/|/tag/|/topics?/|"
    r"/collections?/|/blog/?$|/news/?$|/learn/?$|/resources?/?$)",
    re.I,
)
SKIP_URL = re.compile(
    r"(privacy|terms|login|signup|subscribe|contact|about|careers|cookie|"
    r"facebook|instagram|linkedin|twitter|x\.com|youtube)",
    re.I,
)


def hostname(url: str) -> str:
    return urllib.parse.urlparse(url).hostname.lower().rstrip(".") if urllib.parse.urlparse(url).hostname else ""


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _resolves_private(host: str) -> bool:
    """Reject hostnames that resolve to loopback/private/link-local addresses."""
    try:
        addresses = socket.getaddrinfo(host, None)
    except OSError:
        # DNS failure is handled by the browser; this check is only a local
        # network guard, so an unresolvable public host is not treated as safe.
        return True
    for row in addresses:
        address = row[4][0]
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return True
        if parsed.is_private or parsed.is_loopback or parsed.is_link_local or parsed.is_reserved:
            return True
    return False


def public_url_allowed(url: str, source_host: str | None = None) -> tuple[bool, str]:
    """Validate a public HTTP URL and optionally keep it on one source host."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not host:
        return False, "url must use http or https"
    if host in DISALLOWED_HOSTS or host in DISALLOWED_DOMAINS:
        return False, "host is not allowed for research"
    if _is_ip(host) or _resolves_private(host):
        return False, "private or unresolved host is not allowed"
    if source_host:
        source_host = source_host.lower().rstrip(".")
        if not (host == source_host or host.endswith("." + source_host)):
            return False, "navigation left the configured source domain"
    return True, "ok"


def candidate_url_allowed(url: str, source_host: str) -> tuple[bool, str]:
    allowed, reason = public_url_allowed(url, source_host)
    if not allowed:
        return allowed, reason
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or "/"
    if SKIP_URL.search(url) or NOISE_PATH.search(path):
        return False, "homepage, category, account, or navigation URL"
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if not segments or max(len(segment) for segment in segments) < 8:
        return False, "URL does not look like a specific article"
    return True, "ok"


def build_task(url: str, vertical: str, lens: str, task_type: str, limit: int) -> str:
    focus = {
        "dynamic-source": "a recent product release, research result, policy change, or production workflow change",
        "career": "a recent public job listing with a specific title, employer, location, and requirements",
        "community": "a recent public community signal that can be corroborated by a first-party source",
    }[task_type]
    return f"""Read the public page at {url} for the {lens} lens and {vertical} vertical.

Your job is to find up to {limit} {focus} from this same public source domain.
This is evidence collection, not a general web search.

Hard rules:
- Read-only research. Do not log in, create an account, submit a form, send a message, upload, download, purchase, or follow links outside the source domain.
- Do not use cookies, saved browser profiles, local storage, or personal browsing history.
- Reject homepages, product landing pages, pricing pages, evergreen tutorials, generic comparisons, listicles, and undated pages.
- Each result must be a specific article or public job page with an exact canonical URL, an explicit publication date in YYYY-MM-DD form, and an 80-300 character evidence excerpt from the page.
- Prefer a concrete release, tool capability, workflow, cost/time change, rights/compliance change, or hiring requirement. Never invent a date, number, title, or claim.
- If the page has no qualified items, return status no_signal with an empty results list.

Return only the requested structured result. Do not include commentary outside the schema."""


def normalize_results(payload: dict[str, Any], source_url: str, limit: int) -> dict[str, Any]:
    """Apply deterministic checks after the model's structured response."""
    source_host = hostname(source_url)
    accepted: list[dict[str, str]] = []
    rejected = 0
    seen: set[str] = set()
    for raw in payload.get("results", []) if isinstance(payload, dict) else []:
        if not isinstance(raw, dict):
            rejected += 1
            continue
        title = str(raw.get("title") or "").strip()
        url = str(raw.get("url") or "").strip()
        date = str(raw.get("published_at") or raw.get("date") or "").strip()
        excerpt = re.sub(r"\s+", " ", str(raw.get("evidence_excerpt") or "").strip())
        ok, _reason = candidate_url_allowed(url, source_host)
        if not ok or len(title) < 8 or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date) or len(excerpt) < 80:
            rejected += 1
            continue
        if url in seen:
            continue
        seen.add(url)
        claims = raw.get("claims_supported") or []
        if not isinstance(claims, list):
            claims = [str(claims)]
        accepted.append({
            "title": title,
            "url": url,
            "date": date,
            "summary": excerpt[:320],
            "source_kind": str(raw.get("source_kind") or "first_party").strip(),
            "claims_supported": "; ".join(str(value).strip() for value in claims if str(value).strip())[:320],
            "relevance": str(raw.get("relevance") or "").strip()[:240],
        })
        if len(accepted) >= max(1, limit):
            break
    status = "ok" if accepted else "no_signal"
    reason = "qualified public evidence found" if accepted else "no dated, specific, source-domain evidence passed validation"
    if rejected and accepted:
        reason += f"; rejected {rejected} weak or unsafe result(s)"
    return {
        "status": status,
        "results": accepted,
        "reason": reason,
        "source_url": source_url,
        "source_domain": source_host,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def _llm(provider: str, model: str) -> Any:
    from browser_use import ChatAnthropic, ChatGoogle, ChatOpenAI, ChatOpenRouter

    if provider == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        return ChatOpenRouter(model=model, api_key=key, timeout=45, max_retries=1)
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return ChatOpenAI(model=model, api_key=key, timeout=45, max_retries=1)
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        return ChatAnthropic(model=model, api_key=key, max_retries=1)
    if provider == "google":
        key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured")
        return ChatGoogle(model=model, api_key=key, max_retries=1)
    raise RuntimeError(f"unsupported Browser Use LLM provider: {provider}")


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    allowed, reason = public_url_allowed(args.url)
    if not allowed:
        return {"status": "blocked", "results": [], "reason": reason, "source_url": args.url}
    from pydantic import BaseModel, Field
    from browser_use import Agent, BrowserProfile

    class BrowserEvidence(BaseModel):
        title: str = Field(min_length=8)
        url: str
        published_at: str
        source_kind: str = "first_party"
        evidence_excerpt: str = Field(min_length=80)
        claims_supported: list[str] = Field(default_factory=list)
        relevance: str = ""

    class BrowserResearchResult(BaseModel):
        status: str
        results: list[BrowserEvidence] = Field(default_factory=list)
        reason: str = ""

    provider = os.environ.get("GENLENS_BROWSER_LLM_PROVIDER", "openrouter").strip().lower()
    model = os.environ.get("GENLENS_BROWSER_LLM_MODEL", "openai/gpt-4o-mini").strip()
    profile = BrowserProfile(
        headless=True,
        executable_path="/usr/bin/google-chrome-stable",
        chromium_sandbox=False,
        allowed_domains=[hostname(args.url)],
        prohibited_domains=sorted(DISALLOWED_DOMAINS),
        block_ip_addresses=True,
        accept_downloads=False,
        user_data_dir=None,
        storage_state=None,
        keep_alive=False,
        use_cloud=False,
        enable_default_extensions=False,
    )
    agent = Agent(
        task=build_task(args.url, args.vertical, args.lens, args.task_type, args.limit),
        llm=_llm(provider, model),
        browser_profile=profile,
        output_model_schema=BrowserResearchResult,
        max_failures=2,
        max_actions_per_step=2,
        use_thinking=False,
        flash_mode=True,
        directly_open_url=True,
    )
    history = await agent.run(max_steps=max(1, min(args.max_steps, 20)))
    structured = history.structured_output
    payload = structured.model_dump(mode="json") if structured is not None else {"status": "failed", "results": [], "reason": "no structured output"}
    return normalize_results(payload, args.url, args.limit)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--vertical", required=True)
    parser.add_argument("--lens", choices=["genny", "marti"], default="genny")
    parser.add_argument("--task-type", choices=["dynamic-source", "career", "community"], default="dynamic-source")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    try:
        payload = asyncio.run(_run(args))
    except Exception as exc:
        payload = {
            "status": "failed",
            "results": [],
            "reason": f"Browser Use worker failed: {type(exc).__name__}: {exc}",
            "source_url": args.url,
        }
    encoded = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded)
    print(encoded, end="")
    return 0 if payload.get("status") != "failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
