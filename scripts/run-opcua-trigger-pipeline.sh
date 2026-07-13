#!/usr/bin/env bash
set -euo pipefail

cd /home/ahmed_bahaa/ot-project/opcua-client
source .venv/bin/activate

exec python src/opcua_monitor.py \
  --all-simulator-tags \
  --scenario-id "simulator-mvp-live" \
  --interval-ms 1000
