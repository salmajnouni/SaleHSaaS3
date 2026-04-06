#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Append a structured operational log entry for continuous improvement.

.EXAMPLE
  .\ops_log.ps1 -Category rag -Action "webui_query" -Status ok -Summary "RAG answer included legal context"

.EXAMPLE
  .\ops_log.ps1 -Category infra -Action "docker_restart" -Status warn -Summary "Pipelines recreated" -Details "Manual force-recreate used"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Category,

    [Parameter(Mandatory = $true)]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidateSet("ok", "warn", "fail")]
    [string]$Status,

    [Parameter(Mandatory = $true)]
    [string]$Summary,

    [string]$Details = "",
    [string]$NextStep = "",
    [string]$Metric = ""
)

$projectDir = "C:\saleh26\salehsaas\SaleHSaaS3"
$logFile = Join-Path $projectDir "logs\ops_journal.jsonl"
$logDir = Split-Path -Parent $logFile

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$entry = [ordered]@{
    ts_utc = (Get-Date).ToUniversalTime().ToString("o")
    category = $Category
    action = $Action
    status = $Status
    summary = $Summary
    details = $Details
    next_step = $NextStep
    metric = $Metric
    host = $env:COMPUTERNAME
    user = $env:USERNAME
}

$entry | ConvertTo-Json -Depth 5 -Compress | Add-Content -Path $logFile -Encoding UTF8
Write-Host "Logged to $logFile" -ForegroundColor Green
