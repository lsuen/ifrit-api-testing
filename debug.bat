@echo off
REM ifrit-apitest 全流程调试（Windows）
setlocal enabledelayedexpansion

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python not found. Please install Python 3.10+
  exit /b 1
)

echo == ifrit-apitest debug workflow ==
echo Root: %CD%

python scripts\debug_workflow.py %*
exit /b %ERRORLEVEL%
