---
name: notebooklm-py
description: Use the installed notebooklm-py CLI wrapper to query registered Google NotebookLM notebooks when authenticated.
required_tools:
  - terminal
---

# NotebookLM via notebooklm-py

Use this skill when Jonathan asks Genny to use NotebookLM, notebook memory, notebook-grounded synthesis, or source-grounded research from NotebookLM.

## Installed Runtime

- Python venv: `/root/.hermes/profiles/genny/.venv-notebooklm`
- CLI: `/root/.hermes/profiles/genny/.venv-notebooklm/bin/notebooklm`
- Genny wrapper: `/root/.hermes/profiles/genny/scripts/genlens_notebooklm.py`
- Notebook registry: `/root/.hermes/profiles/genny/data/notebooklm_sources.json`

## Health First

Always check health before querying:

```bash
/root/.hermes/profiles/genny/scripts/genlens_notebooklm.py health
```

If `authenticated` is false, say plainly:

> NotebookLM is installed but not authenticated yet. I need a valid `storage_state.json` or `notebooklm login` before I can read notebooks.

Then fall back to local GenLens files. Do not hallucinate NotebookLM contents.

## Commands

List notebooks:

```bash
/root/.hermes/profiles/genny/scripts/genlens_notebooklm.py list
```

Select the registered GenLens notebook:

```bash
/root/.hermes/profiles/genny/scripts/genlens_notebooklm.py select --hint "genlens"
```

Ask a source-grounded question:

```bash
/root/.hermes/profiles/genny/scripts/genlens_notebooklm.py ask \
  --hint "genlens" \
  "What should GenLens remember from the registered NotebookLM sources?"
```

## Safety

- Treat NotebookLM as optional source-grounded memory, not the sole source of truth.
- Preserve citations when NotebookLM provides them.
- Cache useful answers into local GenLens memory/source bundles only when Jonathan asks or the result directly improves Genny.
- Do not delete notebooks or sources.
- Do not print auth cookies, storage state, or Google session data.
