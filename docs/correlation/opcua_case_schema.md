# OPC UA Case Schema

## Purpose

This document defines the first minimal case object for the OT/SOC MVP. It turns separate Wazuh alerts into one analyst-readable OT operation case.

## Required Evidence

| Evidence | Rule |
|---|---|
| Process value or selected OT tag evidence | 110103 / 110200 / 110201 / 110202 / 110203 / 110204 |
| Network flow evidence | 110104 |

## Optional Evidence

| Evidence | Rule |
|---|---|
| Server-side KEPServerEX diagnostic evidence | 110105 |

## Classification

| Classification | Meaning |
|---|---|
| validation_not_malicious | Visibility event only |
| important_ot_operation | Important process/command context |
| suspicious_ot_operation | Critical command or repeated failure evidence |

## Example Case

```json
{
  "case_type": "confirmed_opcua_operation",
  "classification": "suspicious_ot_operation",
  "tag": "MOTOR1",
  "rule_ids": ["110104", "110202"],
  "evidence": [
    {
      "source": "passive_opcua_monitor"
    },
    {
      "source": "suricata_network_flow"
    }
  ]
}
eof
