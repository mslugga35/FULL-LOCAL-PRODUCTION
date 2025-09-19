#!/bin/bash
echo '========================================'
echo 'FIXING PAID CHANNEL IMAGE ATTACHMENTS'
echo '========================================'

# Check current webhook configuration
echo 'Current webhook URL:'
grep -m1 'webhook.*utab\|WEBHOOK_URL' /root/bots/paid_webhook_sender.js || echo 'Not found in main file'

# Update paid webhook to properly send images
cat > /root/bots/fix_paid_images.js << 'SCRIPT'
const fs = require('fs');
const content = fs.readFileSync('/root/bots/paid_webhook_sender.js', 'utf8');

// Check if webhook is sending files properly
if (!content.includes('FormData') || !content.includes('files[0]')) {
  console.log('WARNING: Paid webhook may not be sending images correctly!');
  console.log('The webhook needs to use FormData and attach files');
}

// Show current webhook URL
const webhookMatch = content.match(/WEBHOOK_URL.*=.*['"](.*?)['"]/) || 
                    content.match(/webhookUrl.*=.*['"](.*?)['"]/) ||
                    content.match(/https:\/\/discord\.com\/api\/webhooks\/[^'"\s]*/);
if (webhookMatch) {
  console.log('Webhook URL found:', webhookMatch[0]);
}
SCRIPT
node /root/bots/fix_paid_images.js

echo ''
echo 'Checking recent paid messages with media...'
ls -la /root/bots/message_queue/paid_uatb/*.jpg /root/bots/message_queue/paid_uatb/*.png /root/bots/message_queue/paid_uatb/*.mp4 2>/dev/null | head -5

echo ''
echo '========================================'
echo 'DIAGNOSIS COMPLETE'
echo '========================================'
