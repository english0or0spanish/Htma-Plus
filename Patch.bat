@echo off
net session >nul 2>&1
if not %errorlevel% == 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)
echo Setting up .htma file defaults...
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "HTMA_BAT=%SCRIPT_DIR%\Htma+.bat"
echo Directory: %SCRIPT_DIR%
echo Batch found! %HTMA_BAT%
if not exist "%HTMA_BAT%" (
    echo ERROR: Htma+.bat not found in %SCRIPT_DIR%
    pause
    exit /b 1
)
echo Creating file defaults for .htma files...
assoc .htma=HtmaFile
ftype HtmaFile="%HTMA_BAT%" "%%1"
echo Success!
echo Adding %SCRIPT_DIR% to system PATH...
setx PATH "%PATH%;%SCRIPT_DIR%" /M >nul 2>&1
if %errorlevel% == 0 (
    echo Success!
) else (
    echo Error: Failed to add to PATH.
)
pause