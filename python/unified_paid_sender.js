const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const fetch = require('node-fetch');

// Configuration
const WEBHOOK_URL = 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN';

const QUEUES = [
  { name: 'uatb', label: '🌐 UATB 🌐' },
  { name: 'paid_uatb', label: '🌐 UATB 🌐' },
  { name: 'diamond', label: '💎 Diamond 💎' },
  { name: 'paid_diamond', label: '💎 Diamond 💎' },
  { name: 'paid_chamba', label: '💎 Chamba 💎' }
];

const BASE_DIR = '/root/bots/message_queue';
const POLL_MS = 2000;

// Send to Discord with attachments
async function sendToDiscord(content, files) {
  try {
    const form = new FormData();
    
    // Add message content
    form.append('payload_json', JSON.stringify({ 
      content: content,
      username: 'Message Bot'
    }));
    
    // Add files
    if (files && files.length > 0) {
      files.forEach((filepath, idx) => {
        if (fs.existsSync(filepath)) {
          const stream = fs.createReadStream(filepath);
          const filename = path.basename(filepath);
          form.append('file' + idx, stream, filename);
        }
      });
    }
    
    // Send webhook
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      body: form,
      headers: form.getHeaders()
    });
    
    if (!response.ok) {
      const text = await response.text();
      console.error('[WEBHOOK ERROR]', response.status, text);
      return false;
    }
    
    return true;
  } catch (e) {
    console.error('[SEND ERROR]', e.message);
    return false;
  }
}

async function processQueue(queueInfo) {
  const queueDir = path.join(BASE_DIR, queueInfo.name);
  
  if (!fs.existsSync(queueDir)) {
    return;
  }
  
  // Get ALL files, not just JSON
  const files = fs.readdirSync(queueDir)
    .filter(f => {
      const filepath = path.join(queueDir, f);
      const stats = fs.statSync(filepath);
      // Process files only, skip directories and tiny files
      return stats.isFile() && stats.size > 100;
    })
    .sort();
  
  for (const file of files) {
    const filePath = path.join(queueDir, file);
    
    // Skip already processed markers
    if (file.endsWith('.processed')) continue;
    
    let content = queueInfo.label;
    let mediaFiles = [];
    
    // Handle JSON files (may have associated media)
    if (file.endsWith('.json')) {
      try {
        const raw = fs.readFileSync(filePath, 'utf-8');
        const payload = JSON.parse(raw);
        
        // Extract text content
        if (payload.text || payload.message || payload.content) {
          const text = payload.text || payload.message || payload.content;
          content = content + '\n' + text;
        }
        
        // Look for associated media files
        const base = file.replace('.json', '');
        const dirFiles = fs.readdirSync(queueDir);
        
        for (const dirFile of dirFiles) {
          if (dirFile.startsWith(base) && !dirFile.endsWith('.json')) {
            const ext = path.extname(dirFile).toLowerCase();
            if (['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webm', '.pdf'].includes(ext)) {
              mediaFiles.push(path.join(queueDir, dirFile));
            }
          }
        }
      } catch (e) {
        console.error('[JSON ERROR]', file, e.message);
        continue;
      }
    } 
    // Handle direct media files
    else {
      const ext = path.extname(file).toLowerCase();
      if (['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.webm', '.pdf', '.oga', '.mp3', '.wav'].includes(ext)) {
        mediaFiles = [filePath];
      } else {
        continue; // Skip unknown file types
      }
    }
    
    // Send to Discord
    console.log('[PROCESS]', file, 'from', queueInfo.name);
    const sent = await sendToDiscord(content, mediaFiles);
    
    if (sent) {
      console.log('[SENT]', file);
      
      // Move files to processed
      const processedDir = path.join(BASE_DIR, 'processed_paid_webhook', queueInfo.name);
      if (!fs.existsSync(processedDir)) {
        fs.mkdirSync(processedDir, { recursive: true });
      }
      
      // Move main file
      try {
        fs.renameSync(filePath, path.join(processedDir, file));
      } catch (e) {
        console.error('[MOVE ERROR]', e.message);
      }
      
      // Move associated media files
      for (const mediaFile of mediaFiles) {
        if (mediaFile !== filePath && fs.existsSync(mediaFile)) {
          try {
            const mediaName = path.basename(mediaFile);
            fs.renameSync(mediaFile, path.join(processedDir, mediaName));
          } catch (e) {
            // Ignore move errors for media
          }
        }
      }
      
      // Rate limit
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

// Main loop
async function main() {
  console.log('[START] Paid Webhook Sender (All Files)');
  console.log('[INFO] Monitoring:', QUEUES.map(q => q.name).join(', '));
  
  while (true) {
    for (const queue of QUEUES) {
      await processQueue(queue);
    }
    await new Promise(r => setTimeout(r, POLL_MS));
  }
}

// Error handling
process.on('unhandledRejection', (err) => {
  console.error('[UNHANDLED]', err);
});

// Start
main().catch(console.error);
