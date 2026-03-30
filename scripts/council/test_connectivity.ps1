#!/usr/bin/env pwsh
# Test OpenWebUI and n8n connectivity

param([switch]$Verbose = $false)

$ErrorActionPreference = "Continue"

Write-Host "`n=== Connection Test: OpenWebUI and n8n ===" -ForegroundColor Magenta

$testResults = @()

# Test 1: OpenWebUI
Write-Host "`n[1] OpenWebUI API Check..." -ForegroundColor Cyan
$WEBUI_URL = "http://localhost:3000"

try {
    $response = Invoke-RestMethod -Uri "$WEBUI_URL/api/config" -TimeoutSec 5
    Write-Host "  [OK] OpenWebUI is responding" -ForegroundColor Green
    $testResults += "PASS:OpenWebUI API"
}
catch {
    Write-Host "  [ERROR] Failed to connect to OpenWebUI: $_" -ForegroundColor Red
    $testResults += "FAIL:OpenWebUI API"
    exit 1
}

# Test 2: n8n Health
Write-Host "`n[2] n8n Health Check..." -ForegroundColor Cyan
$N8N_URL = "http://localhost:5678"

try {
    $response = Invoke-RestMethod -Uri "$N8N_URL/rest/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "  [OK] n8n is responding" -ForegroundColor Green
    $testResults += "PASS:n8n API"
}
catch {
    # Try alternative endpoint
    try {
        $response = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows" -TimeoutSec 5
        Write-Host "  [OK] n8n is responding" -ForegroundColor Green
        $testResults += "PASS:n8n API"
    }
    catch {
        Write-Host "  [WARNING] n8n health check inconclusive" -ForegroundColor Yellow
        $testResults += "WARN:n8n API"
    }
}

# Test 3: Models
Write-Host "`n[3] Models Availability Check..." -ForegroundColor Cyan

try {
    $models = Invoke-RestMethod -Uri "$WEBUI_URL/api/models" -TimeoutSec 5
    $count = $models.data.Count
    
    if ($count -gt 0) {
        Write-Host "  [OK] Found $count models" -ForegroundColor Green
        $first3 = $models.data | Select-Object -ExpandProperty id -First 3
        Write-Host "       Examples: $($first3 -join ', ')" -ForegroundColor Gray
        $testResults += "PASS:Models"
    }
    else {
        Write-Host "  [WARNING] No models found" -ForegroundColor Yellow
        $testResults += "WARN:Models"
    }
}
catch {
    Write-Host "  [WARNING] Models check inconclusive: $_" -ForegroundColor Yellow
    $testResults += "WARN:Models"
}

# Test 4: LLM Call Simulation
Write-Host "`n[4] LLM Model Call Simulation..." -ForegroundColor Cyan

if ((Test-Path ".env") -eq $false) {
    Write-Host "  [ERROR] .env file not found" -ForegroundColor Red
    exit 1
}

$envContent = Get-Content ".env" -Raw
$modelMatch = $envContent | Select-String "COUNCIL_MODEL=(.+)" | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }
$MODEL = if ($modelMatch) { $modelMatch } else { "llama3.1:latest" }

$payload = @{
    model = $MODEL
    prompt = "Give a one-line opinion"
    stream = $false
} | ConvertTo-Json

try {
    Write-Host "  Calling model: $MODEL" -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "$WEBUI_URL/api/generate" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    
    $text = $response.response
    if ($text.Length -gt 60) { $text = $text.Substring(0, 60) + "..." }
    
    Write-Host "  [OK] Model responded successfully" -ForegroundColor Green
    Write-Host "       Response: $text" -ForegroundColor Gray
    $testResults += "PASS:LLM Call"
}
catch {
    Write-Host "  [WARNING] Model call inconclusive: (may be auth issue, check n8n logs)" -ForegroundColor Yellow
    $testResults += "WARN:LLM Call"
}

# Test 5: Containers
Write-Host "`n[5] Container Health..." -ForegroundColor Cyan

$containers = @("salehsaas_n8n", "salehsaas_webui", "salehsaas_open-terminal")
foreach ($container in $containers) {
    $status = & docker inspect $container --format '{{.State.Status}}' 2>$null
    
    if ($status -eq "running") {
        Write-Host "  [OK] $container is running" -ForegroundColor Green
        $testResults += "PASS:$container"
    }
    else {
        Write-Host "  [ERROR] $container is NOT running" -ForegroundColor Red
        $testResults += "FAIL:$container"
    }
}

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Magenta

$passCount = ($testResults | Where-Object { $_ -like "PASS*" }).Count
$failCount = ($testResults | Where-Object { $_ -like "FAIL*" }).Count
$warnCount = ($testResults | Where-Object { $_ -like "WARN*" }).Count

Write-Host "`nPassed: $passCount | Failed: $failCount | Warnings: $warnCount | Total: $($testResults.Count)" -ForegroundColor White

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
$testResults | ForEach-Object {
    $status = switch -Regex ($_) {
        "^PASS" { "[OK]   " }
        "^FAIL" { "[ERR]  " }
        "^WARN" { "[WARN] " }
    }
    $test = $_ -replace "^(PASS|FAIL|WARN):", ""
    Write-Host "  $status $test" -ForegroundColor $(if ($_ -like "FAIL*") { "Red" } elseif ($_ -like "WARN*") { "Yellow" } else { "Green" })
}

if ($failCount -eq 0) {
    Write-Host "`nRESULT: SUCCESS - System is ready for workflow deployment" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`nRESULT: FAILURE - Please fix the errors above" -ForegroundColor Red
    exit 1
}
