# OT SOC Backend MVP

Minimal Django REST backend for importing correlated OPC UA case JSON and exposing it to a future Next.js SOC dashboard.

This backend starts from the committed correlation fixture. It does not read live Wazuh alerts, Suricata EVE logs, or OPC UA monitor JSONL.

## Setup

From the repository root on Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py import_opcua_cases --file ..\tests\fixtures\correlation\opcua_cases_valf.json
python manage.py runserver
```

If the Windows `py` launcher is installed, `py -3 -m venv .venv` can be used instead of `python -m venv .venv`.

## API

```text
GET  /api/health/
GET  /api/cases/
GET  /api/cases/{id}/
GET  /api/evidence/
GET  /api/rules/
GET  /api/tags/
GET  /api/assets/
POST /api/cases/import/
```

## Import Contract

The import command accepts a JSON object or list shaped like the output of:

```text
correlation/opcua_case_correlator.py
```

Duplicate imports are skipped using a deterministic case fingerprint based on the correlated case fields and evidence references.
