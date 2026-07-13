#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export OT_SOC_SKIP_DOTENV=1

echo "[validate] Installing backend validation dependencies"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt pytest
python -m pip install bandit pip-audit

echo "[validate] Django checks, migrations, and tests"
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test soc

echo "[validate] Repository validation tests"
PYTHONPATH="$ROOT_DIR" python -m pytest tests

echo "[validate] OPC UA client lint and tests"
(
  cd opcua-client
  python -m pip install -r requirements-dev.txt
  ruff check src tests
  pytest
)

echo "[validate] Frontend lint and build"
(
  cd frontend
  npm ci
  npm run lint
  npm run build
)

echo "[validate] Docker Compose config"
docker compose config >/dev/null

echo "[validate] Python static analysis"
python -m bandit -r backend correlation opcua-client/src \
  -x "backend/.venv,opcua-client/.venv,backend/soc/tests.py,opcua-client/tests" \
  -ll

echo "[validate] Python dependency audits"
python -m pip_audit -r backend/requirements.txt --progress-spinner off
python -m pip_audit -r opcua-client/requirements.txt --progress-spinner off

echo "[validate] Complete"
