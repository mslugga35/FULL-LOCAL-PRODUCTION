@echo off
REM ============================================================================
REM START_PRODUCTION.bat - Complete Telegram to Discord Routing System
REM Unified production startup script for Windows
REM ============================================================================

title Telegram to Discord Production System

echo.
echo ============================================================================
echo 🚀 TELEGRAM TO DISCORD PRODUCTION SYSTEM
echo ============================================================================
echo.

REM Change to the correct directory
cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

REM Verify we're in the right place
if not exist "config_manager.py" (
    echo ❌ ERROR: config_manager.py not found in current directory
    echo Current directory: %CD%
    echo Please ensure you're running this from the FULL-LOCAL-PRODUCTION folder
    pause
    exit /b 1
)

if not exist "production_controller.py" (
    echo ❌ ERROR: production_controller.py not found
    pause
    exit /b 1
)

if not exist "routing_config.json" (
    echo ❌ ERROR: routing_config.json not found
    pause
    exit /b 1
)

echo ✅ Production files verified
echo.

REM Set Python encoding to UTF-8
set PYTHONIOENCODING=utf-8

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found or not in PATH
    echo Please install Python and ensure it's added to your PATH
    pause
    exit /b 1
)

echo ✅ Python installation verified
echo.

REM Test configuration loading
echo 🔧 Testing configuration...
python config_manager.py
if errorlevel 1 (
    echo ❌ ERROR: Configuration test failed
    echo Please check your routing_config.json file
    pause
    exit /b 1
)

echo ✅ Configuration test passed
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Start the production system
echo 🚀 Starting production system...
echo.
echo *** CTRL+C to stop the system ***
echo.

REM Start with monitoring
python production_controller.py start

REM If we get here, the system stopped
echo.
echo ============================================================================
echo 🛑 PRODUCTION SYSTEM STOPPED
echo ============================================================================

REM Check for error log
if exist "logs\production_controller_*.log" (
    echo.
    echo 📋 Recent log entries:
    for /f %%f in ('dir /b /o-d "logs\production_controller_*.log"') do (
        echo --- Last 10 lines from %%f ---
        powershell "Get-Content 'logs\%%f' | Select-Object -Last 10"
        goto :log_shown
    )
    :log_shown
)

echo.
echo Press any key to exit...
pause >nul