@echo off
setlocal
set "APP=%~dp0FluxoLoad.exe"

if not exist "%APP%" (
    echo Executavel nao encontrado: "%APP%"
    pause
    exit /b 1
)

echo Removendo a marca de download do Windows para este teste...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath '%APP%' -ErrorAction SilentlyContinue"
start "FluxoLoad" "%APP%"
endlocal
