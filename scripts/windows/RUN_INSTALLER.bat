@echo off
:: SaleHSaaS 3.0 - Launcher (runs PowerShell installer)
:: Run this file as Administrator

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_SALEHSAAS3.ps1"
pause
