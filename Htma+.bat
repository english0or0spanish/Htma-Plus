@echo off
pip install wxpython
if "%~1"=="" (
    echo Usage: Htma+.bat filename.htma
    pause
    exit /b
)
python "%~dp0HTMA_PARSE.py" "%~1"
