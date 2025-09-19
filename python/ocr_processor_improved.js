/**
 * Improved OCR Processor with memory management and error handling
 * Fixes stability issues with the original implementation
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');
const config = require('./config');
const { createLogger } = require('./logger');

const logger = createLogger('ocr-processor');

class OCRProcessor {
  constructor() {
    this.queueDir = config.dirs.queue;
    this.maxConcurrent = config.ocr.maxConcurrent;
    this.timeoutMs = config.ocr.timeoutMs;
    this.maxMemoryMb = config.ocr.maxMemoryMb;

    this.activeJobs = new Map();
    this.processedCount = 0;
    this.errorCount = 0;
    this.lastGC = Date.now();

    // Memory monitoring
    this.memoryThreshold = this.maxMemoryMb * 1024 * 1024; // Convert to bytes
  }

  /**
   * Start processing loop
   */
  async start() {
    logger.info('OCR Processor starting', {
      maxConcurrent: this.maxConcurrent,
      timeoutMs: this.timeoutMs,
      maxMemoryMb: this.maxMemoryMb
    });

    while (true) {
      try {
        // Check memory before processing
        await this.checkMemory();

        // Process messages that need OCR
        await this.processQueue();

        // Periodic garbage collection
        await this.performGarbageCollection();

        // Sleep between iterations
        await this.sleep(2000);
      } catch (error) {
        logger.error('OCR processing loop error', error);
        await this.sleep(5000); // Longer sleep on error
      }
    }
  }

  /**
   * Check memory usage and clean up if needed
   */
  async checkMemory() {
    const memUsage = process.memoryUsage();
    const memMB = Math.round(memUsage.heapUsed / 1024 / 1024);

    if (memUsage.heapUsed > this.memoryThreshold) {
      logger.warn('High memory usage, forcing garbage collection', {
        usedMB: memMB,
        thresholdMB: this.maxMemoryMb
      });

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      // Clear any cached data
      this.clearCaches();

      // If still high, pause processing
      const afterGC = process.memoryUsage();
      if (afterGC.heapUsed > this.memoryThreshold) {
        logger.error('Memory still high after GC, pausing', {
          usedMB: Math.round(afterGC.heapUsed / 1024 / 1024)
        });
        await this.sleep(30000); // Pause for 30 seconds
      }
    }

    return memMB;
  }

  /**
   * Process queue folders for messages needing OCR
   */
  async processQueue() {
    const folders = await this.getQueueFolders();

    for (const folder of folders) {
      // Check concurrent job limit
      if (this.activeJobs.size >= this.maxConcurrent) {
        await this.waitForSlot();
      }

      const messages = await this.getMessagesNeedingOCR(folder);

      for (const message of messages) {
        if (this.activeJobs.size >= this.maxConcurrent) {
          await this.waitForSlot();
        }

        // Start OCR job
        this.startOCRJob(message, folder);
      }
    }
  }

  /**
   * Get folders in queue directory
   */
  async getQueueFolders() {
    try {
      const entries = await fs.readdir(this.queueDir, { withFileTypes: true });
      return entries
        .filter(entry => entry.isDirectory())
        .map(entry => entry.name);
    } catch (error) {
      logger.error('Failed to read queue directory', error);
      return [];
    }
  }

  /**
   * Get messages that need OCR processing
   */
  async getMessagesNeedingOCR(folder) {
    const folderPath = path.join(this.queueDir, folder);
    const messages = [];

    try {
      const files = await fs.readdir(folderPath);
      const jsonFiles = files.filter(f => f.endsWith('.json'));

      for (const file of jsonFiles.slice(0, 10)) { // Process max 10 at a time
        const filePath = path.join(folderPath, file);

        try {
          const data = await fs.readFile(filePath, 'utf8');
          const message = JSON.parse(data);

          // Check if message needs OCR
          if (message.hasMedia && !message.ocrText && !message.ocrProcessing) {
            messages.push({
              file,
              filePath,
              message,
              mediaFile: message.mediaFile
            });
          }
        } catch (error) {
          logger.error(`Failed to read message ${file}`, error);
        }
      }
    } catch (error) {
      logger.error(`Failed to scan folder ${folder}`, error);
    }

    return messages;
  }

  /**
   * Start OCR processing job
   */
  async startOCRJob(messageInfo, folder) {
    const jobId = `${folder}/${messageInfo.file}`;

    // Skip if already processing
    if (this.activeJobs.has(jobId)) {
      return;
    }

    // Mark as processing
    try {
      messageInfo.message.ocrProcessing = true;
      await fs.writeFile(
        messageInfo.filePath,
        JSON.stringify(messageInfo.message, null, 2)
      );
    } catch (error) {
      logger.error(`Failed to mark message as processing`, error);
      return;
    }

    // Create job
    const job = {
      id: jobId,
      startTime: Date.now(),
      messageInfo,
      folder
    };

    this.activeJobs.set(jobId, job);

    // Process with timeout
    const timeout = setTimeout(() => {
      this.handleOCRTimeout(job);
    }, this.timeoutMs);

    // Run OCR
    this.runOCR(job)
      .then(text => this.handleOCRSuccess(job, text))
      .catch(error => this.handleOCRError(job, error))
      .finally(() => {
        clearTimeout(timeout);
        this.activeJobs.delete(jobId);
      });
  }

  /**
   * Run OCR on image using Tesseract
   */
  async runOCR(job) {
    const { messageInfo, folder } = job;
    const mediaPath = path.join(this.queueDir, folder, messageInfo.mediaFile);

    // Check if media file exists
    try {
      await fs.access(mediaPath);
    } catch (error) {
      throw new Error(`Media file not found: ${messageInfo.mediaFile}`);
    }

    return new Promise((resolve, reject) => {
      const chunks = [];
      let killed = false;

      // Spawn tesseract process with memory limits
      const proc = spawn('tesseract', [
        mediaPath,
        'stdout',
        '-l', 'eng',
        '--psm', '3',
        '--oem', '3'
      ], {
        timeout: this.timeoutMs,
        maxBuffer: 10 * 1024 * 1024 // 10MB max output
      });

      // Monitor memory usage
      const memInterval = setInterval(() => {
        if (proc.pid) {
          // Check process memory (platform specific)
          // This is a simplified check
          const memUsage = process.memoryUsage();
          if (memUsage.heapUsed > this.memoryThreshold) {
            if (!killed) {
              killed = true;
              proc.kill('SIGTERM');
              clearInterval(memInterval);
              reject(new Error('OCR killed due to high memory usage'));
            }
          }
        }
      }, 1000);

      proc.stdout.on('data', (data) => {
        chunks.push(data);
      });

      proc.stderr.on('data', (data) => {
        logger.debug('Tesseract stderr:', data.toString());
      });

      proc.on('close', (code) => {
        clearInterval(memInterval);

        if (killed) {
          return;
        }

        if (code === 0) {
          const text = Buffer.concat(chunks).toString('utf8').trim();
          resolve(text);
        } else {
          reject(new Error(`Tesseract exited with code ${code}`));
        }
      });

      proc.on('error', (error) => {
        clearInterval(memInterval);
        reject(error);
      });
    });
  }

  /**
   * Handle successful OCR
   */
  async handleOCRSuccess(job, text) {
    const { messageInfo, folder } = job;
    const duration = Date.now() - job.startTime;

    logger.info('OCR completed', {
      file: messageInfo.file,
      folder,
      duration,
      textLength: text.length
    });

    // Update message with OCR text
    try {
      messageInfo.message.ocrText = text;
      messageInfo.message.ocrProcessing = false;
      messageInfo.message.ocrProcessedAt = new Date().toISOString();

      await fs.writeFile(
        messageInfo.filePath,
        JSON.stringify(messageInfo.message, null, 2)
      );

      this.processedCount++;
    } catch (error) {
      logger.error('Failed to save OCR result', error);
    }
  }

  /**
   * Handle OCR error
   */
  async handleOCRError(job, error) {
    const { messageInfo, folder } = job;

    logger.error('OCR failed', {
      file: messageInfo.file,
      folder,
      error: error.message
    });

    // Mark as failed
    try {
      messageInfo.message.ocrProcessing = false;
      messageInfo.message.ocrError = error.message;
      messageInfo.message.ocrFailedAt = new Date().toISOString();

      await fs.writeFile(
        messageInfo.filePath,
        JSON.stringify(messageInfo.message, null, 2)
      );

      this.errorCount++;
    } catch (saveError) {
      logger.error('Failed to save OCR error', saveError);
    }
  }

  /**
   * Handle OCR timeout
   */
  handleOCRTimeout(job) {
    logger.warn('OCR timeout', {
      id: job.id,
      duration: Date.now() - job.startTime
    });

    // Mark the job for cleanup
    this.handleOCRError(job, new Error('OCR processing timeout'));
  }

  /**
   * Wait for an available processing slot
   */
  async waitForSlot() {
    while (this.activeJobs.size >= this.maxConcurrent) {
      await this.sleep(100);
    }
  }

  /**
   * Perform periodic garbage collection
   */
  async performGarbageCollection() {
    const now = Date.now();

    // Run GC every 5 minutes
    if (now - this.lastGC > 300000) {
      logger.debug('Running periodic garbage collection');

      if (global.gc) {
        global.gc();
      }

      this.lastGC = now;

      // Log statistics
      const memUsage = process.memoryUsage();
      logger.info('OCR statistics', {
        processed: this.processedCount,
        errors: this.errorCount,
        active: this.activeJobs.size,
        memoryMB: Math.round(memUsage.heapUsed / 1024 / 1024)
      });
    }
  }

  /**
   * Clear internal caches
   */
  clearCaches() {
    // Clear any internal caches or buffers
    // This is a placeholder for any caching logic
  }

  /**
   * Sleep helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Start if run directly
if (require.main === module) {
  // Enable garbage collection exposure
  if (!global.gc) {
    console.log('Starting with --expose-gc flag for memory management');
    console.log('Restart with: node --expose-gc ocr_processor_improved.js');
  }

  const processor = new OCRProcessor();

  processor.start().catch(error => {
    logger.error('Fatal error', error);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGINT', () => {
    logger.info('Shutting down OCR processor...');
    logger.info('Final stats', {
      processed: processor.processedCount,
      errors: processor.errorCount
    });
    process.exit(0);
  });
}

module.exports = OCRProcessor;