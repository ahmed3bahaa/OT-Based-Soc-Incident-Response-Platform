#!/usr/bin/env bash
set -euo pipefail

cd /home/ahmed_bahaa/ot-project/opcua-client
source .venv/bin/activate

exec python src/opcua_monitor.py \
  --node-id "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.SU_SEVIYESI" \
  --scenario-id "simulator-mvp-live" \
  --interval-ms 1000
