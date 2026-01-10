@echo off

where python >nul 2>&1
if errorlevel 1 (
    winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements
)

where python >nul 2>&1
if errorlevel 1 exit /b

pip install wxpython

if "%~1"=="" (
    exit /b
)

start "" python "%~dp0HTMA_PARSE.py" "%~1"
