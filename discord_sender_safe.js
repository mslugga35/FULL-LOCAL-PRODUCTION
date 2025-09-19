const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const https = require('https');
const crypto = require('crypto');

// ============================================
// ENVIRONMENT CONFIGURATION
// ============================================
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;
if (!WEBHOOK_URL) {
  console.error('[FATAL] DISCORD_WEBHOOK_URL environment variable is required');
  process.exit(1);
}

// Validate webhook URL format
if (!WEBHOOK_URL.match(/^https:\/\/discord\.com\/api\/webhooks\/\d+\/.+$/)) {
  console.error('[FATAL] Invalid webhook URL format');
  process.exit(1);
}

// Queue directories
const QUEUE_DIRS = process.env.QUEUE_DIRS
  ? process.env.QUEUE_DIRS.split(',').map(d => d.trim())
  : [
    './message_queue/uatb',
    './message_queue/paid_uatb',
    './message_queue/diamond',
    './message_queue/paid_diamond',
    './message_queue/paid_chamba',
    './message_queue/free_cappers',
    './message_queue/exclusive_cappers',
    './message_queue/leaked_cappers'
  ];

// Safe defaults following best practices
const MAX_EMBEDS = 5; // Reduced from 10
const MAX_FILES = 1; // Max 1 file per message
const COALESCE_WINDOW_MS = 2000; // 2 second coalescing window
const DUPLICATE_WINDOW_MS = 10 * 60 * 1000; // 10 minutes
const MAX_QUEUE_SIZE = 1000; // Queue pressure control
const GLOBAL_RATE_LIMIT = 5; // Max 5 messages/second globally

// File paths
const STATE_FILE = './logs/.discord_sender_state.json';
const HEALTH_FILE = './logs/discord_sender.lastSend';
const ARCHIVE_DIR = './sent_archive';

// Logging
console.log('[START] Safe Discord Sender with Token Bucket Rate Limiting');
console.log('[CONFIG] Webhook: ***' + WEBHOOK_URL.slice(-6));
console.log('[CONFIG] Max embeds: ' + MAX_EMBEDS);
console.log('[CONFIG] Coalesce window: ' + COALESCE_WINDOW_MS + 'ms');

// ============================================
// TOKEN BUCKET IMPLEMENTATION
// ============================================
class TokenBucket {
  constructor(name, tokensPerSecond = 0.33) { // Default: 1 message per 3 seconds
    this.name = name;
    this.capacity = Math.max(10, tokensPerSecond * 60); // Min 10 tokens
    this.tokens = this.capacity;
    this.tokensPerSecond = tokensPerSecond;
    this.lastRefill = Date.now();
    this.backoffMultiplier = 1;
    this.resetAfter = 0;
    this.remaining = null;
  }

  async take(count = 1) {
    while (true) {
      const now = Date.now();

      // If we have a reset time from Discord headers, wait for it
      if (this.resetAfter > now) {
        const waitMs = this.resetAfter - now;
        console.log(`[BUCKET ${this.name}] Waiting ${Math.ceil(waitMs/1000)}s for rate limit reset`);
        await sleep(waitMs);
        this.tokens = this.capacity; // Reset tokens after wait
        this.resetAfter = 0;
      }

      // Refill tokens based on time passed
      const timePassed = (now - this.lastRefill) / 1000;
      const tokensToAdd = timePassed * this.tokensPerSecond / this.backoffMultiplier;
      this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
      this.lastRefill = now;

      // If we have enough tokens, take them
      if (this.tokens >= count) {
        this.tokens -= count;
        return true;
      }

      // Calculate wait time for next token
      const tokensNeeded = count - this.tokens;
      const waitMs = (tokensNeeded / this.tokensPerSecond) * 1000 * this.backoffMultiplier;
      await sleep(Math.min(waitMs, 5000)); // Cap wait at 5 seconds per iteration
    }
  }

  updateFromHeaders(headers) {
    // Parse Discord rate limit headers
    const remaining = parseInt(headers['x-ratelimit-remaining']);
    const resetAfter = parseFloat(headers['x-ratelimit-reset-after']);
    const retryAfter = parseFloat(headers['retry-after']);

    if (!isNaN(remaining)) {
      this.remaining = remaining;
      // If we're running low, slow down
      if (remaining < 5) {
        this.tokens = Math.min(this.tokens, remaining);
      }
    }

    if (!isNaN(resetAfter)) {
      this.resetAfter = Date.now() + (resetAfter * 1000);
    }

    if (!isNaN(retryAfter)) {
      this.resetAfter = Date.now() + (retryAfter * 1000);
    }
  }

  backoff() {
    this.backoffMultiplier = Math.min(this.backoffMultiplier * 2, 16);
    console.log(`[BUCKET ${this.name}] Backing off, multiplier: ${this.backoffMultiplier}x`);
  }

  resetBackoff() {
    if (this.backoffMultiplier > 1) {
      this.backoffMultiplier = Math.max(1, this.backoffMultiplier / 2);
    }
  }

  getBackoffMs() {
    const baseMs = 5000;
    return Math.min(baseMs * this.backoffMultiplier, 120000); // Cap at 2 minutes
  }
}

// ============================================
// RATE LIMITING & QUEUE MANAGEMENT
// ============================================
const webhookBucket = new TokenBucket('webhook', 0.33); // 1 msg per 3 seconds
const globalBucket = new TokenBucket('global', GLOBAL_RATE_LIMIT);

// Message deduplication
const messageHashes = new Map(); // hash -> timestamp
const messageQueue = [];
const coalesceBuffer = new Map(); // destination -> messages[]

// ============================================
// UTILITIES
// ============================================
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function jitter(factor = 0.15) {
  return (Math.random() - 0.5) * 2 * factor;
}

function hashMessage(content, author) {
  return crypto
    .createHash('md5')
    .update(`${author}:${content}`)
    .digest('hex');
}

function isDuplicate(content, author) {
  const hash = hashMessage(content, author);
  const now = Date.now();

  // Clean old hashes
  for (const [h, timestamp] of messageHashes) {
    if (now - timestamp > DUPLICATE_WINDOW_MS) {
      messageHashes.delete(h);
    }
  }

  // Check if duplicate
  if (messageHashes.has(hash)) {
    return true;
  }

  messageHashes.set(hash, now);
  return false;
}

// ============================================
// HTTP CLIENT
// ============================================
const http = axios.create({
  timeout: 30000,
  httpsAgent: new https.Agent({
    keepAlive: true,
    keepAliveMsecs: 30000,
    maxSockets: 1, // Single connection to avoid bursts
  }),
  validateStatus: null // Handle all status codes
});

// ============================================
// STATE MANAGEMENT
// ============================================
let sentMessages = new Set();
let stats = {
  sent: 0,
  errors: 0,
  rate429: 0,
  duplicates: 0,
  startTime: Date.now()
};

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      sentMessages = new Set(state.sentMessages || []);
      return state;
    }
  } catch (e) {
    console.error('[STATE] Load error:', e.message);
  }
  return { sentMessages: [] };
}

function saveState() {
  try {
    const state = {
      sentMessages: Array.from(sentMessages).slice(-1000), // Keep last 1000
      lastSave: new Date().toISOString(),
      stats
    };
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
  } catch (e) {
    console.error('[STATE] Save error:', e.message);
  }
}

// ============================================
// MESSAGE COALESCING
// ============================================
async function processCoalesceBuffer() {
  while (true) {
    await sleep(COALESCE_WINDOW_MS);

    for (const [destination, messages] of coalesceBuffer) {
      if (messages.length === 0) continue;

      // Take all messages for this destination
      const toSend = messages.splice(0, messages.length);

      // Combine into single payload
      const combined = combineMessages(toSend);
      messageQueue.push(combined);
    }
  }
}

function combineMessages(messages) {
  // Group by type
  const embeds = [];
  const files = [];
  let content = '';

  for (const msg of messages) {
    if (msg.embeds) {
      embeds.push(...msg.embeds);
    }
    if (msg.files) {
      files.push(...msg.files);
    }
    if (msg.content) {
      content += (content ? '\n\n' : '') + msg.content;
    }
  }

  return {
    content: content.slice(0, 2000), // Discord limit
    embeds: embeds.slice(0, MAX_EMBEDS),
    files: files.slice(0, MAX_FILES),
    originalCount: messages.length
  };
}

// ============================================
// WEBHOOK SENDING WITH RATE LIMITS
// ============================================
async function sendToWebhook(payload) {
  // Take tokens from both buckets
  await globalBucket.take(1);
  await webhookBucket.take(1);

  try {
    const form = new FormData();

    // Build Discord payload
    const discordPayload = {
      content: payload.content || null,
      username: process.env.BOT_USERNAME || 'Sports Bot',
      embeds: payload.embeds || [],
      allowed_mentions: { parse: [] } // Prevent pings
    };

    form.append('payload_json', JSON.stringify(discordPayload));

    // Add files if any
    if (payload.files) {
      for (let i = 0; i < payload.files.length && i < MAX_FILES; i++) {
        const file = payload.files[i];
        if (fs.existsSync(file.path)) {
          const stream = fs.createReadStream(file.path);
          form.append(`files[${i}]`, stream, file.name);
        }
      }
    }

    // Send request
    const response = await http.post(WEBHOOK_URL, form, {
      headers: form.getHeaders()
    });

    // Update buckets from headers
    webhookBucket.updateFromHeaders(response.headers);

    // Handle response
    if (response.status === 204 || response.status === 200) {
      // Success
      stats.sent++;
      webhookBucket.resetBackoff();
      globalBucket.resetBackoff();

      console.log(`[SENT] ✓ Status: ${response.status}, Total: ${stats.sent}`);

      // Update health file
      fs.writeFileSync(HEALTH_FILE, new Date().toISOString());
      return true;

    } else if (response.status === 429) {
      // Rate limited
      stats.rate429++;
      const retryAfter = parseFloat(response.headers['retry-after']) || 5;

      console.log(`[RATE] 429 - Retry after ${retryAfter}s`);

      webhookBucket.backoff();
      globalBucket.backoff();

      // Wait and retry
      const waitMs = (retryAfter * 1000) + (jitter() * 1000);
      await sleep(waitMs);

      // Requeue message
      messageQueue.unshift(payload);
      return false;

    } else if (response.status >= 500) {
      // Server error - retry with backoff
      stats.errors++;
      console.log(`[ERROR] ${response.status} - Server error`);

      const backoffMs = webhookBucket.getBackoffMs();
      await sleep(backoffMs + (jitter() * backoffMs));

      // Requeue
      messageQueue.unshift(payload);
      return false;

    } else if (response.status >= 400) {
      // Client error - don't retry
      stats.errors++;
      console.error(`[ERROR] ${response.status} - Client error, dropping message`);

      if (response.data) {
        console.error('[ERROR] Response:', JSON.stringify(response.data));
      }

      return false;
    }

  } catch (error) {
    stats.errors++;
    console.error('[ERROR] Request failed:', error.message);

    // Backoff and retry
    const backoffMs = webhookBucket.getBackoffMs();
    await sleep(backoffMs + (jitter() * backoffMs));

    // Requeue
    messageQueue.unshift(payload);
    return false;
  }
}

// ============================================
// FILE SCANNING
// ============================================
async function scanForMessages() {
  const allJobs = [];

  for (const dir of QUEUE_DIRS) {
    if (!fs.existsSync(dir)) continue;

    const files = fs.readdirSync(dir)
      .filter(f => f.endsWith('.json'))
      .sort((a, b) => {
        // Prioritize paid queues
        const aPaid = a.includes('paid');
        const bPaid = b.includes('paid');
        if (aPaid && !bPaid) return -1;
        if (!aPaid && bPaid) return 1;
        return a.localeCompare(b);
      });

    for (const file of files) {
      const filePath = path.join(dir, file);
      const fileId = `${path.basename(dir)}_${file}`;

      if (sentMessages.has(fileId)) continue;

      try {
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

        // Check for duplicates
        if (isDuplicate(data.content, data.author)) {
          stats.duplicates++;
          console.log(`[SKIP] Duplicate message from ${data.author}`);
          sentMessages.add(fileId);
          continue;
        }

        // Add to coalesce buffer
        const destination = 'default'; // You can customize this
        if (!coalesceBuffer.has(destination)) {
          coalesceBuffer.set(destination, []);
        }

        coalesceBuffer.get(destination).push({
          content: data.content,
          embeds: data.embeds ? data.embeds.slice(0, MAX_EMBEDS) : [],
          files: data.attachments || [],
          fileId,
          filePath,
          priority: dir.includes('paid') ? 1 : 0
        });

        sentMessages.add(fileId);

        // Archive processed file
        const archivePath = path.join(ARCHIVE_DIR, path.basename(dir));
        if (!fs.existsSync(archivePath)) {
          fs.mkdirSync(archivePath, { recursive: true });
        }
        fs.renameSync(filePath, path.join(archivePath, file));

      } catch (e) {
        console.error(`[SCAN] Error reading ${file}:`, e.message);
      }
    }
  }

  // Apply queue pressure control
  if (messageQueue.length > MAX_QUEUE_SIZE) {
    console.log(`[PRESSURE] Queue size ${messageQueue.length} > ${MAX_QUEUE_SIZE}, slowing intake`);
    await sleep(5000);
  }
}

// ============================================
// MAIN PROCESSING LOOP
// ============================================
async function processQueue() {
  while (true) {
    if (messageQueue.length === 0) {
      await sleep(1000);
      continue;
    }

    const message = messageQueue.shift();
    await sendToWebhook(message);

    // Save state periodically
    if (stats.sent % 10 === 0) {
      saveState();
    }

    // Print stats periodically
    if (stats.sent % 25 === 0) {
      const runtime = Math.floor((Date.now() - stats.startTime) / 60000);
      console.log(`[STATS] Runtime: ${runtime}m, Sent: ${stats.sent}, Errors: ${stats.errors}, 429s: ${stats.rate429}, Dupes: ${stats.duplicates}`);
    }
  }
}

// ============================================
// GRACEFUL SHUTDOWN
// ============================================
process.on('SIGINT', () => {
  console.log('[SHUTDOWN] Saving state...');
  saveState();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('[SHUTDOWN] Saving state...');
  saveState();
  process.exit(0);
});

// ============================================
// MAIN
// ============================================
async function main() {
  // Create directories
  if (!fs.existsSync('./logs')) fs.mkdirSync('./logs');
  if (!fs.existsSync(ARCHIVE_DIR)) fs.mkdirSync(ARCHIVE_DIR);

  // Load state
  loadState();

  // Start background tasks
  processCoalesceBuffer(); // Don't await, runs in background

  // Main loops
  const scanLoop = async () => {
    while (true) {
      await scanForMessages();
      await sleep(5000); // Scan every 5 seconds
    }
  };

  // Start scanner and processor
  Promise.all([
    scanLoop(),
    processQueue()
  ]).catch(err => {
    console.error('[FATAL] Main loop error:', err);
    process.exit(1);
  });
}

// Start the application
main().catch(err => {
  console.error('[FATAL] Startup error:', err);
  process.exit(1);
});