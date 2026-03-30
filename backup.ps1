#!/usr/bin/env pwsh
<#
.SYNOPSIS
    SaleHSaaS Automated Backup Script
    نسخ احتياطي تلقائي لجميع البيانات الحيوية

.DESCRIPTION
    يحفظ نسخة احتياطية من:
    - PostgreSQL (n8n + metadata)
    - ChromaDB (vector embeddings)  
    - Open WebUI SQLite + vector DB
    - Configuration files
    - Knowledge files

.USAGE
    .\backup.ps1                  # Full backup
    .\backup.ps1 -Quick           # Quick backup (DB only, no configs)
    
    # Schedule daily at 2 AM:
    # schtasks /create /tn "SaleHSaaS_Backup" /tr "powershell -File C:\saleh26\salehsaas\SaleHSaaS3\backup.ps1" /sc daily /st 02:00
#>

param(
    [switch]$Quick
)

$ErrorActionPreference = "Continue"

# === Configuration ===
$PROJECT_DIR = "C:\saleh26\salehsaas\SaleHSaaS3"
$BACKUP_ROOT = "C:\saleh26\salehsaas\SaleHSaaS3\backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_DIR = Join-Path $BACKUP_ROOT $TIMESTAMP
$MAX_BACKUPS = 7  # Keep last 7 backups

# === Setup ===
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SaleHSaaS Backup - $TIMESTAMP" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
$results = @()

# === 1. PostgreSQL Backup ===
Write-Host "`n[1/5] PostgreSQL..." -ForegroundColor Yellow
try {
    $pgFile = Join-Path $BACKUP_DIR "postgresql_salehsaas.sql"
    docker exec salehsaas_postgres pg_dump -U salehsaas -d salehsaas 2>$null | Out-File -FilePath $pgFile -Encoding utf8
    $pgSize = (Get-Item $pgFile).Length
    if ($pgSize -gt 1000) {
        $results += @{Name="PostgreSQL"; Status="OK"; Size=("{0:N1} KB" -f ($pgSize/1024))}
        Write-Host "  OK - $([math]::Round($pgSize/1024, 1)) KB" -ForegroundColor Green
    } else {
        $results += @{Name="PostgreSQL"; Status="WARN"; Size="Too small"}
        Write-Host "  WARN - File too small ($pgSize bytes)" -ForegroundColor DarkYellow
    }
} catch {
    $results += @{Name="PostgreSQL"; Status="FAIL"; Size=$_.Exception.Message}
    Write-Host "  FAIL - $_" -ForegroundColor Red
}

# === 2. ChromaDB Backup ===
Write-Host "[2/5] ChromaDB..." -ForegroundColor Yellow
try {
    $chromaDir = Join-Path $BACKUP_DIR "chromadb"
    New-Item -ItemType Directory -Path $chromaDir -Force | Out-Null
    docker cp salehsaas_chromadb:/chroma/chroma/ "$chromaDir/" 2>$null
    $chromaFiles = (Get-ChildItem $chromaDir -Recurse -File).Count
    $chromaSize = (Get-ChildItem $chromaDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
    if ($chromaFiles -gt 0) {
        $results += @{Name="ChromaDB"; Status="OK"; Size=("{0:N1} MB, {1} files" -f ($chromaSize/1MB), $chromaFiles)}
        Write-Host "  OK - $([math]::Round($chromaSize/1MB, 1)) MB ($chromaFiles files)" -ForegroundColor Green
    } else {
        $results += @{Name="ChromaDB"; Status="WARN"; Size="No files"}
        Write-Host "  WARN - No files copied" -ForegroundColor DarkYellow
    }
} catch {
    $results += @{Name="ChromaDB"; Status="FAIL"; Size=$_.Exception.Message}
    Write-Host "  FAIL - $_" -ForegroundColor Red
}

# === 3. WebUI SQLite + Vector DB ===
Write-Host "[3/5] Open WebUI..." -ForegroundColor Yellow
try {
    $webuiDir = Join-Path $BACKUP_DIR "webui"
    New-Item -ItemType Directory -Path $webuiDir -Force | Out-Null
    
    # SQLite database
    docker cp salehsaas_webui:/app/backend/data/webui.db "$webuiDir/webui.db" 2>$null
    $webuiSize = (Get-Item "$webuiDir/webui.db" -ErrorAction SilentlyContinue).Length
    
    # Vector DB (optional, large)
    if (-not $Quick) {
        docker cp salehsaas_webui:/app/backend/data/vector_db/chroma.sqlite3 "$webuiDir/chroma.sqlite3" 2>$null
    }
    
    $totalSize = (Get-ChildItem $webuiDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
    $results += @{Name="WebUI"; Status="OK"; Size=("{0:N1} MB" -f ($totalSize/1MB))}
    Write-Host "  OK - $([math]::Round($totalSize/1MB, 1)) MB" -ForegroundColor Green
} catch {
    $results += @{Name="WebUI"; Status="FAIL"; Size=$_.Exception.Message}
    Write-Host "  FAIL - $_" -ForegroundColor Red
}

# === 4. Knowledge Files ===
Write-Host "[4/5] Knowledge files..." -ForegroundColor Yellow
try {
    $knowledgeDir = Join-Path $BACKUP_DIR "knowledge"
    New-Item -ItemType Directory -Path $knowledgeDir -Force | Out-Null
    
    @("knowledge_inbox", "knowledge_processed", "knowledge_failed") | ForEach-Object {
        $src = Join-Path $PROJECT_DIR $_
        if (Test-Path $src) {
            $dest = Join-Path $knowledgeDir $_
            Copy-Item $src $dest -Recurse -Force
        }
    }
    
    $kFiles = (Get-ChildItem $knowledgeDir -Recurse -File | Where-Object { $_.Name -ne ".gitkeep" }).Count
    $results += @{Name="Knowledge"; Status="OK"; Size="$kFiles files"}
    Write-Host "  OK - $kFiles files" -ForegroundColor Green
} catch {
    $results += @{Name="Knowledge"; Status="FAIL"; Size=$_.Exception.Message}
    Write-Host "  FAIL - $_" -ForegroundColor Red
}

# === 5. Config Files (skip if Quick) ===
if (-not $Quick) {
    Write-Host "[5/5] Configuration..." -ForegroundColor Yellow
    try {
        $configDir = Join-Path $BACKUP_DIR "config"
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        
        Copy-Item (Join-Path $PROJECT_DIR "docker-compose.yml") $configDir -Force
        Copy-Item (Join-Path $PROJECT_DIR "pipelines") (Join-Path $configDir "pipelines") -Recurse -Force
        Copy-Item (Join-Path $PROJECT_DIR "config") (Join-Path $configDir "config") -Recurse -Force -ErrorAction SilentlyContinue
        
        $results += @{Name="Config"; Status="OK"; Size="copied"}
        Write-Host "  OK" -ForegroundColor Green
    } catch {
        $results += @{Name="Config"; Status="FAIL"; Size=$_.Exception.Message}
        Write-Host "  FAIL - $_" -ForegroundColor Red
    }
} else {
    Write-Host "[5/5] Config... SKIPPED (Quick mode)" -ForegroundColor DarkGray
}

# === Compress ===
Write-Host "`nCompressing backup..." -ForegroundColor Yellow
$zipFile = "$BACKUP_DIR.zip"
try {
    Compress-Archive -Path "$BACKUP_DIR\*" -DestinationPath $zipFile -Force
    $zipSize = (Get-Item $zipFile).Length
    Remove-Item $BACKUP_DIR -Recurse -Force
    Write-Host "  Compressed: $([math]::Round($zipSize/1MB, 1)) MB" -ForegroundColor Green
} catch {
    Write-Host "  Compression failed, keeping uncompressed" -ForegroundColor DarkYellow
}

# === Cleanup old backups ===
$existingBackups = Get-ChildItem $BACKUP_ROOT -Filter "*.zip" | Sort-Object Name -Descending
if ($existingBackups.Count -gt $MAX_BACKUPS) {
    $toDelete = $existingBackups | Select-Object -Skip $MAX_BACKUPS
    foreach ($old in $toDelete) {
        Remove-Item $old.FullName -Force
        Write-Host "  Cleaned old backup: $($old.Name)" -ForegroundColor DarkGray
    }
}

# === Summary ===
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Backup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
foreach ($r in $results) {
    $color = switch($r.Status) { "OK" { "Green" } "WARN" { "DarkYellow" } default { "Red" } }
    Write-Host ("  [{0}] {1}: {2}" -f $r.Status, $r.Name, $r.Size) -ForegroundColor $color
}
if (Test-Path $zipFile) {
    Write-Host "`n  Archive: $zipFile" -ForegroundColor White
}
Write-Host "========================================`n" -ForegroundColor Cyan
