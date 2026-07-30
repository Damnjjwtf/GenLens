#!/usr/bin/env python3
"""Grounded editorial synthesis over already-verified brief cards.

The batch composer produces source-backed, gated cards (title, summary, date,
source, vertical). This module asks the model to WRITE a tight editorial lead
and ranked movers from those cards, so the digest reads as intelligence rather
than a filtered link list, while being structurally forbidden from adding any
fact not present in a card.

Design guarantees:
- Grounded only: the model receives the gated cards and is told to rank,
  connect, and rephrase them, never to introduce a number, name, date, or
  claim that is not in a card. The deterministic brief remains underneath as
  the audit artifact, so any reader can verify.
- Fail open, never block: any missing key, disabled flag, network error,
  timeout, refusal, or malformed response returns None. The composer then
  ships the deterministic brief unchanged. Synthesis is an enhancement layer,
  not a dependency.
- No secrets in output: the API key is read from the environment for the
  request only and never returned, logged, or embedded in the digest.

Raw HTTP via urllib keeps the module stdlib-only, matching the rest of the
Genny scripts (no new dependency on the anthropic SDK).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_TOKENS = 1024
MAX_CARDS = 24

ENV_ENABLED = "GENLENS_SYNTHESIS"
ENV_MODEL = "GENLENS_SYNTH_MODEL"
ENV_PRIMARY_KEY = "ANTHROPIC_API_KEY"
ENV_FALLBACK_KEY = "GENLENS_MODEL_API_KEY"

SYSTEM_PROMPT = (
    "You are Genny, the GenLens production-intelligence editor. You are given a "
    "list of VERIFIED signal cards that already passed a source and fact "
    "check. Write a short editorial digest from them.\n\n"
    "HARD RULES:\n"
    "- Use only facts that appear in the provided cards. Never add a number, "
    "name, date, company, price, or claim that is not in a card.\n"
    "- Every specific claim must trace to a card. Reference cards inline like "
    "[C1], [C2].\n"
    "- If you are unsure whether something is in the cards, leave it out.\n"
    "- No em dashes anywhere. Use commas or colons.\n"
    "- Do not fabricate. Do not speculate beyond the cards.\n\n"
    "STRUCTURE:\n"
    "- Open with a 2 to 3 sentence lead naming the single biggest shift this "
    "week and why it matters to creative technologists.\n"
    "- Then a section 'Top signals' with 3 to 5 ranked bullets. Each bullet is "
    "one line: what changed, then a short clause on why it matters, then the "
    "card reference.\n"
    "- Keep the whole thing under 250 words. Warm, expert, direct. No preamble, "
    "no sign off."
)


def _is_enabled(env: Mapping[str, str]) -> bool:
    raw = env.get(ENV_ENABLED, "1").strip().lower()
    return raw not in ("0", "false", "no", "off", "")


def _resolve_key(env: Mapping[str, str]) -> str:
    return (env.get(ENV_PRIMARY_KEY) or env.get(ENV_FALLBACK_KEY) or "").strip()


def _clean(value: Any) -> str:
    return str(value or "").replace("\n", " ").strip()


def build_card_payload(cards: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Compact, indexed card list for the prompt. Trims to MAX_CARDS."""
    payload: list[dict[str, str]] = []
    for index, card in enumerate(cards[:MAX_CARDS], start=1):
        payload.append(
            {
                "id": f"C{index}",
                "vertical": _clean(card.get("vertical")),
                "date": _clean(card.get("date")),
                "source": _clean(card.get("source")),
                "title": _clean(card.get("title")),
                "summary": _clean(card.get("summary"))[:600],
            }
        )
    return payload


def strip_em_dashes(text: str) -> str:
    """Enforce the GenLens no-em-dash output rule as a deterministic net."""
    return text.replace(" — ", ", ").replace("—", ", ")


def _request_body(cards: list[dict[str, str]], model: str) -> dict[str, Any]:
    user_content = (
        "Verified cards (JSON). Write the digest using only these facts:\n\n"
        + json.dumps(cards, ensure_ascii=False, indent=1)
    )
    return {
        "model": model,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }


def _call_api(body: dict[str, Any], api_key: str, timeout: float) -> dict[str, Any] | None:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_000)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _extract_text(payload: Mapping[str, Any]) -> str | None:
    if payload.get("stop_reason") == "refusal":
        return None
    blocks = payload.get("content")
    if not isinstance(blocks, list):
        return None
    parts = [
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    text = "".join(parts).strip()
    return text or None


def synthesize_brief(
    cards: Sequence[Mapping[str, Any]],
    env: Mapping[str, str] | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str | None:
    """Return a grounded editorial digest, or None to fall back to the brief.

    Never raises. Callers treat None as "no synthesis available" and ship the
    deterministic brief instead.
    """
    env = os.environ if env is None else env
    if not cards or not _is_enabled(env):
        return None
    api_key = _resolve_key(env)
    if not api_key:
        return None

    model = (env.get(ENV_MODEL) or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload = _call_api(_request_body(build_card_payload(cards), model), api_key, timeout)
    if payload is None:
        return None
    text = _extract_text(payload)
    if text is None:
        return None
    return strip_em_dashes(text)
