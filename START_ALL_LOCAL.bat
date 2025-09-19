@echo off
REM ================================================
REM START ALL BOTS LOCALLY - COMPLETE SYSTEM
REM ================================================

echo.
echo ============================================
echo    STARTING ALL LOCAL BOTS
echo    Telegram, OCR, Discord - Everything!
echo ============================================
echo.

cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION

REM Clean start
echo [1/5] Stopping any existing processes...
pm2 stop all >nul 2>&1
pm2 delete all >nul 2>&1
timeout /t 2 >nul

REM Create directories
echo [2/5] Creating necessary directories...
mkdir inbox 2>nul
mkdir message_queue\uatb 2>nul
mkdir message_queue\paid_uatb 2>nul
mkdir message_queue\diamond 2>nul
mkdir message_queue\paid_diamond 2>nul
mkdir message_queue\paid_chamba 2>nul
mkdir message_queue\free_cappers 2>nul
mkdir message_queue\exclusive_cappers 2>nul
mkdir message_queue\leaked_cappers 2>nul
mkdir logs 2>nul
mkdir sent_archive 2>nul
mkdir config 2>nul

REM Check dependencies
echo [3/5] Checking dependencies...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.x
    pause
    exit /b 1
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js
    pause
    exit /b 1
)

REM Install if needed
if not exist node_modules (
    echo Installing Node dependencies...
    npm install axios form-data bottleneck
)

REM Start everything
echo [4/5] Starting all services with PM2...
pm2 start ecosystem-complete.config.js

REM Save PM2 configuration
echo [5/5] Saving PM2 configuration...
pm2 save
pm2 startup windows >nul 2>&1

echo.
echo ============================================
echo    ALL SERVICES STARTED LOCALLY
echo ============================================
echo.
pm2 list
echo.
echo Services Running:
echo - Telegram Collector: Downloads from Telegram
echo - Message Processor: Sorts messages
echo - Discord Sender: Sends to Discord
echo - OCR Processor: Extracts text from images
echo - Watchdog: Monitors and restarts if crash
echo.
echo Commands:
echo - Check status: pm2 list
echo - View logs: pm2 logs
echo - Monitor: pm2 monit
echo - Stop all: pm2 stop all
echo.
echo Everything is now running 100%% LOCALLY!
echo No Hetzner dependency!
echo.
pause