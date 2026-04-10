# ═══════════════════════════════════════════════════════════════════
# SaleH OS - سكريبت التحديث الآمن مع النسخ الاحتياطي التلقائي
# ═══════════════════════════════════════════════════════════════════

# Auto-detect project root from git
$ProjectPath = git rev-parse --show-toplevel 2>$null
if (-not $ProjectPath) {
    $ProjectPath = $PSScriptRoot
    if (-not (Test-Path "$ProjectPath\.git")) {
        Write-Host "  ✗ لا يمكن تحديد مجلد المشروع. شغل السكريبت من داخل المشروع." -ForegroundColor Red
        exit 1
    }
}
$BackupRoot  = Join-Path (Split-Path $ProjectPath) "salehsaas3_backups"
$Timestamp   = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupPath  = "$BackupRoot\backup_$Timestamp"

Set-Location $ProjectPath

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   SaleH OS - التحديث الآمن مع النسخ الاحتياطي" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── الخطوة 1: فحص التعديلات المحلية ──────────────────────────────
Write-Host "▶ الخطوة 1: فحص التعديلات المحلية..." -ForegroundColor Yellow

$ModifiedFiles  = git diff --name-only 2>$null
$UntrackedFiles = git ls-files --others --exclude-standard 2>$null
$StagedFiles    = git diff --cached --name-only 2>$null

$HasChanges = ($ModifiedFiles -or $UntrackedFiles -or $StagedFiles)

if ($HasChanges) {
    Write-Host ""
    Write-Host "  ⚠ تم اكتشاف تعديلات محلية غير مرفوعة:" -ForegroundColor Yellow

    if ($ModifiedFiles) {
        Write-Host ""
        Write-Host "  📝 ملفات معدّلة:" -ForegroundColor White
        $ModifiedFiles | ForEach-Object { Write-Host "     - $_" -ForegroundColor Gray }
    }
    if ($StagedFiles) {
        Write-Host ""
        Write-Host "  ✅ ملفات جاهزة للـ commit:" -ForegroundColor White
        $StagedFiles | ForEach-Object { Write-Host "     - $_" -ForegroundColor Gray }
    }
    if ($UntrackedFiles) {
        Write-Host ""
        Write-Host "  🆕 ملفات جديدة (غير متتبعة):" -ForegroundColor White
        $UntrackedFiles | ForEach-Object { Write-Host "     - $_" -ForegroundColor Gray }
    }

    # ── الخطوة 2: إنشاء نسخة احتياطية تلقائياً ──────────────────
    Write-Host ""
    Write-Host "▶ الخطوة 2: إنشاء نسخة احتياطية تلقائية..." -ForegroundColor Yellow

    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

    # نسخ الملفات المعدّلة
    foreach ($file in ($ModifiedFiles + $StagedFiles + $UntrackedFiles)) {
        if ($file -and (Test-Path "$ProjectPath\$file")) {
            $dest = "$BackupPath\$file"
            $destDir = Split-Path $dest -Parent
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Copy-Item "$ProjectPath\$file" -Destination $dest -Force
        }
    }

    Write-Host "  ✅ تم حفظ النسخة الاحتياطية في:" -ForegroundColor Green
    Write-Host "     $BackupPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  💡 يمكنك استعادة أي ملف من هذا المجلد في أي وقت." -ForegroundColor Gray

} else {
    Write-Host "  ✅ لا توجد تعديلات محلية. المستودع نظيف." -ForegroundColor Green
}

# ── الخطوة 3: تحديث المستودع ──────────────────────────────────────
Write-Host ""
Write-Host "▶ الخطوة 3: تحديث المستودع من GitHub..." -ForegroundColor Yellow

git fetch origin
$pullResult = git pull --ff-only origin main 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "" 
    Write-Host "  ⚠ تعذر التحديث التلقائي (fast-forward). تحقق من التعارضات:" -ForegroundColor Yellow
    Write-Host "  $pullResult" -ForegroundColor Gray
    Write-Host "  للتحديث الإجباري: git reset --hard origin/main (☠ يحذف التعديلات المحلية)" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "  ✅ تم تحديث المستودع بنجاح!" -ForegroundColor Green
}

# ── الخطوة 4: التحقق من وجود dev_studio ──────────────────────────
Write-Host ""
Write-Host "▶ الخطوة 4: التحقق من وجود مجلد dev_studio..." -ForegroundColor Yellow

if (Test-Path "$ProjectPath\dev_studio\docker-compose.dev-studio.yml") {
    Write-Host "  ✅ مجلد dev_studio موجود وجاهز!" -ForegroundColor Green
    Write-Host ""
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "   الخطوة التالية: تشغيل Dev Studio" -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  شغّل الأمر التالي:" -ForegroundColor White
    Write-Host "  docker compose -f dev_studio\docker-compose.dev-studio.yml up -d" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "  ✗ المجلد لا يزال غير موجود. يرجى التواصل مع الدعم." -ForegroundColor Red
}
