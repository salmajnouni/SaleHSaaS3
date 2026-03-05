# ═══════════════════════════════════════════════════════════════════
# SaleH OS - تفعيل نظام n8n AI Builder
# "ولدنا" يبني workflows مباشرة في n8n
# ═══════════════════════════════════════════════════════════════════

$ProjectPath = "D:\SaleHSaaS3"
Set-Location $ProjectPath

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   تفعيل نظام n8n AI Builder" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── الخطوة 1: سحب آخر التحديثات ──────────────────────────────────
Write-Host "▶ الخطوة 1: سحب آخر التحديثات من GitHub..." -ForegroundColor Yellow
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ فشل git pull. تحقق من الاتصال." -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ تم سحب التحديثات." -ForegroundColor Green
Write-Host ""

# ── الخطوة 2: التحقق من مفتاح n8n API في .env ────────────────────
Write-Host "▶ الخطوة 2: التحقق من مفتاح N8N_API_KEY..." -ForegroundColor Yellow
if (-not (Test-Path "$ProjectPath\.env")) {
    Write-Host "  ❌ ملف .env غير موجود. انسخ .env.example وعدّله:" -ForegroundColor Red
    Write-Host "     copy .env.example .env" -ForegroundColor White
    exit 1
}
$envContent = Get-Content "$ProjectPath\.env" -Raw
if ($envContent -notmatch "N8N_API_KEY=\S+") {
    Write-Host "  ⚠ N8N_API_KEY غير موجود في .env" -ForegroundColor Yellow
    Write-Host "  أضف هذا السطر في ملف .env:" -ForegroundColor White
    Write-Host "  N8N_API_KEY=<مفتاحك من n8n → Settings → API>" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  للحصول على المفتاح:" -ForegroundColor White
    Write-Host "  1. افتح http://localhost:5678" -ForegroundColor Gray
    Write-Host "  2. Settings → API → Create API Key" -ForegroundColor Gray
    exit 1
}
Write-Host "  ✅ N8N_API_KEY موجود." -ForegroundColor Green
Write-Host ""

# ── الخطوة 3: إعادة تشغيل MCPO لتحميل أداة n8n_builder ──────────
Write-Host "▶ الخطوة 3: إعادة تشغيل MCPO لتحميل أداة n8n_builder..." -ForegroundColor Yellow
docker compose restart mcpo
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ فشل إعادة تشغيل MCPO." -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ تم إعادة تشغيل MCPO." -ForegroundColor Green
Write-Host ""

# ── الخطوة 4: انتظار 5 ثوانٍ ثم التحقق من حالة الخدمات ──────────
Write-Host "▶ الخطوة 4: انتظار تهيئة الخدمات (5 ثوانٍ)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
docker compose ps --format "table {{.Name}}\t{{.Status}}"
Write-Host ""

# ── الخطوة 5: اختبار اتصال MCPO بـ n8n ──────────────────────────
Write-Host "▶ الخطوة 5: اختبار اتصال MCPO بـ n8n_builder..." -ForegroundColor Yellow
try {
    $mcpoPort = "8020"
    $mcpoKey  = if ($envContent -match 'MCPO_API_KEY=(\S+)') { $Matches[1] } else { "salehsaas-mcpo-key" }
    $response = Invoke-WebRequest -Uri "http://localhost:$mcpoPort/n8n_builder/list_workflows" `
                                  -Headers @{ "Authorization" = "Bearer $mcpoKey" } `
                                  -Method GET -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  ✅ MCPO يتصل بـ n8n بنجاح!" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ لم يتمكن MCPO من الاتصال بـ n8n الآن." -ForegroundColor Yellow
    Write-Host "  تأكد أن n8n يعمل: http://localhost:5678" -ForegroundColor Gray
}
Write-Host ""

Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ النظام جاهز!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "الخطوة التالية في Open WebUI:" -ForegroundColor White
Write-Host "  Admin Settings → Tools → n8n_builder" -ForegroundColor Cyan
Write-Host "  ثم في محادثة 'ولدنا' اكتب:" -ForegroundColor White
Write-Host "  'ابنِ لي workflow يراقب بريدي الإلكتروني'" -ForegroundColor Cyan
Write-Host ""
