param(
    [string]$ProjectRoot = "C:/saleh26/salehsaas/SaleHSaaS3"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$results = @()

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details
    )
    $script:results += [PSCustomObject]@{
        Name    = $Name
        Status  = if ($Passed) { "PASS" } else { "FAIL" }
        Details = $Details
    }
}

function Get-EnvMap {
    param([string]$EnvPath)

    $map = @{}
    if (-not (Test-Path $EnvPath)) {
        return $map
    }

    Get-Content $EnvPath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        $map[$key] = $val
    }
    return $map
}

$workflowMain = Join-Path $ProjectRoot "n8n/workflows/advisory_council_webhook.json"
$workflowTelegram = Join-Path $ProjectRoot "n8n/workflows/advisory_council_telegram_decisions.json"
$dashboardApp = Join-Path $ProjectRoot "ui/arabic_dashboard/app.py"
$dashboardTemplate = Join-Path $ProjectRoot "ui/arabic_dashboard/templates/advisory_council.html"
$envPath = Join-Path $ProjectRoot ".env"
$logsDir = Join-Path $ProjectRoot "logs"

Add-Check "Workflow exists: webhook" (Test-Path $workflowMain) $workflowMain
Add-Check "Workflow exists: telegram decisions" (Test-Path $workflowTelegram) $workflowTelegram
Add-Check "Dashboard app exists" (Test-Path $dashboardApp) $dashboardApp
Add-Check "Council template exists" (Test-Path $dashboardTemplate) $dashboardTemplate
Add-Check ".env exists" (Test-Path $envPath) $envPath

if (Test-Path $workflowMain) {
    try {
        Get-Content $workflowMain -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
        Add-Check "Workflow JSON valid: webhook" $true "JSON parsed successfully"
    } catch {
        Add-Check "Workflow JSON valid: webhook" $false $_.Exception.Message
    }
}

if (Test-Path $workflowTelegram) {
    try {
        Get-Content $workflowTelegram -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
        Add-Check "Workflow JSON valid: telegram decisions" $true "JSON parsed successfully"
    } catch {
        Add-Check "Workflow JSON valid: telegram decisions" $false $_.Exception.Message
    }
}

$envMap = Get-EnvMap -EnvPath $envPath

if ($envMap.Count -gt 0) {
    $webhookUrl = if ($envMap.ContainsKey("COUNCIL_WEBHOOK_URL")) { $envMap["COUNCIL_WEBHOOK_URL"] } else { "" }
    $chatId = if ($envMap.ContainsKey("SALEH_TELEGRAM_CHAT_ID")) { $envMap["SALEH_TELEGRAM_CHAT_ID"] } else { "" }
    $botToken = if ($envMap.ContainsKey("TELEGRAM_BOT_TOKEN")) { $envMap["TELEGRAM_BOT_TOKEN"] } else { "" }
    $secretKey = if ($envMap.ContainsKey("WEBUI_SECRET_KEY")) { $envMap["WEBUI_SECRET_KEY"] } else { "" }
    $allowRemote = if ($envMap.ContainsKey("COUNCIL_ALLOW_REMOTE")) { $envMap["COUNCIL_ALLOW_REMOTE"] } else { "" }

    Add-Check "COUNCIL_WEBHOOK_URL configured" (-not [string]::IsNullOrWhiteSpace($webhookUrl)) $webhookUrl
    Add-Check "SALEH_TELEGRAM_CHAT_ID configured" ($chatId -match "^-?\d+$") "Current: $chatId"
    Add-Check "TELEGRAM_BOT_TOKEN configured" ($botToken -match "^\d+:[A-Za-z0-9_-]{20,}$") "Pattern check"
    Add-Check "WEBUI_SECRET_KEY strong" ($secretKey -match "^[a-fA-F0-9]{64}$") "Must be 64 hex chars"
    Add-Check "COUNCIL_ALLOW_REMOTE hardened" (($allowRemote -eq "false") -or [string]::IsNullOrWhiteSpace($allowRemote)) "Current: $allowRemote"
}

try {
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir | Out-Null
    }
    $probe = Join-Path $logsDir "_council_write_probe.txt"
    "ok" | Set-Content -Path $probe -Encoding UTF8
    Remove-Item $probe -Force
    Add-Check "Logs directory writable" $true $logsDir
} catch {
    Add-Check "Logs directory writable" $false $_.Exception.Message
}

try {
    $dockerLines = docker ps --format "{{.Names}}"
    $hasN8n = $dockerLines -contains "salehsaas_n8n"
    $hasWebUI = $dockerLines -contains "salehsaas_webui"
    Add-Check "Container running: salehsaas_n8n" $hasN8n "docker ps"
    Add-Check "Container running: salehsaas_webui" $hasWebUI "docker ps"
} catch {
    Add-Check "Docker availability" $false $_.Exception.Message
}

$passCount = @($results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count

Write-Host ""
Write-Host "=== Advisory Council Readiness Check ==="
Write-Host "Project: $ProjectRoot"
Write-Host "Pass: $passCount | Fail: $failCount"
Write-Host ""
$results | Format-Table -AutoSize

if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "Result: NOT READY" -ForegroundColor Red
    exit 2
}

Write-Host ""
Write-Host "Result: READY" -ForegroundColor Green
exit 0
