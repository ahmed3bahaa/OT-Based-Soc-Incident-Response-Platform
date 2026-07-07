param(
    [string]$RawPath = "C:\OT-Project\kepserver-logs\raw\Opc Diagnostics.txt",
    [string]$SpoolDir = "C:\OT-Project\kepserver-logs\spool"
)

function Convert-Value {
    param([string]$Value)

    $clean = $Value.Trim()

    $doubleValue = 0.0
    if ([double]::TryParse($clean, [ref]$doubleValue)) {
        return $doubleValue
    }

    if ($clean -eq "true") { return $true }
    if ($clean -eq "false") { return $false }

    return $clean
}

function Get-TagFromNodeId {
    param([string]$NodeId)

    if ($NodeId -match "\.([^.]+)$") {
        return $Matches[1]
    }

    return $NodeId
}

if (!(Test-Path $RawPath)) {
    throw "Raw OPC Diagnostics text file not found: $RawPath"
}

New-Item -ItemType Directory -Force $SpoolDir | Out-Null

$blocks = New-Object System.Collections.Generic.List[object]
$current = $null

Get-Content $RawPath | ForEach-Object {
    $line = $_

    if ($line -match '^\s*(\d{1,2}/\d{1,2}/\d{4})\s+(.+?[AP]M)\s+\[(.+?)\]\s+(WriteRequest|WriteResponse)\s*$') {
        if ($null -ne $current) {
            $blocks.Add($current)
        }

        $current = [PSCustomObject]@{
            LocalDate = $Matches[1]
            LocalTime = $Matches[2]
            AppUri    = $Matches[3]
            Kind      = $Matches[4]
            Lines     = New-Object System.Collections.Generic.List[string]
        }
    }
    else {
        if ($null -ne $current) {
            $current.Lines.Add($line)
        }
    }
}

if ($null -ne $current) {
    $blocks.Add($current)
}

$requests = @{}
$responses = @{}

foreach ($block in $blocks) {
    $text = ($block.Lines -join "`n")

    $handle = $null
    if ($text -match 'requestHandle:\s*(\d+)') {
        $handle = $Matches[1]
    }

    if (-not $handle) {
        continue
    }

    if ($block.Kind -eq "WriteRequest") {
        $requestTimestamp = $null
        $nodeId = $null
        $variantType = $null
        $value = $null

        if ($text -match 'timestamp \(UTC\):\s*([0-9T:\.\-]+)') {
            $requestTimestamp = $Matches[1]
        }

        if ($text -match '(?m)^\s*0000000000:\s+nodeId:\s*(.+?)\s*$') {
            $nodeId = $Matches[1].Trim()
        }

        if ($text -match '(?m)^\s*0000000000:\s+variantType:\s*(.+?)\s*$') {
            $variantType = $Matches[1].Trim()
        }

        if ($text -match '(?m)^\s*0000000000:\s+value:\s*(.+?)\s*$') {
            $value = $Matches[1].Trim()
        }

        $requests[$handle] = [PSCustomObject]@{
            AppUri           = $block.AppUri
            RequestTimestamp = $requestTimestamp
            RequestHandle    = $handle
            NodeId           = $nodeId
            VariantType      = $variantType
            Value            = $value
        }
    }

    if ($block.Kind -eq "WriteResponse") {
        $responseTimestamp = $null
        $serviceCode = $null
        $serviceText = $null
        $writeCode = $null
        $writeText = $null

        if ($text -match 'timestamp \(UTC\):\s*([0-9T:\.\-]+)') {
            $responseTimestamp = $Matches[1]
        }

        if ($text -match 'serviceResult:\s*(0x[0-9A-Fa-f]+)\s*\(([^)]+)\)') {
            $serviceCode = $Matches[1]
            $serviceText = $Matches[2]
        }

        if ($text -match 'writeResults\s+\[\s*0\s*\]:\s*(0x[0-9A-Fa-f]+)\s*\(([^)]+)\)') {
            $writeCode = $Matches[1]
            $writeText = $Matches[2]
        }

        $responses[$handle] = [PSCustomObject]@{
            ResponseTimestamp = $responseTimestamp
            RequestHandle     = $handle
            ServiceCode       = $serviceCode
            ServiceText       = $serviceText
            WriteCode         = $writeCode
            WriteText         = $writeText
        }
    }
}

$count = 0

foreach ($handle in $requests.Keys) {
    if (-not $responses.ContainsKey($handle)) {
        continue
    }

    $req = $requests[$handle]
    $res = $responses[$handle]

    if (-not $req.NodeId) {
        continue
    }

    $outcome = "failure"
    if ($res.ServiceText -eq "Good" -and $res.WriteText -eq "Good") {
        $outcome = "success"
    }

    $timestamp = $res.ResponseTimestamp
    if (-not $timestamp) {
        $timestamp = $req.RequestTimestamp
    }

    if ($timestamp -and $timestamp -notmatch "Z$") {
        $timestamp = "$timestamp" + "Z"
    }

    $event = [ordered]@{
        "@timestamp" = $timestamp
        "event" = [ordered]@{
            "kind" = "event"
            "category" = @("process")
            "type" = @("change")
            "action" = "kepserver_opcua_write"
            "outcome" = $outcome
        }
        "source" = [ordered]@{
            "application_uri" = $req.AppUri
        }
        "destination" = [ordered]@{
            "ip" = "192.168.56.1"
            "port" = 49320
        }
        "network" = [ordered]@{
            "transport" = "tcp"
            "protocol" = "opcua"
        }
        "observer" = [ordered]@{
            "name" = "kepserverex-opc-diagnostics"
            "host" = "My-Win-Machine"
            "role" = "opcua_server_diagnostics"
        }
        "kepserver" = [ordered]@{
            "request_handle" = $req.RequestHandle
            "request_timestamp_utc" = $req.RequestTimestamp
            "response_timestamp_utc" = $res.ResponseTimestamp
            "service_result_code" = $res.ServiceCode
            "service_result" = $res.ServiceText
            "write_result_code" = $res.WriteCode
            "write_result" = $res.WriteText
        }
        "ot" = [ordered]@{
            "protocol" = "opcua"
            "operation" = "write"
            "node_id" = $req.NodeId
            "tag" = (Get-TagFromNodeId $req.NodeId)
            "attribute" = "Value"
            "data_type" = $req.VariantType
            "new_value" = (Convert-Value $req.Value)
            "evidence_source" = "kepserver_opc_diagnostics"
            "change_origin" = "opcua_client_request"
        }
    }

    $eventJson = $event | ConvertTo-Json -Depth 10 -Compress
    $eventId = "$($req.RequestHandle)-$([guid]::NewGuid().ToString())"

    $tmpPath = Join-Path $SpoolDir "kepserver-$eventId.tmp"
    $jsonPath = Join-Path $SpoolDir "kepserver-$eventId.json"

    Set-Content -Path $tmpPath -Value $eventJson -Encoding ascii
    Move-Item -Path $tmpPath -Destination $jsonPath

    $count++
}

Write-Host "[+] Parsed WriteRequest/WriteResponse pairs: $count"
Write-Host "[+] Spool output directory: $SpoolDir"