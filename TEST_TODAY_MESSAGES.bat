@echo off
echo ============================================
echo DAILY MESSAGE TEST - FETCH TODAY'S MESSAGES
echo ============================================
echo.
echo This script fetches ALL messages from today
echo for testing and troubleshooting
echo.
echo [1] Creating today's test directory...
set TODAY=%date:~-4%%date:~4,2%%date:~7,2%
mkdir "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\daily_tests\%TODAY%" 2>nul

echo [2] Running today's message fetch...
cd /d C:\Users\mpmmo\FULL-LOCAL-PRODUCTION
python -u fetch_today_messages.py

echo.
echo [3] Checking results...
echo.
dir /b "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\today_messages\*.json" 2>nul | find /c ".json"
echo messages saved

echo.
echo [4] Quick summary of channels...
python -c "import os, json, glob; files = glob.glob('today_messages/*.json'); channels = set(); [channels.add(json.load(open(f))['channel']) for f in files if os.path.exists(f)]; print('\n'.join(sorted(channels)) if channels else 'No messages found')"

echo.
echo ============================================
echo Messages saved to: today_messages\
echo ============================================
pause