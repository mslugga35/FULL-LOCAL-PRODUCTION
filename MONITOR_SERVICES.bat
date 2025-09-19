@echo off
:loop
cls
echo ========================================
echo SERVICE STATUS MONITOR - %date% %time%
echo ========================================
echo.

echo === PM2 SERVICES ===
pm2 list

echo.
echo === TELEGRAM COLLECTOR LOG (Last 10 lines) ===
if exist logs\telegram-collector.log (
    powershell -command "Get-Content logs\telegram-collector.log -Tail 10"
) else (
    echo No log file yet...
)

echo.
echo === INBOX STATUS ===
dir /b inbox 2>nul | find /c /v "" >temp.txt
set /p count=<temp.txt
del temp.txt
echo Messages in inbox: %count%

echo.
echo === MESSAGE QUEUES ===
for /d %%d in (message_queue\*) do (
    dir /b "%%d" 2>nul | find /c /v "" >temp.txt
    set /p qcount=<temp.txt
    del temp.txt
    echo %%d: %qcount% messages
)

echo.
echo === DISCORD FORWARDER LOG ===
if exist discord-forwarder\forwarder.log (
    powershell -command "Get-Content discord-forwarder\forwarder.log -Tail 5"
) else (
    echo No forwarder log yet...
)

echo.
echo Press Ctrl+C to stop monitoring...
timeout /t 10 /nobreak >nul
goto loop