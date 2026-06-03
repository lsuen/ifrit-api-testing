@echo off
REM ifrit-apitest Web UI Startup Script (Windows)
REM Author: sunwl

setlocal enabledelayedexpansion

set "UI_DIR=%~dp0"
set "PROJECT_DIR=%UI_DIR%.."
cd /d "%UI_DIR%"

echo.
echo ============================================================
echo  ifrit-apitest Web UI Starting...
echo ============================================================
echo.

echo [INFO] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python Version: %PYTHON_VERSION%

set "VENV_DIR=%PROJECT_DIR%.venv"
set "REQUIREMENTS=%UI_DIR%requirements-ui.txt"
set "PYTHON_EXE=D:\CodeFiles\EduFiles\ifrit-apitest\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

if exist "%REQUIREMENTS%" (
    echo [INFO] Checking dependencies...
    "%PYTHON_EXE%" -m pip show flask >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] Installing dependencies...
        "%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS%" --quiet
    )
    echo [SUCCESS] Dependencies OK
)

set "CONFIG_FILE=%UI_DIR%config.yaml"
if not exist "%CONFIG_FILE%" (
    echo [ERROR] Config not found: %CONFIG_FILE%
    pause
    exit /b 1
)
echo [SUCCESS] Config OK

echo.
echo ============================================================
echo  Starting ifrit-apitest Web UI...
echo  URL: http://localhost:5001
echo  Press Ctrl+C to stop
echo ============================================================
echo.

"%PYTHON_EXE%" app.py
