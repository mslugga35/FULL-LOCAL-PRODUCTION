@echo off
echo ========================================
echo STOPPING ALL PRODUCTION BOTS
echo ========================================
echo.

echo Stopping all PM2 processes...
pm2 stop all
timeout /t 2 >nul

echo.
echo Final status:
pm2 list
echo.
echo All bots stopped.
pause
