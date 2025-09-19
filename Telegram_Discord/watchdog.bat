@echo off
REM PM2 Watchdog - Monitors and restarts services
REM This runs continuously to ensure services stay up

echo ========================================
echo PM2 Pipeline Watchdog
echo Started: %date% %time%
echo ========================================
echo.

:LOOP
REM Check if PM2 is running
pm2 pid >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] PM2 daemon not running, starting...
    pm2 resurrect
    timeout /t 5 /nobreak >nul
)

REM Check each service
pm2 describe tg-collector >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] tg-collector not found, starting...
    pm2 start ecosystem.config.js --only tg-collector
)

pm2 describe router >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] router not found, starting...
    pm2 start ecosystem.config.js --only router
)

pm2 describe forwarder >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] forwarder not found, starting...
    pm2 start ecosystem.config.js --only forwarder
)

REM Check for stopped services and restart them
for /f "tokens=2,8" %%a in ('pm2 jlist 2^>nul ^| findstr /C:"\"name\":" /C:"\"status\":"') do (
    if "%%b"=="\"stopped\"" (
        for /f "tokens=2 delims=:" %%c in ("%%a") do (
            set service=%%c
            set service=!service:"=!
            echo [%date% %time%] Restarting stopped service: !service!
            pm2 restart !service!
        )
    )
)

REM Save current state
pm2 save >nul 2>&1

REM Wait 60 seconds before next check
timeout /t 60 /nobreak >nul

REM Loop forever
goto LOOP