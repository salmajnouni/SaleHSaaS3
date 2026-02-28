@echo off
chcp 65001 >nul
cls

:MENU
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║          SaleHSaaS 3.0 - إدارة المنصة                          ║
echo ╠══════════════════════════════════════════════════════════════════╣
echo ║  [1] تشغيل جميع الخدمات         Start All Services             ║
echo ║  [2] إيقاف جميع الخدمات         Stop All Services              ║
echo ║  [3] إعادة تشغيل الخدمات        Restart All Services           ║
echo ║  [4] عرض حالة الخدمات           Show Services Status           ║
echo ║  [5] عرض سجلات الأخطاء          Show Error Logs                ║
echo ║  [6] تحديث المنصة               Update Platform                ║
echo ║  [7] نسخ احتياطي                Backup Data                    ║
echo ║  [8] تحميل نموذج ذكاء اصطناعي  Pull AI Model                  ║
echo ║  [9] فتح لوحة التحكم            Open Dashboard                 ║
echo ║  [0] خروج                       Exit                           ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.
set /p CHOICE="اختر رقماً: "

if "%CHOICE%"=="1" goto START
if "%CHOICE%"=="2" goto STOP
if "%CHOICE%"=="3" goto RESTART
if "%CHOICE%"=="4" goto STATUS
if "%CHOICE%"=="5" goto LOGS
if "%CHOICE%"=="6" goto UPDATE
if "%CHOICE%"=="7" goto BACKUP
if "%CHOICE%"=="8" goto PULL_MODEL
if "%CHOICE%"=="9" goto OPEN_DASHBOARD
if "%CHOICE%"=="0" exit /b 0
goto MENU

:START
echo تشغيل جميع الخدمات...
docker compose up -d
echo [✓] تم التشغيل
pause
goto MENU

:STOP
echo إيقاف جميع الخدمات...
docker compose down
echo [✓] تم الإيقاف
pause
goto MENU

:RESTART
echo إعادة تشغيل الخدمات...
docker compose restart
echo [✓] تمت إعادة التشغيل
pause
goto MENU

:STATUS
echo.
echo حالة الخدمات:
docker compose ps
pause
goto MENU

:LOGS
echo.
echo سجلات الأخطاء (آخر 50 سطر):
docker compose logs --tail=50
pause
goto MENU

:UPDATE
echo تحديث المنصة...
git pull origin main
docker compose pull
docker compose up -d
echo [✓] تم التحديث
pause
goto MENU

:BACKUP
set BACKUP_DIR=backups\%date:~-4,4%-%date:~-7,2%-%date:~-10,2%
mkdir "%BACKUP_DIR%" 2>nul
echo إنشاء نسخة احتياطية في %BACKUP_DIR%...
docker exec salehsaas_postgres pg_dump -U salehsaas_user salehsaas > "%BACKUP_DIR%\database.sql"
echo [✓] تم حفظ قاعدة البيانات
xcopy /E /I /Q data "%BACKUP_DIR%\data" >nul
echo [✓] تم حفظ البيانات
echo [✓] النسخة الاحتياطية في: %BACKUP_DIR%
pause
goto MENU

:PULL_MODEL
echo.
echo النماذج المتاحة:
echo   1. llama3 (موصى به - 4.7GB)
echo   2. mistral (سريع - 4.1GB)
echo   3. qwen2 (عربي جيد - 4.4GB)
echo   4. gemma2 (دقيق - 5.4GB)
echo   5. نموذج مخصص
echo.
set /p MODEL_CHOICE="اختر نموذجاً (1-5): "
if "%MODEL_CHOICE%"=="1" set MODEL=llama3
if "%MODEL_CHOICE%"=="2" set MODEL=mistral
if "%MODEL_CHOICE%"=="3" set MODEL=qwen2
if "%MODEL_CHOICE%"=="4" set MODEL=gemma2
if "%MODEL_CHOICE%"=="5" (
    set /p MODEL="أدخل اسم النموذج: "
)
echo تحميل نموذج %MODEL%...
docker exec salehsaas_ollama ollama pull %MODEL%
echo [✓] تم تحميل النموذج
pause
goto MENU

:OPEN_DASHBOARD
start http://localhost:8000
goto MENU
