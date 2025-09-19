@echo off
echo ========================================
echo    PROCESS MESSAGE BACKLOG NOW
echo ========================================
echo.

cd /d "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION"

echo 🔍 Current pipeline status:
python pipeline_monitor.py

echo.
echo 📥 Processing current backlog...
echo    (This will move messages from recent_messages to message_queue)
echo.

python message_processor_windows.py --once

echo.
echo ✅ Backlog processing complete!
echo.

echo 🔍 Updated pipeline status:
python pipeline_monitor.py

echo.
echo ========================================
echo    BACKLOG PROCESSING COMPLETE
echo ========================================
echo.
echo Next steps:
echo   1. Start the pipeline: START_COMPLETE_PIPELINE.bat
echo   2. Monitor progress:   python pipeline_monitor.py
echo.
pause