/**
 * Google Vision OCR Worker for Hetzner - TEMPORARY FALLBACK VERSION
 * Using existing formatter while Google Vision is pending setup
 */

const fs = require('fs').promises;
const path = require('path');

// Import the sophisticated formatter from local implementation
const formatter = require('./ai_pick_formatter');

// Queue configuration
const QUEUE_DIR = '/root/bots/message_queue';
const FOLDERS = ['free_cappers', 'leaked_cappers', 'exclusive_cappers', 'paid_uatb', 'paid_diamond'];
const CHECK_INTERVAL = 5000;

// Stats tracking
const stats = {
  processed: 0,
  successful: 0,
  failed: 0,
  startTime: Date.now()
};

/**
 * Process existing OCR text with sophisticated cleaning
 */
async function processMessage(jsonPath) {
  try {
    // Read JSON
    const jsonData = await fs.readFile(jsonPath, 'utf8');
    const message = JSON.parse(jsonData);

    // Skip if already processed with new formatter
    if (message.formatter_version === 'v2_sophisticated') {
      return false;
    }

    // Skip if no OCR text
    if (!message.ocr_text && !message.ocr_raw) {
      return false;
    }

    // Get the raw OCR text (prefer raw over formatted)
    const rawText = message.ocr_raw || message.ocr_text;

    // Process with sophisticated formatter
    const processed = formatter.processOCRText(rawText, message.channelName);

    // Update message with cleaned text
    message.ocr_text = processed.formatted;
    message.ocr_cleaned = processed.cleaned;
    message.betting_info = processed.bettingInfo;
    message.formatter_version = 'v2_sophisticated';
    message.formatter_timestamp = new Date().toISOString();

    // Save updated JSON
    await fs.writeFile(jsonPath, JSON.stringify(message, null, 2));

    stats.processed++;
    stats.successful++;

    console.log(`[SUCCESS] Cleaned ${path.basename(jsonPath)} with sophisticated formatter`);

    // Log sample output
    if (stats.successful <= 3 && processed.hasContent) {
      console.log('[SAMPLE] Formatted Output:', processed.formatted.substring(0, 200));
    }

    return true;

  } catch (error) {
    console.error(`[ERROR] Failed to process message:`, error.message);
    stats.failed++;
    return false;
  }
}

/**
 * Process all messages in a folder
 */
async function processFolder(folderName) {
  const folderPath = path.join(QUEUE_DIR, folderName);

  try {
    const files = await fs.readdir(folderPath);
    const jsonFiles = files.filter(f => f.endsWith('.json'));

    let processedCount = 0;

    for (const jsonFile of jsonFiles) {
      const jsonPath = path.join(folderPath, jsonFile);
      const processed = await processMessage(jsonPath);
      if (processed) processedCount++;

      // Rate limiting - process max 20 per cycle per folder
      if (processedCount >= 20) break;
    }

    if (processedCount > 0) {
      console.log(`[FOLDER] Processed ${processedCount} messages in ${folderName}`);
    }

  } catch (error) {
    console.error(`[ERROR] Failed to process folder ${folderName}:`, error.message);
  }
}

/**
 * Main processing loop
 */
async function main() {
  console.log('========================================');
  console.log(' SOPHISTICATED OCR TEXT CLEANER');
  console.log('========================================');
  console.log('[INFO] Cleaning existing OCR text with advanced formatter');
  console.log('[INFO] Processing folders:', FOLDERS.join(', '));
  console.log('[INFO] Check interval: ' + (CHECK_INTERVAL/1000) + ' seconds');
  console.log('');

  // Main loop
  while (true) {
    for (const folder of FOLDERS) {
      await processFolder(folder);
    }

    // Log stats every 10 cycles
    if (stats.processed > 0 && stats.processed % 50 === 0) {
      const runtime = Math.floor((Date.now() - stats.startTime) / 1000);
      console.log(`[STATS] Runtime: ${runtime}s | Processed: ${stats.processed} | Success: ${stats.successful} | Failed: ${stats.failed}`);
    }

    // Wait before next cycle
    await new Promise(resolve => setTimeout(resolve, CHECK_INTERVAL));
  }
}

// Handle shutdown gracefully
process.on('SIGINT', () => {
  console.log('\n[SHUTDOWN] Saving stats and exiting...');
  const runtime = Math.floor((Date.now() - stats.startTime) / 1000);
  console.log(`[FINAL] Runtime: ${runtime}s | Processed: ${stats.processed} | Success: ${stats.successful} | Failed: ${stats.failed}`);
  process.exit(0);
});

// Start the worker
main().catch(error => {
  console.error('[FATAL] Worker crashed:', error);
  process.exit(1);
});
