# Simulator Path Decision

## Decision

The project attempted to use the real KEPServerEX .opf live. The OPC UA server and namespace could be reached, but the real-device values showed Bad/Unknown/Null quality because the real PLC/RTU devices behind the .opf are not available in the local environment.

Therefore, the project continues with the simulator .opf as the live MVP environment.

## Meaning

The simulator path is not random. It is a small slice inspired by the real .opf structure and is used to prove the minimal OT SOC pipeline.

## Current Live MVP Pipeline

```text
UaExpert GUI change
→ passive OPC UA monitor
→ opcua_monitor.jsonl
→ Wazuh rule 110103

OPC UA network traffic
→ Suricata EVE
→ Windows Wazuh agent
→ Wazuh rule 110104

KEPServer diagnostics
→ normalized JSON spool
→ Wazuh rule 110105
