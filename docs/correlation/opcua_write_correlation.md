# OPC UA Write Correlation Design

## Purpose

This document defines the first validation-level correlation model for confirmed OPC UA write activity in the OT water/process lab.

The purpose is not to classify every successful OPC UA write as malicious. A successful write may be normal engineering, HMI, SCADA, or testbed activity. The goal is to combine multiple evidence sources into one confirmed OT operation event that can later be used by the incident-response/case layer.

## Current Evidence Sources

### Rule 110103 — Passive OPC UA Datachange Observed

Source: secure passive OPC UA monitor.

Meaning: the monitored process tag value changed.

Current monitored node:

```text
ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.SU_SEVIYESI
