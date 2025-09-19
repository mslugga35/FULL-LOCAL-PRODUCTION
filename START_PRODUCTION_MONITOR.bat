@echo off
echo =======================================================
echo TELEGRAM TO DISCORD PRODUCTION MONITOR
echo Real-time System Monitoring and Health Checks
echo =======================================================

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

echo Checking environment...
if not exist "routing_config.json" (
    echo ERROR: routing_config.json not found!
    pause
    exit /b 1
)

echo Creating required directories...
if not exist "logs" mkdir logs

echo Validating Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found or not in PATH!
    pause
    exit /b 1
)

echo Installing GUI dependencies...
python -m pip install psutil tkinter

echo.
echo Starting Production Monitor...
echo This will open a GUI window for real-time monitoring.
echo.

python production_monitor.py

echo.
echo Production Monitor stopped.
pause