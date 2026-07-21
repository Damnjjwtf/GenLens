# NotebookLM Integration

Genny can use NotebookLM as an optional source-grounded research layer.

Current registered notebook:

- `Shared NotebookLM Source`
- `https://notebooklm.google.com/notebook/ea254699-b839-4a10-81a7-abe127ab63b3?utm_source=nlmm_share`

Seed source:

- `data/genlens_notebooklm_bundle.md`
- `data/notebooklm_sources.json`

## What NotebookLM Is For

- Long synthesis over GenLens sources
- Citation-backed comparison of tools and verticals
- Memory over research notes and prior briefing material
- Audio overview generation if useful later

## What It Is Not For

- Inventing fresh news
- Bypassing the GenLens source registry
- Replacing source verification
- Storing secrets

## Auth Note

NotebookLM MCP requires a human Google login session. Do not paste Google passwords or 2FA codes into agent chats.

If Genny cannot authenticate, she should say plainly that a notebook is registered but unreadable, then ask for exported source text/transcripts or continue from local GenLens files.
