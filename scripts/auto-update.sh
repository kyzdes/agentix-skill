#!/usr/bin/env bash
# Optional SessionStart updater for the Agentix plugin in Claude Code and Codex.

set -eu

# Installing the plugin must never create an implicit network mutation. Users
# who want marketplace updates opt in explicitly in their shell environment.
case "${AGENTIX_PLUGIN_AUTO_UPDATE:-0}" in
  1 | true | TRUE | yes | YES | on | ON) ;;
  *) exit 0 ;;
esac

# Codex exposes PLUGIN_DATA to hooks. Claude Code uses the documented
# CLAUDE_PLUGIN_ROOT compatibility variable, but does not expose PLUGIN_DATA.
# This distinction lets one hook update only the host that installed it.
if [ -n "${PLUGIN_DATA:-}" ]; then
  CLIENT="codex"
  MARKETPLACE="${AGENTIX_CODEX_MARKETPLACE:-agentix}"
  PLUGIN_REF="${AGENTIX_CODEX_PLUGIN_REF:-agentix@${MARKETPLACE}}"
  CLIENT_BIN="$(command -v codex || true)"
  CACHE_ROOT="${AGENTIX_PLUGIN_CACHE_ROOT:-${PLUGIN_DATA}/agentix-plugin}"
else
  CLIENT="claude"
  MARKETPLACE="${AGENTIX_CLAUDE_MARKETPLACE:-claude-skills}"
  PLUGIN_REF="${AGENTIX_CLAUDE_PLUGIN_REF:-agentix@${MARKETPLACE}}"
  CLIENT_BIN="$(command -v claude || true)"
  agentix_user_home="${HOME:-}"
  CACHE_ROOT="${AGENTIX_PLUGIN_CACHE_ROOT:-${agentix_user_home}/.cache/agentix-plugin}"
fi

STAMP="${CACHE_ROOT}/last-update"
LOCK_DIR="${CACHE_ROOT}/update.lock"
LOG="${CACHE_ROOT}/update.log"
DEBOUNCE_SEC="${AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC:-14400}"
MAX_LOG_BYTES="${AGENTIX_PLUGIN_AUTO_UPDATE_LOG_BYTES:-65536}"
LOCK_STALE_SEC=120

[ -n "$CACHE_ROOT" ] || exit 0
case "$DEBOUNCE_SEC" in *[!0-9]* | "") DEBOUNCE_SEC=14400 ;; esac
case "$MAX_LOG_BYTES" in *[!0-9]* | "") MAX_LOG_BYTES=65536 ;; esac
[ "$MAX_LOG_BYTES" -ge 4096 ] || MAX_LOG_BYTES=4096

[ -n "$CLIENT_BIN" ] && [ -x "$CLIENT_BIN" ] || exit 0

if [ "$CLIENT" = "claude" ]; then
  INSTALLED_JSON="${AGENTIX_PLUGIN_CLAUDE_INSTALL_JSON:-${agentix_user_home}/.claude/plugins/installed_plugins.json}"
  [ -f "$INSTALLED_JSON" ] || exit 0
  python3 - "$INSTALLED_JSON" "$PLUGIN_REF" <<'PY' >/dev/null 2>&1 || exit 0
import json
import sys

path, plugin_ref = sys.argv[1:]
with open(path, encoding="utf-8") as source:
    plugins = json.load(source).get("plugins", {})
raise SystemExit(0 if plugin_ref in plugins else 1)
PY
fi

mkdir -p "$CACHE_ROOT"
chmod 700 "$CACHE_ROOT" 2>/dev/null || true

mtime() {
  if [ "$(uname)" = "Darwin" ]; then
    stat -f %m "$1" 2>/dev/null || printf '0\n'
  else
    stat -c %Y "$1" 2>/dev/null || printf '0\n'
  fi
}

now="$(date +%s)"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  lock_age=$((now - $(mtime "$LOCK_DIR")))
  [ "$lock_age" -ge "$LOCK_STALE_SEC" ] || exit 0
  rmdir "$LOCK_DIR" 2>/dev/null || exit 0
  mkdir "$LOCK_DIR" 2>/dev/null || exit 0
fi
# shellcheck disable=SC2329 # invoked through the EXIT/HUP/INT/TERM trap below
release_lock() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
trap 'release_lock' EXIT HUP INT TERM

# The debounce check is inside the lock so concurrent SessionStart hooks cannot
# both pass it. The stamp is replaced atomically after an attempted update.
if [ -f "$STAMP" ]; then
  age=$((now - $(mtime "$STAMP")))
  [ "$age" -ge "$DEBOUNCE_SEC" ] || exit 0
fi

{
  printf '%s\n' "--- $(date -u '+%Y-%m-%dT%H:%M:%SZ') ---"
  if [ "$CLIENT" = "codex" ]; then
    "$CLIENT_BIN" plugin marketplace upgrade "$MARKETPLACE" 2>&1 | sed 's/^/  /' || true
    printf '  reinstalling %s\n' "$PLUGIN_REF"
    "$CLIENT_BIN" plugin add "$PLUGIN_REF" 2>&1 | sed 's/^/    /' || true
  else
    "$CLIENT_BIN" plugin marketplace update "$MARKETPLACE" 2>&1 | sed 's/^/  /' || true
    printf '  updating %s\n' "$PLUGIN_REF"
    "$CLIENT_BIN" plugin update "$PLUGIN_REF" 2>&1 | sed 's/^/    /' || true
  fi
} >> "$LOG" 2>&1
chmod 600 "$LOG" 2>/dev/null || true

stamp_tmp="${STAMP}.$$"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$stamp_tmp"
mv -f "$stamp_tmp" "$STAMP"
chmod 600 "$STAMP" 2>/dev/null || true

log_size="$(wc -c < "$LOG" | tr -d ' ')"
if [ "$log_size" -gt "$MAX_LOG_BYTES" ]; then
  log_tmp="${LOG}.$$"
  tail -c "$MAX_LOG_BYTES" "$LOG" > "$log_tmp"
  chmod 600 "$log_tmp" 2>/dev/null || true
  mv -f "$log_tmp" "$LOG"
fi

exit 0
