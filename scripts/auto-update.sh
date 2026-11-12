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

DEBOUNCE_SEC="${AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC:-14400}"
MAX_LOG_BYTES="${AGENTIX_PLUGIN_AUTO_UPDATE_LOG_BYTES:-65536}"

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

# Python is already used for package validation. Skip optional updates when it
# is unavailable; never fall back to an unprotected updater.
command -v python3 >/dev/null 2>&1 || exit 0
exec python3 "$(dirname "${BASH_SOURCE[0]}")/auto-update.py" \
  "$CACHE_ROOT" "$CLIENT" "$CLIENT_BIN" "$MARKETPLACE" "$PLUGIN_REF" \
  "$DEBOUNCE_SEC" "$MAX_LOG_BYTES"
