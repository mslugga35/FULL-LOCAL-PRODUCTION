const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

// Webhook for paid server
const WEBHOOK_URL = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN';
const QUEUE_DIR = '/root/bots/message_queue';
const PROCESSED_DIR = '/root/bots/message_queue/processed_paid_webhook';

let sentMessages = new Set();

async function loadSentHistory() {
  try {
    const historyFile = path.join(PROCESSED_DIR, 'sent_history.json');
    const data = await fs.readFile(historyFile, 'utf8');
    const history = JSON.parse(data);
    const today = new Date().toDateString();
    if (history.date === today) {
      sentMessages = new Set(history.messages);
      console.log(`[INFO] Loaded ${sentMessages.size} sent messages from today`);
    }
  } catch (error) {
    console.log('[INFO] Starting fresh sent history');
  }
}

async function saveSentHistory() {
  await fs.mkdir(PROCESSED_DIR, { recursive: true });
  const historyFile = path.join(PROCESSED_DIR, 'sent_history.json');
  const history = {
    date: new Date().toDateString(),
    messages: Array.from(sentMessages)
  };
  await fs.writeFile(historyFile, JSON.stringify(history, null, 2));
}

async function waitForOCR(message, filepath) {
  // If message has media that needs OCR, wait for it
  if (message.hasMedia && message.needsOcr && !message.ocrText) {
    console.log(`[WAIT] Waiting for OCR on message ${message.id}...`);
    
    // Wait up to 30 seconds for OCR
    for (let i = 0; i < 6; i++) {
      await new Promise(r => setTimeout(r, 5000));
      
      // Re-read the file to check for OCR updates
      try {
        const updatedData = await fs.readFile(filepath, 'utf8');
        const updatedMessage = JSON.parse(updatedData);
        if (updatedMessage.ocrText) {
          console.log(`[OCR] OCR completed for message ${message.id}`);
          return updatedMessage;
        }
      } catch (e) {}
    }
    
    console.log(`[WARN] OCR timeout for message ${message.id}, sending without OCR`);
  }
  
  return message;
}

async function processFolder(folderName) {
  const folderPath = path.join(QUEUE_DIR, folderName);
  
  try {
    const files = await fs.readdir(folderPath);
    const jsonFiles = files.filter(f => f.endsWith('.json'));
    
    for (const file of jsonFiles) {
      const filepath = path.join(folderPath, file);
      
      try {
        let data = await fs.readFile(filepath, 'utf8');
        let message = JSON.parse(data);
        
        // Skip if already sent
        if (sentMessages.has(message.id)) {
          continue;
        }
        
        // Wait for OCR if needed
        message = await waitForOCR(message, filepath);
        
        // Get the channel name (try multiple fields)
        const channelName = message.channel_title || message.channelTitle || message.channelName || message.chat_title || folderName;
        
        // Build message content
        let content = `**💎 PAID - ${channelName}**\n`;
        
        if (message.text) {
          content += message.text;
        }
        
        if (message.ocrText) {
          content += `\n\n📸 **OCR Text:**\n\`\`\`\n${message.ocrText}\n\`\`\``;
        }
        
        // Send to webhook
        await axios.post(WEBHOOK_URL, {
          content: content.substring(0, 2000),
          username: 'Paid Cappers Bot'
        });
        
        console.log(`[SENT] ${channelName} -> Paid Server via webhook`);
        
        // Mark as sent
        sentMessages.add(message.id);
        
        // Move to processed
        await fs.mkdir(path.join(PROCESSED_DIR, folderName), { recursive: true });
        await fs.rename(filepath, path.join(PROCESSED_DIR, folderName, file));
        
        // Move media if exists
        if (message.mediaFile) {
          try {
            await fs.rename(
              path.join(folderPath, message.mediaFile),
              path.join(PROCESSED_DIR, folderName, message.mediaFile)
            );
          } catch (e) {}
        }
        
        // Rate limit
        await new Promise(r => setTimeout(r, 1200));
        
      } catch (error) {
        console.error(`[ERROR] Failed to process ${file}:`, error.message);
      }
    }
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.error(`[ERROR] Failed to process folder ${folderName}:`, error);
    }
  }
}

async function run() {
  console.log('[START] Paid Webhook Sender - Fixed');
  console.log('[INFO] Server: 675908407617650697');
  console.log('[INFO] Webhook configured for paid channels');
  console.log('[INFO] OCR check enabled - will wait for OCR before sending');
  
  await loadSentHistory();
  
  while (true) {
    await processFolder('paid_cappers');
    await processFolder('paid_uatb');
    await processFolder('paid_diamond');
    
    // Save history periodically
    if (sentMessages.size % 5 === 0) {
      await saveSentHistory();
    }
    
    await new Promise(r => setTimeout(r, 10000)); // Check every 10 seconds
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n[STOP] Saving state and shutting down...');
  await saveSentHistory();
  process.exit(0);
});

run().catch(error => {
  console.error('[FATAL] Error:', error);
  process.exit(1);
});
