# =============================================================================
# SBC RAG Bootstrap Runner (Windows)
# Orchestrates: register sources -> build manifest -> stage to knowledge_inbox
# =============================================================================

param(
    [string]$Sbc501 = "",
    [string]$Sbc701 = "",
    [string]$Sbc801 = "",
    [string]$Edition = "",
    [string]$PublicationDate = "",
    [string]$EffectiveDate = "",
    [string]$ApprovedBy = "",
    [string]$SourceUrl501 = "",
    [string]$SourceUrl701 = "",
    [string]$SourceUrl801 = "",
    [switch]$Stage,
    [switch]$DryRun,
    [switch]$Overwrite
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

    $registerArgs = @("scripts/mep/register_sbc_sources.py")

    if ($Sbc501) { $registerArgs += @("--sbc501", $Sbc501) }
    if ($Sbc701) { $registerArgs += @("--sbc701", $Sbc701) }
    if ($Sbc801) { $registerArgs += @("--sbc801", $Sbc801) }
    if ($Edition) { $registerArgs += @("--edition", $Edition) }
    if ($PublicationDate) { $registerArgs += @("--publication-date", $PublicationDate) }
    if ($EffectiveDate) { $registerArgs += @("--effective-date", $EffectiveDate) }
    if ($ApprovedBy) { $registerArgs += @("--approved-by", $ApprovedBy) }
    if ($SourceUrl501) { $registerArgs += @("--source-url-501", $SourceUrl501) }
    if ($SourceUrl701) { $registerArgs += @("--source-url-701", $SourceUrl701) }
    if ($SourceUrl801) { $registerArgs += @("--source-url-801", $SourceUrl801) }

    Write-Host "`n[1/3] Updating source register..." -ForegroundColor Yellow
    & $PythonExe @registerArgs

    Write-Host "`n[2/3] Building ingestion manifest..." -ForegroundColor Yellow
    & $PythonExe "scripts/mep/prepare_sbc_manifest.py"

    if ($Stage) {
        Write-Host "`n[3/3] Staging approved files into knowledge_inbox..." -ForegroundColor Yellow
        $stageArgs = @("scripts/mep/stage_sbc_ingestion.py")
        if ($DryRun) { $stageArgs += "--dry-run" }
        if ($Overwrite) { $stageArgs += "--overwrite" }
        & $PythonExe @stageArgs
    } else {
        Write-Host "`n[3/3] Staging skipped (use -Stage to enable)." -ForegroundColor DarkYellow
    }

    Write-Host "`nDone." -ForegroundColor Green
}
finally {
    Pop-Location
}
