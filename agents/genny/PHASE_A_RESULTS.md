# Phase A Discovery Results

Date: 2026-07-23
Source: read-only commands run by Jonathan in the VPS console. No secrets
were viewed or recorded.

## System Resources

- Total RAM: 3.8 GiB
- Available RAM: 2.6 GiB (Hermes gateway and system use ~1.2 GiB)
- Swap: 0 B (none configured)
- CPU cores: 2
- Root disk: 58 GiB total, 43 GiB free (26% used)

## Ollama Status

- Installed: yes
- Models present:
  - `llama3.2:1b` (1.3 GB, pulled ~8 weeks ago)
  - `qwen2.5:1.5b` (986 MB, pulled ~8 weeks ago)

## Hermes Configuration

- Service: `hermes-gateway-genny.service`, active, runs
  `/usr/local/bin/hermes -p genny gateway run --replace` as root with
  `WorkingDirectory=/root`.
- Restart policy: on-failure, 3s.
- Model/provider setting surface: **verified 2026-07-23** from `hermes --help`
  and `hermes -p genny --help`:
  - Persistent model and provider live in `config.yaml` under `model.provider`
    (per profile), edited via `hermes model` (interactive picker),
    `hermes config set model <name>`, or `hermes config edit`.
  - Per-invocation override: `-m/--model` (e.g. `anthropic/claude-sonnet-4.6`)
    and `--provider`, or the `HERMES_INFERENCE_MODEL` env var.
  - Hermes has a built-in **fallback chain**: `hermes fallback list|add|remove`.
    This natively satisfies the handoff's "explicit, named fallback" rule; no
    custom routing layer is needed on the Hermes side.
  - Provider credentials load from the profile `.env`; the `LM_MODEL` variable
    assumed earlier is NOT part of the documented surface. Use the
    `config.yaml` / `hermes model` path instead.

## Decision (per the Model Choice Matrix)

Total RAM is 3.8 GiB, which is **under the 6 GiB minimum** for the smallest
recommended model (`qwen3:4b`). Per the handoff matrix:

> Under 6 GiB usable RAM: do not run a local LLM. Use a hosted fallback only
> after approval.

**Recommended model: none (local).** Do not pull `qwen3:4b` or larger on this
box. With no swap configured, loading a 4B-class model risks the OOM killer
taking down the Hermes gateway itself.

The two already-installed 1B-class models are the only things this box can
physically run. They are usable for a low-stakes routing experiment but are
below the quality bar for editorial work, and even they leave thin headroom
beside the gateway process.

## Options for Jonathan (choose one)

1. **Hosted fallback (handoff-preferred for this hardware).** Pick exactly one
   named provider and model per Phase D rules. Requires explicit approval and
   a fresh API key stored only in the VPS `.env`.
2. **Upgrade the VPS to 8+ GiB RAM**, then rerun Phase A and proceed to
   `qwen3:4b`. This is spend and requires explicit approval.
3. **Short local experiment with the existing `qwen2.5:1.5b` or `llama3.2:1b`**
   (no new install, no spend). Expect weak quality; treat as a plumbing test
   of the OpenAI-compatible boundary only, not a production choice.

## Live Runtime Evidence (2026-07-23, Discord)

Observed in a Discord DM with Genny (screenshot reviewed, no secrets):

- Primary model request failed with **HTTP 401 (non-retryable)**: the primary
  provider's credential is invalid or revoked, consistent with the security
  cleanup that revoked the exposed keys.
- Hermes then **fell back to `google/gemini-3.1-flash-lite` via OpenRouter**
  and answered normally. Two implications:
  1. The OpenRouter credential on the VPS is still live. The handoff's
     security cleanup calls for revoking it unless OpenRouter is the chosen
     route; it currently is not.
  2. Genny is running production traffic on an unpinned free-tier fallback,
     which violates locked decision #5 (fallback must be explicit, named,
     and bounded). This strengthens the case for completing Phase B promptly.
- NotebookLM MCP reported unauthenticated: expected, known constraint.

Decision (2026-07-23): **Option 1, hosted provider.** Provider: Anthropic.
Model: `claude-haiku-4-5` (upgrade path: `claude-sonnet-5` via one config
change). Configure via `hermes -p genny model` on the VPS; key lives only in
the VPS profile. Then set an explicit fallback chain via `hermes fallback`
and revoke the OpenRouter key unless it is the named fallback.

Approved by: Jonathan (chat, 2026-07-23)
Proceed to Phase B: yes (Anthropic key setup on VPS pending)
