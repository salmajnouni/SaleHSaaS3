#Requires -RunAsAdministrator
# =============================================================================
# SaleHSaaS 3.0 - Smart Installer (PowerShell)
# =============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$INSTALL_DIR = "D:\SaleHSaaS3"
$REPO_URL    = "https://github.com/salmajnouni/SaleHSaaS3.git"

# ── Colors ────────────────────────────────────────────────────────────────────
function Write-Green  { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Yellow { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Red    { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-Cyan   { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-White  { param($msg) Write-Host $msg -ForegroundColor White }

function Show-Header {
    Clear-Host
    Write-Cyan  "================================================================"
    Write-Cyan  "   SaleHSaaS 3.0 - Smart Installer"
    Write-Cyan  "   Made with pride in Makkah Al-Mukarramah, Saudi Arabia"
    Write-Cyan  "================================================================"
    Write-Host ""
    Write-White "  Install path : $INSTALL_DIR"
    Write-Host ""
}

function Show-Step {
    param([int]$num, [int]$total, [string]$title)
    Write-Host ""
    Write-Cyan "----------------------------------------------------------------"
    Write-Cyan "  Step $num / $total : $title"
    Write-Cyan "----------------------------------------------------------------"
    Write-Host ""
}

function Pause-Script {
    Write-Host ""
    Write-Yellow "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# =============================================================================
Show-Header

# =============================================================================
# STEP 1 - Check Requirements
# =============================================================================
Show-Step 1 6 "Checking Requirements"

# Docker
Write-White "  Checking Docker..."
$dockerVer = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Docker is not installed!"
    Write-Yellow ""
    Write-Yellow "  Please install Docker Desktop from:"
    Write-Yellow "  https://www.docker.com/products/docker-desktop/"
    Write-Yellow ""
    $open = Read-Host "  Open download page now? (y/n)"
    if ($open -eq "y") { Start-Process "https://www.docker.com/products/docker-desktop/" }
    exit 1
}
Write-Green "  [OK] Docker: $dockerVer"

# Docker Engine running
Write-White "  Checking Docker Engine..."
docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Docker Desktop is installed but NOT running!"
    Write-Yellow "  Please open Docker Desktop and wait for 'Docker is running'"
    Write-Yellow "  Then re-run this script."
    $open = Read-Host "  Open Docker Desktop now? (y/n)"
    if ($open -eq "y") { Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" }
    exit 1
}
Write-Green "  [OK] Docker Engine is running"

# Docker Compose
Write-White "  Checking Docker Compose..."
docker compose version >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Docker Compose not available"
    Write-Yellow "  Please update Docker Desktop to version 3.0 or newer"
    exit 1
}
Write-Green "  [OK] Docker Compose is available"

# Git
Write-White "  Checking Git..."
$gitVer = git --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Git is not installed!"
    Write-Yellow "  Please install Git from: https://git-scm.com/download/win"
    $open = Read-Host "  Open download page now? (y/n)"
    if ($open -eq "y") { Start-Process "https://git-scm.com/download/win" }
    exit 1
}
Write-Green "  [OK] Git: $gitVer"

# GPU
Write-White "  Checking NVIDIA GPU..."
nvidia-smi >$null 2>&1
if ($LASTEXITCODE -eq 0) {
    $gpuName = (nvidia-smi --query-gpu=name --format=csv,noheader 2>$null).Trim()
    Write-Green "  [OK] GPU: $gpuName (will be used for AI acceleration)"
    $GPU_AVAILABLE = $true
} else {
    Write-Yellow "  [WARN] No NVIDIA GPU detected - AI will run on CPU (slower)"
    $GPU_AVAILABLE = $false
}

# Disk space on D:\
Write-White "  Checking disk space on D:\..."
$disk = Get-PSDrive D -ErrorAction SilentlyContinue
if ($disk) {
    $freeGB = [math]::Round($disk.Free / 1GB, 1)
    if ($freeGB -lt 50) {
        Write-Yellow "  [WARN] Only $freeGB GB free on D:\ (50 GB recommended)"
    } else {
        Write-Green "  [OK] Free space on D:\: $freeGB GB"
    }
}

Write-Host ""
Write-Green "  All requirements satisfied! Ready to install."
Pause-Script

# =============================================================================
# STEP 2 - Clone / Update Repository
# =============================================================================
Show-Step 2 6 "Cloning Repository from GitHub"

if (Test-Path "$INSTALL_DIR\.git") {
    Write-Yellow "  Project already exists at $INSTALL_DIR"
    Write-White "  Updating to latest version..."
    Set-Location $INSTALL_DIR
    git pull origin main
    Write-Green "  [OK] Updated successfully"
} else {
    Write-White "  Cloning into $INSTALL_DIR ..."
    Set-Location D:\
    git clone $REPO_URL SaleHSaaS3
    if ($LASTEXITCODE -ne 0) {
        Write-Red "  [FAIL] Clone failed! Check your internet connection."
        exit 1
    }
    Write-Green "  [OK] Cloned successfully"
    Set-Location $INSTALL_DIR
}

Write-Green "  Working directory: $(Get-Location)"

# =============================================================================
# STEP 3 - Create .env file
# =============================================================================
Show-Step 3 6 "Creating Environment File (.env)"

function New-RandomPassword {
    param([int]$length = 24)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#%^&*"
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes = New-Object byte[] $length
    $rng.GetBytes($bytes)
    $result = ""
    foreach ($b in $bytes) { $result += $chars[$b % $chars.Length] }
    return $result
}

if (Test-Path ".env") {
    Write-Yellow "  .env file already exists."
    $update = Read-Host "  Recreate it with new passwords? (y/n)"
    if ($update -ne "y") {
        Write-Green "  [OK] Keeping existing .env"
        goto ENV_DONE
    }
    Remove-Item ".env"
}

Write-White "  Generating secure random passwords..."

$PG_PASS      = New-RandomPassword 20
$REDIS_PASS   = New-RandomPassword 20
$WEBUI_KEY    = New-RandomPassword 32
$N8N_PASS     = New-RandomPassword 20
$N8N_ENC      = New-RandomPassword 32
$SEARXNG_SEC  = New-RandomPassword 32
$DASH_KEY     = New-RandomPassword 32
$CODE_PASS    = New-RandomPassword 20
$GRAFANA_PASS = New-RandomPassword 20
$ALLM_JWT     = New-RandomPassword 32

$envContent = @"
# SaleHSaaS 3.0 - Environment Configuration
# Made with pride in Makkah Al-Mukarramah, Saudi Arabia
# Auto-generated on $(Get-Date -Format "yyyy-MM-dd HH:mm")
# DO NOT share this file with anyone

# Database
POSTGRES_DB=salehsaas
POSTGRES_USER=salehsaas_user
POSTGRES_PASSWORD=$PG_PASS

# Redis
REDIS_PASSWORD=$REDIS_PASS

# Ollama - AI Engine
OLLAMA_PORT=11434
OLLAMA_NUM_PARALLEL=2
DEFAULT_MODEL=llama3

# Open WebUI
OPEN_WEBUI_PORT=3000
WEBUI_SECRET_KEY=$WEBUI_KEY
ENABLE_SIGNUP=false

# n8n Automation
N8N_PORT=5678
N8N_USER=admin
N8N_PASSWORD=$N8N_PASS
N8N_ENCRYPTION_KEY=$N8N_ENC

# Qdrant Vector DB
QDRANT_PORT=6333
QDRANT_API_KEY=

# SearXNG Search
SEARXNG_PORT=8080
SEARXNG_SECRET=$SEARXNG_SEC

# Dashboard
DASHBOARD_PORT=8000
DASHBOARD_SECRET_KEY=$DASH_KEY
FLASK_DEBUG=false

# Code Server
CODE_SERVER_PORT=8443
CODE_SERVER_PASSWORD=$CODE_PASS

# Grafana
GRAFANA_PORT=3001
GRAFANA_USER=admin
GRAFANA_PASSWORD=$GRAFANA_PASS

# AnythingLLM
ANYTHINGLLM_PORT=3002
ANYTHINGLLM_JWT_SECRET=$ALLM_JWT
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Green "  [OK] .env file created with secure random passwords"

:ENV_DONE

# =============================================================================
# STEP 4 - Create Required Directories
# =============================================================================
Show-Step 4 6 "Creating Required Directories"

$dirs = @(
    "data\uploads",
    "data\exports",
    "logs",
    "config\postgres",
    "config\prometheus",
    "config\searxng",
    "config\grafana\dashboards",
    "backups"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Green "  [OK] Created: $dir"
    } else {
        Write-White "  [--] Exists:  $dir"
    }
}

# =============================================================================
# STEP 5 - Pull Docker Images & Start Services
# =============================================================================
Show-Step 5 6 "Downloading Docker Images & Starting Services"

Write-Yellow "  This may take 15-30 minutes depending on your internet speed..."
Write-Host ""

docker compose pull
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Failed to pull some images. Check internet connection."
    exit 1
}
Write-Green "  [OK] All images downloaded"

Write-Host ""
Write-White "  Starting all services..."
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Red "  [FAIL] Failed to start services."
    Write-Yellow "  Check logs: docker compose logs --tail=30"
    exit 1
}
Write-Green "  [OK] All services started"

# =============================================================================
# STEP 6 - Download AI Models
# =============================================================================
Show-Step 6 6 "Downloading AI Models"

Write-Yellow "  Waiting 30 seconds for Ollama to initialize..."
Start-Sleep -Seconds 30

Write-White "  Downloading llama3 model (~4.7 GB)..."
docker exec salehsaas_ollama ollama pull llama3
if ($LASTEXITCODE -eq 0) {
    Write-Green "  [OK] llama3 downloaded"
} else {
    Write-Yellow "  [WARN] llama3 download failed - you can retry from MANAGE_SALEHSAAS.bat"
}

Write-White "  Downloading nomic-embed-text model (for RAG)..."
docker exec salehsaas_ollama ollama pull nomic-embed-text
if ($LASTEXITCODE -eq 0) {
    Write-Green "  [OK] nomic-embed-text downloaded"
} else {
    Write-Yellow "  [WARN] nomic-embed-text download failed - retry later"
}

# =============================================================================
# DONE
# =============================================================================
Clear-Host
Write-Cyan  "================================================================"
Write-Green "   SaleHSaaS 3.0 - Installation Complete!"
Write-Cyan  "   Made with pride in Makkah Al-Mukarramah, Saudi Arabia"
Write-Cyan  "================================================================"
Write-Host ""
Write-White "  SERVICES:"
Write-Host ""
Write-Green "   Main Dashboard    : http://localhost:8000"
Write-Green "   Open WebUI (AI)   : http://localhost:3000"
Write-Green "   AnythingLLM       : http://localhost:3002"
Write-Green "   n8n Automation    : http://localhost:5678"
Write-Green "   SearXNG Search    : http://localhost:8080"
Write-Green "   Code Server       : http://localhost:8443"
Write-Green "   Grafana Monitor   : http://localhost:3001"
Write-Host ""
Write-Cyan  "================================================================"
Write-Yellow "  Passwords saved in: $INSTALL_DIR\.env"
Write-Yellow "  Keep this file safe - do not share it!"
Write-Cyan  "================================================================"
Write-Host ""
Write-White "  All data is processed locally - Zero external transmission"
Write-Host ""

$openDash = Read-Host "  Open Dashboard now? (y/n)"
if ($openDash -eq "y") {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:8000"
}

Write-Host ""
Write-White "  To manage services later, run: MANAGE_SALEHSAAS.bat"
Write-Host ""
Pause-Script
