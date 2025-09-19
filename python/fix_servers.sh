#!/bin/bash
# Update discord_sender.js to use correct server for free content
sed -i 's/675908407617650697/1390050801136701642/g' /root/bots/discord_sender.js

# Ensure paid_webhook_sender.js uses the paid server
grep -q '675908407617650697' /root/bots/paid_webhook_sender.js || echo 'Paid webhook already correct'

echo 'Server IDs updated:'
echo 'Free/Leaked → 1390050801136701642'
echo 'Paid → 675908407617650697'

# Restart both
pm2 restart discord-sender
pm2 restart paid-webhook
