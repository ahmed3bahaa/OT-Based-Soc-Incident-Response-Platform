$ErrorActionPreference = "Stop"

$SuricataExe = "C:\Program Files\Suricata\suricata.exe"
$SuricataConfig = "C:\Program Files\Suricata\suricata.yaml"
$Interface = "\Device\NPF_{94020164-8482-4F84-B737-B79277317271}"
$OutputDir = "C:\OT-Project\suricata-output\flow-proof-current"

$WrapperLog = Join-Path $OutputDir "suricata-startup-wrapper.log"
$StdoutLog = Join-Path $OutputDir "suricata-wrapper-stdout.log"
$StderrLog = Join-Path $OutputDir "suricata-wrapper-stderr.log"

New-Item -ItemType Directory -Force $OutputDir | Out-Null

"[$(Get-Date -Format o)] Starting Suricata scheduled wrapper" | Out-File -FilePath $WrapperLog -Append

if (-not (Test-Path $SuricataExe)) {
    throw "Suricata executable not found: $SuricataExe"
}

if (-not (Test-Path $SuricataConfig)) {
    throw "Suricata config not found: $SuricataConfig"
}

# Stop old Suricata process to avoid duplicate writers to eve.json
Get-Process suricata -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

$ArgumentString = "-c `"$SuricataConfig`" -i `"$Interface`" -l `"$OutputDir`" -k none"

"[$(Get-Date -Format o)] Executable: $SuricataExe" | Out-File -FilePath $WrapperLog -Append
"[$(Get-Date -Format o)] Arguments: $ArgumentString" | Out-File -FilePath $WrapperLog -Append

$Process = Start-Process `
    -FilePath $SuricataExe `
    -ArgumentList $ArgumentString `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 5

$Running = Get-Process -Id $Process.Id -ErrorAction SilentlyContinue

if (-not $Running) {
    "[$(Get-Date -Format o)] Suricata exited early. Check suricata.log and wrapper stderr." | Out-File -FilePath $WrapperLog -Append
    exit 1
}

"[$(Get-Date -Format o)] Suricata started successfully. PID=$($Process.Id)" | Out-File -FilePath $WrapperLog -Append
exit 0
