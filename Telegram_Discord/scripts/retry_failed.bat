
@echo off
set BASE=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
for /r "%BASE%\message_queue" %%F in (*.error.json) do (
  move "%%F" "%BASE%\message_queue"
)
echo Re-queued failed messages.
