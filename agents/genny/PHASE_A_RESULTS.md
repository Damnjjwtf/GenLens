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
- Model/provider setting surface: **not yet verified.** `hermes --help` and
  `hermes -p genny --help` output still needed before changing any model
  configuration.

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

Approved by: pending
Proceed to Phase B: no (blocked on option choice above)
