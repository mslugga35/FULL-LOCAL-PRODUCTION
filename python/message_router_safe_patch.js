#!/usr/bin/env node
/**
 * SAFE Message Router Patch - Fixes UATB image routing
 * Adds _media suffix to images when routing to queue folders
 * Preserves existing Diamond functionality
 */

const fs = require('fs').promises;
const path = require('path');

const INBOX_DIR = '/root/inbox';
const QUEUE_DIR = '/root/bots/message_queue';

// Channel mappings (same as original)
const CHANNEL_MAPPINGS = {
  '🌐 UATB 🌐': 'paid_uatb',
  'UATB': 'paid_uatb',
  'DIAMOND 💎 VIP PACKAGE': 'paid_diamond',
  'DIAMOND VIP PACKAGE': 'paid_diamond',
  'DIAMOND': 'paid_diamond',
  'Chamba': 'paid_diamond',
  // Add other mappings as needed
  'uatb': 'paid_uatb',
  'diamond': 'paid_diamond',
  'chamba': 'paid_diamond'
};

async function routeMessage(jsonFile) {
  try {
    const jsonPath = path.join(INBOX_DIR, jsonFile);
    const data = JSON.parse(await fs.readFile(jsonPath, 'utf8'));

    // Determine target folder
    const chatTitle = (data.chat_title || '').toLowerCase();
    let targetFolder = null;

    // Check exact matches first
    for (const [key, folder] of Object.entries(CHANNEL_MAPPINGS)) {
      if (chatTitle.includes(key.toLowerCase())) {
        targetFolder = folder;
        break;
      }
    }

    if (!targetFolder) {
      console.log(`[WARNING] No mapping for: ${data.chat_title}`);
      return;
    }

    const destDir = path.join(QUEUE_DIR, targetFolder);
    await fs.mkdir(destDir, { recursive: true });

    // Copy JSON
    const destJsonPath = path.join(destDir, jsonFile);
    await fs.writeFile(destJsonPath, JSON.stringify(data, null, 2));
    console.log(`[ROUTED] JSON to ${targetFolder}: ${jsonFile}`);

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

      if (sourceImagePath) {
        // Create destination path with _media suffix
        const destImageName = `${baseName}_media${imageExt}`;
        const destImagePath = path.join(destDir, destImageName);

        // Copy (not move) to preserve original for safety
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
    if (data.media_file) {
      try {
        const origMediaPath = path.join(INBOX_DIR, data.media_file.replace('_media', ''));
        await fs.unlink(origMediaPath);
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

// Run continuously
async function run() {
  console.log('[START] SAFE Message Router started');
  console.log('[MONITOR] Monitoring:', INBOX_DIR);
  console.log('[ROUTING] Routing to:', QUEUE_DIR);

  while (true) {
    await processInbox();
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

run().catch(console.error);