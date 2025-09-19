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
    './message_queue/uatb',
    './message_queue/paid_uatb',
    './message_queue/diamond',
    './message_queue/paid_diamond',
    './message_queue/paid_chamba'
    // NOTE: free_cappers, exclusive_cappers, leaked_cappers should NOT be here
    // They use bot transport to server 1390050801136701642, NOT webhook
  ];

// Performance tuning
const TEXT_BATCH_SIZE = parseInt(process.env.TEXT_BATCH_SIZE) || 10;
const FILE_BATCH_SIZE = parseInt(process.env.FILE_BATCH_SIZE) || 10;
const FLOOR_DELAY_MS = parseInt(process.env.FLOOR_DELAY_MS) || 5000; // 5 seconds between requests (12 per minute, well under 30 limit)
const PROCESS_NAME = process.env.PROCESS_NAME || 'discord-sender';

// File paths - LOCAL
const STATE_FILE = `./logs/.${PROCESS_NAME}_state.json`;
const HEALTH_FILE = `./logs/${PROCESS_NAME}.lastSend`;
const ARCHIVE_DIR = './sent_archive';

// Logging configuration - NEVER log full webhook URL
console.log('[START] LOCAL Discord Sender with CF Protection - ' + PROCESS_NAME);
console.log('[CONFIG] Webhook: ***' + WEBHOOK_URL.slice(-6)); // Only show last 6 chars
console.log('[CONFIG] Queues:', QUEUE_DIRS.map(d => path.basename(d)).join(', '));
console.log('[CONFIG] Batch: Text=' + TEXT_BATCH_SIZE + ', Files=' + FILE_BATCH_SIZE);
console.log('[CONFIG] Min delay: ' + FLOOR_DELAY_MS + 'ms');

// ============================================
// CLOUDFLARE 1015 CIRCUIT BREAKER
// ============================================
let cfBlockedUntil = 0;

async function checkCFGate() {
  const now = Date.now();
  if (now < cfBlockedUntil) {
    const remainingMs = cfBlockedUntil - now;
    const remainingMin = Math.ceil(remainingMs / 60000);
    console.log(`[CF] Still in cooldown, ${remainingMin} minutes remaining...`);

    // Wait up to 1 minute then check again
    const waitTime = Math.min(remainingMs, 60000);
    await new Promise(r => setTimeout(r, waitTime));
    return checkCFGate(); // Recursive check
  }
}

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
  cf1015: 0,
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
    // Use atomic write (write to temp, then rename)
    const tempFile = STATE_FILE + '.tmp';
    fs.writeFileSync(tempFile, JSON.stringify({
      sent: Array.from(sentMessages).slice(-10000), // Keep last 10k
      stats: stats,
      updated: new Date().toISOString()
    }));
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
      cf1015: stats.cf1015,
      uptime: Date.now() - stats.sessionStart
    }));
  } catch (e) {
    // Silent fail for health file
  }
}

// ============================================
// ENHANCED 429 HANDLER WITH CF 1015 DETECTION
// ============================================
http.interceptors.response.use(
  response => response,
  async (error) => {
    const res = error.response;

    // Check for Cloudflare 1015 ban
    if (res && res.status === 429) {
      const bodyStr = typeof res.data === 'string' ? res.data : JSON.stringify(res.data || '');
      const isCF1015 =
        bodyStr.includes('1015') ||
        bodyStr.includes('error code: 1015') ||
        (res.headers && /cloudflare/i.test(res.headers['server'] || ''));

      if (isCF1015) {
        // CLOUDFLARE BAN DETECTED - CIRCUIT BREAKER ACTIVATED
        const cooldownMs = 30 * 60 * 1000; // 30 minutes
        cfBlockedUntil = Date.now() + cooldownMs;
        stats.cf1015++;

        console.error('================================================');
        console.error('[CF] ERROR 1015: CLOUDFLARE IP BAN DETECTED!');
        console.error('[CF] Server IP is banned at Cloudflare edge');
        console.error('[CF] Entering 30-minute cooldown period...');
        console.error('[CF] Will resume at: ' + new Date(cfBlockedUntil).toLocaleTimeString());
        console.error('================================================');

        // Save state immediately
        saveState();

        // Don't retry this request
        return Promise.reject(new Error('CF_1015_BAN'));
      }

      // Normal Discord 429 handling
      const data = res.data || {};
      const headers = res.headers || {};

      // Parse retry_after correctly
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
    if (res && res.status >= 500) {
      const attempt = (error.config._attempt || 0) + 1;
      if (attempt <= 3) {
        error.config._attempt = attempt;
        const backoff = Math.min(1000 * Math.pow(2, attempt), 10000);
        console.log(`[RETRY] ${res.status} attempt=${attempt} wait=${backoff}ms`);
        await new Promise(resolve => setTimeout(resolve, backoff));
        return http.request(error.config);
      }
    }

    return Promise.reject(error);
  }
);

// ============================================
// QUEUE SCANNING
// ============================================
function scanQueues() {
  const jobs = [];

  for (const dir of QUEUE_DIRS) {
    if (!fs.existsSync(dir)) continue;

    const files = fs.readdirSync(dir);
    for (const file of files) {
      // Skip hidden files and already-done markers
      if (file.startsWith('.') || file.endsWith('.done')) continue;

      const fullPath = path.join(dir, file);

      // Check if it's a file
      const stats = fs.statSync(fullPath);
      if (!stats.isFile()) continue;

      // Skip tiny files (likely empty or corrupt)
      if (stats.size < 50) continue;

      // Extract base ID from filename
      const match = file.match(/^(\d+_\d+_\d+)/);
      const baseId = match ? match[1] : file.replace(/\.[^.]+$/, '');

      // Determine file type
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

  // Sort by modification time (oldest first)
  jobs.sort((a, b) => a.mtime - b.mtime);
  return jobs;
}

// ============================================
// GROUP JOBS BY BASE ID
// ============================================
function groupJobsByBase(jobs) {
  const groups = new Map();

  for (const job of jobs) {
    if (!groups.has(job.baseId)) {
      groups.set(job.baseId, { json: null, media: [] });
    }

    const group = groups.get(job.baseId);
    if (job.isJson) {
      group.json = job;
    } else if (job.isMedia) {
      group.media.push(job);
    }
  }

  return Array.from(groups.values());
}

// ============================================
// BUILD BATCH
// ============================================
async function buildBatch(groups, maxGroups = 10) {
  const batch = {
    embeds: [],
    files: [],
    jobs: [],
    content: ''
  };

  let processedGroups = 0;

  for (const group of groups) {
    if (processedGroups >= maxGroups) break;
    if (batch.files.length >= FILE_BATCH_SIZE) break;

    // Skip if already sent
    const groupId = group.json?.baseId || group.media[0]?.baseId;
    if (!groupId || sentMessages.has(groupId)) continue;

    // Process JSON (text content)
    if (group.json && batch.embeds.length < TEXT_BATCH_SIZE) {
      try {
        const content = JSON.parse(fs.readFileSync(group.json.fullPath, 'utf8'));
        const text = content.text || content.message || content.content || '';

        if (text) {
          // Add as embed for better formatting
          batch.embeds.push({
            description: text.slice(0, 4096),
            color: group.json.queue.includes('uatb') ? 0x00ff00 :
                   group.json.queue.includes('diamond') || group.json.queue.includes('chamba') ? 0x00bfff :
                   group.json.queue.includes('free') ? 0x808080 : 0x9B59B6,
            footer: {
              text: group.json.queue.toUpperCase().replace(/_/g, ' ')
            },
            timestamp: new Date().toISOString()
          });
        }

        batch.jobs.push(group.json);
      } catch (e) {
        console.error('[JSON ERROR]', group.json.file, e.message);
      }
    }

    // Add media files (up to limit)
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

    processedGroups++;
  }

  // Set content label based on queue type
  if (batch.jobs.length > 0) {
    const queue = batch.jobs[0].queue;
    if (queue.includes('uatb')) {
      batch.content = '🎯 **UATB PICKS**';
    } else if (queue.includes('diamond') || queue.includes('chamba')) {
      batch.content = '💎 **DIAMOND PICKS**';
    } else if (queue.includes('free')) {
      batch.content = '📊 **FREE PICKS**';
    } else if (queue.includes('exclusive')) {
      batch.content = '⭐ **EXCLUSIVE PICKS**';
    } else {
      batch.content = '📊 **PICKS UPDATE**';
    }
  }

  return batch;
}

// ============================================
// SEND BATCH WITH CF GATE
// ============================================
async function sendBatch(batch) {
  if (batch.jobs.length === 0) return true;

  // Check Cloudflare gate before sending
  await checkCFGate();

  return limiter.schedule(async () => {
    try {
      const form = new FormData();

      // Build payload with embeds
      const payload = {
        content: batch.content,
        username: process.env.BOT_USERNAME || 'Sports Bot',
        embeds: batch.embeds.slice(0, 10), // Max 10 embeds
        allowed_mentions: { parse: [] } // Prevent pings
      };

      form.append('payload_json', JSON.stringify(payload));

      // Add files
      batch.files.forEach((file, i) => {
        if (fs.existsSync(file.path)) {
          const stream = fs.createReadStream(file.path);
          form.append(`files[${i}]`, stream, file.name);
        }
      });

      // Send to Discord
      const response = await http.post(WEBHOOK_URL, form, {
        headers: form.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity
      });

      // Check response
      if (response.status === 204 || response.status === 200) {
        // Success!
        stats.posts++;
        stats.messages += batch.jobs.length;
        stats.batches++;

        console.log(`[POST] ✓ embeds=${batch.embeds.length} files=${batch.files.length} jobs=${batch.jobs.length} total=${stats.posts}`);

        // Mark jobs as sent
        for (const job of batch.jobs) {
          sentMessages.add(job.baseId);

          // Create .done marker
          try {
            fs.writeFileSync(job.fullPath + '.done', new Date().toISOString());
          } catch (e) {
            // Silent fail for done marker
          }

          // Archive to date-based folder
          const today = new Date().toISOString().slice(0, 10);
          const archiveDir = path.join(ARCHIVE_DIR, today, job.queue);

          if (!fs.existsSync(archiveDir)) {
            fs.mkdirSync(archiveDir, { recursive: true });
          }

          try {
            fs.renameSync(job.fullPath, path.join(archiveDir, job.file));
          } catch (e) {
            // File might already be moved
          }
        }

        // Update health and state
        updateHealth();
        saveState();

        return true;
      } else {
        // Unexpected status
        console.error('[SEND] Unexpected status:', response.status);
        stats.errors++;
        return false;
      }
    } catch (error) {
      // Check if it's CF 1015 error
      if (error.message === 'CF_1015_BAN') {
        console.error('[SEND] Skipping batch due to CF ban');
        return false;
      }

      console.error('[SEND ERROR]', error.response?.status || error.message);
      stats.errors++;

      // Don't retry on 400 errors (bad request)
      if (error.response?.status === 400) {
        console.error('[BAD REQUEST] Marking batch as sent to skip');
        // Mark as sent to skip bad batch
        for (const job of batch.jobs) {
          sentMessages.add(job.baseId);
        }
        saveState();
        return false;
      }

      throw error; // Let limiter handle retry
    }
  });
}

// ============================================
// MAIN LOOP WITH CF PROTECTION
// ============================================
async function main() {
  console.log('[INFO] Session started at:', new Date().toLocaleString());
  console.log('[INFO] Cloudflare 1015 protection: ENABLED');
  console.log('[INFO] Will pause for 30 minutes if CF ban detected');

  // Reset session stats
  stats = {
    posts: 0,
    messages: 0,
    batches: 0,
    rate429: 0,
    cf1015: 0,
    errors: 0,
    sessionStart: Date.now()
  };

  while (true) {
    try {
      // Check CF gate at start of each cycle
      await checkCFGate();

      const jobs = scanQueues();

      if (jobs.length === 0) {
        // No jobs, wait a bit
        await new Promise(resolve => setTimeout(resolve, 2000));
        continue;
      }

      // Count new jobs
      const newJobs = jobs.filter(j => !sentMessages.has(j.baseId));
      console.log(`[SCAN] Found ${jobs.length} total, ${newJobs.length} new to process`);

      if (newJobs.length === 0) {
        // All caught up, wait longer
        await new Promise(resolve => setTimeout(resolve, 5000));
        continue;
      }

      // Group by baseId
      const groups = groupJobsByBase(jobs);

      // Process in batches
      let processed = 0;
      while (processed < groups.length) {
        // Check CF gate before each batch
        await checkCFGate();

        const batch = await buildBatch(groups.slice(processed), 10);

        if (batch.jobs.length === 0) {
          processed += 10; // Skip empty batch
          continue;
        }

        const success = await sendBatch(batch);
        if (!success && cfBlockedUntil > Date.now()) {
          // CF ban detected, break out of batch loop
          console.log('[MAIN] CF ban detected, entering cooldown...');
          break;
        }

        processed += 10;
      }

      // Print stats periodically
      if (stats.posts > 0 && stats.posts % 10 === 0) {
        const runtime = Math.floor((Date.now() - stats.sessionStart) / 60000);
        console.log(`[STATS] Runtime: ${runtime}m, Posts: ${stats.posts}, Messages: ${stats.messages}, 429s: ${stats.rate429}, CF1015s: ${stats.cf1015}`);
      }

    } catch (error) {
      console.error('[LOOP ERROR]', error.message);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// ============================================
// GRACEFUL SHUTDOWN
// ============================================
process.on('SIGINT', () => {
  const runtime = Math.floor((Date.now() - stats.sessionStart) / 60000);
  console.log('\n[SHUTDOWN] Saving state...');
  console.log(`[FINAL] Runtime: ${runtime}m`);
  console.log(`[FINAL] Posts: ${stats.posts}, Messages: ${stats.messages}`);
  console.log(`[FINAL] Rate limits: 429s=${stats.rate429}, CF1015s=${stats.cf1015}`);
  saveState();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('[SHUTDOWN] Saving state...');
  saveState();
  process.exit(0);
});

// ============================================
// START
// ============================================
main().catch(error => {
  console.error('[FATAL]', error);
  process.exit(1);
});