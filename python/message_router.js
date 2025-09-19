#!/usr/bin/env node
/**
 * Hybrid Message Router - Uses Channel IDs first, names as fallback
 * Best of both worlds - reliable ID routing with name compatibility
 */

const fs = require('fs').promises;
const path = require('path');

const INBOX_DIR = '/root/inbox';
const QUEUE_DIR = '/root/bots/message_queue';

// Primary: Channel ID mappings (most reliable)
const CHANNEL_ID_MAP = {
  '1560546587': 'leaked_cappers',  // Cappers leaked
  '-1002592669126': 'free_cappers',      // Cappers Free
  '-1002608783933': 'exclusive_cappers', // Exclusive Cappers
  '-1002177758646': 'paid_uatb',         // UATB
  '-1002470080886': 'paid_diamond',      // Diamond/Chamba
};

// Fallback: Name mappings (for legacy/test messages)
const CHANNEL_NAME_MAP = {
  '🌐 UATB 🌐': 'paid_uatb',
  'UATB': 'paid_uatb',
  'CAPPERS FREE💥': 'free_cappers',
  'DIAMOND 💎 VIP PACKAGE': 'paid_diamond',
  'DIAMOND VIP PACKAGE': 'paid_diamond',
  'DIAMOND': 'paid_diamond',
  'Chamba': 'paid_diamond',
  'CAPPERS FREE': 'free_cappers',
  'HANDICAPPERS LEAKED🔥': 'leaked_cappers',
  'HANDICAPPERS LEAKED': 'leaked_cappers',
  '***EXCLUSIVE PLAYS***': 'exclusive_cappers',
  'EXCLUSIVE PLAYS': 'exclusive_cappers',
  '👑 Exclusive Cappers 👑': 'exclusive_cappers',
};

async function routeMessage(jsonFile) {
  try {
    const jsonPath = path.join(INBOX_DIR, jsonFile);
    const data = JSON.parse(await fs.readFile(jsonPath, 'utf8'));

    // Try ID first (most reliable)
    let targetFolder = CHANNEL_ID_MAP[String(data.chat_id)];
    
    // Fallback to name matching
    if (!targetFolder && data.chat_title) {
      // Try exact match first
      targetFolder = CHANNEL_NAME_MAP[data.chat_title];
      
      // Try partial match if no exact match
      if (!targetFolder) {
        const titleLower = data.chat_title.toLowerCase();
        for (const [key, folder] of Object.entries(CHANNEL_NAME_MAP)) {
          if (titleLower.includes(key.toLowerCase())) {
            targetFolder = folder;
            break;
          }
        }
      }
    }

    if (!targetFolder) {
      console.log(`[WARNING] No mapping for ID: ${data.chat_id} / Name: ${data.chat_title}`);
      return;
    }

    const destDir = path.join(QUEUE_DIR, targetFolder);
    await fs.mkdir(destDir, { recursive: true });

    // Copy JSON
    const destJsonPath = path.join(destDir, jsonFile);
    await fs.writeFile(destJsonPath, JSON.stringify(data, null, 2));
    console.log(`[ROUTED] to ${targetFolder}: ${jsonFile} (ID: ${data.chat_id})`);

    // Handle media file with _media suffix
    if (data.media_file || data.has_media) {
      const baseName = jsonFile.replace('.json', '');
      const possibleExts = ['.jpg', '.jpeg', '.png', '.webp'];
      
      for (const ext of possibleExts) {
        const testPath = path.join(INBOX_DIR, baseName + ext);
        try {
          await fs.access(testPath);
          
          // Found the image
          const destImageName = `${baseName}_media${ext}`;
          const destImagePath = path.join(destDir, destImageName);
          
          const imageData = await fs.readFile(testPath);
          await fs.writeFile(destImagePath, imageData);
          
          console.log(`[IMAGE] Copied with _media suffix: ${destImageName}`);
          
          // Update JSON with media file name
          data.media_file = destImageName;
          await fs.writeFile(destJsonPath, JSON.stringify(data, null, 2));
          
          // Clean up original image
          await fs.unlink(testPath);
          break;
        } catch {}
      }
    }

    // Remove JSON from inbox
    await fs.unlink(jsonPath);

  } catch (error) {
    console.error(`[ERROR] Error routing ${jsonFile}:`, error.message);
  }
}

async function processInbox() {
  try {
    const files = await fs.readdir(INBOX_DIR);
    const jsonFiles = files.filter(f => f.endsWith('.json'));

    if (jsonFiles.length === 0) {
      console.log('[INBOX] No messages to route');
      return;
    }

    console.log(`[INBOX] Found ${jsonFiles.length} messages to route`);

    for (const jsonFile of jsonFiles) {
      await routeMessage(jsonFile);
    }
  } catch (error) {
    console.error('Error processing inbox:', error);
  }
}

// Run continuously
async function run() {
  console.log('[START] Hybrid Message Router (ID + Name) started');
  console.log('[PRIMARY] Using Channel IDs when available');
  console.log('[FALLBACK] Using Channel Names as backup');
  console.log('[MONITOR] Monitoring:', INBOX_DIR);
  console.log('[ROUTING] Routing to:', QUEUE_DIR);

  while (true) {
    await processInbox();
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

run().catch(console.error);
