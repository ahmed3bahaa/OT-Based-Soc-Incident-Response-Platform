#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${OT_SOC_REPO_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
OPCUA_CLIENT_DIR="${OPCUA_CLIENT_DIR:-$REPO_ROOT/opcua-client}"
LOG_FILE="${OPCUA_MONITOR_AUTOMATION_LOG:-$OPCUA_CLIENT_DIR/logs/opcua_monitor_automation.out}"
PID_FILE="${OPCUA_MONITOR_PID_FILE:-$OPCUA_CLIENT_DIR/logs/opcua_monitor.pid}"

echo "[ubuntu-monitor] OPC UA client dir: $OPCUA_CLIENT_DIR"

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE")"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "[ubuntu-monitor] Running PID=$pid"
  else
    echo "[ubuntu-monitor] PID file exists, but process is not running."
  fi
else
  echo "[ubuntu-monitor] No PID file found."
fi

if pgrep -af "src/opcua_monitor.py.*--all-simulator-tags" >/dev/null 2>&1; then
  echo "[ubuntu-monitor] Matching monitor process:"
  pgrep -af "src/opcua_monitor.py.*--all-simulator-tags"
else
  echo "[ubuntu-monitor] No matching monitor process found."
fi

if [ -f "$OPCUA_CLIENT_DIR/.env" ]; then
  endpoint="$(grep -E '^OPCUA_ENDPOINT=' "$OPCUA_CLIENT_DIR/.env" | tail -n 1 | cut -d= -f2- | sed 's/^"//; s/"$//')"
  username_set="no"
  password_set="no"
  if grep -Eq '^OPCUA_USERNAME=.+$' "$OPCUA_CLIENT_DIR/.env"; then
    username_set="yes"
  fi
  if grep -Eq '^OPCUA_PASSWORD=.+$' "$OPCUA_CLIENT_DIR/.env"; then
    password_set="yes"
  fi
  echo "[ubuntu-monitor] OPCUA_ENDPOINT=${endpoint:-unset}"
  echo "[ubuntu-monitor] OPCUA_USERNAME set: $username_set"
  echo "[ubuntu-monitor] OPCUA_PASSWORD set: $password_set"
else
  echo "[ubuntu-monitor] opcua-client/.env missing."
fi

if [ -f "$LOG_FILE" ]; then
  echo "[ubuntu-monitor] Log: $LOG_FILE"
  echo "[ubuntu-monitor] Last 25 log lines:"
  tail -n 25 "$LOG_FILE"
else
  echo "[ubuntu-monitor] Log file not found: $LOG_FILE"
fi
