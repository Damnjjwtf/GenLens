#!/usr/bin/env bash
set -euo pipefail

REPO_ARCHIVE_URL="${REPO_ARCHIVE_URL:-https://github.com/Damnjjwtf/GenLens/archive/refs/heads/main.tar.gz}"
PROFILE_DIR="${PROFILE_DIR:-/root/.hermes/profiles/genny}"
SERVICE_NAME="${SERVICE_NAME:-hermes-gateway-genny.service}"
REPO_DIR=""
RESTART_SERVICE=1
DRY_RUN=0

usage() {
  cat <<'USAGE'
Sync the repo's Genny package into the live Hermes profile.

Usage:
  sync_to_hermes_profile.sh [--repo-dir PATH] [--profile-dir PATH] [--service NAME] [--no-restart] [--dry-run]

Defaults:
  --profile-dir /root/.hermes/profiles/genny
  --service hermes-gateway-genny.service

If --repo-dir is omitted and the script is not running from a GenLens checkout,
it downloads the latest GitHub main archive and syncs from that copy.

Secrets are preserved:
  - existing .env is never overwritten
  - existing state/ is never removed
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir)
      REPO_DIR="${2:-}"
      shift 2
      ;;
    --profile-dir)
      PROFILE_DIR="${2:-}"
      shift 2
      ;;
    --service)
      SERVICE_NAME="${2:-}"
      shift 2
      ;;
    --no-restart)
      RESTART_SERVICE=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

log() {
  printf '[genny-sync] %s\n' "$*"
}

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
  else
    "$@"
  fi
}

find_source_dir() {
  local base="$1"
  if [[ -d "$base/agents/genny" ]]; then
    printf '%s\n' "$base/agents/genny"
    return 0
  fi
  if [[ -f "$base/AGENT.md" && -d "$base/scripts" && -d "$base/data" ]]; then
    printf '%s\n' "$base"
    return 0
  fi
  return 1
}

TMP_DIR=""
cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

SOURCE_DIR=""
if [[ -n "$REPO_DIR" ]]; then
  SOURCE_DIR="$(find_source_dir "$REPO_DIR")" || {
    echo "Could not find agents/genny under --repo-dir: $REPO_DIR" >&2
    exit 1
  }
else
  if SOURCE_DIR="$(find_source_dir "$PWD" 2>/dev/null)"; then
    :
  else
    TMP_DIR="$(mktemp -d /tmp/genlens-genny-sync.XXXXXX)"
    ARCHIVE="$TMP_DIR/genlens-main.tar.gz"
    log "Downloading latest GenLens main archive"
    run curl -fsSL "$REPO_ARCHIVE_URL" -o "$ARCHIVE"
    run tar -xzf "$ARCHIVE" -C "$TMP_DIR"
    SOURCE_DIR="$(find "$TMP_DIR" -maxdepth 3 -type d -path '*/agents/genny' -print -quit)"
    if [[ -z "$SOURCE_DIR" ]]; then
      echo "Downloaded archive did not contain agents/genny" >&2
      exit 1
    fi
  fi
fi

log "Source: $SOURCE_DIR"
log "Target: $PROFILE_DIR"

if [[ ! -f "$SOURCE_DIR/scripts/genlens_send_email.py" ]]; then
  echo "Missing expected sender script: $SOURCE_DIR/scripts/genlens_send_email.py" >&2
  exit 1
fi

run install -d "$PROFILE_DIR"
run install -d "$PROFILE_DIR/docs" "$PROFILE_DIR/data" "$PROFILE_DIR/prompts" "$PROFILE_DIR/scripts" "$PROFILE_DIR/skills"
run install -d "$PROFILE_DIR/state"

if [[ ! -f "$PROFILE_DIR/.env" && -f "$SOURCE_DIR/.env.example" ]]; then
  log "Creating .env from .env.example; fill secrets before sending email"
  run cp "$SOURCE_DIR/.env.example" "$PROFILE_DIR/.env"
else
  log "Preserving existing .env"
fi

run cp "$SOURCE_DIR/AGENT.md" "$PROFILE_DIR/AGENT.md"
run cp "$SOURCE_DIR/AGENT.md" "$PROFILE_DIR/SOUL.md"
if [[ -f "$SOURCE_DIR/docs/SOUL-compact.md" ]]; then
  run cp "$SOURCE_DIR/docs/SOUL-compact.md" "$PROFILE_DIR/SOUL-compact.md"
fi
if [[ -f "$SOURCE_DIR/README.md" ]]; then
  run cp "$SOURCE_DIR/README.md" "$PROFILE_DIR/README.md"
fi
if [[ -f "$SOURCE_DIR/requirements.txt" ]]; then
  run cp "$SOURCE_DIR/requirements.txt" "$PROFILE_DIR/requirements.txt"
fi

run cp -R "$SOURCE_DIR/docs/." "$PROFILE_DIR/docs/"
run cp -R "$SOURCE_DIR/data/." "$PROFILE_DIR/data/"
run cp -R "$SOURCE_DIR/prompts/." "$PROFILE_DIR/prompts/"
run cp -R "$SOURCE_DIR/scripts/." "$PROFILE_DIR/scripts/"
run cp -R "$SOURCE_DIR/skills/." "$PROFILE_DIR/skills/"

run chmod +x "$PROFILE_DIR"/scripts/*.py
run chmod +x "$PROFILE_DIR/scripts/sync_to_hermes_profile.sh"

if [[ "$DRY_RUN" -eq 0 ]]; then
  log "Checking Python syntax"
  python3 - <<PY
from pathlib import Path
import ast
for path in Path("$PROFILE_DIR/scripts").glob("*.py"):
    ast.parse(path.read_text())
print("ok")
PY
fi

if [[ "$DRY_RUN" -eq 0 && -f "$PROFILE_DIR/requirements.txt" ]]; then
  log "Installing Python requirements"
  python3 -m pip install -r "$PROFILE_DIR/requirements.txt"
fi

if [[ "$RESTART_SERVICE" -eq 1 ]]; then
  log "Restarting $SERVICE_NAME"
  run systemctl restart "$SERVICE_NAME"
  run systemctl status "$SERVICE_NAME" --no-pager
else
  log "Skipping service restart"
fi

log "Done"
