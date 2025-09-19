#!/usr/bin/env node
/**
 * Message Router - Routes messages from inbox to correct queue folders
 * Fixes the routing issue where messages get stuck
 */

const fs = require('fs').promises;
const path = require('path');

// Directories
const INBOX_DIR = '/root/inbox';
const QUEUE_DIR = '/root/bots/message_queue';

// Channel name to folder mapping
const CHANNEL_MAPPINGS = {
  // Exact matches
  'CAPPERS FREE💥': 'free_cappers',
  'CAPPERS FREE': 'free_cappers',
  'HANDICAPPERS LEAKED🔥': 'leaked_cappers',
  'HANDICAPPERS LEAKED': 'leaked_cappers',
  '***EXCLUSIVE PLAYS***': 'exclusive_cappers',
  'EXCLUSIVE PLAYS': 'exclusive_cappers',
  '🌐 UATB 🌐': 'paid_uatb',
  'UATB': 'paid_uatb',
  'DIAMOND 💎 VIP PACKAGE': 'paid_diamond',
  'DIAMOND VIP PACKAGE': 'paid_diamond',
  'DIAMOND': 'paid_diamond',
  
  // Partial matches (fallback)
  'free': 'free_cappers',
  'leaked': 'leaked_cappers',
  'exclusive': 'exclusive_cappers',
  'uatb': 'paid_uatb',
  'diamond': 'paid_diamond',
  'paid': 'paid_cappers',
  'vip': 'paid_cappers',
  'premium': 'paid_cappers'
};

class MessageRouter {
  constructor() {
    this.stats = {
      processed: 0,
      routed: 0,
      errors: 0,
      startTime: Date.now()
    };
  }

  async start() {
    console.log('🚀 MESSAGE ROUTER STARTED');
    console.log('=======================');
    console.log(`Inbox: ${INBOX_DIR}`);
    console.log(`Queue: ${QUEUE_DIR}`);
    console.log('=======================\n');

    // Ensure queue directories exist
    await this.ensureQueueDirs();

    // Main processing loop
    while (true) {
      try {
        await this.processInbox();
        await new Promise(r => setTimeout(r, 5000)); // Check every 5 seconds
      } catch (error) {
        console.error('❌ Main loop error:', error.message);
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  async ensureQueueDirs() {
    const folders = ['free_cappers', 'leaked_cappers', 'exclusive_cappers', 
                    'paid_uatb', 'paid_diamond', 'paid_cappers'];
    
    for (const folder of folders) {
      const dir = path.join(QUEUE_DIR, folder);
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        // Directory might already exist
      }
    }
    console.log('✅ Queue directories ready\n');
  }

  async processInbox() {
    try {
      // Check if inbox exists
      const exists = await fs.access(INBOX_DIR).then(() => true).catch(() => false);
      if (!exists) {
        console.log('⚠️  Inbox directory not found');
        return;
      }

      // Get all JSON files
      const files = await fs.readdir(INBOX_DIR);
      const jsonFiles = files.filter(f => f.endsWith('.json'));

      if (jsonFiles.length === 0) {
        return; // No messages to process
      }

      console.log(`📥 Found ${jsonFiles.length} messages in inbox`);

      for (const file of jsonFiles) {
        const sourcePath = path.join(INBOX_DIR, file);
        await this.routeMessage(sourcePath);
      }

    } catch (error) {
      console.error('❌ Error processing inbox:', error.message);
      this.stats.errors++;
    }
  }

  async routeMessage(filePath) {
    try {
      // Read the message
      const data = await fs.readFile(filePath, 'utf8');
      const message = JSON.parse(data);
      
      // Determine destination folder
      const folder = this.determineFolder(message);
      
      if (!folder) {
        console.log(`  ⚠️  Cannot route ${path.basename(filePath)} - unknown channel`);
        return;
      }

      // Move to appropriate queue folder
      const destDir = path.join(QUEUE_DIR, folder);
      const destPath = path.join(destDir, path.basename(filePath));
      
      // Add routing info to message
      message.routed_from = 'inbox';
      message.routed_to = folder;
      message.routed_at = new Date().toISOString();
      
      // Write to destination
      await fs.writeFile(destPath, JSON.stringify(message, null, 2));
// Move media file if it exists      if (message.media_file) {        const mediaSourcePath = path.join(INBOX_DIR, message.media_file);        const mediaDestPath = path.join(destDir, message.media_file);                try {          await fs.access(mediaSourcePath);          await fs.rename(mediaSourcePath, mediaDestPath);          console.log(`    📸 Moved image: ${message.media_file}`);        } catch (err) {          console.log(`    ⚠️  Image not found: ${message.media_file}`);        }      }
      
      // Delete from inbox
      await fs.unlink(filePath);
      
      console.log(`  ✅ Routed to ${folder}: ${path.basename(filePath)}`);
      this.stats.routed++;
      
    } catch (error) {
      console.error(`  ❌ Error routing ${path.basename(filePath)}:`, error.message);
      this.stats.errors++;
    }
    
    this.stats.processed++;
  }

  determineFolder(message) {
    // Try to get channel title from various fields
    const channelTitle = message.chat_title || 
                        message.channel_title || 
                        message.from || 
                        message.channel || 
                        '';
    
    // First try exact match
    for (const [pattern, folder] of Object.entries(CHANNEL_MAPPINGS)) {
      if (channelTitle === pattern) {
        return folder;
      }
    }
    
    // Then try case-insensitive contains match
    const lowerTitle = channelTitle.toLowerCase();
    for (const [pattern, folder] of Object.entries(CHANNEL_MAPPINGS)) {
      if (lowerTitle.includes(pattern.toLowerCase())) {
        return folder;
      }
    }
    
    // Check message text for clues
    const text = (message.text || '').toLowerCase();
    if (text.includes('free') || text.includes('cappers free')) {
      return 'free_cappers';
    }
    if (text.includes('leaked') || text.includes('handicappers')) {
      return 'leaked_cappers';
    }
    if (text.includes('exclusive')) {
      return 'exclusive_cappers';
    }
    if (text.includes('uatb')) {
      return 'paid_uatb';
    }
    if (text.includes('diamond') || text.includes('chamba')) {
      return 'paid_diamond';
    }
    if (text.includes('paid') || text.includes('premium') || text.includes('vip')) {
      return 'paid_cappers';
    }
    
    // Default fallback
    console.log(`  ⚠️  Unknown channel: "${channelTitle}"`);
    return null;
  }

  getStats() {
    const uptime = Math.floor((Date.now() - this.stats.startTime) / 1000);
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    
    return {
      uptime: `${hours}h ${minutes}m`,
      processed: this.stats.processed,
      routed: this.stats.routed,
      errors: this.stats.errors,
      successRate: this.stats.processed > 0 
        ? Math.round(this.stats.routed / this.stats.processed * 100) 
        : 0
    };
  }
}

// Status endpoint
const express = require('express');
const app = express();
const PORT = process.env.ROUTER_PORT || 3007;

let router = null;

app.get('/', (req, res) => {
  const stats = router ? router.getStats() : {};
  
  res.send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Message Router</title>
        <meta http-equiv="refresh" content="30">
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
          }
          .container { max-width: 600px; margin: 0 auto; }
          .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2rem;
          }
          .stat {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
          }
          .stat:last-child { border-bottom: none; }
          .success { color: #4ade80; }
          .error { color: #f87171; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>📬 Message Router</h1>
          <div class="card">
            <div class="stat">
              <span>Status</span>
              <span>${router ? '🟢 Running' : '🔴 Starting'}</span>
            </div>
            <div class="stat">
              <span>Uptime</span>
              <span>${stats.uptime || '0h 0m'}</span>
            </div>
            <div class="stat">
              <span>Processed</span>
              <span>${stats.processed || 0}</span>
            </div>
            <div class="stat">
              <span>Routed</span>
              <span class="success">${stats.routed || 0} (${stats.successRate || 0}%)</span>
            </div>
            <div class="stat">
              <span>Errors</span>
              <span class="error">${stats.errors || 0}</span>
            </div>
          </div>
        </div>
      </body>
    </html>
  `);
});

app.listen(PORT, () => {
  console.log(`📡 Status dashboard at http://localhost:${PORT}`);
});

// Start the router
async function main() {
  router = new MessageRouter();
  await router.start();
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Shutting down...');
  if (router) {
    const stats = router.getStats();
    console.log(`Final stats: ${stats.routed} routed, ${stats.errors} errors`);
  }
  process.exit(0);
});

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});