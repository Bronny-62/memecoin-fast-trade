@echo off
chcp 65001 >nul
title Monitor Service

echo Starting Monitor Service...

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo Python not found. Please install Python.
        pause
        exit /b 1
    ) else (
        set PYTHON=python3
    )
) else (
    set PYTHON=python
)

echo Using Python: %PYTHON%

:: Check virtual environment
set CREATED_VENV=0
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    %PYTHON% -m venv .venv
    set CREATED_VENV=1
)

:: Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
if "%CREATED_VENV%"=="1" (
    pip install --disable-pip-version-check -r requirements.txt
) else (
    pip install --disable-pip-version-check -q -r requirements.txt >nul
)
if errorlevel 1 (
    echo Dependency installation failed.
    call deactivate
    pause
    exit /b 1
)
if "%CREATED_VENV%"=="1" (
    echo Dependencies installed successfully.
) else (
    echo Dependencies check passed.
)

set PYTHONPATH=%CD%\src;%PYTHONPATH%

echo.
echo === 平台兼容性检查 ===
%PYTHON% -m monitoring_service.tools.platform_check
if errorlevel 1 (
    echo [ERROR] 平台兼容性检查失败。
    call deactivate
    pause
    exit /b 1
)

:: Check Telegram authorization and connectivity on every startup
echo.
echo === Telegram 授权与机器人连接检查 ===
echo [SETUP] 每次启动都会检查 Telegram 会话与机器人联通性。
echo [SETUP] 如果当前未授权，将自动进入手机号和验证码验证流程。
echo.
%PYTHON% -m monitoring_service.tools.telegram_auth
if errorlevel 1 (
    echo Telegram authorization or connectivity check failed.
    call deactivate
    pause
    exit /b 1
)

:: Clean up existing processes on port 8051 ONLY (do not affect port 8050)
echo Checking for existing services on port 8051...
set FOUND_PROCESS=0
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8051" 2^>nul') do (
    set FOUND_PROCESS=1
    echo Terminating process on port 8051 [PID: %%a]...
    taskkill /PID %%a /F >nul 2>&1
)
if %FOUND_PROCESS%==0 (
    echo Port 8051 is available.
) else (
    echo Process terminated.
)
echo Note: Other systems on port 8050 are NOT affected.

:: Start service
echo ==========================================
echo MemeCoin Fast Trade 1.0
echo Starting service (MemeCoin Fast Trade 1.0) on port 8051...
echo Service URL: http://localhost:8051
echo WebSocket: ws://localhost:8051/ws
echo.
echo Config Path:
echo   - config\config.ini
echo   - config\token_mapping.json
echo   - config\monitored_users.json
echo   - BSC uses Sigma Bot
echo   - XLayer uses BasedBot
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.
%PYTHON% -m monitoring_service

:: Cleanup
call deactivate
pause

