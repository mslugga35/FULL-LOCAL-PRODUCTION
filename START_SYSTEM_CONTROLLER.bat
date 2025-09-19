@echo off
echo =======================================================
echo TELEGRAM TO DISCORD SYSTEM CONTROLLER
echo Production Startup Script
echo =======================================================

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

echo Checking environment...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please ensure .env file exists with required credentials.
    pause
    exit /b 1
)

if not exist "routing_config.json" (
    echo ERROR: routing_config.json not found!
    echo Please ensure configuration file exists.
    pause
    exit /b 1
)

echo Creating required directories...
if not exist "logs" mkdir logs
if not exist "message_queue" mkdir message_queue

echo Validating Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found or not in PATH!
    pause
    exit /b 1
)

echo Installing/updating requirements...
python -m pip install -r requirements_production.txt

echo.
echo Starting System Controller...
echo Press Ctrl+C to stop the system
echo.

python system_controller.py

echo.
echo System Controller stopped.
pause