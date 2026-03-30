# =============================================================================
# SaleHSaaS - UTF-8 Safe Runner for Python Data Pipelines (Windows PowerShell)
# =============================================================================

param(
    [ValidateSet("health", "report", "update", "discover", "force", "uqn", "reembed")]
    [string]$Task = "health",

    [string[]]$ExtraArgs = @(),

    [switch]$NoTee
)

$ErrorActionPreference = "Stop"

function Set-ConsoleUtf8 {
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [Console]::InputEncoding = $utf8NoBom
    [Console]::OutputEncoding = $utf8NoBom
    $global:OutputEncoding = $utf8NoBom
    chcp 65001 > $null
    $env:PYTHONUTF8 = "1"
}

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
}

function Get-PythonExe {
    param([string]$ProjectRoot)

    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    throw "Python executable not found at $venvPython. Activate or create .venv first."
}

function Ensure-LogDirectory {
    param([string]$ProjectRoot)

    $logsDir = Join-Path $ProjectRoot "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    return $logsDir
}

function Invoke-PipelineScript {
    param(
        [string]$PythonExe,
        [string]$ProjectRoot,
        [string]$ScriptRelativePath,
        [string[]]$Arguments,
        [string]$LogFileName,
        [switch]$DisableTee
    )

    $scriptPath = Join-Path $ProjectRoot $ScriptRelativePath
    if (-not (Test-Path $scriptPath)) {
        throw "Script not found: $scriptPath"
    }

    $logsDir = Ensure-LogDirectory -ProjectRoot $ProjectRoot
    $logPath = Join-Path $logsDir $LogFileName

    Write-Host ""
    Write-Host "Project : $ProjectRoot" -ForegroundColor Cyan
    Write-Host "Python  : $PythonExe" -ForegroundColor Cyan
    Write-Host "Script  : $ScriptRelativePath" -ForegroundColor Cyan
    Write-Host "Args    : $($Arguments -join ' ')" -ForegroundColor Cyan
    if (-not $DisableTee) {
        Write-Host "Log     : $logPath" -ForegroundColor Cyan
    }
    Write-Host ""

    Push-Location $ProjectRoot
    try {
        if ($DisableTee) {
            & $PythonExe $scriptPath @Arguments
        } else {
            & $PythonExe $scriptPath @Arguments 2>&1 | Tee-Object -FilePath $logPath
        }
    } finally {
        Pop-Location
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Pipeline exited with code $LASTEXITCODE"
    }
}

function New-TimestampedLogName {
    param([string]$Prefix)
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    return "${Prefix}_${stamp}.log"
}

Set-ConsoleUtf8
$projectRoot = Get-ProjectRoot
$pythonExe = Get-PythonExe -ProjectRoot $projectRoot

switch ($Task) {
    "health" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "auto_update_laws.py" `
            -Arguments @("--report") `
            -LogFileName (New-TimestampedLogName -Prefix "auto_update_health") `
            -DisableTee:$NoTee
    }

    "report" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "auto_update_laws.py" `
            -Arguments @("--report") + $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "auto_update_report") `
            -DisableTee:$NoTee
    }

    "update" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "auto_update_laws.py" `
            -Arguments $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "auto_update_run") `
            -DisableTee:$NoTee
    }

    "discover" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "auto_update_laws.py" `
            -Arguments @("--discover") + $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "auto_update_discover") `
            -DisableTee:$NoTee
    }

    "force" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "auto_update_laws.py" `
            -Arguments @("--force") + $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "auto_update_force") `
            -DisableTee:$NoTee
    }

    "uqn" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "scripts\uqn_scraper.py" `
            -Arguments $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "uqn_scraper") `
            -DisableTee:$NoTee
    }

    "reembed" {
        Invoke-PipelineScript -PythonExe $pythonExe -ProjectRoot $projectRoot `
            -ScriptRelativePath "scripts\reembed_qwen3.py" `
            -Arguments $ExtraArgs `
            -LogFileName (New-TimestampedLogName -Prefix "reembed_qwen3") `
            -DisableTee:$NoTee
    }
}

Write-Host ""
Write-Host "Done: task '$Task' completed successfully." -ForegroundColor Green
