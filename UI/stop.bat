@echo off
REM ============================================================
REM ifrit-apitest Web UI 停止脚本（Windows）
REM 作者：孙文龙
REM 用途：停止后台运行的 UI 服务
REM ============================================================

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "UI_DIR=%~dp0"
cd /d "%UI_DIR%"

echo.
echo ============================================================
echo  ifrit-apitest Web UI 停止中...
echo ============================================================
echo.

REM ============================================================
REM 读取 PID 文件
REM ============================================================

set "PID_FILE=%UI_DIR%ui.pid"

if not exist "%PID_FILE%" (
    echo [WARN] PID 文件不存在，服务可能未运行
    pause
    exit /b 0
)

set /p PID=<"%PID_FILE%"

REM 检查进程是否存在
tasklist /FI "PID eq %PID%" 2>nul | find /I /N "python.exe">nul
if %errorlevel% neq 0 (
    echo [WARN] 进程 %PID% 不存在，清理 PID 文件
    del "%PID_FILE%"
    pause
    exit /b 0
)

REM ============================================================
REM 停止服务
REM ============================================================

echo [INFO] 正在停止 UI 服务 (PID: %PID%)...

REM 尝试优雅停止
taskkill /PID %PID% >nul 2>&1

REM 等待进程退出
timeout /t 3 /nobreak >nul

REM 检查是否已退出
tasklist /FI "PID eq %PID%" 2>nul | find /I /N "python.exe">nul
if %errorlevel% equ 0 (
    echo [WARN] 进程未响应，强制终止...
    taskkill /F /PID %PID% >nul 2>&1
)

REM 清理 PID 文件
del "%PID_FILE%" 2>nul

REM 检查最终状态
tasklist /FI "PID eq %PID%" 2>nul | find /I /N "python.exe">nul
if %errorlevel% neq 0 (
    echo [SUCCESS] UI 服务已停止
) else (
    echo [ERROR] 停止失败，请手动在任务管理器中结束进程 %PID%
)

echo.
echo ============================================================
echo  ifrit-apitest Web UI 已停止
echo ============================================================
echo.

pause
