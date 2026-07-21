#!/usr/bin/env python3
"""Genny wrapper around notebooklm-py.

The wrapper keeps NotebookLM optional and fail-closed. It never pretends to have
notebook access when auth is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
NOTEBOOKLM_BIN = Path(os.environ.get(
    "NOTEBOOKLM_BIN",
    str(BASE_DIR / ".venv-notebooklm" / "bin" / "notebooklm"),
))
STATE_PATH = Path(os.environ.get("GENLENS_NOTEBOOKLM_STATE", str(BASE_DIR / "state" / "notebooklm_state.json")))
DEFAULT_NOTEBOOK_HINT = os.environ.get("GENLENS_NOTEBOOKLM_HINT", "genlens")


def run(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [str(NOTEBOOKLM_BIN), *args]
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def health() -> dict[str, object]:
    if not NOTEBOOKLM_BIN.exists():
        return {"installed": False, "authenticated": False, "error": f"notebooklm CLI not found at {NOTEBOOKLM_BIN}"}
    proc = run(["doctor"])
    output = (proc.stdout + proc.stderr).strip()
    authenticated = "Auth" in output and "not authenticated" not in output and "✗ fail" not in output
    return {
        "installed": True,
        "authenticated": authenticated,
        "doctor_exit": proc.returncode,
        "doctor": output,
    }


def list_notebooks() -> str:
    h = health()
    if not h["authenticated"]:
        return json.dumps(h, indent=2)
    proc = run(["list", "--json"])
    if proc.returncode != 0:
        return proc.stderr or proc.stdout
    return proc.stdout


def select_notebook(hint: str) -> str:
    h = health()
    if not h["authenticated"]:
        return json.dumps(h, indent=2)
    proc = run(["list", "--json"])
    if proc.returncode != 0:
        return proc.stderr or proc.stdout
    notebooks = json.loads(proc.stdout or "[]")
    lowered = hint.lower()
    match = None
    for notebook in notebooks:
        title = str(notebook.get("title") or notebook.get("name") or "")
        nb_id = str(notebook.get("id") or "")
        if lowered in title.lower() or lowered in nb_id.lower():
            match = notebook
            break
    if not match:
        return f"No NotebookLM notebook matched hint: {hint}"
    nb_id = str(match.get("id"))
    use = run(["use", nb_id])
    if use.returncode != 0:
        return use.stderr or use.stdout
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"active_notebook_id": nb_id, "hint": hint, "notebook": match}, indent=2) + "\n")
    return f"Selected NotebookLM notebook: {match.get('title') or match.get('name') or nb_id} ({nb_id})"


def ask(question: str, notebook_hint: str | None = None) -> str:
    h = health()
    if not h["authenticated"]:
        return (
            "NotebookLM is installed but not authenticated. "
            "Run notebooklm login or copy a valid storage_state.json before asking notebook questions.\n\n"
            + json.dumps(h, indent=2)
        )
    if notebook_hint:
        selected = select_notebook(notebook_hint)
        if selected.startswith("No NotebookLM") or "not authenticated" in selected:
            return selected
    proc = run(["ask", question])
    if proc.returncode != 0:
        return proc.stderr or proc.stdout
    return proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("list")
    select = sub.add_parser("select")
    select.add_argument("--hint", default=DEFAULT_NOTEBOOK_HINT)
    ask_parser = sub.add_parser("ask")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--hint", default="")
    args = parser.parse_args()

    if args.cmd == "health":
        print(json.dumps(health(), indent=2))
    elif args.cmd == "list":
        print(list_notebooks())
    elif args.cmd == "select":
        print(select_notebook(args.hint))
    elif args.cmd == "ask":
        print(ask(args.question, args.hint or None))
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
