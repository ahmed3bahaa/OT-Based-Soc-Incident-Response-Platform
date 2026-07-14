#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${OT_SOC_REPO_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
OPCUA_CLIENT_DIR="${OPCUA_CLIENT_DIR:-$REPO_ROOT/opcua-client}"
SCENARIO_ID="${OPCUA_MONITOR_SCENARIO_ID:-simulator-mvp-live}"
INTERVAL_MS="${OPCUA_MONITOR_INTERVAL_MS:-1000}"
PYTHON_BIN="${PYTHON:-python}"

cd "$OPCUA_CLIENT_DIR"

if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" src/opcua_monitor.py \
  --all-simulator-tags \
  --scenario-id "$SCENARIO_ID" \
  --interval-ms "$INTERVAL_MS"
