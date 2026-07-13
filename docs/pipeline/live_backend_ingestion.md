# Live Backend Ingestion

## Goal

Cases should appear in the backend and frontend without manually running the correlation script or import command after every test.

## Current Live MVP Flow

```text
Wazuh alert or Vector event
-> Django live ingest endpoint
-> LiveAlert buffer
-> backend correlation window
-> confirmed_opcua_operation Case
-> frontend auto-refresh
```

The backend still requires both sides of evidence before creating a confirmed case:

- OPC UA process/tag rule: `110103`, `110200`, `110201`, `110202`, `110203`, `110204`, or `110205`
- Suricata network-flow rule: `110104`

Optional diagnostic evidence:

- KEPServerEX diagnostic rule: `110105`

## HTTP Endpoints

```text
POST /api/ingest/wazuh-alerts/
POST /api/ingest/vector-alerts/
GET  /api/live-alerts/
GET  /api/cases/
```

The POST endpoints accept:

- one alert object
- a JSON array of alerts
- `{"events": [...]}`
- `{"alerts": [...]}`
- OpenSearch/Wazuh Indexer response shape with `hits.hits`

## File Watcher

On the Wazuh manager:

```bash
python manage.py watch_wazuh_alerts \
  --file /var/ossec/logs/alerts/alerts.json \
  --wait \
  --window-seconds 900
```

For a one-time local backfill:

```bash
python manage.py watch_wazuh_alerts \
  --file ./alerts.json \
  --from-start \
  --once \
  --window-seconds 60
```

## Wazuh / Indexer API Polling

```bash
export WAZUH_INDEXER_ALERTS_URL="https://127.0.0.1:9200/wazuh-alerts-*/_search"
export WAZUH_API_USERNAME="admin"
export WAZUH_API_PASSWORD="admin"
python manage.py poll_wazuh_alerts --insecure
```

The poller fetches matching rule IDs and sends them through the same live correlation service.

## Vector

Use:

```text
vector/django-live-ingest.toml
```

It tails Wazuh `alerts.json`, filters the OT rule IDs, and posts them to:

```text
http://127.0.0.1:8000/api/ingest/vector-alerts/
```

## PostgreSQL 18

SQLite remains the default. Docker Compose uses PostgreSQL 18. PostgreSQL is enabled by setting either:

```text
DATABASE_URL=postgresql://ot_soc:ot_soc@127.0.0.1:5434/ot_soc
```

Or:

```text
POSTGRES_DB=ot_soc
POSTGRES_USER=ot_soc
POSTGRES_PASSWORD=ot_soc
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5434
```

Then run:

```bash
python manage.py migrate
```

When changing a local Docker volume from an older PostgreSQL major version to PostgreSQL 18, do not reuse the old `/var/lib/postgresql/data` mount directly. PostgreSQL 18 Docker images expect the volume to be mounted at `/var/lib/postgresql`, with the actual database stored in a major-version-specific subdirectory. This project uses the `postgres18-data` volume and lets Django rebuild the schema with migrations. For data you need to keep, use a proper dump/restore or major-version upgrade process.

For host tools such as pgAdmin, connect to `127.0.0.1:5434`. Inside Docker, the backend still uses `db:5432`.
The Docker host port is intentionally `5434` to avoid colliding with a local PostgreSQL service already bound to `5433`.
