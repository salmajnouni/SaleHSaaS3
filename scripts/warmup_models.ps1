# warmup_models.ps1 - Pre-load council models into GPU VRAM
# Run after Ollama starts to avoid cold-start timeouts
# Usage: .\scripts\warmup_models.ps1

$ErrorActionPreference = "SilentlyContinue"
$OllamaUrl = "http://127.0.0.1:11434"

Write-Host "[warmup] Checking Ollama availability..."
$retries = 0
while ($retries -lt 30) {
    try {
        $null = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 5
        break
    } catch {
        $retries++
        Write-Host "[warmup] Ollama not ready, retrying ($retries/30)..."
        Start-Sleep -Seconds 2
    }
}
if ($retries -ge 30) { Write-Host "[warmup] ERROR: Ollama not reachable"; exit 1 }

$models = @("qwen3:32b", "qwen2.5:7b")

foreach ($model in $models) {
    Write-Host "[warmup] Loading $model into VRAM..."
    $body = @{
        model = $model
        prompt = "hello"
        stream = $false
        keep_alive = "-1"
        options = @{ num_predict = 1 }
    } | ConvertTo-Json

    try {
        $null = Invoke-RestMethod -Uri "$OllamaUrl/api/generate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 300
        Write-Host "[warmup] $model loaded successfully"
    } catch {
        Write-Host "[warmup] WARNING: Failed to load $model - $($_.Exception.Message)"
    }
}

Write-Host "[warmup] All models pre-loaded. Checking status:"
ollama ps
Write-Host "[warmup] Done."
