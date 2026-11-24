@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "PYTHON_EXE="

where py >nul 2>nul
if not errorlevel 1 for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
if not defined PYTHON_EXE (
  where winget >nul 2>nul
  if errorlevel 1 goto :erro
  echo Python nao encontrado. Tentando instalar Python 3.14 pelo WinGet...
  winget install --id Python.Python.3.14 -e --scope user --accept-source-agreements --accept-package-agreements
  if errorlevel 1 goto :erro
  if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
)
if not defined PYTHON_EXE goto :erro

set "FLUXOLOAD_SOURCE=%CD%"
set "FLUXOLOAD_PYTHON=%PYTHON_EXE%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$arg=@('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $env:FLUXOLOAD_SOURCE 'scripts\instalar_fluxoload.ps1'),'-SourceRoot',$env:FLUXOLOAD_SOURCE,'-PythonExe',$env:FLUXOLOAD_PYTHON); $p=Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList $arg; exit $p.ExitCode"
if errorlevel 1 goto :erro
exit /b 0

:erro
echo A instalacao do FluxoLoad nao foi concluida.
if exist "%TEMP%\FluxoLoad-install.log" (
  echo.
  echo Detalhes do erro:
  type "%TEMP%\FluxoLoad-install.log"
  echo.
  echo O log completo esta em: %TEMP%\FluxoLoad-install.log
)
pause
exit /b 1
