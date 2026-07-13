# DevSecOps Lifecycle

## Current Scope

The project now has a practical MVP DevSecOps loop:

```text
code change
-> tests and config validation
-> dependency/security scans
-> Docker compose validation
-> review
-> lab deployment
```

## Implemented Controls

- Django system checks, migration checks, and backend tests.
- Repository validation tests for Wazuh XML, Vector config, Docker Compose, fixtures, and correlation behavior.
- OPC UA client `ruff` and `pytest`.
- Frontend `eslint` and production build.
- OpenAPI schema generation and endpoint validation.
- Docker Compose stack for frontend, backend, and PostgreSQL.
- Gitleaks secret scanning.
- Python static analysis with Bandit.
- Python dependency audit with `pip-audit`.
- Frontend dependency audit with `npm audit --audit-level=high`.
- Dependabot configuration for backend, OPC UA client, frontend, and GitHub Actions.

## Pipeline Files

```text
.github/workflows/ci.yml
.github/workflows/security.yml
.github/dependabot.yml
.gitleaks.toml
scripts/validate-ci.sh
scripts/validate-local.ps1
```

## OT-Specific Validation

The repository validation tests protect the OT detection contract:

- required Wazuh rule IDs stay present
- Vector sends OT alerts to Django live ingestion
- Docker frontend uses the backend service URL internally
- correlation fixtures keep the minimal case schema
- process evidence still requires Suricata flow confirmation

## Coming Phases

Next DevSecOps improvements should be added when those product features exist:

- evidence hashing and chain-of-custody checks
- case lifecycle audit trail tests
- production deployment hardening checks
- stricter PostgreSQL-only deployment gate
- image vulnerability scanning
- signed release artifacts
- backup and restore validation

The project should stay human-reviewed. DevSecOps should prevent unsafe changes
and catch regressions; it should not introduce auto-response or SOAR behavior.
