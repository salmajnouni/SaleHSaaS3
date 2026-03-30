param(
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

function Write-Info($msg)  { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host $msg -ForegroundColor Red }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")
Set-Location $repoRoot

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    & docker compose @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose command failed: docker compose $($ComposeArgs -join ' ')"
    }
}

function Show-Status {
    Write-Info "Checking open-terminal service status..."
    docker compose ps open-terminal
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "open-terminal is not running (or not created)."
    }
}

try {
    switch ($Action) {
        "start" {
            Write-Info "Starting open-terminal via profile..."
            Invoke-Compose -ComposeArgs @("--profile", "open-terminal", "up", "-d", "open-terminal")
            Show-Status
            Write-Ok "Open Terminal started."
            Write-Info "If Files pane still shows an error, refresh OpenWebUI page."
        }
        "stop" {
            Write-Info "Stopping open-terminal..."
            docker compose stop open-terminal | Out-Null
            docker compose rm -f open-terminal | Out-Null
            Show-Status
            Write-Ok "Open Terminal stopped and removed."
            Write-Info "To avoid UI warnings, disable Open Terminal integration/icon in OpenWebUI settings."
        }
        "status" {
            Show-Status
        }
    }
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}
