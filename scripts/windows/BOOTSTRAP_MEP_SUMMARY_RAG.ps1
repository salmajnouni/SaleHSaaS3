# =============================================================================
# MEP Summary-Only RAG Bootstrap (Windows)
# Generates paraphrased cards and stages them into knowledge_inbox.
# =============================================================================

param(
    [switch]$Stage,
    [switch]$Overwrite,
    [switch]$NoStage
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    throw "Python executable not found at $PythonExe"
}

Push-Location $ProjectRoot
try {
    Write-Host "Project: $ProjectRoot" -ForegroundColor Cyan
    Write-Host "Python : $PythonExe" -ForegroundColor Cyan

    $cmdParts = @("scripts/mep/build_summary_cards.py")

    if (-not $NoStage) {
        $cmdParts += "--stage"
    }

    if ($Overwrite) {
        $cmdParts += "--overwrite"
    }

    & $PythonExe @cmdParts

    Write-Host "`nDone." -ForegroundColor Green
}
finally {
    Pop-Location
}
