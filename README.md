# OT/ICS Incident Response Platform

A human-supervised incident-response proof of concept for a simulated water-management OT environment.

The project is inspired by the CENTER Water testbed at Sakarya University. The current local environment is a controlled simulation and does not reproduce the complete physical CENTER topology, real PLC/RTU behavior, vendor-specific timing, or real physical water-process effects.

## Objective

The platform is designed to:

1. Collect network and process-operation evidence.
2. Send events to Wazuh.
3. Normalize Wazuh alerts through Vector.
4. Send normalized events to Django REST Framework.
5. Enrich events with OT asset, tag, authorization, maintenance-window, and criticality context.
6. Calculate explainable risk.
7. Create incidents and select response playbooks.
8. Require human approval before containment.
9. Preserve evidence hashes and an audit timeline.
10. Display incidents in a Next.js SOC dashboard.

Wazuh handles collection, decoding, basic detection, and alert generation.

Django will handle deeper OT context, correlation, noise reduction, risk scoring, incident creation, approval workflows, and evidence management.

## Planned Data Flow

Python OPC UA client and UaExpert
→ Secure OPC UA connection
→ KEPServerEX Simulator
→ Suricata network evidence and Python operation JSON
→ Wazuh
→ Vector
→ Django REST Framework and PostgreSQL
→ Next.js SOC Dashboard

## Current Verified Milestones

- Secure OPC UA communication using Basic256Sha256 with Sign and Encrypt.
- Controlled OPC UA write scenarios with read-before-write verification.
- JSON Lines operation logging.
- Suricata capture on the VirtualBox Host-Only adapter.
- Windows Wazuh agent collection of Suricata EVE JSON.
- Ubuntu Wazuh manager collection of OPC UA operation JSON.
- End-to-end verification of both:
  - Suricata network-flow evidence.
  - Python process-operation evidence.

## Repository Structure

- `opcua-client/` — Secure OPC UA scenario client and logging.
- `suricata/` — Rules and sanitized configuration templates.
- `wazuh/` — OT rules, decoders, and configuration templates.
- `vector/` — Event normalization configuration.
- `backend/` — Django REST Framework backend.
- `frontend/` — Next.js SOC dashboard.
- `scripts/` — Supporting automation scripts.
- `tests/` — Unit and integration tests.
- `docs/` — Architecture, methodology, and operational documentation.
- `.github/workflows/` — CI security and quality gates.

## Current Development Status

Implemented:

- Secure Python OPC UA scenario client.
- OPC UA operation JSON logger.
- Suricata network-flow collection.
- Wazuh ingestion verification for both evidence sources.

Not yet implemented:

- Environment-specific Wazuh OT rules.
- Vector normalization.
- Django REST ingestion.
- PostgreSQL models.
- Asset and tag enrichment.
- Explainable risk scoring.
- Incident approval workflow.
- Next.js SOC dashboard.
- Docker Compose deployment.
- CI/CD security gates.

## Repository Security

The repository must not contain:

- `.env` files containing secrets.
- Private keys or runtime certificates.
- Runtime JSONL, EVE, archive, or application logs.
- PCAP or PCAPNG captures.
- KEPServer diagnostic files.
- Wazuh credentials or API tokens.
- Database runtime data.
- Sensitive infrastructure inventories.

Only sanitized templates, source code, documentation, tests, rules, and decoders should be committed.

## Limitations

The current simulation does not reproduce:

- Real PLC or RTU behavior.
- Real physical water-process effects.
- Vendor-specific timing and failures.
- Native Modbus, S7, DNP3, or EtherCAT field traffic.
- The complete CENTER Water topology.

The downstream architecture is intended to remain compatible with later integration into the physical testbed.
