
@echo off
pm2 stop tg-collector
pm2 stop router
pm2 stop forwarder
pm2 save
echo Stopped all
