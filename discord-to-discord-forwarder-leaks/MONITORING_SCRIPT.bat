@echo off
title Discord Forwarder Monitor
color 0A

echo ==========================================
echo    Discord Forwarder Monitoring Panel
echo ==========================================
echo.

:monitor
echo [%TIME%] Checking status...
echo.

echo === PM2 STATUS ===
pm2 status | findstr discord-forwarder-python
echo.

echo === RECENT ACTIVITY ===
tail -5 forwarder.log
echo.

echo === ERROR CHECK ===
tail -20 forwarder.log | findstr "ERROR WARNING" > nul
if %errorlevel% == 0 (
    echo WARNING: Recent errors detected!
    tail -20 forwarder.log | findstr "ERROR WARNING"
) else (
    echo No recent errors detected.
)
echo.

echo === MESSAGE COUNT ===
for /f %%a in ('type forwarder.log ^| findstr /c:"Forwarded:" ^| find /c /v ""') do set count=%%a
echo Total messages forwarded: %count%
echo.

echo ==========================================
echo Press Ctrl+C to exit, waiting 60 seconds...
timeout /t 60 /nobreak > nul
cls
goto monitor