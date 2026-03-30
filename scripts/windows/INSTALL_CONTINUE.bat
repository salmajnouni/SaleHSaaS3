@echo off
:: SaleHSaaS 3.0 - Install Continue.dev in Code Server
:: Run this after docker compose is up

REM WARNING:
REM Legacy helper for old Code Server flow. Not part of current runtime by default.
REM Keep for historical/dev recovery usage only.

echo.
echo ================================================================
echo   Installing Continue.dev in Code Server
echo   Connecting to local llama3 via Ollama
echo ================================================================
echo.

if /I not "%ALLOW_LEGACY_CODE_SERVER%"=="true" (
    echo [SKIP] Legacy Code Server flow is disabled by default.
    echo [INFO] Set ALLOW_LEGACY_CODE_SERVER=true then rerun if needed.
    goto :end
)

docker ps --format "{{.Names}}" | findstr /I "salehsaas_code_server" >nul
if %errorLevel% neq 0 (
    echo [SKIP] Container salehsaas_code_server is not running.
    echo [INFO] Start legacy dev studio first if you intentionally need this flow.
    goto :end
)

:: Step 1 - Install Continue extension inside code-server container
echo [1/3] Installing Continue.dev extension...
docker exec salehsaas_code_server code-server --install-extension Continue.continue
if %errorLevel% neq 0 (
    echo [FAIL] Extension install failed. Trying alternative method...
    docker exec salehsaas_code_server bash -c "curl -fsSL https://open-vsx.org/api/Continue/continue/latest/file/Continue.continue-latest.vsix -o /tmp/continue.vsix && code-server --install-extension /tmp/continue.vsix"
)
echo [OK] Continue.dev installed

:: Step 2 - Copy config file
echo [2/3] Copying Continue.dev config...
docker exec salehsaas_code_server bash -c "mkdir -p /home/coder/.continue"
docker cp config\continue\config.json salehsaas_code_server:/home/coder/.continue/config.json
echo [OK] Config copied

:: Step 3 - Restart code-server
echo [3/3] Restarting Code Server...
docker restart salehsaas_code_server
echo [OK] Code Server restarted

echo.
echo ================================================================
echo   Done! Open http://localhost:8443
echo   Look for the Continue icon in the left sidebar
echo ================================================================
echo.
:end
pause
