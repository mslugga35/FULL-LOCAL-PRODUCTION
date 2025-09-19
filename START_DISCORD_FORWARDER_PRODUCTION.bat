@echo off
echo Starting Discord Forwarder Production...
echo.
echo This will continuously monitor message_queue folders and forward to Discord
echo using the routing configuration in routing_config.json
echo.
echo Routes configured:
echo - paid_uatb ^-^> webhook channel 1403837637730762875
echo - paid_diamond ^-^> webhook channel 1403837637730762875
echo - free_cappers\cappers_free ^-^> bot channel 1403894557615325216
echo - free_cappers\cappers_leaked ^-^> bot channel 1403894596186017962
echo - free_cappers\exclusive_cappers ^-^> bot channel 1403894653660692500
echo.
echo Press Ctrl+C to stop the forwarder
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import discord, aiohttp" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Required packages not found. Installing...
    pip install -r requirements_production.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please ensure .env file exists with DISCORD_BOT_TOKEN
    pause
    exit /b 1
)

REM Check if routing_config.json exists
if not exist "routing_config.json" (
    echo ERROR: routing_config.json not found
    echo Please ensure routing configuration file exists
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Create processed_messages directory if it doesn't exist
if not exist "processed_messages" mkdir processed_messages

echo Starting Discord Forwarder Production...
python discord_forwarder_production.py

pause