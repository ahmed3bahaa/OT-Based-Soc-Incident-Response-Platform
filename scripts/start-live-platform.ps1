param(
    [switch]$NoBuild,
    [switch]$SkipSuricata,
    [switch]$SkipPoller,
    [switch]$SkipKepServerCheck,
    [switch]$SkipHealthCheck,
    [switch]$StartUbuntuMonitor,
    [string]$KepServerHost = $(if ($env:LAB_KEPSERVER_HOST) { $env:LAB_KEPSERVER_HOST } else { "127.0.0.1" }),
    [int]$KepServerPort = $(if ($env:LAB_KEPSERVER_PORT) { [int]$env:LAB_KEPSERVER_PORT } else { 49320 }),
    [string]$UbuntuHost = $env:LAB_UBUNTU_HOST,
    [string]$UbuntuUser = $env:LAB_UBUNTU_USER,
    [string]$UbuntuOpcuaClientDir = $(if ($env:LAB_UBUNTU_OPCUA_CLIENT_DIR) { $env:LAB_UBUNTU_OPCUA_CLIENT_DIR } else { "~/ot-project/opcua-client" }),
    [string]$SshKeyPath = $env:LAB_UBUNTU_SSH_KEY,
    [string]$ScenarioId = $(if ($env:LAB_MONITOR_SCENARIO_ID) { $env:LAB_MONITOR_SCENARIO_ID } else { "uaexpert-live-test" }),
    [int]$IntervalMs = $(if ($env:LAB_MONITOR_INTERVAL_MS) { [int]$env:LAB_MONITOR_INTERVAL_MS } else { 1000 }),
    [int]$HealthTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SuricataScript = Join-Path $Root "suricata\scripts\start-suricata-flow-proof.ps1"

Set-Location $Root

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

function Get-DotEnvValue {
    param([string]$Name)

    $EnvPath = Join-Path $Root ".env"
    if (-not (Test-Path $EnvPath)) {
        return $null
    }

    $Match = Get-Content $EnvPath |
        Where-Object { $_ -match "^\s*$Name\s*=" -and $_ -notmatch "^\s*#" } |
        Select-Object -Last 1

    if (-not $Match) {
        return $null
    }

    return ($Match -replace "^\s*$Name\s*=", "").Trim().Trim('"').Trim("'")
}

function Invoke-DockerComposeUp {
    param(
        [string[]]$Services,
        [switch]$WithWazuhProfile
    )

    $Args = @("compose")
    if ($WithWazuhProfile) {
        $Args += @("--profile", "wazuh-poller")
    }

    $Args += @("up", "-d")
    if (-not $NoBuild) {
        $Args += "--build"
    }

    $Args += $Services

    Write-Host "[live-start] docker $($Args -join ' ')"
    & docker @Args
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose failed for services: $($Services -join ', ')"
    }
}

function Wait-HttpEndpoint {
    param(
        [string]$Url,
        [int]$TimeoutSeconds
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
                Write-Host "[live-start] Ready: $Url"
                return
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }

    throw "Timed out waiting for $Url"
}

function Start-UbuntuOpcuaMonitor {
    if (-not $UbuntuHost -or -not $UbuntuUser) {
        throw "Set LAB_UBUNTU_HOST and LAB_UBUNTU_USER, or pass -UbuntuHost and -UbuntuUser."
    }

    Require-Command ssh

$RemoteScript = @'
set -e
cd "__OPCUA_CLIENT_DIR__"
if [ -x "../scripts/start-ubuntu-monitor.sh" ]; then
  OPCUA_CLIENT_DIR="$PWD" \
  OPCUA_MONITOR_SCENARIO_ID="__SCENARIO_ID__" \
  OPCUA_MONITOR_INTERVAL_MS=__INTERVAL_MS__ \
  "../scripts/start-ubuntu-monitor.sh"
  exit 0
fi
if [ -d ".venv" ]; then
  . .venv/bin/activate
fi
PYTHON_BIN="${PYTHON:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
mkdir -p logs
if pgrep -f "src/opcua_monitor.py.*--all-simulator-tags" >/dev/null 2>&1; then
  echo "OPC UA monitor already running"
else
  nohup "$PYTHON_BIN" src/opcua_monitor.py --all-simulator-tags --scenario-id "__SCENARIO_ID__" --interval-ms __INTERVAL_MS__ > logs/opcua_monitor_automation.out 2>&1 &
  echo "Started OPC UA monitor PID=$!"
fi
'@

    $RemoteScript = $RemoteScript.
        Replace("__OPCUA_CLIENT_DIR__", $UbuntuOpcuaClientDir).
        Replace("__SCENARIO_ID__", $ScenarioId).
        Replace("__INTERVAL_MS__", [string]$IntervalMs)

    $EncodedScript = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($RemoteScript.Replace("`r`n", "`n")))
    $RemoteCommand = "printf '%s' '$EncodedScript' | base64 -d | bash"
    $Target = "$UbuntuUser@$UbuntuHost"
    $SshArgs = @()
    if ($SshKeyPath) {
        $SshArgs += @("-i", $SshKeyPath)
    }
    $SshArgs += @($Target, $RemoteCommand)

    Write-Host "[live-start] Starting Ubuntu OPC UA monitor on $Target"
    & ssh @SshArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start Ubuntu OPC UA monitor over SSH."
    }
}

Require-Command docker

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Warning "No .env file found. Docker Compose will use defaults. Copy .env.example to .env for Wazuh/PostgreSQL credentials."
}

if (-not $SkipPoller) {
    $WazuhUrl = if ($env:WAZUH_INDEXER_ALERTS_URL) { $env:WAZUH_INDEXER_ALERTS_URL } else { Get-DotEnvValue "WAZUH_INDEXER_ALERTS_URL" }
    if (-not $WazuhUrl -or $WazuhUrl -match "<") {
        Write-Warning "WAZUH_INDEXER_ALERTS_URL is empty or still a placeholder. The wazuh-poller service will start, but it cannot ingest real alerts until .env is configured."
    }
}

if (-not $SkipKepServerCheck) {
    Write-Host "[live-start] Checking KEPServerEX OPC UA endpoint $KepServerHost`:$KepServerPort"
    $KepReady = Test-NetConnection -ComputerName $KepServerHost -Port $KepServerPort -InformationLevel Quiet -WarningAction SilentlyContinue
    if (-not $KepReady) {
        Write-Warning "KEPServerEX was not reachable at $KepServerHost`:$KepServerPort. Start/configure it before changing tags in UaExpert."
    }
}

Invoke-DockerComposeUp -Services @("db", "backend", "frontend")

if (-not $SkipPoller) {
    Invoke-DockerComposeUp -Services @("wazuh-poller") -WithWazuhProfile
}

if (-not $SkipSuricata) {
    if (-not (Test-Path $SuricataScript)) {
        throw "Suricata startup script not found: $SuricataScript"
    }

    Write-Host "[live-start] Starting Suricata flow proof"
    & $SuricataScript
}

if ($StartUbuntuMonitor) {
    Start-UbuntuOpcuaMonitor
}

if (-not $SkipHealthCheck) {
    Wait-HttpEndpoint -Url "http://127.0.0.1:8000/api/health/" -TimeoutSeconds $HealthTimeoutSeconds
    Wait-HttpEndpoint -Url "http://127.0.0.1:3000" -TimeoutSeconds $HealthTimeoutSeconds
}

Write-Host ""
Write-Host "[live-start] Platform startup complete"
Write-Host "  Frontend: http://127.0.0.1:3000"
Write-Host "  Backend:  http://127.0.0.1:8000/api/"
Write-Host "  Swagger:  http://127.0.0.1:8000/api/docs/"
Write-Host ""
Write-Host "Next operator action: change a monitored tag in UaExpert."
Write-Host "Monitored tags: DEBI, MOTOR1, MOTOR2, SAMANDIRA, SU_SEVIYESI, ScenarioID, VALF"
