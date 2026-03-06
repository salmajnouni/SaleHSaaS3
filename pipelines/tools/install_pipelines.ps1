# =============================================================================
# install_pipelines.ps1 - تثبيت كل الـ Pipelines في Open WebUI
# =============================================================================
# الاستخدام: .\install_pipelines.ps1
# المتطلبات: Open WebUI يعمل على http://localhost:3000
# =============================================================================

param(
    [string]$OpenWebUIUrl = "http://localhost:3000",
    [string]$ApiKey = ""
)

# ألوان الإخراج
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info    { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error   { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║        SaleHSaaS - تثبيت الـ Pipelines في Open WebUI        ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# قائمة الـ Pipelines للتثبيت
$pipelines = @(
    @{
        file = "n8n_expert_pipeline.py"
        name = "n8n Automation Expert"
        id   = "n8n-expert-pipeline"
    },
    @{
        file = "legal_expert_pipeline.py"
        name = "Legal Compliance Expert"
        id   = "legal-expert-pipeline"
    },
    @{
        file = "financial_expert_pipeline.py"
        name = "Financial Intelligence Expert"
        id   = "financial-expert-pipeline"
    },
    @{
        file = "hr_expert_pipeline.py"
        name = "HR Management Expert"
        id   = "hr-expert-pipeline"
    },
    @{
        file = "cybersecurity_expert_pipeline.py"
        name = "Cybersecurity Expert"
        id   = "cybersecurity-expert-pipeline"
    },
    @{
        file = "social_media_expert_pipeline.py"
        name = "Social Media Expert"
        id   = "social-media-expert-pipeline"
    },
    @{
        file = "orchestrator_pipeline.py"
        name = "SaleHSaaS Orchestrator"
        id   = "orchestrator-pipeline"
    }
)

# الحصول على API Key إذا لم يُعطَ
if (-not $ApiKey) {
    Write-Info "أدخل API Key الخاص بـ Open WebUI (من Settings > Account > API Keys):"
    $ApiKey = Read-Host "API Key"
}

$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
}

# التحقق من الاتصال بـ Open WebUI
Write-Info "التحقق من الاتصال بـ Open WebUI على $OpenWebUIUrl ..."
try {
    $health = Invoke-RestMethod -Uri "$OpenWebUIUrl/health" -Method GET -ErrorAction Stop
    Write-Success "Open WebUI يعمل بشكل صحيح"
} catch {
    Write-Error "تعذّر الاتصال بـ Open WebUI على $OpenWebUIUrl"
    Write-Warning "تأكد من تشغيل docker-compose up -d أولاً"
    exit 1
}

# التحقق من خدمة Pipelines
Write-Info "التحقق من خدمة Pipelines ..."
try {
    $pipelinesHealth = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/pipelines/list" -Method GET -Headers $headers -ErrorAction Stop
    Write-Success "خدمة Pipelines تعمل"
} catch {
    Write-Warning "خدمة Pipelines غير متاحة — تأكد من تشغيل salehsaas_pipelines"
    Write-Info "تشغيل: docker-compose up -d pipelines"
}

Write-Host ""
Write-Info "بدء تثبيت الـ Pipelines..."
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($pipeline in $pipelines) {
    $filePath = Join-Path $PSScriptRoot $pipeline.file

    if (-not (Test-Path $filePath)) {
        Write-Warning "الملف غير موجود: $($pipeline.file) — تخطي"
        $failCount++
        continue
    }

    Write-Info "تثبيت: $($pipeline.name) ..."

    # قراءة محتوى الملف
    $content = Get-Content $filePath -Raw -Encoding UTF8

    # بناء الطلب
    $body = @{
        id      = $pipeline.id
        name    = $pipeline.name
        content = $content
    } | ConvertTo-Json -Depth 3

    try {
        # محاولة التحديث أولاً، ثم الإنشاء إذا لم يكن موجوداً
        try {
            $result = Invoke-RestMethod `
                -Uri "$OpenWebUIUrl/api/v1/pipelines/upload" `
                -Method POST `
                -Headers $headers `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
                -ContentType "application/json; charset=utf-8" `
                -ErrorAction Stop

            Write-Success "تم تثبيت: $($pipeline.name)"
            $successCount++
        } catch {
            # محاولة بديلة عبر multipart form
            $boundary = [System.Guid]::NewGuid().ToString()
            $LF = "`r`n"
            $bodyLines = (
                "--$boundary",
                "Content-Disposition: form-data; name=`"file`"; filename=`"$($pipeline.file)`"",
                "Content-Type: text/x-python",
                "",
                $content,
                "--$boundary--"
            ) -join $LF

            $result2 = Invoke-RestMethod `
                -Uri "$OpenWebUIUrl/api/v1/pipelines/upload" `
                -Method POST `
                -Headers @{ "Authorization" = "Bearer $ApiKey" } `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($bodyLines)) `
                -ContentType "multipart/form-data; boundary=$boundary" `
                -ErrorAction Stop

            Write-Success "تم تثبيت (multipart): $($pipeline.name)"
            $successCount++
        }
    } catch {
        Write-Error "فشل تثبيت: $($pipeline.name) — $($_.Exception.Message)"
        $failCount++
    }
}

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "📊 ملخص التثبيت:" -ForegroundColor White
Write-Success "نجح: $successCount Pipeline"
if ($failCount -gt 0) {
    Write-Error "فشل: $failCount Pipeline"
}
Write-Host "══════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
Write-Info "للتحقق من التثبيت: افتح http://localhost:3000 > Admin > Pipelines"
Write-Info "أو استخدم: curl -H 'Authorization: Bearer $ApiKey' $OpenWebUIUrl/api/v1/pipelines/list"
