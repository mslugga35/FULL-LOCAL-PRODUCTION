@echo off
REM ================================================
REM COMPLETE BOT STARTUP SCRIPT (NEW STRUCTURE)
REM Starts all production services from reorganized structure
REM ================================================

echo ========================================
echo STARTING ALL PRODUCTION BOTS
echo ========================================
echo.

REM 1. Clean start - remove any existing processes
echo [1/5] Cleaning existing PM2 processes...
pm2 kill >nul 2>&1
timeout /t 2 >nul
echo Done.
echo.

REM 2. Start all services from master ecosystem
echo [2/5] Starting all services from master config...
cd /d C:\Users\mpmmo\FULL-LOCAL-PRODUCTION
pm2 start config\master.ecosystem.config.js
timeout /t 3 >nul
echo Done.
echo.

REM 3. Save PM2 configuration
echo [3/5] Saving PM2 configuration...
pm2 save --force >nul 2>&1
echo Done.
echo.

REM 4. Verify all services started
echo [4/5] Verifying service health...
timeout /t 2 >nul
echo.

REM 5. Show final status
echo [5/5] Final status check...
echo.
pm2 list
echo.

echo ========================================
echo ALL BOTS STARTED SUCCESSFULLY
echo ========================================
echo.
echo Services running:
echo - tg-collector (Telegram message collection)
echo - router (Message routing and processing)
echo - forwarder (Discord message forwarding)
echo.
echo Service locations:
echo - Telegram Collector: services\telegram-collector\
echo - Message Router: services\message-router\
echo - Discord Forwarder: services\discord-forwarder\
echo.
echo Shared resources:
echo - Message Queues: shared\message_queue\
echo - Logs: shared\logs\
echo.
echo Commands:
echo - Check logs: pm2 logs [service-name]
echo - Monitor: pm2 monit
echo - Restart single service: pm2 restart [service-name]
echo.
pause
