#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Detect operational deviations from logs/ops_journal.jsonl and emit a JSON report.

.DESCRIPTION
  Reads JSONL entries, filters by time window, identifies non-ok statuses,
  groups repeated deviations, and writes a machine-readable report.
#>

param(
    [int]$SinceHours = 168,
    [string]$ProjectDir = "C:\saleh26\salehsaas\SaleHSaaS3",
    [string]$JournalPath = "",
    [string]$OutPath = "",
    [switch]$AppendScanEvent
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($JournalPath)) {
    $JournalPath = Join-Path $ProjectDir "logs\ops_journal.jsonl"
}

if ([string]::IsNullOrWhiteSpace($OutPath)) {
    $OutPath = Join-Path $ProjectDir "logs\deviation_report_latest.json"
}

if (-not (Test-Path $JournalPath)) {
    Write-Host "Journal not found: $JournalPath" -ForegroundColor Red
    exit 1
}

$fromUtc = (Get-Date).ToUniversalTime().AddHours(-1 * $SinceHours)
$lines = Get-Content -Path $JournalPath -ErrorAction Stop
$entries = @()

# Filter out non-reportable deviations (test signals, closed/resolved actions)
# When a deviation is closed with a code change, add its action here to suppress the old warn entry.
$filterOutActions = @(
    "synthetic_deviation",           # test signal only
    "missing_env_vars_compose_warning"   # closed: added defaults in docker-compose.yml (commit 72e157b)
    # python_task_runner_internal — CLOSED FOR REAL: external n8nio/runners:2.14.2 sidecar (task_runners service)
)

foreach ($line in $lines) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
    try {
        $obj = $trimmed | ConvertFrom-Json -ErrorAction Stop
        $ts = $null
        try { $ts = [datetime]::Parse($obj.ts_utc).ToUniversalTime() } catch { continue }
        
        # Skip test/filtered-out actions
        if ($obj.action -in $filterOutActions) { continue }
        
        if ($ts -ge $fromUtc) {
            $entries += [PSCustomObject]@{
                ts_utc    = $ts.ToString("o")
                category  = [string]$obj.category
                action    = [string]$obj.action
                status    = ([string]$obj.status).ToLowerInvariant()
                summary   = [string]$obj.summary
                details   = [string]$obj.details
                next_step = [string]$obj.next_step
                host      = [string]$obj.host
            }
        }
    } catch {
        continue
    }
}

if ($entries.Count -eq 0) {
    $emptyReport = [ordered]@{
        generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        since_hours = $SinceHours
        total_events = 0
        deviations = 0
        warning_count = 0
        failure_count = 0
        top_deviations = @()
    }
    $emptyReport | ConvertTo-Json -Depth 8 | Set-Content -Path $OutPath -Encoding UTF8
    Write-Host "No events in selected window. Report: $OutPath" -ForegroundColor Yellow
    exit 0
}

$deviations = @($entries | Where-Object { $_.status -in @("warn", "fail") })
$warnCount = @($deviations | Where-Object { $_.status -eq "warn" }).Count
$failCount = @($deviations | Where-Object { $_.status -eq "fail" }).Count

$grouped = @($deviations |
    Group-Object -Property category, action, status |
    Sort-Object -Property Count -Descending |
    ForEach-Object {
        $sample = $_.Group | Sort-Object -Property ts_utc -Descending | Select-Object -First 1
        [ordered]@{
            key = $_.Name
            count = $_.Count
            category = $sample.category
            action = $sample.action
            status = $sample.status
            last_seen_utc = $sample.ts_utc
            latest_summary = $sample.summary
            latest_next_step = $sample.next_step
        }
    })

$report = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    since_hours = $SinceHours
    total_events = $entries.Count
    deviations = $deviations.Count
    warning_count = $warnCount
    failure_count = $failCount
    top_deviations = $grouped
}

$report | ConvertTo-Json -Depth 10 | Set-Content -Path $OutPath -Encoding UTF8

Write-Host "Deviation scan completed." -ForegroundColor Cyan
Write-Host "Total events: $($entries.Count)" -ForegroundColor Gray
Write-Host "Deviations: $($deviations.Count) (warn=$warnCount, fail=$failCount)" -ForegroundColor Gray
Write-Host "Report: $OutPath" -ForegroundColor Green

if ($grouped.Count -gt 0) {
    Write-Host "Top deviations:" -ForegroundColor Yellow
    $grouped | Select-Object -First 5 | ForEach-Object {
        Write-Host ("- [{0}] {1}/{2} x{3}" -f $_.status, $_.category, $_.action, $_.count) -ForegroundColor DarkYellow
    }
}

if ($AppendScanEvent) {
    $scanStatus = if ($failCount -gt 0) { "fail" } elseif ($warnCount -gt 0) { "warn" } else { "ok" }
    $scanSummary = "Deviation scan: deviations=$($deviations.Count), warn=$warnCount, fail=$failCount"
    $scanEntry = [ordered]@{
        ts_utc = (Get-Date).ToUniversalTime().ToString("o")
        category = "governance"
        action = "deviation_scan"
        status = $scanStatus
        summary = $scanSummary
        details = "Auto-generated by ops_detect_deviations.ps1"
        next_step = "Review logs/deviation_report_latest.json and address top deviations"
        metric = "since_hours=$SinceHours"
        host = $env:COMPUTERNAME
        user = $env:USERNAME
    }
    $scanEntry | ConvertTo-Json -Depth 6 -Compress | Add-Content -Path $JournalPath -Encoding UTF8
    Write-Host "Scan event appended to journal." -ForegroundColor DarkGray
}
