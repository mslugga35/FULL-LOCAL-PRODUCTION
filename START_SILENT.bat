@echo off
REM ================================================
REM SILENT LOCAL PRODUCTION - NO CONSOLE WINDOWS
REM Everything runs in background
REM ================================================

cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION

REM Install dependencies silently
if not exist node_modules (
    npm install axios form-data bottleneck >nul 2>&1
)

REM Create necessary directories
mkdir inbox 2>nul
mkdir message_queue\uatb 2>nul
mkdir message_queue\paid_uatb 2>nul
mkdir message_queue\diamond 2>nul
mkdir message_queue\paid_diamond 2>nul
mkdir message_queue\paid_chamba 2>nul
mkdir message_queue\free_cappers 2>nul
mkdir logs 2>nul

REM Stop any existing PM2 processes
pm2 stop all >nul 2>&1
pm2 delete all >nul 2>&1

REM Start everything silently with PM2
pm2 start ecosystem.config.js --silent >nul 2>&1
pm2 save --silent >nul 2>&1

REM Set up Windows startup (silent)
pm2 startup windows --silent >nul 2>&1

REM Create VBS script for completely silent operation
echo Set objShell = CreateObject("Wscript.Shell") > start_hidden.vbs
echo objShell.Run "pm2 resurrect", 0, False >> start_hidden.vbs

REM Success notification (minimal)
echo Production started silently. Check with: pm2 list
timeout /t 2 >nul
exit