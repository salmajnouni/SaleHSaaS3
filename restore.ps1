###############################################################################
# SaleH SaaS - سكريبت الاستعادة الكاملة
# يُشغَّل مرة واحدة بعد docker compose down -v لاستعادة كل الإعدادات
# الاستخدام: .\restore.ps1
###############################################################################

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "SaleH SaaS - Restore"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   SaleH SaaS - استعادة كاملة للنظام" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── التحقق من وجود ملف .env ──────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Write-Host "[1/5] إنشاء ملف .env من النموذج..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "      تم إنشاء .env — يمكنك تعديل القيم لاحقاً" -ForegroundColor Green
} else {
    Write-Host "[1/5] ملف .env موجود بالفعل" -ForegroundColor Green
}

# ── انتظار جاهزية n8n ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/5] انتظار جاهزية n8n..." -ForegroundColor Yellow
$n8nReady = $false
$attempts = 0
while (-not $n8nReady -and $attempts -lt 30) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5678/healthz" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $n8nReady = $true
        }
    } catch {}
    if (-not $n8nReady) {
        Write-Host "      انتظار... ($attempts/30)" -ForegroundColor Gray
        Start-Sleep -Seconds 3
        $attempts++
    }
}

if (-not $n8nReady) {
    Write-Host "      تحذير: n8n لم يستجب. تأكد من تشغيل: docker compose up -d" -ForegroundColor Red
    Write-Host "      ثم أعد تشغيل هذا السكريبت." -ForegroundColor Red
    exit 1
}
Write-Host "      n8n جاهز!" -ForegroundColor Green

# ── إنشاء API Key في n8n ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/5] إنشاء API Key في n8n..." -ForegroundColor Yellow

# قراءة بيانات الدخول من .env
$envContent = Get-Content ".env" | Where-Object { $_ -match "=" -and $_ -notmatch "^#" }
$envVars = @{}
foreach ($line in $envContent) {
    $parts = $line -split "=", 2
    if ($parts.Count -eq 2) {
        $envVars[$parts[0].Trim()] = $parts[1].Trim()
    }
}

$n8nUser = if ($envVars["N8N_USER"]) { $envVars["N8N_USER"] } else { "admin" }
$n8nPass = if ($envVars["N8N_PASSWORD"]) { $envVars["N8N_PASSWORD"] } else { "REPLACE_WITH_STRONG_N8N_PASSWORD" }

if ($n8nPass -eq "REPLACE_WITH_STRONG_N8N_PASSWORD") {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "  │  يجب إنشاء API Key يدوياً من n8n:                      │" -ForegroundColor Yellow
    Write-Host "  │  1. افتح http://localhost:5678                          │" -ForegroundColor Yellow
    Write-Host "  │  2. Settings → n8n API → Add API Key                   │" -ForegroundColor Yellow
    Write-Host "  │  3. الاسم: bridge                                       │" -ForegroundColor Yellow
    Write-Host "  │  4. انسخ الـ Key وضعه في .env:                         │" -ForegroundColor Yellow
    Write-Host "  │     N8N_API_KEY=الـ_key_هنا                             │" -ForegroundColor Yellow
    Write-Host "  │  5. أعد تشغيل: docker compose restart n8n_bridge       │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
} else {
    # محاولة إنشاء API Key تلقائياً
    try {
        $loginBody = @{ email = "$n8nUser@salehsaas.local"; password = $n8nPass } | ConvertTo-Json
        $loginResponse = Invoke-RestMethod -Uri "http://localhost:5678/rest/login" -Method POST -Body $loginBody -ContentType "application/json" -SessionVariable session
        
        $apiKeyBody = @{ label = "bridge-auto" } | ConvertTo-Json
        $apiKeyResponse = Invoke-RestMethod -Uri "http://localhost:5678/rest/api-key" -Method POST -Body $apiKeyBody -ContentType "application/json" -WebSession $session
        
        $newApiKey = $apiKeyResponse.data.apiKey
        
        # تحديث .env
        $envFile = Get-Content ".env"
        $envFile = $envFile -replace "^N8N_API_KEY=.*", "N8N_API_KEY=$newApiKey"
        $envFile | Set-Content ".env"
        
        Write-Host "      تم إنشاء API Key تلقائياً وحفظه في .env" -ForegroundColor Green
        
        # إعادة تشغيل bridge
        Write-Host "      إعادة تشغيل n8n_bridge..." -ForegroundColor Yellow
        docker compose restart n8n_bridge 2>&1 | Out-Null
        Write-Host "      تم إعادة تشغيل n8n_bridge" -ForegroundColor Green
        
    } catch {
        Write-Host "      لم يتمكن السكريبت من إنشاء API Key تلقائياً." -ForegroundColor Yellow
        Write-Host "      أنشئه يدوياً من: http://localhost:5678/settings/api" -ForegroundColor Yellow
    }
}

# ── استيراد الـ Workflows ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "[4/5] استيراد الـ Workflows في n8n..." -ForegroundColor Yellow

$workflowFiles = Get-ChildItem "n8n_workflows\*.json" -ErrorAction SilentlyContinue
if ($workflowFiles.Count -eq 0) {
    Write-Host "      لا توجد ملفات workflows للاستيراد" -ForegroundColor Gray
} else {
    # قراءة N8N_API_KEY المحدّث
    $envContent2 = Get-Content ".env" | Where-Object { $_ -match "^N8N_API_KEY=" }
    $currentApiKey = ""
    if ($envContent2) {
        $currentApiKey = ($envContent2 -split "=", 2)[1].Trim()
    }
    
    if ($currentApiKey -and $currentApiKey -ne "REPLACE_WITH_STRONG_N8N_PASSWORD") {
        $headers = @{ "X-N8N-API-KEY" = $currentApiKey }
        $imported = 0
        $failed = 0
        
        foreach ($file in $workflowFiles) {
            try {
                $wfContent = Get-Content $file.FullName -Raw
                $wfData = $wfContent | ConvertFrom-Json
                
                # إزالة الـ id لتجنب تعارض الـ IDs
                $wfData.PSObject.Properties.Remove("id")
                $wfData.PSObject.Properties.Remove("createdAt")
                $wfData.PSObject.Properties.Remove("updatedAt")
                
                $body = $wfData | ConvertTo-Json -Depth 20
                $result = Invoke-RestMethod -Uri "http://localhost:5678/api/v1/workflows" -Method POST -Headers $headers -Body $body -ContentType "application/json"
                Write-Host "      استُورد: $($wfData.name)" -ForegroundColor Green
                $imported++
            } catch {
                Write-Host "      فشل: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
                $failed++
            }
        }
        Write-Host "      النتيجة: $imported مستورد، $failed فشل" -ForegroundColor Cyan
    } else {
        Write-Host "      تخطي — N8N_API_KEY غير محدد في .env" -ForegroundColor Yellow
        Write-Host "      بعد إضافة الـ Key، شغّل: .\restore.ps1 --workflows-only" -ForegroundColor Yellow
    }
}

# ── إعداد Open WebUI ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] تعليمات إعداد Open WebUI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "  │  افتح http://localhost:3000 وأكمل:                         │" -ForegroundColor Cyan
Write-Host "  │                                                             │" -ForegroundColor Cyan
Write-Host "  │  1. أدخل الاسم الكامل وأنشئ حساب Admin                    │" -ForegroundColor Cyan
Write-Host "  │                                                             │" -ForegroundColor Cyan
Write-Host "  │  2. Admin Panel → Settings → Connections                   │" -ForegroundColor Cyan
Write-Host "  │     Pipelines URL: http://pipelines:9099                   │" -ForegroundColor Cyan
Write-Host "  │     API Key: salehsaas-pipelines-key                       │" -ForegroundColor Cyan
Write-Host "  │                                                             │" -ForegroundColor Cyan
Write-Host "  │  3. Admin Panel → Settings → Connections → OpenAI          │" -ForegroundColor Cyan
Write-Host "  │     URL: http://n8n_bridge:3333/v1                         │" -ForegroundColor Cyan
Write-Host "  │     API Key: salehsaas-bridge-key                          │" -ForegroundColor Cyan
Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   اكتملت الاستعادة!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Open WebUI : http://localhost:3000" -ForegroundColor White
Write-Host "  n8n        : http://localhost:5678" -ForegroundColor White
Write-Host "  Pipelines  : http://localhost:9099" -ForegroundColor White
Write-Host ""
