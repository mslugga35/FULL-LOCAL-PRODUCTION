
@echo off
set BASE=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
powershell -Command "Get-ChildItem -Directory $env:BASE\sent_archive | Where-Object {$_.CreationTime -lt (Get-Date).AddDays(-7)} | ForEach-Object { Compress-Archive -Path $_.FullName -DestinationPath ($_.FullName + '.zip'); Remove-Item -Recurse -Force $_.FullName }"
echo Cleaned archives older than 7 days.
