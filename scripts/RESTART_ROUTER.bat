@echo off
echo Restarting Message Router...
pm2 restart router
pm2 logs router --lines 20
pause
