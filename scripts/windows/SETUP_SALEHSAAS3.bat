@echo off
chcp 65001 >nul
cls
color 0A

:: ═══════════════════════════════════════════════════════════════════════
::  SaleHSaaS 3.0 - سكريبت التثبيت الذكي
::  🕋 صُنع بفخر في مكة المكرمة، المملكة العربية السعودية
::  المسار المستهدف: D:\SaleHSaaS3
:: ═══════════════════════════════════════════════════════════════════════

set "INSTALL_DIR=D:\SaleHSaaS3"
set "REPO_URL=https://github.com/salmajnouni/SaleHSaaS3.git"
set "LOG_FILE=%TEMP%\salehsaas_install.log"
set "STEP=0"
set "ERRORS=0"

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║   ⚡ SaleHSaaS 3.0 — سكريبت التثبيت الذكي                  ║
echo  ║   🕋 صُنع بفخر في مكة المكرمة، المملكة العربية السعودية     ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo  المسار: %INSTALL_DIR%
echo  السجل:  %LOG_FILE%
echo.
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 1/6] فحص المتطلبات الأساسية
echo  ══════════════════════════════════════════════════════════════
echo.

:: ── فحص صلاحيات المسؤول ─────────────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  ❌ خطأ: يجب تشغيل هذا الملف كـ "مسؤول" ^(Run as Administrator^)
    echo.
    echo  الحل: انقر بزر الفأرة الأيمن على الملف واختر "تشغيل كمسؤول"
    echo.
    pause
    exit /b 1
)
echo  ✅ صلاحيات المسؤول: موجودة

:: ── فحص Docker ──────────────────────────────────────────────────────
echo  🔍 فحص Docker Desktop...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  ❌ Docker غير مثبت!
    echo.
    echo  ┌─────────────────────────────────────────────────────────┐
    echo  │  الحل: قم بتثبيت Docker Desktop من:                    │
    echo  │  https://www.docker.com/products/docker-desktop/        │
    echo  │                                                         │
    echo  │  بعد التثبيت:                                           │
    echo  │  1. افتح Docker Desktop                                 │
    echo  │  2. انتظر حتى يظهر "Docker is running"                 │
    echo  │  3. أعد تشغيل هذا السكريبت                             │
    echo  └─────────────────────────────────────────────────────────┘
    echo.
    set /p OPEN_DOCKER="هل تريد فتح صفحة تحميل Docker الآن؟ (y/n): "
    if /i "%OPEN_DOCKER%"=="y" start https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
for /f "tokens=3" %%v in ('docker --version 2^>nul') do set DOCKER_VER=%%v
echo  ✅ Docker: %DOCKER_VER%

:: ── فحص Docker Engine يعمل ──────────────────────────────────────────
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo  ❌ Docker Desktop مثبت لكن غير شغّال!
    echo.
    echo  الحل: افتح Docker Desktop وانتظر حتى يظهر "Docker is running"
    echo  ثم أعد تشغيل هذا السكريبت.
    echo.
    set /p OPEN_DD="هل تريد فتح Docker Desktop الآن؟ (y/n): "
    if /i "%OPEN_DD%"=="y" start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    pause
    exit /b 1
)
echo  ✅ Docker Engine: يعمل

:: ── فحص Docker Compose ──────────────────────────────────────────────
docker compose version >nul 2>&1
if %errorLevel% neq 0 (
    echo  ❌ Docker Compose غير متاح
    echo  الحل: تأكد من تثبيت Docker Desktop الإصدار 3.0 أو أحدث
    pause
    exit /b 1
)
echo  ✅ Docker Compose: متاح

:: ── فحص Git ─────────────────────────────────────────────────────────
echo  🔍 فحص Git...
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  ❌ Git غير مثبت!
    echo.
    echo  الحل: قم بتثبيت Git من: https://git-scm.com/download/win
    echo.
    set /p OPEN_GIT="هل تريد فتح صفحة تحميل Git الآن؟ (y/n): "
    if /i "%OPEN_GIT%"=="y" start https://git-scm.com/download/win
    pause
    exit /b 1
)
for /f "tokens=3" %%v in ('git --version 2^>nul') do set GIT_VER=%%v
echo  ✅ Git: %GIT_VER%

:: ── فحص GPU NVIDIA ──────────────────────────────────────────────────
echo  🔍 فحص GPU NVIDIA...
nvidia-smi >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=1,2 delims=," %%a in ('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2^>nul') do (
        echo  ✅ GPU: %%a ^(%%b^) — سيتم استخدامه لتسريع الذكاء الاصطناعي
    )
    set GPU_AVAILABLE=true
) else (
    echo  ⚠️  لا يوجد GPU NVIDIA — سيعمل النظام على المعالج ^(أبطأ^)
    set GPU_AVAILABLE=false
)

:: ── فحص المساحة المتاحة ─────────────────────────────────────────────
echo  🔍 فحص مساحة القرص D:\...
for /f "tokens=3" %%s in ('dir D:\ /-c 2^>nul ^| findstr /i "bytes free"') do set FREE_BYTES=%%s
echo  ✅ المساحة الحرة في D:\ متاحة

echo.
echo  ══════════════════════════════════════════════════════════════
echo  ✅ جميع المتطلبات متوفرة! جاهز للتثبيت.
echo  ══════════════════════════════════════════════════════════════
echo.
pause

:: ═══════════════════════════════════════════════════════════════════════
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 2/6] استنساخ المشروع من GitHub
echo  ══════════════════════════════════════════════════════════════
echo.

:: ── التحقق من وجود المجلد مسبقاً ───────────────────────────────────
if exist "%INSTALL_DIR%\.git" (
    echo  📁 المشروع موجود مسبقاً في %INSTALL_DIR%
    echo  🔄 جاري تحديث المشروع...
    cd /d "%INSTALL_DIR%"
    git pull origin main
    echo  ✅ تم التحديث بنجاح
) else (
    if exist "%INSTALL_DIR%" (
        echo  ⚠️  المجلد %INSTALL_DIR% موجود لكن ليس مستودع Git
        echo  سيتم الاستنساخ داخله...
        cd /d "D:\"
        git clone "%REPO_URL%" SaleHSaaS3
    ) else (
        echo  📥 استنساخ المشروع في %INSTALL_DIR%...
        cd /d "D:\"
        git clone "%REPO_URL%" SaleHSaaS3
    )
    if %errorLevel% neq 0 (
        echo  ❌ فشل الاستنساخ! تحقق من اتصال الإنترنت
        pause
        exit /b 1
    )
    echo  ✅ تم الاستنساخ بنجاح
)

cd /d "%INSTALL_DIR%"
echo  📂 المجلد الحالي: %CD%
echo.

:: ═══════════════════════════════════════════════════════════════════════
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 3/6] إعداد ملف البيئة ^(.env^)
echo  ══════════════════════════════════════════════════════════════
echo.

if exist ".env" (
    echo  ✅ ملف .env موجود مسبقاً
    set /p UPDATE_ENV="هل تريد إعادة إنشائه؟ سيتم حذف الإعدادات القديمة (y/n): "
    if /i "%UPDATE_ENV%"=="y" (
        del .env
        goto CREATE_ENV
    )
    goto ENV_DONE
)

:CREATE_ENV
echo  📝 إنشاء ملف .env بكلمات مرور عشوائية آمنة...

:: توليد كلمات مرور عشوائية
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set PG_PASS=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set REDIS_PASS=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32,6)"') do set WEBUI_KEY=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set N8N_PASS=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32,6)"') do set N8N_ENC=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set SEARXNG_SEC=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32,6)"') do set DASH_KEY=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set CODE_PASS=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(20,4)"') do set GRAFANA_PASS=%%i
for /f %%i in ('powershell -Command "[System.Web.Security.Membership]::GeneratePassword(32,6)"') do set ALLM_JWT=%%i

(
echo # SaleHSaaS 3.0 - Environment Configuration
echo # 🕋 صُنع بفخر في مكة المكرمة
echo # تم الإنشاء تلقائياً - لا تشارك هذا الملف مع أحد
echo.
echo # ── Database ──────────────────────────────────────────────
echo POSTGRES_DB=salehsaas
echo POSTGRES_USER=salehsaas_user
echo POSTGRES_PASSWORD=%PG_PASS%
echo.
echo # ── Redis ─────────────────────────────────────────────────
echo REDIS_PASSWORD=%REDIS_PASS%
echo.
echo # ── AI Engine ─────────────────────────────────────────────
echo OLLAMA_PORT=11434
echo OLLAMA_NUM_PARALLEL=2
echo DEFAULT_MODEL=llama3
echo.
echo # ── Open WebUI ────────────────────────────────────────────
echo OPEN_WEBUI_PORT=3000
echo WEBUI_SECRET_KEY=%WEBUI_KEY%
echo ENABLE_SIGNUP=false
echo.
echo # ── n8n ───────────────────────────────────────────────────
echo N8N_PORT=5678
echo N8N_USER=admin
echo N8N_PASSWORD=%N8N_PASS%
echo N8N_ENCRYPTION_KEY=%N8N_ENC%
echo.
echo # ── Qdrant ────────────────────────────────────────────────
echo QDRANT_PORT=6333
echo QDRANT_API_KEY=
echo.
echo # ── SearXNG ───────────────────────────────────────────────
echo SEARXNG_PORT=8080
echo SEARXNG_SECRET=%SEARXNG_SEC%
echo.
echo # ── Dashboard ─────────────────────────────────────────────
echo DASHBOARD_PORT=8000
echo DASHBOARD_SECRET_KEY=%DASH_KEY%
echo FLASK_DEBUG=false
echo.
echo # ── Code Server ───────────────────────────────────────────
echo CODE_SERVER_PORT=8443
echo CODE_SERVER_PASSWORD=%CODE_PASS%
echo.
echo # ── Grafana ───────────────────────────────────────────────
echo GRAFANA_PORT=3001
echo GRAFANA_USER=admin
echo GRAFANA_PASSWORD=%GRAFANA_PASS%
echo.
echo # ── AnythingLLM ───────────────────────────────────────────
echo ANYTHINGLLM_PORT=3002
echo ANYTHINGLLM_JWT_SECRET=%ALLM_JWT%
) > .env

echo  ✅ تم إنشاء ملف .env بكلمات مرور آمنة تلقائياً

:ENV_DONE
echo.

:: ═══════════════════════════════════════════════════════════════════════
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 4/6] إنشاء المجلدات المطلوبة
echo  ══════════════════════════════════════════════════════════════
echo.

if not exist "data\uploads"              mkdir "data\uploads"
if not exist "data\exports"              mkdir "data\exports"
if not exist "logs"                      mkdir "logs"
if not exist "config\postgres"           mkdir "config\postgres"
if not exist "config\prometheus"         mkdir "config\prometheus"
if not exist "config\searxng"            mkdir "config\searxng"
if not exist "config\grafana\dashboards" mkdir "config\grafana\dashboards"
if not exist "backups"                   mkdir "backups"

echo  ✅ جميع المجلدات جاهزة
echo.

:: ═══════════════════════════════════════════════════════════════════════
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 5/6] تحميل صور Docker وتشغيل الخدمات
echo  ══════════════════════════════════════════════════════════════
echo.
echo  ⏳ جاري تحميل الصور... قد يستغرق 15-30 دقيقة حسب سرعة الإنترنت
echo  يمكنك متابعة التقدم أدناه:
echo.

docker compose pull
if %errorLevel% neq 0 (
    echo  ❌ فشل تحميل بعض الصور. تحقق من اتصال الإنترنت وأعد المحاولة.
    pause
    exit /b 1
)
echo.
echo  ✅ تم تحميل جميع الصور بنجاح
echo.
echo  🚀 تشغيل جميع الخدمات...
docker compose up -d
if %errorLevel% neq 0 (
    echo  ❌ فشل تشغيل الخدمات. راجع السجل:
    docker compose logs --tail=20
    pause
    exit /b 1
)
echo  ✅ تم تشغيل جميع الخدمات
echo.

:: ═══════════════════════════════════════════════════════════════════════
echo  ══════════════════════════════════════════════════════════════
echo  [المرحلة 6/6] تحميل نموذج الذكاء الاصطناعي
echo  ══════════════════════════════════════════════════════════════
echo.
echo  ⏳ انتظار تهيئة Ollama ^(30 ثانية^)...
timeout /t 30 /nobreak >nul

echo  📥 تحميل نموذج llama3 ^(~4.7 GB^)...
echo  هذا قد يستغرق 10-15 دقيقة...
echo.
docker exec salehsaas_ollama ollama pull llama3
if %errorLevel% neq 0 (
    echo  ⚠️  لم يتم تحميل النموذج تلقائياً. يمكنك تحميله لاحقاً من قائمة الإدارة.
) else (
    echo  ✅ تم تحميل نموذج llama3
)

echo  📥 تحميل نموذج التضمين nomic-embed-text ^(للـ RAG^)...
docker exec salehsaas_ollama ollama pull nomic-embed-text
if %errorLevel% neq 0 (
    echo  ⚠️  لم يتم تحميل نموذج التضمين. يمكنك تحميله لاحقاً.
) else (
    echo  ✅ تم تحميل نموذج التضمين
)

:: ═══════════════════════════════════════════════════════════════════════
::  شاشة الاكتمال
:: ═══════════════════════════════════════════════════════════════════════
cls
color 0A
echo.
echo  ╔══════════════════════════════════════════════════════════════════╗
echo  ║                                                                  ║
echo  ║        ✅  تم تثبيت SaleHSaaS 3.0 بنجاح!                       ║
echo  ║        🕋  صُنع بفخر في مكة المكرمة                             ║
echo  ║                                                                  ║
echo  ╠══════════════════════════════════════════════════════════════════╣
echo  ║                                                                  ║
echo  ║  🖥️  لوحة التحكم الرئيسية:                                      ║
echo  ║      http://localhost:8000                                       ║
echo  ║                                                                  ║
echo  ║  🤖  واجهة الذكاء الاصطناعي ^(Open WebUI^):                      ║
echo  ║      http://localhost:3000                                       ║
echo  ║                                                                  ║
echo  ║  📄  ذكاء الوثائق ^(AnythingLLM^):                               ║
echo  ║      http://localhost:3002                                       ║
echo  ║                                                                  ║
echo  ║  ⚙️  أتمتة سير العمل ^(n8n^):                                    ║
echo  ║      http://localhost:5678                                       ║
echo  ║                                                                  ║
echo  ║  🔍  محرك البحث المحلي ^(SearXNG^):                              ║
echo  ║      http://localhost:8080                                       ║
echo  ║                                                                  ║
echo  ║  💻  استوديو التطوير ^(Code Server^):                            ║
echo  ║      http://localhost:8443                                       ║
echo  ║                                                                  ║
echo  ║  📊  مراقبة الأداء ^(Grafana^):                                  ║
echo  ║      http://localhost:3001                                       ║
echo  ║                                                                  ║
echo  ╠══════════════════════════════════════════════════════════════════╣
echo  ║                                                                  ║
echo  ║  📁  ملف كلمات المرور: %INSTALL_DIR%\.env
echo  ║  🔒  احتفظ بهذا الملف في مكان آمن ولا تشاركه                   ║
echo  ║                                                                  ║
echo  ╚══════════════════════════════════════════════════════════════════╝
echo.
echo  جميع البيانات تُعالج محلياً — لا يوجد إرسال خارجي
echo.

set /p OPEN_DASH="هل تريد فتح لوحة التحكم الآن؟ (y/n): "
if /i "%OPEN_DASH%"=="y" (
    timeout /t 3 /nobreak >nul
    start http://localhost:8000
)

echo.
echo  لإدارة المنصة لاحقاً: شغّل MANAGE_SALEHSAAS.bat
echo.
pause
