@echo off
REM Install Windows Task Scheduler task for auto-start
REM Run this script as Administrator

echo ========================================
echo Installing Telegram-Discord Pipeline Auto-Start
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Please right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set working directory
cd /d C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord

REM Delete existing task if present
echo Removing any existing task...
schtasks /delete /tn "TelegramDiscordPipeline" /f >nul 2>&1

REM Import the task from XML
echo Installing scheduled task...
schtasks /create /xml "pipeline-autostart-task.xml" /tn "TelegramDiscordPipeline"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Auto-start task installed!
    echo ========================================
    echo.
    echo The pipeline will now automatically start:
    echo   - 30 seconds after system boot
    echo   - 10 seconds after user login
    echo.
    echo To test: schtasks /run /tn "TelegramDiscordPipeline"
    echo To view: schtasks /query /tn "TelegramDiscordPipeline" /v
    echo To remove: schtasks /delete /tn "TelegramDiscordPipeline" /f
) else (
    echo.
    echo ========================================
    echo ERROR: Failed to install task
    echo ========================================
    echo.
    echo Alternative method - Create task manually:
    echo.
    echo 1. Open Task Scheduler (taskschd.msc)
    echo 2. Click "Create Basic Task"
    echo 3. Name: TelegramDiscordPipeline
    echo 4. Trigger: When the computer starts
    echo 5. Action: Start a program
    echo 6. Program: C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\start-pipeline.bat
    echo 7. Finish and edit properties:
    echo    - Run whether user is logged on or not
    echo    - Run with highest privileges
    echo    - Add second trigger: At log on
)

echo.
pause