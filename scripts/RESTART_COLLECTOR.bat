@echo off
echo Restarting Telegram Collector...
pm2 restart tg-collector
pm2 logs tg-collector --lines 20
pause
