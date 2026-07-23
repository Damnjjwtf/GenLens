#!/usr/bin/env python3
"""Provider-neutral model runtime health check for the Genny Hermes profile.

Reads only non-secret runtime settings, validates that local providers stay on
loopback, optionally probes the OpenAI-compatible ``/models`` endpoint, and
emits a stable JSON health document suitable for Discord, API, or dashboard
display.

Never prints API keys, webhook URLs, full environment values, or response
bodies. See docs/MODEL_RUNTIME_HANDOFF.md (Phase C).
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

HEALTH_DOC_TYPE = "genlens_model_health"
HEALTH_DOC_VERSION = 1

ENV_PROVIDER = "GENLENS_MODEL_PROVIDER"
ENV_BASE_URL = "GENLENS_MODEL_BASE_URL"
ENV_MODEL = "GENLENS_MODEL_NAME"
ENV_TIMEOUT = "GENLENS_MODEL_TIMEOUT_SECONDS"
ENV_FALLBACK = "GENLENS_MODEL_FALLBACK_PROVIDER"
ENV_API_KEY = "GENLENS_MODEL_API_KEY"

DEFAULT_PROVIDER = "ollama"
DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_TIMEOUT_SECONDS = 15.0

LOCAL_PROVIDERS = {"ollama", "vllm", "local"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

REDACTED = "[redacted]"


@dataclasses.dataclass
class ModelConfig:
    provider: str
    base_url: str
    model: str
    timeout_seconds: float
    fallback_provider: str
    api_key: str
    errors: list[str]


def load_config(env: Mapping[str, str]) -> ModelConfig:
    errors: list[str] = []

    provider = env.get(ENV_PROVIDER, DEFAULT_PROVIDER).strip().lower()
    base_url = env.get(ENV_BASE_URL, DEFAULT_BASE_URL).strip().rstrip("/")
    model = env.get(ENV_MODEL, "").strip()
    fallback = env.get(ENV_FALLBACK, "none").strip().lower() or "none"
    api_key = env.get(ENV_API_KEY, "").strip()

    if not model:
        errors.append(f"{ENV_MODEL} is not set; the runtime has no model configured")

    raw_timeout = env.get(ENV_TIMEOUT, "").strip()
    timeout_seconds = DEFAULT_TIMEOUT_SECONDS
    if raw_timeout:
        try:
            timeout_seconds = float(raw_timeout)
        except ValueError:
            errors.append(f"{ENV_TIMEOUT} must be a number, got a non-numeric value")
        else:
            if timeout_seconds <= 0:
                errors.append(f"{ENV_TIMEOUT} must be positive")

    split = urllib.parse.urlsplit(base_url)
    if split.scheme not in ("http", "https") or not split.hostname:
        errors.append(f"{ENV_BASE_URL} is not a valid http(s) URL")

    return ModelConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
        fallback_provider=fallback,
        api_key=api_key,
        errors=errors,
    )


def is_local_provider(provider: str) -> bool:
    return provider in LOCAL_PROVIDERS


def base_url_host(base_url: str) -> str:
    return urllib.parse.urlsplit(base_url).hostname or ""


def is_loopback_host(host: str) -> bool:
    return host.lower() in LOOPBACK_HOSTS


def validate_endpoint(config: ModelConfig) -> list[str]:
    """Return endpoint policy issues (empty list when compliant)."""
    issues: list[str] = []
    host = base_url_host(config.base_url)
    if not host:
        return issues
    scheme = urllib.parse.urlsplit(config.base_url).scheme

    if is_local_provider(config.provider):
        if not is_loopback_host(host):
            issues.append(
                f"local provider '{config.provider}' must use a loopback host "
                f"(127.0.0.1 / localhost), got '{host}'"
            )
    else:
        if scheme != "https":
            issues.append(
                f"hosted provider '{config.provider}' must use https, got '{scheme}'"
            )
        if is_loopback_host(host):
            issues.append(
                f"hosted provider '{config.provider}' points at loopback host "
                f"'{host}'; check {ENV_BASE_URL}"
            )
    return issues


def redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, REDACTED)
    return text


def probe_headers(config: ModelConfig) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if config.api_key:
        if config.provider == "anthropic":
            headers["x-api-key"] = config.api_key
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Authorization"] = f"Bearer {config.api_key}"
    return headers


def parse_model_ids(payload: Any) -> list[str]:
    """Accept OpenAI-compatible ({"data": [...]}) and Ollama ({"models": [...]}) shapes."""
    rows: list[Any] = []
    if isinstance(payload, dict):
        for key in ("data", "models"):
            if isinstance(payload.get(key), list):
                rows = payload[key]
                break
    ids: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            identifier = row.get("id") or row.get("name") or row.get("model")
            if isinstance(identifier, str):
                ids.append(identifier)
    return ids


def probe_models(config: ModelConfig) -> dict[str, Any]:
    """Probe GET {base_url}/models. Returns derived fields only, never the body."""
    result: dict[str, Any] = {
        "ok": False,
        "status_code": None,
        "latency_ms": None,
        "model_count": None,
        "configured_model_present": None,
        "error": None,
    }
    url = f"{config.base_url}/models"
    request = urllib.request.Request(url, headers=probe_headers(config))
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            body = response.read(1_000_000)
            result["status_code"] = response.status
    except urllib.error.HTTPError as error:
        result["status_code"] = error.code
        if error.code in (401, 403):
            hint = "credential rejected; check the provider API key on the VPS"
        else:
            hint = "endpoint reachable but returned an error status"
        result["error"] = f"HTTP {error.code} from {url}: {hint}"
        return result
    except (TimeoutError, socket.timeout):
        result["error"] = (
            f"timed out after {config.timeout_seconds:g}s reaching {url}; "
            "is the runtime process up?"
        )
        return result
    except urllib.error.URLError as error:
        reason = redact(str(error.reason), [config.api_key])
        if isinstance(error.reason, (TimeoutError, socket.timeout)):
            result["error"] = (
                f"timed out after {config.timeout_seconds:g}s reaching {url}; "
                "is the runtime process up?"
            )
        else:
            result["error"] = f"cannot reach {url}: {reason}"
        return result

    result["latency_ms"] = int((time.monotonic() - started) * 1000)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        result["error"] = f"{url} did not return valid JSON"
        return result

    ids = parse_model_ids(payload)
    result["model_count"] = len(ids)
    if config.model:
        result["configured_model_present"] = config.model in ids
    result["ok"] = True
    return result


def build_health_document(
    config: ModelConfig,
    endpoint_issues: list[str],
    probe: dict[str, Any] | None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    healthy = not config.errors and not endpoint_issues
    if probe is not None:
        healthy = healthy and bool(probe.get("ok"))
        if probe.get("configured_model_present") is False:
            healthy = False

    return {
        "type": HEALTH_DOC_TYPE,
        "version": HEALTH_DOC_VERSION,
        "checked_at": checked_at
        or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "provider": config.provider,
        "base_url_host": base_url_host(config.base_url),
        "model": config.model or None,
        "timeout_seconds": config.timeout_seconds,
        "fallback_provider": config.fallback_provider,
        "api_key_configured": bool(config.api_key),
        "config_errors": list(config.errors),
        "endpoint_issues": list(endpoint_issues),
        "probe": probe,
        "healthy": healthy,
    }


def render_text(doc: dict[str, Any]) -> str:
    lines = [
        f"provider: {doc['provider']}",
        f"host: {doc['base_url_host']}",
        f"model: {doc['model'] or '(not set)'}",
        f"fallback: {doc['fallback_provider']}",
        f"api key configured: {'yes' if doc['api_key_configured'] else 'no'}",
    ]
    for issue in doc["config_errors"]:
        lines.append(f"config error: {issue}")
    for issue in doc["endpoint_issues"]:
        lines.append(f"endpoint issue: {issue}")
    probe = doc.get("probe")
    if probe is None:
        lines.append("probe: skipped (run with --check)")
    elif probe["ok"]:
        present = probe.get("configured_model_present")
        presence = (
            "configured model available"
            if present
            else "configured model NOT in list"
            if present is False
            else "model presence unknown"
        )
        lines.append(
            f"probe: ok ({probe['model_count']} models, {probe['latency_ms']}ms, {presence})"
        )
    else:
        lines.append(f"probe: FAILED ({probe['error']})")
    lines.append(f"healthy: {'yes' if doc['healthy'] else 'NO'}")
    return "\n".join(lines)


def run(argv: list[str], env: Mapping[str, str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="probe the runtime's /models endpoint (read-only network call)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the health document as JSON",
    )
    args = parser.parse_args(argv)

    config = load_config(env)
    endpoint_issues = validate_endpoint(config)
    probe = None
    if args.check and not config.errors:
        probe = probe_models(config)

    doc = build_health_document(config, endpoint_issues, probe)
    rendered = (
        json.dumps(doc, indent=2, sort_keys=True) if args.json else render_text(doc)
    )
    print(redact(rendered, [config.api_key]))
    return 0 if doc["healthy"] else 1


def main() -> None:
    import os

    sys.exit(run(sys.argv[1:], os.environ))


if __name__ == "__main__":
    main()
