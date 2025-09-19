@echo off
REM Telegram-Discord Pipeline Auto-Start Script
REM This script ensures all services start on system boot

echo ========================================
echo Starting Telegram-Discord Pipeline
echo ========================================
echo.

REM Set working directory
cd /d C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord

REM Wait for system to stabilize after boot
echo Waiting for system to stabilize...
timeout /t 10 /nobreak > nul

REM Check if PM2 is available
where pm2 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PM2 not found in PATH
    echo Please install PM2: npm install -g pm2
    pause
    exit /b 1
)

REM Kill any existing PM2 daemon (clean start)
echo Cleaning up any existing PM2 processes...
pm2 kill >nul 2>&1
timeout /t 2 /nobreak > nul

REM Start PM2 and resurrect saved processes
echo Starting PM2 daemon...
pm2 resurrect
if %ERRORLEVEL% NEQ 0 (
    echo Failed to resurrect saved processes.
    echo Starting services manually...

    REM Fallback: Start services manually
    pm2 start ecosystem.config.js

    REM Save the process list
    pm2 save
)

REM Wait a moment for services to start
timeout /t 5 /nobreak > nul

REM Check service status
echo.
echo ========================================
echo Checking service status...
echo ========================================
pm2 list

REM Keep services running with auto-restart
echo.
echo ========================================
echo Services configured with auto-restart
echo ========================================
pm2 restart tg-collector --update-env
pm2 restart router --update-env
pm2 restart forwarder --update-env

REM Log startup completion
echo.
echo ========================================
echo Pipeline startup complete!
echo Time: %date% %time%
echo ========================================

REM Create a log entry
echo [%date% %time%] Pipeline started successfully >> startup.log

REM Keep window open for 10 seconds to show status
timeout /t 10

REM Minimize to system tray (PM2 continues running)
exit