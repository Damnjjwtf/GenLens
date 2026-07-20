---
name: genlens-market-flywheel
description: Turn GenLens source, tool, job, and role signals into market maps, proof builds, flywheels, and new product opportunities.
required_tools:
  - terminal
---

# GenLens Market Flywheel

Use this skill when Jonathan asks whether a product idea is good for GenLens, how to adapt a career/job/arbitrage system to GenLens, what network effects exist, what Genny can build next, or how Genny can become more powerful.

## Core Files

- Product strategy: `/root/.hermes/profiles/genny/data/genlens_product_strategy.md`
- Operating modes: `/root/.hermes/profiles/genny/data/genlens_operating_modes.json`
- Role memo: `/root/.hermes/profiles/genny/data/genlens_role_intelligence.md`
- Structured role signals: `/root/.hermes/profiles/genny/data/role_signals.json`
- Source registry: `/root/.hermes/profiles/genny/data/genny_sources.json`
- Tools manifest: `/root/.hermes/profiles/genny/data/genlens_tools_manifest.md`

## Script

Use:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_role_radar.py --mode all
```

Modes:

- `--mode roles`: observed, emerging, and forecast roles.
- `--mode builds`: proof-build ideas tied to roles.
- `--mode map`: role/tool/company clusters.
- `--mode products`: GenLens product opportunities.
- `--mode all`: complete market intelligence artifact.

## How To Think

Genny should not only summarize signals. She should create leverage from them.

The operating loop is:

1. Source signals reveal tools.
2. Tools reveal workflow clusters.
3. Workflow clusters reveal new roles.
4. New roles reveal proof builds.
5. Proof builds reveal user needs.
6. User needs reveal GenLens products.
7. Products attract more users and more submitted signals.

## Output Rules

- Label every role as `observed`, `emerging`, or `forecast`.
- Separate facts from strategy.
- Do not pretend a forecast role exists as a real job.
- Tie product ideas to repeated signals, tool clusters, role gaps, or user pain.
- Prefer practical artifacts: role maps, proof-builds, hiring briefs, tool stack blueprints, source dashboards, and paid reports.
