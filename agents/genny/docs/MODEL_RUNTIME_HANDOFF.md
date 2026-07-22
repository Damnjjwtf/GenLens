# Genny / Marti Model Runtime Handoff

Status: implementation brief for Claude Code
Owner: Jonathan
Last updated: 2026-07-22

## The Job

Build a local-first, provider-neutral model runtime for the Genny Hermes profile.
It must support inexpensive experimentation now and a clean path to hosted or
GPU-backed inference later, without changing GenLens's evidence, promotion, or
human-review rules.

Do not treat "free" as the production strategy. The production strategy is
that the model can be replaced without rewriting Genny or Marti.

## What Is Already True

- VPS host: `209.74.85.95`, SSH port: `22022`.
- Live profile: `/root/.hermes/profiles/genny`.
- Live service: `hermes-gateway-genny.service`.
- GitHub `main` is the source of truth. Deploy only by running:

  ```bash
  curl -fsSL https://raw.githubusercontent.com/Damnjjwtf/GenLens/main/agents/genny/scripts/sync_to_hermes_profile.sh | bash
  ```

- The deployed sync preserves the live `.env` and `state/` directory.
- The signal pipeline is deliberately deterministic and source-grounded. Model
  output must not promote a signal, create a fact, mark a human review, or
  bypass the Marti promotion gate.
- Marti Discord delivery code is merged on `main`, but a new webhook still
  needs to be created and stored only in the VPS `.env` after the secret
  cleanup below.
- Hosted GenLens product data belongs in Neon Postgres. The VPS JSON state is
  an append-only runtime audit/cache, not the future product database.

## Security Cleanup Is Blocking

A screenshot of the VPS `.env` was accidentally shared. No secret values are
stored in this document or the repository.

Before adding any new provider, revoke and replace every exposed credential:

- Discord bot token: already replaced and `hermes-gateway-genny.service` was
  restarted successfully.
- Marti Discord webhook: deleted; create a new one later and do not paste it
  into chat, GitHub, screenshots, or logs.
- OpenAI API key: revoke. Do not create a replacement unless a paid OpenAI
  route is explicitly chosen.
- Gemini/Google API keys: revoke and replace only if Gemini becomes the
  chosen fallback.
- DeepSeek API key: revoke and replace only if it becomes an approved route.
- Resend API key: revoke and replace, because email delivery remains active.
- OpenRouter API key: revoke. Replace only if an OpenRouter route is chosen.

Never read, print, commit, diff, or screenshot `/root/.hermes/profiles/genny/.env`.

## Locked Architecture Decisions

1. **Code before model.** RSS ingestion, recency, source trust, filtering,
   deduplication, card contracts, decision actions, promotion, and delivery
   stay deterministic Python.
2. **OpenAI-compatible boundary.** Genny should talk to one configured
   OpenAI-compatible base URL and model name. Ollama, a hosted provider, and a
   future vLLM server must be interchangeable behind that boundary.
3. **Local first.** Ollama is the first runtime to evaluate. It costs no API
   spend, keeps routine agent traffic private, and works with the existing
   localhost OpenAI-compatible endpoint.
4. **No blind model install.** Choose the model only after inspecting VPS RAM,
   CPU, disk, and existing Ollama installation.
5. **Fallback is explicit.** No random free-model routing in production. A
   fallback must be named, have a bounded budget/rate policy, and be observable.
6. **No autonomous spend.** Adding a paid provider, a credit card, a GPU host,
   or a scheduled live-send job requires Jonathan's explicit approval.

## Phase A: Read-Only VPS Discovery

SSH to `root@209.74.85.95 -p 22022` and run:

```bash
free -h; echo; nproc; echo; df -h /; echo; ollama list
```

Capture only the non-secret output. Also inspect (without printing secrets):

```bash
systemctl cat hermes-gateway-genny.service
hermes --help
hermes -p genny --help
```

Determine where Hermes reads its model name and provider settings. The profile
has previously used `LM_BASE_URL=http://127.0.0.1:11434/v1`; do not assume an
`LM_MODEL` variable is supported until the installed Hermes help/config proves
it.

### Model Choice Matrix

After Phase A, use this matrix to select the initial local model:

| VPS RAM (usable) | Recommended Model | Rationale |
|---|---|---|
| Under 6 GiB | None (hosted fallback only) | CPU LLMs need ≥6 GiB headroom. Do not run local inference. |
| 6–11 GiB | `qwen3:4b` | Best CPU-only first test. Fast, good instruction following. |
| 12–23 GiB | `qwen3:8b` | Better quality and reasoning. Acceptable latency on modern CPU. |
| 24+ GiB | `qwen3:14b` | Highest quality, but still CPU-bound on this VPS. Evaluate latency. |

**Do not use a giant model on this VPS.** It risks swapping, service instability,
and a worse Discord experience. Ollama's explicit Qwen model sizes are part of
the operational constraint, not a quality benchmark.

### Phase A Output Template

Create a file `agents/genny/PHASE_A_RESULTS.md` with this structure (no secrets):

```markdown
# Phase A Discovery Results
Date: YYYY-MM-DD

## System Resources
- Total RAM: X GiB
- Usable RAM: X GiB
- CPU cores: N
- Root disk free: X GiB

## Ollama Status
- Installed: yes|no
- Running: yes|no
- Models present: [list or "none"]

## Hermes Configuration
- Service status: active|inactive|error
- Profile directory: exists|missing
- State files: [list of signal_ledger, decision_queue, etc.]
- Model provider variables: [LM_MODEL, LM_BASE_URL, etc. — no secrets]

## Decision
Recommended model: qwen3:4b | qwen3:8b | qwen3:14b | hosted-only
Reasoning: [brief]

Approved by: [human name]
Proceed to Phase B: yes|no
```

## Phase B: Install and Verify Ollama Only After Phase A Approval

If Phase A confirms the VPS can support the selected model:

1. Install or upgrade Ollama using its current official Linux instructions.
2. Pull the selected explicit model tag, for example:

   ```bash
   ollama pull qwen3:4b
   ```

3. Ensure Ollama starts at boot and listens only on loopback, not a public
   interface.
4. Verify both native and OpenAI-compatible health paths:

   ```bash
   ollama list
   curl -fsS http://127.0.0.1:11434/api/tags
   curl -fsS http://127.0.0.1:11434/v1/models
   ```

5. Confirm the actual Hermes model setting from Phase A, configure it in the
   live `.env` without printing it, and restart only this service:

   ```bash
   systemctl restart hermes-gateway-genny.service
   systemctl --no-pager --full status hermes-gateway-genny.service
   ```

6. Send one harmless Discord prompt to Genny and confirm a useful response.

Do not expose port `11434` to the Internet. Do not add a model token to Git.

## Phase C: Build the Provider-Neutral Contract in This Repo

Create a small, tested runtime adapter under `agents/genny/` only after Phase A
confirms Hermes's configuration surface. The adapter should not replace Hermes;
it should make operator configuration and verification legible.

Required capabilities:

- Read only non-secret settings: provider label, base URL host, model name,
  timeout, and whether a fallback is configured.
- Validate that a local provider endpoint uses loopback by default.
- Probe `/v1/models` with a short timeout and return an actionable error.
- Report a stable JSON health document suitable for future Discord, API, or
  dashboard display.
- Never include API keys, webhook URLs, full environment values, or response
  bodies in output.
- Provide `--check` (read-only) and `--json` modes.
- Write tests for local endpoint validation, missing configuration, timeout,
  redaction, and a successful OpenAI-compatible model-list response.

Suggested non-secret configuration names for the adapter:

```text
GENLENS_MODEL_PROVIDER=ollama
GENLENS_MODEL_BASE_URL=http://127.0.0.1:11434/v1
GENLENS_MODEL_NAME=qwen3:4b
GENLENS_MODEL_TIMEOUT_SECONDS=15
GENLENS_MODEL_FALLBACK_PROVIDER=none
```

Do not change the active Hermes variables until their supported names are
verified on the VPS.

## Phase D: Hosted Fallback, Not Yet Enabled

When there is real user traffic, choose exactly one explicit fallback provider.
The adapter must keep the same OpenAI-compatible boundary. Require:

- named provider and model, never an unpinned random free router;
- request timeout and one bounded retry;
- daily request/token cap and alerting;
- per-request provider/model/latency/error audit fields, with no prompt or
  secret logging by default;
- local-first policy, with fallback only when local health is down or an
  operator selects it;
- an operator kill switch.

OpenRouter's free route is acceptable for a short experiment, not a production
dependency: free availability and limits vary. Do not implement it as an
automatic fallback.

## Acceptance Checklist

- [ ] All exposed credentials have been revoked or replaced; no secrets appear
      in git, docs, terminal screenshots, or logs.
- [ ] VPS resources and Hermes configuration surface are recorded without
      secrets.
- [ ] Chosen Ollama model runs locally without swapping or destabilizing the
      Genny service.
- [ ] `hermes-gateway-genny.service` is `active (running)` after the change.
- [ ] Genny responds through Discord using the selected local model.
- [ ] Genny's source, ledger, decision, review, promotion, and email/Discord
      delivery guards behave exactly as before.
- [ ] Model adapter `--check --json` is tested and redacts secrets.
- [ ] Full `agents/genny/tests` suite passes.
- [ ] Any repo change is committed under `agents/genny/`, merged to `main`,
      and deployed via the sync script.

## Out of Scope for This Handoff

- Neon/Postgres product migration.
- A public Ollama endpoint.
- GPU hosting or vLLM deployment.
- Automatic paid-provider fallback.
- Sending live Marti briefs before her current promotion gate passes.
- Changing Genny/Marti evidence or human-review governance.
