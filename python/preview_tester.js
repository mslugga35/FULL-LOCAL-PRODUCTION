/**
 * Preview Tester
 * Test messages in preview mode to see what would be sent
 */

require('dotenv').config();
process.env.PREVIEW_MODE = 'true';

const Discord = require('discord.js');
const fs = require('fs').promises;
const path = require('path');
const { formatEnhancedMessage } = require('./message_enhancer');

console.log('=== PREVIEW MODE TESTER ===');
console.log('This will show what messages would be sent without actually sending them');

// Use the same logic as the main sender
const CONFIG = {
  queueDir: '/root/bots/message_queue',
  processedDir: '/root/bots/message_queue/processed'
};

const FOLDER_MAPPING = {
  'free_cappers': { channel: 'free_cappers', label: '📢 Free', isPaid: false },
  'leaked_cappers': { channel: 'leaked_cappers', label: '🔓 Leaked', isPaid: false },
  'exclusive_cappers': { channel: 'exclusive_cappers', label: '⭐ Exclusive', isPaid: false },
  'paid_uatb': { channel: 'uatb_diamond', label: '🌐 UATB 🌐', isPaid: true },
  'paid_diamond': { channel: 'uatb_diamond', label: '💎 Chamba 💎', isPaid: true },
  'paid_chamba': { channel: 'uatb_diamond', label: '💎 Chamba 💎', isPaid: true }
};

async function previewMessage(folderName, fileName) {
  const filePath = path.join(CONFIG.queueDir, folderName, fileName);
  
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    const msg = JSON.parse(content);
    
    const mapping = FOLDER_MAPPING[folderName];
    if (!mapping) return;
    
    console.log();
    console.log('Message data:', JSON.stringify(msg, null, 2));
    
    const isPaidFolder = mapping.isPaid;
    let message = '';
    
    if (isPaidFolder) {
      message = ;
      if (msg.caption && msg.caption.trim()) {
        message += msg.caption;
      } else if (msg.text && msg.text.trim()) {
        message += msg.text;
      } else if (msg.ocr_text && msg.ocr_text.trim()) {
        message += msg.ocr_text;
      } else if (msg.has_media) {
        message += '📸 *[Image]*';
      }
    } else {
      if (msg.ocr_text || msg.text || msg.caption) {
        message = formatEnhancedMessage(
          mapping.label,
          msg.text || msg.caption,
          msg.ocr_text
        );
      } else if (msg.has_media) {
        message = ;
      }
    }
    
    console.log('Formatted message:');
    console.log(message);
    
    // Check for image
    if (msg.has_media && msg.media_file) {
      const imagePath = path.join(CONFIG.queueDir, folderName, msg.media_file);
      try {
        await fs.stat(imagePath);
        console.log();
        if (isPaidFolder) {
          console.log('📎 Image would be ATTACHED (paid channel)');
        } else {
          console.log('📋 Image available but not attached (free channel)');
        }
      } catch {
        console.log();
      }
    }
    
    console.log();
    console.log('---');
    
  } catch (error) {
    console.error(, error.message);
  }
}

async function scanForPreview() {
  console.log('\nScanning for messages to preview...');
  
  const folders = await fs.readdir(CONFIG.queueDir);
  
  for (const folder of folders) {
    if (folder === 'processed' || folder.startsWith('.') || folder.startsWith('old_')) {
      continue;
    }
    
    const folderPath = path.join(CONFIG.queueDir, folder);
    try {
      const stats = await fs.stat(folderPath);
      if (!stats.isDirectory()) continue;
      
      const files = await fs.readdir(folderPath);
      const jsonFiles = files.filter(f => f.endsWith('.json'));
      
      if (jsonFiles.length > 0) {
        console.log();
        for (const file of jsonFiles.slice(0, 3)) { // Preview first 3
          await previewMessage(folder, file);
        }
      }
    } catch (err) {
      // Skip invalid folders
    }
  }
}

scanForPreview().catch(console.error);
