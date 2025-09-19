@echo off
:: MONITOR TELEGRAM PRODUCTION COLLECTOR

echo.
echo =========================================================
echo TELEGRAM PRODUCTION COLLECTOR MONITOR
echo =========================================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

:monitor_loop

cls
echo =========================================================
echo TELEGRAM PRODUCTION COLLECTOR STATUS
echo Time: %date% %time%
echo =========================================================
echo.

:: Check if lock file exists
if exist "telegram_capture.lock" (
    for /f %%i in (telegram_capture.lock) do set LOCK_PID=%%i
    echo Lock file found - PID: %LOCK_PID%

    :: Check if process is actually running
    tasklist /fi "PID eq %LOCK_PID%" 2>nul | findstr "%LOCK_PID%" >nul
    if not errorlevel 1 (
        echo Status: RUNNING
        echo PID: %LOCK_PID%

        :: Get process details
        for /f "tokens=5" %%m in ('tasklist /fi "PID eq %LOCK_PID%" /fo table ^| findstr "%LOCK_PID%"') do echo Memory Usage: %%m
    ) else (
        echo Status: NOT RUNNING (stale lock file)
        echo Action needed: Remove stale lock or restart
    )
) else (
    echo Lock file: NOT FOUND
    echo Status: NOT RUNNING
)

echo.
echo =========================================================
echo RECENT ACTIVITY
echo =========================================================

:: Show recent log entries if available
set TODAY=%date:~10,4%%date:~4,2%%date:~7,2%
set LOGFILE=logs\telegram_collector_%TODAY%.log

if exist "%LOGFILE%" (
    echo Last 10 log entries:
    echo.
    powershell -command "Get-Content '%LOGFILE%' | Select-Object -Last 10"
) else (
    echo No log file found for today: %LOGFILE%
)

echo.
echo =========================================================
echo INBOX STATUS
echo =========================================================

if exist "inbox" (
    for /f %%i in ('dir inbox\*.json /b 2^>nul ^| find /c ".json"') do echo Messages today: %%i
    for /f %%i in ('dir inbox\media\*.* /b 2^>nul ^| find /c /v ""') do echo Media files: %%i

    :: Show recent files
    echo.
    echo Recent files:
    dir inbox\*.json /o-d /b 2>nul | head -n 5
) else (
    echo Inbox directory not found
)

echo.
echo =========================================================
echo CONTROLS
echo =========================================================
echo [R] Refresh     [S] Start     [T] Stop     [L] View Logs     [Q] Quit
echo.

choice /c RSTLQ /n /m "Select option: "
set CHOICE=%errorlevel%

if %CHOICE%==1 goto :monitor_loop
if %CHOICE%==2 (
    echo.
    echo Starting collector...
    call START_TELEGRAM_PRODUCTION.bat
    goto :monitor_loop
)
if %CHOICE%==3 (
    echo.
    echo Stopping collector...
    call STOP_TELEGRAM_PRODUCTION.bat
    goto :monitor_loop
)
if %CHOICE%==4 (
    echo.
    echo Opening log file...
    if exist "%LOGFILE%" (
        notepad "%LOGFILE%"
    ) else (
        echo No log file found
        pause
    )
    goto :monitor_loop
)

echo.
echo Monitor closed
pause