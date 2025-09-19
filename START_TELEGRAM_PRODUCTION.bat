@echo off
:: PRODUCTION TELEGRAM COLLECTOR STARTUP
:: Single-instance, robust, production-ready

echo.
echo =========================================================
echo TELEGRAM PRODUCTION COLLECTOR STARTUP
echo =========================================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found or not in PATH
    echo Please install Python 3.8+ and ensure it's in your PATH
    pause
    exit /b 1
)

:: Check if required packages are installed
echo Checking dependencies...
python -c "import telethon, asyncio" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages not installed
    echo Installing telethon...
    pip install telethon cryptg
    if errorlevel 1 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Check if session is configured
if not exist ".env" (
    echo.
    echo WARNING: No .env file found
    echo You need to authenticate first.
    echo.
    choice /c YN /m "Run authentication setup now? (Y/N)"
    if errorlevel 2 goto :skip_auth

    echo.
    echo Running authentication...
    python auth_session_production.py
    if errorlevel 1 (
        echo Authentication failed
        pause
        exit /b 1
    )
)

:skip_auth

:: Check for existing instance
if exist "telegram_capture.lock" (
    echo.
    echo WARNING: Lock file found - checking if instance is running...

    :: Try to read PID from lock file
    for /f %%i in (telegram_capture.lock) do set LOCK_PID=%%i

    :: Check if PID is running
    tasklist /fi "PID eq %LOCK_PID%" 2>nul | findstr "%LOCK_PID%" >nul
    if not errorlevel 1 (
        echo ERROR: Another instance is already running (PID: %LOCK_PID%)
        echo Use STOP_TELEGRAM_PRODUCTION.bat to stop it first
        pause
        exit /b 1
    ) else (
        echo Removing stale lock file...
        del telegram_capture.lock
    )
)

:: Create log directory if it doesn't exist
if not exist "logs" mkdir logs

:: Start the collector
echo.
echo Starting Telegram Production Collector...
echo Monitor logs in: logs\telegram_collector_%date:~10,4%%date:~4,2%%date:~7,2%.log
echo.
echo To stop: Press Ctrl+C or run STOP_TELEGRAM_PRODUCTION.bat
echo To monitor: run MONITOR_TELEGRAM_PRODUCTION.bat
echo.

:: Start with error handling
python telegram_production_collector.py
set EXIT_CODE=%errorlevel%

:: Check exit code
if %EXIT_CODE% equ 0 (
    echo.
    echo Collector stopped normally
) else (
    echo.
    echo Collector stopped with error code: %EXIT_CODE%
    echo Check logs for details
)

pause