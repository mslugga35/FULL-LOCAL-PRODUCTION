@echo off
:: COMPLETE VALIDATION OF TELEGRAM PRODUCTION SETUP
:: Checks all components and reports readiness status

echo.
echo =========================================================
echo TELEGRAM PRODUCTION SETUP VALIDATION
echo =========================================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

set ERRORS=0
set WARNINGS=0

:: Check 1: Required files
echo [1/10] Checking required files...
if exist "telegram_production_collector.py" (
    echo   ✓ Main collector script
) else (
    echo   ✗ Main collector script MISSING
    set /a ERRORS+=1
)

if exist "auth_session_production.py" (
    echo   ✓ Authentication script
) else (
    echo   ✗ Authentication script MISSING
    set /a ERRORS+=1
)

if exist "test_telegram_connection.py" (
    echo   ✓ Connection test script
) else (
    echo   ✗ Connection test script MISSING
    set /a ERRORS+=1
)

:: Check 2: Directory structure
echo [2/10] Checking directory structure...
if exist "inbox" (
    echo   ✓ Inbox directory
) else (
    echo   ✗ Inbox directory MISSING
    mkdir inbox
    echo   → Created inbox directory
)

if exist "inbox\media" (
    echo   ✓ Media directory
) else (
    echo   ✗ Media directory MISSING
    mkdir inbox\media
    echo   → Created media directory
)

if exist "logs" (
    echo   ✓ Logs directory
) else (
    echo   ✗ Logs directory MISSING
    mkdir logs
    echo   → Created logs directory
)

:: Check 3: Python installation
echo [3/10] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python not found or not in PATH
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   ✓ Python %%v
)

:: Check 4: Required packages
echo [4/10] Checking required packages...
python -c "import telethon" >nul 2>&1
if errorlevel 1 (
    echo   ✗ telethon package missing
    set /a ERRORS+=1
) else (
    echo   ✓ telethon package
)

python -c "import asyncio" >nul 2>&1
if errorlevel 1 (
    echo   ✗ asyncio package missing
    set /a ERRORS+=1
) else (
    echo   ✓ asyncio package
)

:: Check 5: Environment configuration
echo [5/10] Checking environment configuration...
if exist ".env" (
    echo   ✓ Environment file exists

    findstr "TELEGRAM_STRING_SESSION=" .env >nul
    if errorlevel 1 (
        echo   ! No session string in .env file
        set /a WARNINGS+=1
    ) else (
        for /f "tokens=2 delims==" %%s in ('findstr "TELEGRAM_STRING_SESSION=" .env') do (
            if "%%s"=="" (
                echo   ! Session string is empty
                set /a WARNINGS+=1
            ) else (
                echo   ✓ Session string configured
            )
        )
    )
) else (
    echo   ✗ Environment file missing
    set /a ERRORS+=1
)

:: Check 6: Lock file status
echo [6/10] Checking lock file status...
if exist "telegram_capture.lock" (
    for /f %%i in (telegram_capture.lock) do set LOCK_PID=%%i

    tasklist /fi "PID eq %LOCK_PID%" 2>nul | findstr "%LOCK_PID%" >nul
    if not errorlevel 1 (
        echo   ! Instance already running (PID: %LOCK_PID%)
        set /a WARNINGS+=1
    ) else (
        echo   ! Stale lock file found - will be removed
        del telegram_capture.lock
        set /a WARNINGS+=1
    )
) else (
    echo   ✓ No lock file (ready to start)
)

:: Check 7: Permissions
echo [7/10] Checking permissions...
echo test > inbox\test_write.tmp 2>nul
if exist "inbox\test_write.tmp" (
    echo   ✓ Inbox write permissions
    del inbox\test_write.tmp
) else (
    echo   ✗ Cannot write to inbox directory
    set /a ERRORS+=1
)

echo test > logs\test_write.tmp 2>nul
if exist "logs\test_write.tmp" (
    echo   ✓ Logs write permissions
    del logs\test_write.tmp
) else (
    echo   ✗ Cannot write to logs directory
    set /a ERRORS+=1
)

:: Check 8: Network connectivity
echo [8/10] Checking network connectivity...
ping -n 1 google.com >nul 2>&1
if errorlevel 1 (
    echo   ✗ No internet connectivity
    set /a ERRORS+=1
) else (
    echo   ✓ Internet connectivity
)

:: Check 9: Telegram API accessibility
echo [9/10] Checking Telegram API accessibility...
ping -n 1 149.154.175.57 >nul 2>&1
if errorlevel 1 (
    echo   ! Cannot reach Telegram servers (may be blocked)
    set /a WARNINGS+=1
) else (
    echo   ✓ Telegram servers reachable
)

:: Check 10: Management scripts
echo [10/10] Checking management scripts...
if exist "START_TELEGRAM_PRODUCTION.bat" (
    echo   ✓ Start script
) else (
    echo   ✗ Start script missing
    set /a ERRORS+=1
)

if exist "STOP_TELEGRAM_PRODUCTION.bat" (
    echo   ✓ Stop script
) else (
    echo   ✗ Stop script missing
    set /a ERRORS+=1
)

if exist "MONITOR_TELEGRAM_PRODUCTION.bat" (
    echo   ✓ Monitor script
) else (
    echo   ✗ Monitor script missing
    set /a ERRORS+=1
)

:: Summary
echo.
echo =========================================================
echo VALIDATION SUMMARY
echo =========================================================
echo.

if %ERRORS% equ 0 (
    if %WARNINGS% equ 0 (
        echo ✓ ALL CHECKS PASSED - READY FOR PRODUCTION
        echo.
        echo Next steps:
        echo 1. If not authenticated: python auth_session_production.py
        echo 2. Test connection: python test_telegram_connection.py
        echo 3. Start collector: START_TELEGRAM_PRODUCTION.bat
        set RESULT=0
    ) else (
        echo ⚠ READY WITH WARNINGS (%WARNINGS% warnings)
        echo.
        echo The system should work but check warnings above.
        echo Next steps:
        echo 1. Review warnings above
        echo 2. If not authenticated: python auth_session_production.py
        echo 3. Test connection: python test_telegram_connection.py
        echo 4. Start collector: START_TELEGRAM_PRODUCTION.bat
        set RESULT=0
    )
) else (
    echo ❌ NOT READY (%ERRORS% errors, %WARNINGS% warnings)
    echo.
    echo Fix the errors above before proceeding:

    if %ERRORS% gtr 0 (
        echo.
        echo Common solutions:
        echo • Missing Python: Install from https://python.org
        echo • Missing packages: pip install telethon cryptg
        echo • Missing files: Run SETUP_PRODUCTION_TELEGRAM.bat
        echo • Permission issues: Run as administrator
    )
    set RESULT=1
)

echo.
echo Files location: %CD%
echo.
echo For help, see: TELEGRAM_PRODUCTION_README.md
echo.

pause
exit /b %RESULT%