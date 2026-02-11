@echo off
echo Restarting Discord Forwarder...
pm2 restart forwarder
pm2 logs forwarder --lines 20
pause
