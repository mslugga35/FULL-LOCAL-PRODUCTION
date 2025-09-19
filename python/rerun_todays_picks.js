require('dotenv').config();
const fs = require('fs').promises;
const path = require('path');

const ARCHIVE_DIR = '/root/bots/message_queue/archived_20250916';

async function rerunTodaysPicks() {
  console.log('=== RERUNNING TODAY\'S PICKS ===');
  
  try {
    // Check if archive directory exists
    const files = await fs.readdir(ARCHIVE_DIR);
    const jsonFiles = files.filter(f => f.endsWith('.json'));
    
    console.log(`Found ${jsonFiles.length} messages from today`);
    
    // Copy first 10 messages back to free_cappers for testing
    const testMessages = jsonFiles.slice(0, 10);
    
    for (const file of testMessages) {
      const srcPath = path.join(ARCHIVE_DIR, file);
      const dstPath = path.join('/root/bots/message_queue/free_cappers', `test_${file}`);
      
      await fs.copyFile(srcPath, dstPath);
      console.log(`Copied: ${file}`);
    }
    
    console.log('\n✅ Test messages queued for processing');
    console.log('Discord sender will pick them up shortly...');
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

rerunTodaysPicks();
