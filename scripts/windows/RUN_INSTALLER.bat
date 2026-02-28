@echo off
:: SaleHSaaS 3.0 - Launcher
:: Auto-elevates to Administrator if needed

net session >nul 2>&1
if %errorLevel% == 0 goto :RUN

:: Not admin - re-launch as admin automatically
echo Requesting Administrator privileges...
powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b

:RUN
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_SALEHSAAS3.ps1"
pause
