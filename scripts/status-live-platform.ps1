param(
    [string]$KepServerHost = $(if ($env:LAB_KEPSERVER_HOST) { $env:LAB_KEPSERVER_HOST } else { "127.0.0.1" }),
    [int]$KepServerPort = $(if ($env:LAB_KEPSERVER_PORT) { [int]$env:LAB_KEPSERVER_PORT } else { 49320 }),
    [string]$SuricataOutputDir = $(if ($env:LAB_SURICATA_OUTPUT_DIR) { $env:LAB_SURICATA_OUTPUT_DIR } else { "C:\OT-Project\suricata-output\flow-proof-current" })
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Test-HttpEndpoint {
    param([string]$Url)

    try {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
        return "OK ($($Response.StatusCode))"
    }
    catch {
        return "DOWN ($($_.Exception.Message))"
    }
}

Write-Host "[live-status] Docker Compose"
docker compose --profile wazuh-poller ps

Write-Host ""
Write-Host "[live-status] HTTP endpoints"
Write-Host "  Backend health: $(Test-HttpEndpoint 'http://127.0.0.1:8000/api/health/')"
Write-Host "  Frontend:       $(Test-HttpEndpoint 'http://127.0.0.1:3000')"
Write-Host "  Swagger:        http://127.0.0.1:8000/api/docs/"

Write-Host ""
Write-Host "[live-status] KEPServerEX"
$KepReady = Test-NetConnection -ComputerName $KepServerHost -Port $KepServerPort -InformationLevel Quiet -WarningAction SilentlyContinue
Write-Host "  OPC UA endpoint $KepServerHost`:$KepServerPort reachable: $KepReady"

Write-Host ""
Write-Host "[live-status] Suricata"
$Suricata = Get-Process suricata -ErrorAction SilentlyContinue
if ($Suricata) {
    $Suricata | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
}
else {
    Write-Host "  Suricata process is not running."
}

$EvePath = Join-Path $SuricataOutputDir "eve.json"
if (Test-Path $EvePath) {
    $EveItem = Get-Item $EvePath
    Write-Host "  eve.json: $($EveItem.FullName)"
    Write-Host "  size: $($EveItem.Length) bytes, modified: $($EveItem.LastWriteTime)"
}
else {
    Write-Host "  eve.json not found at $EvePath"
}

Write-Host ""
Write-Host "[live-status] Recent Wazuh poller logs"
docker compose --profile wazuh-poller logs --tail 20 wazuh-poller
