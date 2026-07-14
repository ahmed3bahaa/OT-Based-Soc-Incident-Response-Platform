#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${OT_SOC_REPO_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
OPCUA_CLIENT_DIR="${OPCUA_CLIENT_DIR:-$REPO_ROOT/opcua-client}"
SCENARIO_ID="${OPCUA_MONITOR_SCENARIO_ID:-uaexpert-live-test}"
INTERVAL_MS="${OPCUA_MONITOR_INTERVAL_MS:-1000}"
LOG_FILE="${OPCUA_MONITOR_AUTOMATION_LOG:-$OPCUA_CLIENT_DIR/logs/opcua_monitor_automation.out}"
PID_FILE="${OPCUA_MONITOR_PID_FILE:-$OPCUA_CLIENT_DIR/logs/opcua_monitor.pid}"
PYTHON_BIN="${PYTHON:-python}"

cd "$OPCUA_CLIENT_DIR"
mkdir -p logs

if [ -f "$PID_FILE" ]; then
  existing_pid="$(cat "$PID_FILE")"
  if [ -n "$existing_pid" ] && kill -0 "$existing_pid" >/dev/null 2>&1; then
    echo "[ubuntu-monitor] OPC UA monitor already running PID=$existing_pid"
    exit 0
  fi
fi

if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

if [ ! -f ".env" ]; then
  echo "[ubuntu-monitor] Warning: opcua-client/.env is missing. Copy .env.example to .env and set OPC UA credentials if KEPServerEX requires them." >&2
fi

nohup "$PYTHON_BIN" src/opcua_monitor.py \
  --all-simulator-tags \
  --scenario-id "$SCENARIO_ID" \
  --interval-ms "$INTERVAL_MS" \
  > "$LOG_FILE" 2>&1 &

pid="$!"
echo "$pid" > "$PID_FILE"

echo "[ubuntu-monitor] Started OPC UA monitor PID=$pid"
echo "[ubuntu-monitor] Log: $LOG_FILE"
echo "[ubuntu-monitor] Tags: DEBI, MOTOR1, MOTOR2, SAMANDIRA, SU_SEVIYESI, ScenarioID, VALF"
