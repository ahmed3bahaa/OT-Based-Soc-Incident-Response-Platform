# GUI-Triggered OPC UA Telemetry Pipeline

## Purpose

This document records the automated telemetry pipeline triggered by changing an OPC UA value from UaExpert GUI.

This pipeline is validation-level OT visibility. It does not classify a successful OPC UA value change as malicious.

## Trigger

The operator changes the value of:

```text
ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.SU_SEVIYESI
