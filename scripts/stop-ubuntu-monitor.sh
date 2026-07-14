#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${OT_SOC_REPO_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
OPCUA_CLIENT_DIR="${OPCUA_CLIENT_DIR:-$REPO_ROOT/opcua-client}"
PID_FILE="${OPCUA_MONITOR_PID_FILE:-$OPCUA_CLIENT_DIR/logs/opcua_monitor.pid}"

stopped="false"

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE")"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "[ubuntu-monitor] Stopping PID=$pid"
    kill "$pid"
    stopped="true"
  fi
  rm -f "$PID_FILE"
fi

matching_pids="$(pgrep -f "src/opcua_monitor.py.*--all-simulator-tags" || true)"
if [ -n "$matching_pids" ]; then
  echo "[ubuntu-monitor] Stopping matching monitor processes: $matching_pids"
  # shellcheck disable=SC2086
  kill $matching_pids || true
  stopped="true"
fi

if [ "$stopped" = "true" ]; then
  echo "[ubuntu-monitor] Stop requested."
else
  echo "[ubuntu-monitor] No running OPC UA monitor found."
fi
