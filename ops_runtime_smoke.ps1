#!/usr/bin/env pwsh
<#!
.SYNOPSIS
  Runtime smoke test for core SaleHSaaS services with optional journal logging.

.DESCRIPTION
  Verifies:
  - Docker services state via docker compose ps
  - HTTP reachability for Open WebUI, ChromaDB, Pipelines, and n8n health
  Writes a JSON report to logs/runtime_smoke_latest.json
  Optionally appends an entry to logs/ops_journal.jsonl via ops_log.ps1
#>

param(
    [string]$ProjectDir = "C:\saleh26\salehsaas\SaleHSaaS3",
    [switch]$SkipJournal
)

$ErrorActionPreference = "Stop"

$reportPath = Join-Path $ProjectDir "logs\runtime_smoke_latest.json"
$opsLogPath = Join-Path $ProjectDir "ops_log.ps1"

Set-Location $ProjectDir

function Test-Endpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSec = 8,
        [int[]]$AcceptedStatus = @(200)
    )

    try {
        $resp = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSec -UseBasicParsing
        $ok = $AcceptedStatus -contains [int]$resp.StatusCode
        return [ordered]@{
            name = $Name
            ok = $ok
            status_code = [int]$resp.StatusCode
            url = $Url
            error = ""
        }
    }
    catch {
        return [ordered]@{
            name = $Name
            ok = $false
            status_code = 0
            url = $Url
            error = $_.Exception.Message
        }
    }
}

$composeRaw = docker compose ps --format "{{.Name}}|{{.State}}|{{.Status}}" 2>&1
$composeLines = @()
foreach ($line in $composeRaw) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line -split "\|", 3
    if ($parts.Count -eq 3) {
        $composeLines += [ordered]@{
            name = $parts[0]
            state = $parts[1]
            status = $parts[2]
        }
    }
}

$checks = @(
    (Test-Endpoint -Name "open_webui" -Url "http://localhost:3000" -AcceptedStatus @(200, 302, 401, 403, 404)),
    (Test-Endpoint -Name "chromadb" -Url "http://localhost:8010/api/v1/heartbeat" -AcceptedStatus @(200)),
    (Test-Endpoint -Name "pipelines" -Url "http://localhost:9099" -AcceptedStatus @(200, 302, 401, 403, 404)),
    (Test-Endpoint -Name "n8n" -Url "http://localhost:5678/healthz" -AcceptedStatus @(200))
)

$failed = @($checks | Where-Object { -not $_.ok })
$status = if ($failed.Count -eq 0) { "ok" } else { "warn" }
$summary = if ($failed.Count -eq 0) {
    "Runtime smoke PASS: core services reachable"
}
else {
    "Runtime smoke WARN: failed checks = " + (($failed | ForEach-Object { $_.name }) -join ", ")
}

$report = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    project_dir = $ProjectDir
    status = $status
    summary = $summary
    compose_services = $composeLines
    endpoint_checks = $checks
}

$reportDir = Split-Path -Parent $reportPath
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8

if (-not $SkipJournal -and (Test-Path $opsLogPath)) {
    $details = "report=logs/runtime_smoke_latest.json"
    & $opsLogPath -Category runtime -Action runtime_smoke -Status $status -Summary $summary -Details $details -NextStep "If warn, inspect failed service logs and retry smoke"
}

Write-Host "Smoke report written: $reportPath" -ForegroundColor Green
Write-Host $summary -ForegroundColor Cyan

if ($failed.Count -gt 0) {
    Write-Host "Failed checks:" -ForegroundColor Yellow
    foreach ($item in $failed) {
        Write-Host ("- {0} ({1})" -f $item.name, $item.error) -ForegroundColor DarkYellow
    }
    exit 1
}

exit 0
