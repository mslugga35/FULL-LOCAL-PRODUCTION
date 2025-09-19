@echo off
echo ==================================================
echo STARTING ALL LOCAL PRODUCTION BOTS
echo ==================================================
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION

REM Kill any existing Python processes
echo Stopping existing Python processes...
taskkill /F /IM python.exe 2>nul

REM Start PM2 processes (Discord sender and watchdog)
echo.
echo Starting PM2 services...
pm2 start ecosystem-fixed.config.js

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start Python processes in separate windows
echo.
echo Starting Python bots...

REM Start Telegram collector
start /MIN "Telegram Collector" cmd /c "cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION && python python\telegram_to_discord.py"

REM Start Message processor
start /MIN "Message Processor" cmd /c "cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION && python python\message_processor.py"

REM Start OCR processor if it exists
if exist python\ocr_processor.py (
    start /MIN "OCR Processor" cmd /c "cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION && python python\ocr_processor.py"
)

echo.
echo ==================================================
echo ALL SERVICES STARTED
echo ==================================================
echo.
echo Monitoring status...
timeout /t 5 /nobreak >nul
pm2 list
echo.
echo Python processes:
tasklist | findstr python.exe
echo.
echo Done! All bots are running locally.
pause