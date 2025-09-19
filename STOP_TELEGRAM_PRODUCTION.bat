@echo off
:: STOP TELEGRAM PRODUCTION COLLECTOR

echo.
echo =========================================================
echo STOPPING TELEGRAM PRODUCTION COLLECTOR
echo =========================================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

:: Check if lock file exists
if not exist "telegram_capture.lock" (
    echo No lock file found - collector may not be running
    goto :check_processes
)

:: Read PID from lock file
for /f %%i in (telegram_capture.lock) do set LOCK_PID=%%i

echo Found lock file with PID: %LOCK_PID%

:: Check if process is running
tasklist /fi "PID eq %LOCK_PID%" 2>nul | findstr "%LOCK_PID%" >nul
if errorlevel 1 (
    echo Process %LOCK_PID% is not running - removing stale lock file
    del telegram_capture.lock
    goto :check_processes
)

:: Terminate the process gracefully first
echo Sending termination signal to PID %LOCK_PID%...
taskkill /pid %LOCK_PID% /t
timeout /t 5 /nobreak >nul

:: Check if it's still running
tasklist /fi "PID eq %LOCK_PID%" 2>nul | findstr "%LOCK_PID%" >nul
if not errorlevel 1 (
    echo Process still running, forcing termination...
    taskkill /f /pid %LOCK_PID% /t
    timeout /t 2 /nobreak >nul
)

:: Remove lock file
if exist "telegram_capture.lock" del telegram_capture.lock

:check_processes
:: Also check for any python processes running the collector
echo.
echo Checking for any remaining collector processes...

for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" ^| findstr "telegram_production_collector"') do (
    echo Found additional process: %%i
    taskkill /f /pid %%i
)

echo.
echo Telegram Production Collector stopped
echo.
pause