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
GIT_OPTIONS=()
if ! "$GIT_BIN" --version >/dev/null 2>&1; then
  if [[ -x "$CODEX_FALLBACK_GIT" ]]; then
    GIT_BIN="$CODEX_FALLBACK_GIT"
    if command -v gh >/dev/null 2>&1; then
      GIT_OPTIONS=(-c "credential.helper=!gh auth git-credential")
    fi
  else
    echo "Git is unavailable. Install Git or accept the Xcode command-line tools license." >&2
    exit 1
  fi
fi

git_cmd() {
  "$GIT_BIN" "${GIT_OPTIONS[@]}" "$@"
}

action="${1:-status}"

case "$action" in
  status)
    git_cmd status --short --branch
    ;;
  pull)
    if [[ -n "$(git_cmd status --porcelain -- agents/genny)" ]]; then
      echo "Genny has local changes. Commit or resolve them before pulling." >&2
      exit 1
    fi
    git_cmd pull --ff-only
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
    git_cmd add -- agents/genny
    if git_cmd diff --cached --quiet; then
      echo "No Genny changes to publish."
      exit 0
    fi
    git_cmd commit -m "$message"
    branch="$(git_cmd branch --show-current)"
    git_cmd push -u origin "$branch"
    git_cmd rev-parse --short HEAD
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
