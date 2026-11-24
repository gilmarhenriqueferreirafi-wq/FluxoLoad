@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
set "PYTHON_EXE="

rem Primeiro tenta o Python Launcher, que normalmente atualiza o PATH sozinho.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; print(sys.executable)" > "%TEMP%\fluxoload-python-path.txt" 2>nul
    if not errorlevel 1 set /p PYTHON_EXE=<"%TEMP%\fluxoload-python-path.txt"
    del /q "%TEMP%\fluxoload-python-path.txt" >nul 2>nul
)

rem Depois tenta o python.exe disponível no PATH.
if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)

rem Se não houver Python, instala o Python oficial pelo WinGet.
if not defined PYTHON_EXE (
    echo Python nao encontrado. Tentando instalar a versao oficial mais recente...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo O WinGet nao esta disponivel neste computador.
        echo Instale o Python em https://www.python.org/downloads/ e execute este arquivo novamente.
        pause
        exit /b 1
    )
    winget install --id Python.Python.3.14 -e --scope user --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo Nao foi possivel instalar o Python automaticamente.
        pause
        exit /b 1
    )
    if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
    if not defined PYTHON_EXE if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python313\python.exe"
    if not defined PYTHON_EXE (
        echo Python foi instalado, mas o executavel nao foi localizado.
        echo Feche e abra este arquivo novamente para atualizar o PATH.
        pause
        exit /b 1
    )
)

if not exist "%PYTHON_EXE%" (
    echo Python nao localizado: %PYTHON_EXE%
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual local...
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 goto :erro
)

echo Atualizando ferramentas do pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :erro

echo Instalando dependencias do FluxoLoad...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro

echo Iniciando FluxoLoad pelo codigo-fonte...
".venv\Scripts\python.exe" run.py
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" echo O FluxoLoad terminou com codigo %EXIT_CODE%.
pause
exit /b %EXIT_CODE%

:erro
echo Falha ao preparar o ambiente do FluxoLoad.
pause
exit /b 1
