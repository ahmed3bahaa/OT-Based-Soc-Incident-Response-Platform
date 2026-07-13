# OT SOC Frontend MVP

Custom Next.js frontend for the OT-Based SOC Incident Response Platform MVP.

The app connects to the Django backend and presents:

- confirmed OPC UA operation cases
- nested evidence timelines
- Wazuh rule catalog context
- OT simulator tag inventory
- MVP lab asset inventory
- dashboard summary counts for analyst triage

## Backend API

Default API base URL:

```text
http://127.0.0.1:8000/api
```

Override when needed:

```powershell
$env:OT_SOC_API_BASE_URL="http://127.0.0.1:8000/api"
$env:NEXT_PUBLIC_OT_SOC_API_BASE_URL="http://127.0.0.1:8000/api"
```

For Docker Compose, the frontend uses the backend service name internally and
the host URL for browser-visible links:

```text
OT_SOC_API_BASE_URL=http://backend:8000/api
NEXT_PUBLIC_OT_SOC_API_BASE_URL=http://127.0.0.1:8000/api
```

## Run Locally

Start the Django backend first:

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py import_opcua_cases --file ..\tests\fixtures\correlation\opcua_cases_mixed.json
python manage.py runserver
```

Then start the frontend:

```powershell
cd ..\frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Routes

```text
/          Command console
/cases     Case triage
/cases/:id Case evidence detail
/rules     Detection rule catalog
/tags      OT tag inventory
/assets    Lab asset map
```

## Scope

This frontend is backend-first and human-review focused. It does not implement authentication, SOAR, auto-response, or AI workflows. It visualizes cases imported or live-correlated by the Django backend and refreshes open pages every five seconds.

## Validation

```powershell
npm run lint
npm run build
```
