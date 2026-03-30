# SaleH SaaS 4.0 - Setup Script
# Run as Administrator in PowerShell

# WARNING:
# This script has inherited messages from older layouts.
# Runtime truth must always be validated against docker-compose.yml.

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SaleH SaaS 4.0 - Setup Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Check Docker ---
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    docker info 2>&1 | Out-Null
    Write-Host "  OK: Docker is running." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# --- Step 2: Check Ollama ---
Write-Host "[2/5] Checking Ollama models..." -ForegroundColor Yellow
$ollamaList = ollama list 2>&1
if ($ollamaList -notmatch "nomic-embed-text") {
    Write-Host "  Downloading nomic-embed-text (required for embeddings)..." -ForegroundColor Yellow
    ollama pull nomic-embed-text
    Write-Host "  OK: nomic-embed-text downloaded." -ForegroundColor Green
} else {
    Write-Host "  OK: nomic-embed-text found." -ForegroundColor Green
}

if ($ollamaList -notmatch "llama3") {
    Write-Host "  INFO: No llama3 model found. Downloading llama3.1..." -ForegroundColor Yellow
    ollama pull llama3.1
    Write-Host "  OK: llama3.1 downloaded." -ForegroundColor Green
} else {
    Write-Host "  OK: LLM model found." -ForegroundColor Green
}

# --- Step 3: Setup .env file ---
Write-Host "[3/5] Setting up .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".\.env")) {
    Copy-Item -Path ".\.env.example" -Destination ".\.env"
    Write-Host ""
    Write-Host "  IMPORTANT: .env file created from .env.example" -ForegroundColor Red
    Write-Host "  Please open .env and change all passwords before continuing!" -ForegroundColor Red
    Write-Host ""
    Read-Host "  Press Enter after editing .env to continue..."
} else {
    Write-Host "  OK: .env file exists." -ForegroundColor Green
}

# --- Step 4: Pull latest images ---
Write-Host "[4/5] Pulling latest Docker images..." -ForegroundColor Yellow
docker-compose pull
Write-Host "  OK: Images pulled." -ForegroundColor Green

# --- Step 5: Build and start containers ---
Write-Host "[5/5] Building and starting containers..." -ForegroundColor Yellow
docker-compose up -d --build --remove-orphans
Write-Host "  OK: Containers started." -ForegroundColor Green

# --- Done ---
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "   SaleH SaaS 4.0 is ready!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  Open WebUI  (main interface) : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  n8n         (automation)     : http://localhost:5678" -ForegroundColor Cyan
Write-Host "  Open Terminal(dev terminal)  : http://localhost:8000" -ForegroundColor Cyan
Write-Host "  ChromaDB    (vector database): http://localhost:8010" -ForegroundColor Cyan
Write-Host ""
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "  - First time: Create admin account in Open WebUI." -ForegroundColor Yellow
Write-Host "  - Upload legal documents from the 'Documents' tab." -ForegroundColor Yellow
Write-Host "  - Validate active services with docker compose ps." -ForegroundColor Yellow
Write-Host ""
