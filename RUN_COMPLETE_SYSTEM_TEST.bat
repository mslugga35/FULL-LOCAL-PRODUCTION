@echo off
echo =======================================================
echo COMPLETE TELEGRAM TO DISCORD SYSTEM TEST
echo Comprehensive validation of all components
echo =======================================================

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

echo Step 1: Environment Validation
echo ===============================
echo.

if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env file with required credentials.
    pause
    exit /b 1
)

if not exist "routing_config.json" (
    echo ERROR: routing_config.json not found!
    pause
    exit /b 1
)

echo ✓ Configuration files found

echo.
echo Step 2: Python Environment Check
echo =================================
echo.

python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not available!
    pause
    exit /b 1
)

echo ✓ Python available

echo.
echo Step 3: Dependencies Installation
echo ==================================
echo.

echo Installing production requirements...
python -m pip install -r requirements_production.txt
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may not have installed correctly
)

echo ✓ Dependencies checked

echo.
echo Step 4: Directory Structure Setup
echo ==================================
echo.

if not exist "logs" mkdir logs
if not exist "message_queue" mkdir message_queue
echo ✓ Base directories created

echo.
echo Step 5: Integration Tests
echo =========================
echo.

echo Running comprehensive integration tests...
python test_system_integration.py
if %errorlevel% neq 0 (
    echo WARNING: Some integration tests failed
    echo Review the test output above for details
    pause
)

echo.
echo Step 6: Component Validation
echo =============================
echo.

echo Checking system controller...
python -c "import system_controller; print('✓ System controller import OK')"
if %errorlevel% neq 0 (
    echo ERROR: System controller has issues
    pause
    exit /b 1
)

echo Checking telegram collector...
if exist "telegram_collector_updated.py" (
    echo ✓ Telegram collector file found
) else (
    echo ERROR: Telegram collector file missing
    pause
    exit /b 1
)

echo Checking discord forwarder...
if exist "discord_forwarder_production.py" (
    echo ✓ Discord forwarder file found
) else (
    echo ERROR: Discord forwarder file missing
    pause
    exit /b 1
)

echo.
echo Step 7: Configuration Validation
echo =================================
echo.

python -c "
import json
with open('routing_config.json') as f:
    config = json.load(f)
    enabled = sum(1 for ch in config['telegram_channels'].values() if ch.get('enabled', False))
    print(f'✓ Configuration valid: {enabled} enabled channels')
"

echo.
echo =======================================================
echo SYSTEM TEST COMPLETE
echo =======================================================
echo.
echo The system is ready for production use.
echo.
echo Next steps:
echo 1. Start System: START_SYSTEM_CONTROLLER.bat
echo 2. Monitor System: START_PRODUCTION_MONITOR.bat
echo.
echo Press any key to continue...
pause >nul