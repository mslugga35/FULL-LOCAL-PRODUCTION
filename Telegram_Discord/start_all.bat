
@echo off
cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  .\.venv\Scripts\pip.exe install -r requirements.txt
)
pm2 start "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\src\telegram_collector.py" --name tg-collector --interpreter "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.venv\Scripts\python.exe"
pm2 start "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\src\router.py"              --name router       --interpreter "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.venv\Scripts\python.exe"
pm2 start "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\src\forwarder.py"           --name forwarder    --interpreter "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.venv\Scripts\python.exe"
pm2 save
echo Started tg-collector, router, forwarder
