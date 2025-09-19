@echo off
echo ================================================
echo STARTING ALL LOCAL PRODUCTION SERVICES
echo ================================================
echo.

echo [1/5] Stopping any existing services...
pm2 delete all 2>nul

echo.
echo [2/5] Starting Discord Sender...
pm2 start discord_sender.js --name discord-sender

echo.
echo [3/5] Starting Watchdog...
pm2 start scripts/watchdog.js --name watchdog

echo.
echo [4/5] Starting Telegram Collector (Python)...
start /b python python/telegram_to_discord.py

echo.
echo [5/5] Starting Discord-to-Discord Forwarder (Python)...
cd discord-forwarder
start /b python forwarder.py
cd ..

echo.
echo ================================================
echo ALL SERVICES STARTED!
echo ================================================
echo.
echo Services Running:
echo - Discord Sender (PM2)
echo - Watchdog (PM2)
echo - Telegram Collector (Python - 5 channels)
echo - Discord Forwarder (Python - 49 channels)
echo.
echo To check status: pm2 list
echo To view logs: pm2 logs
echo.
pause