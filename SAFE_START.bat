@echo off
REM ================================================
REM SAFE START - Discord Sender Only
REM No duplicates, no ban risk
REM ================================================

cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION

echo.
echo ========================================
echo SAFE START - Discord Sender Only
echo ========================================
echo.

REM Make sure everything is stopped first
pm2 stop all >nul 2>&1
pm2 delete all >nul 2>&1

echo [1/3] Ensuring clean state...
timeout /t 2 >nul

echo [2/3] Creating necessary directories...
mkdir logs 2>nul
mkdir message_queue 2>nul
mkdir sent_archive 2>nul

echo [3/3] Starting Discord sender ONLY (safe mode)...
pm2 start ecosystem.config.js --only discord-sender

echo.
echo ========================================
echo STARTED: Discord Sender Only
echo ========================================
echo.
echo This is SAFE MODE - Only Discord sender running
echo No Python bots = No Telegram = No new messages
echo This just processes existing messages safely
echo.
pm2 list
echo.
echo To check status: pm2 list
echo To view logs: pm2 logs discord-sender
echo To stop: pm2 stop all
echo.
pause