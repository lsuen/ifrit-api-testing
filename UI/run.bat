@echo off
setlocal
set "UI_DIR=%~dp0"
cd /d "%UI_DIR%"

echo ============================================================
echo  ifrit API 自动化测试平台 Web UI
echo ============================================================

where python >nul 2>&1 || (echo [ERROR] 未找到 Python & exit /b 1)

set "VENV=%UI_DIR%.venv"
if not exist "%VENV%\Scripts\python.exe" (
    python -m venv "%VENV%"
    "%VENV%\Scripts\python.exe" -m pip install -r requirements-ui.txt -q
)

echo 访问: http://127.0.0.1:5001
"%VENV%\Scripts\python.exe" app.py
