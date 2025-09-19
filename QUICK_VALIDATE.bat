@echo off
echo =======================================================
echo QUICK SYSTEM VALIDATION
echo =======================================================

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

python validate_config.py

echo.
echo Press any key to continue...
pause >nul