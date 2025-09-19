@echo off
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION

REM Set environment variables for local paths
set INBOX_DIR=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\inbox
set TG_SESSION_FILE=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\telegram_session.session
set TG_API_ID=29479443
set TG_API_HASH=e3a7a7226cf446bbfd5366f7da75cdfa

REM Set webhook URLs for PAID channels only
set WEBHOOK_UATB=https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN
set WEBHOOK_DIAMOND=https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN

REM FREE channels use bot delivery - NO WEBHOOKS
REM WEBHOOK_CAPPERS_FREE - REMOVED (uses bot)
REM WEBHOOK_CAPPERS_LEAKED - REMOVED (uses bot)
REM WEBHOOK_EXCLUSIVE - REMOVED (uses bot)

echo Starting Telegram Collector with local paths...
python python\telegram_to_discord.py