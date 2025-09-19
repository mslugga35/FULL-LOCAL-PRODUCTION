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
