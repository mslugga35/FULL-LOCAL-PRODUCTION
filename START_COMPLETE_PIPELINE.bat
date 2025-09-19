@echo off
echo ========================================
echo    COMPLETE MESSAGE PIPELINE STARTUP
echo ========================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

echo 🔍 Checking pipeline health first...
python pipeline_monitor.py
echo.

echo 🛑 Stopping any existing services...
pm2 stop all
pm2 delete all
timeout /t 3

echo.
echo 🚀 Starting complete message pipeline...
echo.

echo 📡 Starting services with new ecosystem config...
pm2 start ecosystem-windows-fixed.config.js

echo.
echo ⏳ Waiting for services to initialize...
timeout /t 10

echo.
echo 📊 Service status:
pm2 status

echo.
echo 🔍 Initial pipeline health check:
python pipeline_monitor.py

echo.
echo ========================================
echo    PIPELINE STARTUP COMPLETE
echo ========================================
echo.
echo Services running:
echo   • telegram-collector   (Collects messages from Telegram)
echo   • message-processor     (Routes recent_messages to queue folders)
echo   • discord-sender        (Sends from queue to Discord webhooks)
echo   • discord-forwarder     (Discord-to-Discord forwarding)
echo.
echo Monitor with:
echo   pm2 status
echo   pm2 logs
echo   python pipeline_monitor.py
echo.
pause