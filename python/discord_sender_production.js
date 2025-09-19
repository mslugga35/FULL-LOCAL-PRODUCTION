const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const https = require('https');
const Bottleneck = require('bottleneck');

// ============================================
// CRITICAL: ENVIRONMENT CONFIGURATION ONLY
// ============================================
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
if (!WEBHOOK_URL) {
  console.error('[FATAL] DISCORD_WEBHOOK_URL environment variable is required');
  console.error('[HELP] Set it with: export DISCORD_WEBHOOK_URL="your-webhook-url"');
  process.exit(1);
}

// Validate webhook URL format
if (!WEBHOOK_URL.match(/^https:\/\/discord\.com\/api\/webhooks\/\d+\/.+$/)) {
  console.error('[FATAL] Invalid webhook URL format');
  process.exit(1);
}

// Support custom queue directories via env (for sharding)
const QUEUE_DIRS = process.env.QUEUE_DIRS
  ? process.env.QUEUE_DIRS.split(',').map(d => d.trim())
  : [
    '/root/bots/message_queue/uatb',
    '/root/bots/message_queue/paid_uatb',
    '/root/bots/message_queue/diamond',
    '/root/bots/message_queue/paid_diamond',
    '/root/bots/message_queue/paid_chamba'
  ];

// Performance tuning
const TEXT_BATCH_SIZE = parseInt(process.env.TEXT_BATCH_SIZE) || 10;
const FILE_BATCH_SIZE = parseInt(process.env.FILE_BATCH_SIZE) || 10;
const FLOOR_DELAY_MS = parseInt(process.env.FLOOR_DELAY_MS) || 350; // Minimum ms between requests
const PROCESS_NAME = process.env.PROCESS_NAME || 'discord-sender';

// File paths
const STATE_FILE = `/root/bots/.${PROCESS_NAME}_state.json`;
const HEALTH_FILE = `/tmp/${PROCESS_NAME}.lastSend`;
const ARCHIVE_DIR = '/root/bots/sent_archive';

// Logging configuration - NEVER log full webhook URL
console.log('[START] Discord Sender Production - ' + PROCESS_NAME);
console.log('[CONFIG] Webhook: ***' + WEBHOOK_URL.slice(-6)); // Only show last 6 chars
console.log('[CONFIG] Queues:', QUEUE_DIRS.map(d => path.basename(d)).join(', '));
console.log('[CONFIG] Batch: Text=' + TEXT_BATCH_SIZE + ', Files=' + FILE_BATCH_SIZE);
console.log('[CONFIG] Min delay: ' + FLOOR_DELAY_MS + 'ms');

// ============================================
// RATE LIMITER CONFIGURATION
// ============================================
const limiter = new Bottleneck({
  maxConcurrent: 1,  // CRITICAL: Never parallel to same webhook
  minTime: FLOOR_DELAY_MS
});

// ============================================
// HTTP CLIENT WITH KEEP-ALIVE
// ============================================
const http = axios.create({
  timeout: 30000,
  httpsAgent: new https.Agent({
    keepAlive: true,
    keepAliveMsecs: 30000,
    maxSockets: 10,
    maxFreeSockets: 10
  }),
  validateStatus: null // Handle all status codes
});

// ============================================
// STATE MANAGEMENT
// ============================================
let sentMessages = new Set();
let stats = {
  posts: 0,
  messages: 0,
  batches: 0,
  rate429: 0,
  errors: 0,
  sessionStart: Date.now()
};

// Load previous state
if (fs.existsSync(STATE_FILE)) {
  try {
    const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    sentMessages = new Set(state.sent || []);
    console.log('[STATE] Loaded ' + sentMessages.size + ' sent messages from previous session');
  } catch (e) {
    console.error('[STATE] Failed to load:', e.message);
  }
}

function saveState() {
  try {
    const state = {
      sent: Array.from(sentMessages).slice(-20000), // Keep last 20k
      stats: stats,
      updated: new Date().toISOString()
    };

    // Atomic write: write to temp, then rename
    const tempFile = STATE_FILE + '.tmp';
    fs.writeFileSync(tempFile, JSON.stringify(state, null, 2));
    fs.renameSync(tempFile, STATE_FILE);
  } catch (e) {
    console.error('[STATE] Save failed:', e.message);
  }
}

function updateHealth() {
  try {
    fs.writeFileSync(HEALTH_FILE, JSON.stringify({
      timestamp: Date.now(),
      posts: stats.posts,
      messages: stats.messages,
      rate429: stats.rate429,
      uptime: Date.now() - stats.sessionStart
    }));
  } catch (e) {
    // Silent fail for health file
  }
}

// ============================================
// CRITICAL FIX: 429 RATE LIMIT HANDLER
// ============================================
http.interceptors.response.use(
  response => response,
  async (error) => {
    const res = error.response;

    if (res && res.status === 429) {
      const data = res.data || {};
      const headers = res.headers || {};

      // CRITICAL FIX: Parse retry_after correctly
      let waitMs = 5000; // Default 5 seconds

      // Webhook rate limits come in JSON body
      if (typeof data.retry_after === 'number') {
        // Check if it's seconds or milliseconds
        if (data.retry_after < 1000) {
          // Likely seconds, convert to ms
          waitMs = Math.ceil(data.retry_after * 1000);
        } else {
          // Already milliseconds
          waitMs = Math.ceil(data.retry_after);
        }
      }

      // Header-based rate limits (for other endpoints)
      else if (headers['x-ratelimit-reset-after']) {
        // This is in seconds with decimal
        waitMs = Math.ceil(parseFloat(headers['x-ratelimit-reset-after']) * 1000);
      }
      else if (headers['retry-after']) {
        // Can be seconds as integer
        const retry = parseInt(headers['retry-after']);
        waitMs = retry * (retry < 1000 ? 1000 : 1); // Convert if needed
      }

      // Cap wait time at 5 minutes (something is wrong if longer)
      if (waitMs > 300000) {
        console.error('[RL] Suspicious wait time: ' + waitMs + 'ms, capping at 5 minutes');
        waitMs = 300000;
      }

      const isGlobal = data.global === true || headers['x-ratelimit-global'] === 'true';
      console.error(`[RL] 429 ${isGlobal ? 'GLOBAL' : 'ROUTE'} wait=${waitMs}ms`);
      stats.rate429++;

      // Wait exactly as Discord tells us
      await new Promise(resolve => setTimeout(resolve, waitMs));

      // Retry the request
      error.config._retry429 = (error.config._retry429 || 0) + 1;
      if (error.config._retry429 > 3) {
        console.error('[RL] Too many 429 retries, failing request');
        return Promise.reject(error);
      }

      return http.request(error.config);
    }

    // Exponential backoff for 5xx errors
    if (res && res.status >= 500 && res.status < 600) {
      const attempt = (error.config._attempt || 0) + 1;
      if (attempt <= 3) {
        error.config._attempt = attempt;
        const backoff = Math.min(1000 * Math.pow(2, attempt), 10000);
        const jitter = Math.random() * 500; // Add jitter
        console.log(`[RETRY] ${res.status} attempt=${attempt} wait=${backoff + jitter}ms`);
        await new Promise(resolve => setTimeout(resolve, backoff + jitter));
        return http.request(error.config);
      }
    }

    return Promise.reject(error);
  }
);

// ============================================
// QUEUE SCANNING WITH DEDUPLICATION
// ============================================
function scanQueues() {
  const jobs = [];

  for (const dir of QUEUE_DIRS) {
    if (!fs.existsSync(dir)) continue;

    let files;
    try {
      files = fs.readdirSync(dir);
    } catch (e) {
      console.error('[SCAN] Failed to read dir ' + dir + ':', e.message);
      continue;
    }

    for (const file of files) {
      // Skip temp files, done markers, and hidden files
      if (file.startsWith('.') ||
          file.endsWith('.tmp') ||
          file.endsWith('.done') ||
          file.endsWith('.processing')) {
        continue;
      }

      const fullPath = path.join(dir, file);

      let stats;
      try {
        stats = fs.statSync(fullPath);
      } catch (e) {
        continue; // File might have been moved
      }

      // Skip directories and tiny files
      if (!stats.isFile() || stats.size < 100) continue;

      // Extract base ID from filename
      const match = file.match(/^(\d{8}_\d{6}_\d+)/);
      const baseId = match ? match[1] : file.replace(/\.[^.]+$/, '');

      const isJson = file.endsWith('.json');
      const isMedia = /\.(jpg|jpeg|png|gif|webp|mp4|mov|webm|pdf|oga|mp3|wav)$/i.test(file);

      if (isJson || isMedia) {
        jobs.push({
          file,
          fullPath,
          dir,
          baseId,
          isJson,
          isMedia,
          mtime: stats.mtimeMs,
          size: stats.size,
          queue: path.basename(dir)
        });
      }
    }
  }

  // Sort by mtime for chronological order
  jobs.sort((a, b) => a.mtime - b.mtime);
  return jobs;
}

// ============================================
// GROUP JOBS BY BASE ID
// ============================================
function groupJobsByBase(jobs) {
  const groups = new Map();

  for (const job of jobs) {
    // Create unique key for this message
    const messageKey = job.baseId + '_' + job.queue;

    if (!groups.has(messageKey)) {
      groups.set(messageKey, {
        key: messageKey,
        baseId: job.baseId,
        queue: job.queue,
        json: null,
        media: []
      });
    }

    const group = groups.get(messageKey);
    if (job.isJson) {
      group.json = job;
    } else if (job.isMedia) {
      group.media.push(job);
    }
  }

  return Array.from(groups.values());
}

// ============================================
// BUILD OPTIMIZED BATCH
// ============================================
async function buildBatch(groups, maxGroups = 10) {
  const batch = {
    embeds: [],
    files: [],
    jobs: [],
    content: '',
    queueType: null
  };

  let processedGroups = 0;

  for (const group of groups) {
    // Stop if we've hit limits
    if (processedGroups >= maxGroups) break;
    if (batch.embeds.length >= TEXT_BATCH_SIZE) break;
    if (batch.files.length >= FILE_BATCH_SIZE) break;

    // Skip if already sent
    if (sentMessages.has(group.key)) continue;

    // Mark as processing to prevent double-send
    const processingMarker = group.json ?
      group.json.fullPath + '.processing' :
      group.media[0]?.fullPath + '.processing';

    if (processingMarker && fs.existsSync(processingMarker)) {
      continue; // Already being processed
    }

    // Process JSON content
    if (group.json && batch.embeds.length < TEXT_BATCH_SIZE) {
      try {
        const content = JSON.parse(fs.readFileSync(group.json.fullPath, 'utf8'));
        const text = content.text || content.message || content.content || '';

        if (text) {
          batch.embeds.push({
            description: text.slice(0, 4096),
            color: group.queue.includes('uatb') ? 0x00ff00 :
                   group.queue.includes('diamond') || group.queue.includes('chamba') ? 0x00bfff :
                   group.queue.includes('free') ? 0xffff00 : 0x808080,
            footer: {
              text: group.queue.toUpperCase().replace(/_/g, ' ')
            },
            timestamp: new Date().toISOString()
          });

          batch.jobs.push(group.json);
        }
      } catch (e) {
        console.error('[JSON] Parse error ' + group.json.file + ':', e.message);
      }
    }

    // Add media files (respecting limit)
    for (const mediaJob of group.media) {
      if (batch.files.length >= FILE_BATCH_SIZE) break;

      // Verify file still exists
      if (!fs.existsSync(mediaJob.fullPath)) continue;

      batch.files.push({
        path: mediaJob.fullPath,
        name: mediaJob.file
      });
      batch.jobs.push(mediaJob);
    }

    // Track queue type for labeling
    if (!batch.queueType && group.queue) {
      batch.queueType = group.queue;
    }

    processedGroups++;
  }

  // Set content label based on queue type
  if (batch.queueType) {
    if (batch.queueType.includes('uatb')) {
      batch.content = '🌐 **UATB PICKS** 🌐';
    } else if (batch.queueType.includes('diamond') || batch.queueType.includes('chamba')) {
      batch.content = '💎 **DIAMOND PICKS** 💎';
    } else if (batch.queueType.includes('free')) {
      batch.content = '📊 **FREE PICKS** 📊';
    } else if (batch.queueType.includes('exclusive')) {
      batch.content = '⭐ **EXCLUSIVE PICKS** ⭐';
    } else {
      batch.content = '📊 **PICKS UPDATE** 📊';
    }
  }

  return batch;
}

// ============================================
// SEND BATCH WITH PROPER ERROR HANDLING
// ============================================
async function sendBatch(batch) {
  if (batch.jobs.length === 0) return true;

  // Create processing markers
  const markers = [];
  for (const job of batch.jobs) {
    const marker = job.fullPath + '.processing';
    try {
      fs.writeFileSync(marker, Date.now().toString());
      markers.push(marker);
    } catch (e) {
      // Continue without marker
    }
  }

  return limiter.schedule(async () => {
    try {
      const form = new FormData();

      // Build webhook payload
      const payload = {
        content: batch.content,
        username: process.env.BOT_USERNAME || 'Sports Bot',
        embeds: batch.embeds.slice(0, 10),
        allowed_mentions: { parse: [] }
      };

      form.append('payload_json', JSON.stringify(payload));

      // Attach files
      let fileIndex = 0;
      for (const file of batch.files) {
        if (!fs.existsSync(file.path)) continue;

        try {
          const stream = fs.createReadStream(file.path);
          form.append(`files[${fileIndex}]`, stream, file.name);
          fileIndex++;
        } catch (e) {
          console.error('[FILE] Failed to attach ' + file.name + ':', e.message);
        }
      }

      // Send to Discord
      const response = await http.post(WEBHOOK_URL, form, {
        headers: form.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      });

      // Check response
      if (response.status >= 200 && response.status < 300) {
        // Success!
        stats.posts++;
        stats.messages += batch.jobs.length;
        stats.batches++;

        console.log(`[POST] embeds=${batch.embeds.length} files=${fileIndex} jobs=${batch.jobs.length} total_posts=${stats.posts}`);

        // Mark all jobs as sent
        const archiveDate = new Date().toISOString().slice(0, 10);
        const archivePath = path.join(ARCHIVE_DIR, archiveDate, batch.queueType || 'misc');

        for (const job of batch.jobs) {
          // Add to sent set
          const messageKey = job.baseId + '_' + job.queue;
          sentMessages.add(messageKey);

          // Create done marker
          try {
            fs.writeFileSync(job.fullPath + '.done', new Date().toISOString());
          } catch (e) {
            // Continue without done marker
          }

          // Archive file
          try {
            if (!fs.existsSync(archivePath)) {
              fs.mkdirSync(archivePath, { recursive: true });
            }
            fs.renameSync(job.fullPath, path.join(archivePath, job.file));
          } catch (e) {
            // If archive fails, try moving to processed
            try {
              const processedDir = path.join(job.dir, '..', 'processed', path.basename(job.dir));
              if (!fs.existsSync(processedDir)) {
                fs.mkdirSync(processedDir, { recursive: true });
              }
              fs.renameSync(job.fullPath, path.join(processedDir, job.file));
            } catch (e2) {
              console.error('[MOVE] Failed to archive ' + job.file);
            }
          }
        }

        // Update health
        updateHealth();
        saveState();

        return true;
      } else {
        // Non-success status
        stats.errors++;
        console.error(`[HTTP] Status ${response.status}:`, response.data);

        // On 400 errors, skip this batch
        if (response.status >= 400 && response.status < 500) {
          console.error('[SKIP] Bad request, marking as sent to skip');
          for (const job of batch.jobs) {
            const messageKey = job.baseId + '_' + job.queue;
            sentMessages.add(messageKey);
          }
          saveState();
        }

        return false;
      }
    } catch (error) {
      stats.errors++;
      console.error('[ERROR] Send failed:', error.message);

      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        // Network error, will retry
        console.error('[NETWORK] Will retry after delay');
      }

      return false;
    } finally {
      // Clean up processing markers
      for (const marker of markers) {
        try {
          fs.unlinkSync(marker);
        } catch (e) {
          // Silent cleanup
        }
      }
    }
  });
}

// ============================================
// MAIN PROCESSING LOOP
// ============================================
async function main() {
  console.log('[READY] Starting main loop');

  let lastScanTime = 0;
  let emptyScans = 0;

  while (true) {
    try {
      const now = Date.now();

      // Scan for jobs
      const jobs = scanQueues();

      if (jobs.length === 0) {
        emptyScans++;

        // Longer wait if consistently empty
        const waitTime = emptyScans > 10 ? 5000 : 2000;
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }

      emptyScans = 0;

      // Filter out already sent
      const newJobs = jobs.filter(j => {
        const messageKey = j.baseId + '_' + j.queue;
        return !sentMessages.has(messageKey);
      });

      if (newJobs.length > 0) {
        console.log(`[SCAN] Found ${jobs.length} total, ${newJobs.length} new to process`);

        // Group by base ID
        const groups = groupJobsByBase(newJobs);

        // Process in batches
        let processed = 0;
        while (processed < groups.length) {
          const batchGroups = groups.slice(processed, processed + 10);
          const batch = await buildBatch(batchGroups, 10);

          if (batch.jobs.length === 0) {
            processed += 10;
            continue;
          }

          const success = await sendBatch(batch);

          if (!success) {
            // On failure, wait before retry
            await new Promise(resolve => setTimeout(resolve, 5000));
          }

          processed += batchGroups.length;
        }
      }

      // Periodic state save
      if (now - lastScanTime > 30000) {
        saveState();
        lastScanTime = now;

        // Log stats periodically
        const uptime = Math.floor((now - stats.sessionStart) / 1000);
        console.log(`[STATS] Uptime: ${uptime}s, Posts: ${stats.posts}, Messages: ${stats.messages}, 429s: ${stats.rate429}, Errors: ${stats.errors}`);
      }

    } catch (error) {
      console.error('[LOOP] Unexpected error:', error.message);
      stats.errors++;
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// ============================================
// GRACEFUL SHUTDOWN
// ============================================
process.on('SIGINT', () => {
  console.log('\n[SHUTDOWN] Received SIGINT, saving state...');
  console.log(`[FINAL] Posts: ${stats.posts}, Messages: ${stats.messages}, 429s: ${stats.rate429}, Errors: ${stats.errors}`);
  saveState();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n[SHUTDOWN] Received SIGTERM, saving state...');
  saveState();
  process.exit(0);
});

process.on('uncaughtException', (error) => {
  console.error('[FATAL] Uncaught exception:', error);
  saveState();
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[FATAL] Unhandled rejection at:', promise, 'reason:', reason);
  saveState();
  process.exit(1);
});

// ============================================
// START
// ============================================
console.log('[INIT] Starting Discord Sender Production');
console.log('[INIT] Process:', PROCESS_NAME);
console.log('[INIT] PID:', process.pid);

main().catch(error => {
  console.error('[FATAL] Main loop crashed:', error);
  saveState();
  process.exit(1);
});