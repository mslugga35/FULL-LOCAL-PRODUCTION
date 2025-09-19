#!/usr/bin/env node
/**
 * ID-Based Message Router - Uses Telegram Channel IDs for reliable routing
 * No more emoji/naming issues - uses immutable channel IDs
 */

const fs = require('fs').promises;
const path = require('path');

const INBOX_DIR = '/root/inbox';
const QUEUE_DIR = '/root/bots/message_queue';

// Channel ID to folder mapping - MUCH MORE RELIABLE!
const CHANNEL_ID_MAP = {
  '-1002592669126': 'free_cappers',      // Cappers Free
  '-1001560546587': 'leaked_cappers',    // Leaked Cappers
  '-1002608783933': 'exclusive_cappers', // Exclusive Cappers
  '-1002177758646': 'paid_uatb',         // UATB
  '-1002470080886': 'paid_diamond',      // Diamond/Chamba
};

// Optional: Keep name mappings as fallback for legacy messages
const FALLBACK_NAME_MAP = {
  'uatb': 'paid_uatb',
  'diamond': 'paid_diamond',
  'chamba': 'paid_diamond',
  'free': 'free_cappers',
  'leaked': 'leaked_cappers',
  'exclusive': 'exclusive_cappers'
};

async function routeMessage(jsonFile) {
  try {
    const jsonPath = path.join(INBOX_DIR, jsonFile);
    const data = JSON.parse(await fs.readFile(jsonPath, 'utf8'));

    // Primary: Use chat_id for routing (most reliable)
    let targetFolder = CHANNEL_ID_MAP[String(data.chat_id)];

    // Fallback: Try channel name if ID not found (for legacy/test messages)
    if (!targetFolder && data.chat_title) {
      const titleLower = data.chat_title.toLowerCase();
      for (const [key, folder] of Object.entries(FALLBACK_NAME_MAP)) {
        if (titleLower.includes(key)) {
          targetFolder = folder;
          console.log(`[FALLBACK] Using name mapping for: ${data.chat_title}`);
          break;
        }
      }
    }

    if (!targetFolder) {
      console.log(`[WARNING] No mapping for ID: ${data.chat_id} (${data.chat_title || 'Unknown'})`);
      return;
    }

    const destDir = path.join(QUEUE_DIR, targetFolder);
    await fs.mkdir(destDir, { recursive: true });

    // Copy JSON
    const destJsonPath = path.join(destDir, jsonFile);
    await fs.writeFile(destJsonPath, JSON.stringify(data, null, 2));
    console.log(`[ROUTED] ID ${data.chat_id} to ${targetFolder}: ${jsonFile}`);

    // Handle media file with _media suffix
    if (data.media_file || data.has_media) {
      const baseName = jsonFile.replace('.json', '');

      // Find the actual image file
      const possibleExts = ['.jpg', '.jpeg', '.png', '.webp'];
      let sourceImagePath = null;
      let imageExt = null;

      for (const ext of possibleExts) {
        const testPath = path.join(INBOX_DIR, baseName + ext);
        try {
          await fs.access(testPath);
          sourceImagePath = testPath;
          imageExt = ext;
          break;
        } catch {}
      }

      // Clean up image if found {
        // Create destination path with _media suffix
        const destImageName = `${baseName}_media${imageExt}`;
        const destImagePath = path.join(destDir, destImageName);

        // Copy image
        const imageData = await fs.readFile(sourceImagePath);
        await fs.writeFile(destImagePath, imageData);

        console.log(`[IMAGE] Copied with _media suffix: ${destImageName}`);

        // Update JSON to reflect media file
        data.media_file = destImageName;
        await fs.writeFile(destJsonPath, JSON.stringify(data, null, 2));
      } else {
        console.log(`[WARNING] No image found for ${baseName}`);
      }
    }

    // Remove from inbox after successful routing
    await fs.unlink(jsonPath);
    // Clean up image if found {
      try {
        await fs.unlink(sourceImagePath);
      } catch {}
    }

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

// Display mapping on startup for clarity
function displayMappings() {
  console.log('=== CHANNEL ID MAPPINGS ===');
  for (const [id, folder] of Object.entries(CHANNEL_ID_MAP)) {
    console.log(`  ${id} → ${folder}`);
  }
  console.log('===========================');
}

// Run continuously
async function run() {
  console.log('[START] ID-Based Message Router started');
  displayMappings();
  console.log('[MONITOR] Monitoring:', INBOX_DIR);
  console.log('[ROUTING] Routing to:', QUEUE_DIR);

  while (true) {
    await processInbox();
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

run().catch(console.error);