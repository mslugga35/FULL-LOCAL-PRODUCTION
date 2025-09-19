/**
 * Enhanced OCR Processor with Claude Vision
 * Falls back to Tesseract if Claude is unavailable
 */

require('dotenv').config();
const fs = require('fs').promises;
const path = require('path');
const Tesseract = require('tesseract.js');
const axios = require('axios');

const CONFIG = {
  queueDir: '/root/bots/message_queue',
  claudeApiKey: process.env.CLAUDE_API_KEY,
  checkInterval: 3000,
  maxRetries: 3
};

class EnhancedOCRProcessor {
  constructor() {
    this.processing = new Set();
    this.tesseractWorker = null;
  }

  async init() {
    console.log('[OCR] Starting Enhanced OCR Processor with Claude Vision');

    if (CONFIG.claudeApiKey) {
      console.log('[OCR] ✅ Claude API configured');
    } else {
      console.log('[OCR] ⚠️  No Claude API key, will use Tesseract only');
    }

    // Initialize Tesseract as fallback
    this.tesseractWorker = await Tesseract.createWorker('eng');
    console.log('[OCR] Tesseract initialized as fallback');
  }

  /**
   * Extract text using Claude Vision API
   */
  async extractWithClaude(imagePath) {
    if (!CONFIG.claudeApiKey) {
      return null;
    }

    try {
      console.log(`[CLAUDE] Processing: ${path.basename(imagePath)}`);

      // Read image as base64
      const imageBuffer = await fs.readFile(imagePath);
      const base64Image = imageBuffer.toString('base64');

      const response = await axios.post(
        'https://api.anthropic.com/v1/messages',
        {
          model: 'claude-3-haiku-20240307', // Cheaper, faster model for OCR
          max_tokens: 1000,
          messages: [{
            role: 'user',
            content: [
              {
                type: 'image',
                source: {
                  type: 'base64',
                  media_type: 'image/jpeg',
                  data: base64Image
                }
              },
              {
                type: 'text',
                text: `Extract text from this sports betting image for Discord.

                      Format EXACTLY like this:
                      CapperName
                      Team1 ML -150 (2U)
                      Team2 +3.5 (1U)
                      Over 45.5 (1U)

                      Rules:
                      - First line: Capper name only
                      - Then list each pick on its own line
                      - Include team, bet type (ML/spread/total), odds, units
                      - NO extra text, NO explanations
                      - Keep it simple and clean for Discord`
              }
            ]
          }]
        },
        {
          headers: {
            'x-api-key': CONFIG.claudeApiKey,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
          },
          timeout: 15000
        }
      );

      const extractedText = response.data.content[0].text;
      console.log(`[CLAUDE] ✅ Extracted ${extractedText.length} chars`);
      return extractedText;

    } catch (error) {
      console.error(`[CLAUDE] Error:`, error.response?.data || error.message);
      return null;
    }
  }

  /**
   * Fallback to Tesseract OCR
   */
  async extractWithTesseract(imagePath) {
    try {
      console.log(`[TESSERACT] Processing: ${path.basename(imagePath)}`);

      const { data: { text } } = await this.tesseractWorker.recognize(imagePath);

      console.log(`[TESSERACT] Extracted ${text.length} chars`);
      return text;
    } catch (error) {
      console.error(`[TESSERACT] Error:`, error.message);
      return '';
    }
  }

  /**
   * Process a single message that needs OCR
   */
  async processMessage(folder, jsonFile) {
    const jsonPath = path.join(CONFIG.queueDir, folder, jsonFile);

    // Prevent double processing
    const key = `${folder}/${jsonFile}`;
    if (this.processing.has(key)) {
      return;
    }
    this.processing.add(key);

    try {
      // Read message data
      const content = await fs.readFile(jsonPath, 'utf-8');
      const messageData = JSON.parse(content);

      // Skip if already processed
      if (messageData.ocr_done || !messageData.has_media) {
        this.processing.delete(key);
        return;
      }

      // Find the image file
      const imagePath = path.join(CONFIG.queueDir, folder, messageData.media_file);

      try {
        await fs.access(imagePath);
      } catch {
        console.log(`[OCR] Image not found: ${messageData.media_file}`);
        this.processing.delete(key);
        return;
      }

      console.log(`[OCR] Processing ${folder}/${jsonFile}`);

      // Try Claude first, then fallback to Tesseract
      let ocrText = await this.extractWithClaude(imagePath);

      if (!ocrText || ocrText.length < 10) {
        console.log(`[OCR] Claude failed or returned empty, trying Tesseract`);
        ocrText = await this.extractWithTesseract(imagePath);
      }

      // Clean up the text
      ocrText = ocrText
        .replace(/\r\n/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      // Update message with OCR text
      messageData.ocr_text = ocrText;
      messageData.ocr_done = true;
      messageData.ocr_empty = !ocrText || ocrText.length < 5;
      messageData.ocr_processed_at = new Date().toISOString();
      messageData.ocr_method = ocrText && ocrText.length > 10 ? 'claude' : 'tesseract';

      // Write back
      await fs.writeFile(jsonPath, JSON.stringify(messageData, null, 2));

      console.log(`[OCR] ✅ Completed ${folder}/${jsonFile} (${messageData.ocr_method})`);

      if (ocrText && ocrText.length > 20) {
        console.log(`[OCR] Preview: ${ocrText.substring(0, 100)}...`);
      }

    } catch (error) {
      console.error(`[OCR] Error processing ${key}:`, error.message);
    } finally {
      this.processing.delete(key);
    }
  }

  /**
   * Scan all queues for messages needing OCR
   */
  async scanQueues() {
    try {
      const folders = await fs.readdir(CONFIG.queueDir);

      for (const folder of folders) {
        // Skip special folders
        if (folder === 'processed' || folder.startsWith('.')) {
          continue;
        }

        const folderPath = path.join(CONFIG.queueDir, folder);
        const stats = await fs.stat(folderPath);

        if (!stats.isDirectory()) {
          continue;
        }

        // Get all JSON files
        const files = await fs.readdir(folderPath);
        const jsonFiles = files.filter(f => f.endsWith('.json'));

        // Process messages that need OCR
        for (const jsonFile of jsonFiles) {
          const jsonPath = path.join(folderPath, jsonFile);

          try {
            const content = await fs.readFile(jsonPath, 'utf-8');
            const data = JSON.parse(content);

            // Check if needs OCR
            if (data.has_media && !data.ocr_done) {
              await this.processMessage(folder, jsonFile);
              // Rate limit for Claude API
              if (CONFIG.claudeApiKey) {
                await new Promise(resolve => setTimeout(resolve, 500));
              }
            }
          } catch (err) {
            // Skip invalid files
          }
        }
      }
    } catch (error) {
      console.error('[OCR] Queue scan error:', error.message);
    }
  }

  /**
   * Start the processor
   */
  async start() {
    await this.init();

    console.log('[OCR] Starting queue monitoring...');

    while (true) {
      await this.scanQueues();
      await new Promise(resolve => setTimeout(resolve, CONFIG.checkInterval));
    }
  }

  /**
   * Cleanup
   */
  async cleanup() {
    if (this.tesseractWorker) {
      await this.tesseractWorker.terminate();
    }
  }
}

// Start the service
const processor = new EnhancedOCRProcessor();

process.on('SIGINT', async () => {
  console.log('\n[OCR] Shutting down...');
  await processor.cleanup();
  process.exit(0);
});

processor.start().catch(error => {
  console.error('[OCR] Fatal error:', error);
  process.exit(1);
});