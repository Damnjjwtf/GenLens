#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Keep Genny work synchronized through GitHub.

Usage:
  genny_workspace_sync.sh status
  genny_workspace_sync.sh pull
  genny_workspace_sync.sh publish "Commit message"
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_DIR"

GIT_BIN="${GIT_BIN:-git}"
CODEX_FALLBACK_GIT="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/git"
if ! "$GIT_BIN" --version >/dev/null 2>&1; then
  if [[ -x "$CODEX_FALLBACK_GIT" ]]; then
    GIT_BIN="$CODEX_FALLBACK_GIT"
  else
    echo "Git is unavailable. Install Git or accept the Xcode command-line tools license." >&2
    exit 1
  fi
fi

action="${1:-status}"

case "$action" in
  status)
    "$GIT_BIN" status --short --branch
    ;;
  pull)
    if [[ -n "$("$GIT_BIN" status --porcelain -- agents/genny)" ]]; then
      echo "Genny has local changes. Commit or resolve them before pulling." >&2
      exit 1
    fi
    "$GIT_BIN" pull --ff-only
    ;;
  publish)
    message="${2:-}"
    if [[ -z "$message" ]]; then
      echo "A commit message is required." >&2
      usage >&2
      exit 2
    fi
    python3 -m compileall -q agents/genny/scripts
    while IFS= read -r script; do
      bash -n "$script"
    done < <(find agents/genny/scripts -maxdepth 1 -type f -name '*.sh' -print)
    "$GIT_BIN" add -- agents/genny
    if "$GIT_BIN" diff --cached --quiet; then
      echo "No Genny changes to publish."
      exit 0
    fi
    "$GIT_BIN" commit -m "$message"
    branch="$("$GIT_BIN" branch --show-current)"
    "$GIT_BIN" push -u origin "$branch"
    "$GIT_BIN" rev-parse --short HEAD
    ;;
  -h|--help)
    usage
    ;;
  *)
    echo "Unknown action: $action" >&2
    usage >&2
    exit 2
    ;;
esac
