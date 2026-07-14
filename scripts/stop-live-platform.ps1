param(
    [switch]$StopSuricata,
    [switch]$StopUbuntuMonitor,
    [string]$UbuntuHost = $env:LAB_UBUNTU_HOST,
    [string]$UbuntuUser = $env:LAB_UBUNTU_USER,
    [string]$SshKeyPath = $env:LAB_UBUNTU_SSH_KEY
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "[live-stop] Stopping Docker Compose services"
docker compose --profile wazuh-poller down
if ($LASTEXITCODE -ne 0) {
    throw "docker compose down failed."
}

if ($StopSuricata) {
    Write-Host "[live-stop] Stopping Suricata"
    Get-Process suricata -ErrorAction SilentlyContinue | Stop-Process -Force
}

if ($StopUbuntuMonitor) {
    if (-not $UbuntuHost -or -not $UbuntuUser) {
        throw "Set LAB_UBUNTU_HOST and LAB_UBUNTU_USER, or pass -UbuntuHost and -UbuntuUser."
    }

    if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: ssh"
    }

    $Target = "$UbuntuUser@$UbuntuHost"
    $SshArgs = @()
    if ($SshKeyPath) {
        $SshArgs += @("-i", $SshKeyPath)
    }
    $SshArgs += @($Target, "pkill -f 'src/opcua_monitor.py.*--all-simulator-tags' || true")

    Write-Host "[live-stop] Stopping Ubuntu OPC UA monitor on $Target"
    & ssh @SshArgs
}

Write-Host "[live-stop] Complete"
