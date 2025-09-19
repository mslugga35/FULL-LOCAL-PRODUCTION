@echo off
echo ============================================
echo TELEGRAM SINGLE-INSTANCE CAPTURE
echo ============================================

echo.
echo [1] Killing any existing Python processes...
taskkill /f /im python.exe >nul 2>&1
echo [OK] Cleaned up processes

echo.
echo [2] Removing old lockfile if exists...
del "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\telegram_capture.lock" >nul 2>&1
echo [OK] Lockfile cleaned

echo.
echo [3] Starting single-instance capture...
cd /d C:\Users\mpmmo\FULL-LOCAL-PRODUCTION
python -u telegram_universal_capture_singleton.py

echo.
echo [EXIT] Script ended
pause