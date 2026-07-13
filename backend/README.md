# OT SOC Backend MVP

Minimal Django REST backend for importing correlated OPC UA case JSON and exposing it to a future Next.js SOC dashboard.

This backend can still import committed correlation fixtures, and it now also accepts live Wazuh/Vector alert payloads for immediate backend-side correlation.

The current live MVP path also supports Wazuh/Vector alert ingestion. Incoming alerts are stored in a rolling live-alert buffer, correlated immediately, and imported as `confirmed_opcua_operation` cases when process evidence and Suricata flow evidence match within the configured window.

## Setup

From the repository root on Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_catalogs
python manage.py import_opcua_cases --file ..\tests\fixtures\correlation\opcua_cases_valf.json
python manage.py runserver
```

If the Windows `py` launcher is installed, `py -3 -m venv .venv` can be used instead of `python -m venv .venv`.

## API

```text
GET  /api/health/
GET  /api/summary/
GET  /api/cases/
GET  /api/cases/{id}/
GET  /api/evidence/
GET  /api/live-alerts/
GET  /api/rules/
GET  /api/tags/
GET  /api/assets/
POST /api/cases/import/
POST /api/ingest/wazuh-alerts/
POST /api/ingest/vector-alerts/
```

List endpoints are paginated:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": []
}
```

Useful query parameters:

```text
GET /api/cases/?classification=suspicious_ot_operation
GET /api/cases/?tag=VALF
GET /api/cases/?rule_id=110203
GET /api/cases/?search=valve
GET /api/cases/?ordering=-created_at_from_case
GET /api/evidence/?rule_id=110104
GET /api/live-alerts/?rule_id=110203
GET /api/rules/?classification_hint=suspicious_ot_operation
GET /api/tags/?is_writable=true
GET /api/assets/?platform=Windows
```

## Swagger / OpenAPI

```text
GET /api/schema/
GET /api/docs/
```

Open `http://127.0.0.1:8000/api/docs/` after starting the server to view the Swagger UI.

## Import Contract

The import command accepts a JSON object or list shaped like the output of:

```text
correlation/opcua_case_correlator.py
```

Duplicate imports are skipped using a deterministic case fingerprint based on the correlated case fields and evidence references.

Malformed payloads are rejected before database writes and return an `errors` array from the API.

## Live Ingestion

The live ingestion API accepts a single Wazuh alert, a list of alerts, a Vector wrapper such as `{"events": [...]}`, or an OpenSearch/Wazuh Indexer response with `hits.hits`.

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/ingest/wazuh-alerts/?window_seconds=900" `
  -ContentType application/json `
  -InFile .\wazuh-alerts-batch.json
```

Automatic file watcher on the Wazuh manager:

```powershell
python manage.py watch_wazuh_alerts --file /var/ossec/logs/alerts/alerts.json --wait
```

Backfill or test once from an existing file:

```powershell
python manage.py watch_wazuh_alerts --file .\alerts.json --from-start --once --window-seconds 60
```

Poll a Wazuh Indexer/OpenSearch alerts endpoint:

```powershell
$env:WAZUH_INDEXER_ALERTS_URL="https://<WAZUH_INDEXER_IP>:9200/wazuh-alerts-*/_search"
$env:WAZUH_API_USERNAME="<INDEXER_USER>"
$env:WAZUH_API_PASSWORD="<INDEXER_PASSWORD>"
$env:WAZUH_API_INSECURE="true"
python manage.py poll_wazuh_alerts
```

The poller can also use `WAZUH_ALERTS_URL`, `WAZUH_API_TOKEN`, `WAZUH_ALERTS_METHOD`, `WAZUH_ALERTS_BODY`, `WAZUH_ALERTS_SIZE`, and `WAZUH_ALERTS_LOOKBACK_SECONDS`.

When running with Docker Compose, put these values in the repository root `.env` file
and start the optional poller profile:

```powershell
docker compose --profile wazuh-poller up -d wazuh-poller
```

Vector can send matching Wazuh alerts directly to Django using:

```text
../vector/django-live-ingest.toml
```

## Management Commands

```powershell
python manage.py seed_catalogs
python manage.py import_opcua_cases --file ..\tests\fixtures\correlation\opcua_cases_valf.json
python manage.py import_opcua_cases --file ..\tests\fixtures\correlation\opcua_cases_mixed.json
python manage.py watch_wazuh_alerts --file /var/ossec/logs/alerts/alerts.json --wait
python manage.py poll_wazuh_alerts --url https://127.0.0.1:9200/wazuh-alerts-*/_search --insecure
```

`seed_catalogs` creates or updates the MVP rule, tag, and asset catalogs. The import command also calls the same seed step as a convenience.

## Environment Settings

The local defaults are development-friendly. Override these when needed:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CORS_ALLOWED_ORIGINS
DATABASE_URL
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
WAZUH_ALERTS_URL
WAZUH_INDEXER_ALERTS_URL
WAZUH_API_USERNAME
WAZUH_API_PASSWORD
WAZUH_API_TOKEN
```

Comma-separate list values, for example:

```powershell
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
$env:DJANGO_CORS_ALLOWED_ORIGINS="http://127.0.0.1:3000,http://localhost:3000"
```

PostgreSQL can be enabled with either a URL:

```powershell
$env:DATABASE_URL="postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@127.0.0.1:5434/ot_soc"
python manage.py migrate
```

Or separate variables:

```powershell
$env:POSTGRES_DB="ot_soc"
$env:POSTGRES_USER="<POSTGRES_USER>"
$env:POSTGRES_PASSWORD="<POSTGRES_PASSWORD>"
$env:POSTGRES_HOST="127.0.0.1"
$env:POSTGRES_PORT="5434"
python manage.py migrate
```
