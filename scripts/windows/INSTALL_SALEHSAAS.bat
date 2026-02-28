@echo off
chcp 65001 >nul
cls

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║          SaleHSaaS 3.0 - مثبّت المنصة السيادية                 ║
echo ║          منصة الذكاء الأعمال السيادية - التثبيت التلقائي        ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

:: ── Check Admin Privileges ──────────────────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [خطأ] يجب تشغيل هذا الملف كمسؤول (Run as Administrator)
    echo [ERROR] Please run as Administrator
    pause
    exit /b 1
)

:: ── Check Docker ─────────────────────────────────────────────────────────────
echo [1/7] التحقق من Docker...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [خطأ] Docker غير مثبت. يرجى تثبيت Docker Desktop أولاً
    echo [ERROR] Docker not found. Please install Docker Desktop first.
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [✓] Docker موجود

:: ── Check Docker Compose ─────────────────────────────────────────────────────
echo [2/7] التحقق من Docker Compose...
docker compose version >nul 2>&1
if %errorLevel% neq 0 (
    echo [خطأ] Docker Compose غير متاح
    pause
    exit /b 1
)
echo [✓] Docker Compose موجود

:: ── Check NVIDIA GPU ─────────────────────────────────────────────────────────
echo [3/7] التحقق من GPU NVIDIA...
nvidia-smi >nul 2>&1
if %errorLevel% equ 0 (
    echo [✓] GPU NVIDIA موجود - سيتم استخدامه للذكاء الاصطناعي
    set GPU_AVAILABLE=true
) else (
    echo [!] لا يوجد GPU NVIDIA - سيعمل النظام على المعالج فقط (أبطأ)
    set GPU_AVAILABLE=false
)

:: ── Setup Environment ────────────────────────────────────────────────────────
echo [4/7] إعداد ملف البيئة...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [!] تم إنشاء ملف .env من القالب
    echo [!] يرجى تعديل كلمات المرور في ملف .env قبل المتابعة!
    echo.
    echo     افتح الملف: %CD%\.env
    echo     وعدّل جميع القيم التي تحتوي على CHANGE_THIS
    echo.
    set /p CONTINUE="هل عدّلت كلمات المرور؟ (y/n): "
    if /i "%CONTINUE%" neq "y" (
        echo تم الإلغاء. عدّل ملف .env ثم أعد التشغيل.
        pause
        exit /b 0
    )
) else (
    echo [✓] ملف .env موجود
)

:: ── Create Required Directories ──────────────────────────────────────────────
echo [5/7] إنشاء المجلدات المطلوبة...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\exports" mkdir "data\exports"
if not exist "logs" mkdir "logs"
if not exist "config\postgres" mkdir "config\postgres"
if not exist "config\prometheus" mkdir "config\prometheus"
if not exist "config\searxng" mkdir "config\searxng"
if not exist "config\grafana\dashboards" mkdir "config\grafana\dashboards"
echo [✓] المجلدات جاهزة

:: ── Pull Docker Images ───────────────────────────────────────────────────────
echo [6/7] تحميل صور Docker (قد يستغرق وقتاً)...
docker compose pull
if %errorLevel% neq 0 (
    echo [خطأ] فشل في تحميل الصور
    pause
    exit /b 1
)
echo [✓] تم تحميل جميع الصور

:: ── Start Services ───────────────────────────────────────────────────────────
echo [7/7] تشغيل جميع الخدمات...
docker compose up -d
if %errorLevel% neq 0 (
    echo [خطأ] فشل في تشغيل الخدمات
    pause
    exit /b 1
)

:: ── Wait for Services ────────────────────────────────────────────────────────
echo.
echo انتظار تهيئة الخدمات (30 ثانية)...
timeout /t 30 /nobreak >nul

:: ── Pull Default AI Model ────────────────────────────────────────────────────
echo تحميل نموذج الذكاء الاصطناعي الافتراضي (llama3)...
docker exec salehsaas_ollama ollama pull llama3
echo [✓] تم تحميل النموذج

:: ── Success Message ──────────────────────────────────────────────────────────
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                    ✅ تم التثبيت بنجاح!                         ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║  لوحة التحكم الرئيسية:  http://localhost:8000                   ║
echo ║  واجهة الذكاء الاصطناعي: http://localhost:3000                  ║
echo ║  أتمتة سير العمل (n8n): http://localhost:5678                   ║
echo ║  محرك البحث المحلي:     http://localhost:8080                   ║
echo ║  استوديو التطوير:       http://localhost:8443                   ║
echo ║  مراقبة الأداء:         http://localhost:3001                   ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
echo جميع البيانات تُعالج محلياً - لا يوجد إرسال خارجي
echo All data processed locally - Zero external transmission
echo.
pause
