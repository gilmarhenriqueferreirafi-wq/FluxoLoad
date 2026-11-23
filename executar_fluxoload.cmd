@echo off
setlocal
set "APP=%~dp0beta1.1youtube_estable_FluxoLoad.exe"

if not exist "%APP%" (
    echo Executavel nao encontrado.
    echo Extraia o ZIP completo antes de executar este arquivo.
    pause
    exit /b 1
)

start "FluxoLoad" "%APP%"
endlocal
