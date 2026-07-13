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

## Docker MVP Stack

The backend, frontend, and PostgreSQL 18 database can run together with Docker Compose:

```powershell
docker compose up --build
```

Open:

```text
Frontend: http://127.0.0.1:3000
Backend:  http://127.0.0.1:8000/api/
Swagger:  http://127.0.0.1:8000/api/docs/
PostgreSQL for pgAdmin/host tools: 127.0.0.1:5434
```

The frontend container talks to the backend container through:

```text
OT_SOC_API_BASE_URL=http://backend:8000/api
```

Browser-visible API links use:

```text
NEXT_PUBLIC_OT_SOC_API_BASE_URL=http://127.0.0.1:8000/api
```

PostgreSQL 18 uses the `postgres18-data` Docker volume mounted at:

```text
/var/lib/postgresql
```

The PostgreSQL container still listens on `5432` inside Docker, but Docker exposes
it to Windows on `5434`. Use `127.0.0.1:5434` from pgAdmin or local scripts.
This avoids collisions with a local PostgreSQL service already listening on `5433`.

If an older PostgreSQL volume was created with the previous `/var/lib/postgresql/data`
mount, recreate the stack with the PostgreSQL 18 layout:

```powershell
docker compose down
docker compose up --build
```

Use `docker compose down -v` only when you intentionally want to delete disposable
lab database data and let Django rebuild the schema from migrations.

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

- Secure Python OPC UA scenario client and passive monitor.
- OPC UA operation JSON logging.
- Suricata network-flow collection.
- Wazuh ingestion verification for process and network evidence.
- Environment-specific Wazuh OT simulator rules.
- Correlation script for `confirmed_opcua_operation` case JSON.
- Django REST backend for cases, evidence, rules, tags, assets, Swagger, and live alert ingestion.
- Backend-side live Wazuh/Vector alert correlation with a file watcher and configurable Wazuh/Indexer API poller.
- SQLite local database with PostgreSQL environment configuration.
- Next.js SOC dashboard for imported/live correlated cases.
- Vector HTTP sink example for sending Wazuh alerts into Django.

Not yet implemented:

- Production deployment packaging.
- Full analyst case lifecycle, notes, evidence hashing, and approval workflow.
- Advanced OT risk scoring beyond the current explainable rule-based classification.
- Production-grade image hardening and release signing.

## Validation

Local full validation:

```powershell
.\scripts\validate-local.ps1
```

Linux/CI validation:

```bash
./scripts/validate-ci.sh
```

The CI pipeline covers Django tests, repository validation, OPC UA client tests,
frontend lint/build, OpenAPI validation, Docker Compose validation, dependency
audits, and secret scanning.

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
