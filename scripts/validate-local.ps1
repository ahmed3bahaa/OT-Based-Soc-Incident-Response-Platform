$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:PYTHONIOENCODING = "utf-8"
$env:OT_SOC_SKIP_DOTENV = "1"

Write-Host "[validate] Installing backend validation dependencies"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt pytest
python -m pip install bandit pip-audit

Write-Host "[validate] Django checks, migrations, and tests"
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test soc

Write-Host "[validate] Repository validation tests"
$env:PYTHONPATH = $Root
python -m pytest tests

Write-Host "[validate] OPC UA client lint and tests"
Push-Location opcua-client
python -m pip install -r requirements-dev.txt
ruff check src tests
pytest
Pop-Location

Write-Host "[validate] Frontend lint and build"
Push-Location frontend
npm ci
npm run lint
npm run build
Pop-Location

Write-Host "[validate] Docker Compose config"
docker compose config | Out-Null

Write-Host "[validate] Python static analysis"
python -m bandit -r backend correlation opcua-client/src `
  -x "backend/.venv,opcua-client/.venv,backend/soc/tests.py,opcua-client/tests" `
  -ll

Write-Host "[validate] Python dependency audits"
python -m pip_audit -r backend/requirements.txt --progress-spinner off
python -m pip_audit -r opcua-client/requirements.txt --progress-spinner off

Write-Host "[validate] Complete"
