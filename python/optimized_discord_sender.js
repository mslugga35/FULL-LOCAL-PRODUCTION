const fs = require('fs');
const path = require('path');
const axios = require('axios');
const FormData = require('form-data');
const https = require('https');
const Bottleneck = require('bottleneck');

// Configuration
const WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL || 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN';

const QUEUES = [
  '/root/bots/message_queue/uatb',
  '/root/bots/message_queue/paid_uatb',
  '/root/bots/message_queue/diamond',
  '/root/bots/message_queue/paid_diamond',
  '/root/bots/message_queue/paid_chamba'
];

const TEXT_BATCH_SIZE = 10;  // Max embeds per message
const FILE_BATCH_SIZE = 10;  // Max files per message
const STATE_FILE = '/root/bots/.discord_sender_state.json';

// Rate limiter - strictly one request at a time
const limiter = new Bottleneck({
  maxConcurrent: 1,
  minTime: 250 // Minimum 250ms between requests
});

// Axios with keep-alive for connection reuse
const http = axios.create({
  timeout: 30000,
  httpsAgent: new https.Agent({
    keepAlive: true,
    keepAliveMsecs: 30000,
    maxSockets: 10
  })
});

// State management for idempotency
let sentMessages = new Set();
if (fs.existsSync(STATE_FILE)) {
  try {
    const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    sentMessages = new Set(state.sent || []);
  } catch (e) {
    console.error('[STATE] Failed to load state:', e.message);
  }
}

function saveState() {
  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify({
      sent: Array.from(sentMessages).slice(-10000), // Keep last 10k
      updated: new Date().toISOString()
    }));
  } catch (e) {
    console.error('[STATE] Failed to save:', e.message);
  }
}

// 429 rate limit handler with exact retry_after
http.interceptors.response.use(
  response => response,
  async (error) => {
    if (error.response && error.response.status === 429) {
      const data = error.response.data || {};
      const headers = error.response.headers || {};

      // Get retry_after from body (webhooks) or headers
      let waitMs = 5000; // Default fallback

      if (data.retry_after) {
        waitMs = Math.ceil(data.retry_after * 1000);
      } else if (headers['x-ratelimit-reset-after']) {
        waitMs = Math.ceil(parseFloat(headers['x-ratelimit-reset-after']) * 1000);
      } else if (headers['retry-after']) {
        waitMs = parseInt(headers['retry-after']) * 1000;
      }

      const isGlobal = data.global || headers['x-ratelimit-global'] === 'true';
      console.log(`[RATE LIMIT] ${isGlobal ? 'GLOBAL' : 'ROUTE'} - waiting ${waitMs}ms`);

      // Wait exactly as Discord tells us
      await new Promise(resolve => setTimeout(resolve, waitMs));

      // Retry the request
      return http.request(error.config);
    }

    // Exponential backoff for 5xx errors
    if (error.response && error.response.status >= 500) {
      const attempt = (error.config._attempt || 0) + 1;
      if (attempt <= 3) {
        error.config._attempt = attempt;
        const backoff = Math.min(1000 * Math.pow(2, attempt), 10000);
        console.log(`[RETRY] ${error.response.status} - attempt ${attempt}, wait ${backoff}ms`);
        await new Promise(resolve => setTimeout(resolve, backoff));
        return http.request(error.config);
      }
    }

    return Promise.reject(error);
  }
);

// Scan all queues and return jobs
function scanQueues() {
  const jobs = [];

  for (const dir of QUEUES) {
    if (!fs.existsSync(dir)) continue;

    const files = fs.readdirSync(dir);
    for (const file of files) {
      if (file.startsWith('.')) continue;

      const fullPath = path.join(dir, file);
      const stats = fs.statSync(fullPath);
      if (!stats.isFile() || stats.size < 100) continue;

      // Extract base ID from filename (e.g., 20250917_195527_18000)
      const match = file.match(/^(\d+_\d+_\d+)/);
      const baseId = match ? match[1] : file;

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

  // Sort by mtime to preserve order
  jobs.sort((a, b) => a.mtime - b.mtime);
  return jobs;
}

// Group jobs by baseId for efficient batching
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

// Build a batch of messages (text + files combined)
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
    if (sentMessages.has(groupId)) continue;

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
                   group.json.queue.includes('diamond') ? 0x00bfff : 0x808080,
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
      batch.content = '🌐 **UATB PICKS** 🌐';
    } else if (queue.includes('diamond') || queue.includes('chamba')) {
      batch.content = '💎 **DIAMOND PICKS** 💎';
    } else {
      batch.content = '📊 **PICKS UPDATE** 📊';
    }
  }

  return batch;
}

// Send batch to Discord webhook with rate limiting
async function sendBatch(batch) {
  if (batch.jobs.length === 0) return true;

  return limiter.schedule(async () => {
    try {
      const form = new FormData();

      // Build payload with embeds
      const payload = {
        content: batch.content,
        username: 'Sports Bot',
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

      // Mark jobs as sent
      for (const job of batch.jobs) {
        sentMessages.add(job.baseId);

        // Move to processed
        const processedDir = path.join(job.dir, '..', 'processed', path.basename(job.dir));
        if (!fs.existsSync(processedDir)) {
          fs.mkdirSync(processedDir, { recursive: true });
        }

        try {
          fs.renameSync(job.fullPath, path.join(processedDir, job.file));
        } catch (e) {
          // File might be already moved by another job in the group
        }
      }

      console.log(`[SENT] ${batch.jobs.length} items in 1 request (${batch.embeds.length} texts, ${batch.files.length} files)`);
      saveState();

      return true;
    } catch (error) {
      console.error('[SEND ERROR]', error.response?.status || error.message);

      // Don't retry on 400 errors (bad request)
      if (error.response?.status === 400) {
        console.error('[BAD REQUEST] Skipping batch:', error.response.data);
        // Mark as sent to skip
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

// Main processing loop
async function main() {
  console.log('[START] Optimized Discord Sender with Batching');
  console.log('[INFO] Webhook:', WEBHOOK_URL.slice(0, 50) + '...');
  console.log('[INFO] Batch sizes: Text=' + TEXT_BATCH_SIZE + ', Files=' + FILE_BATCH_SIZE);
  console.log('[INFO] Monitoring queues:', QUEUES.map(q => path.basename(q)).join(', '));

  while (true) {
    try {
      const jobs = scanQueues();

      if (jobs.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        continue;
      }

      console.log(`[SCAN] Found ${jobs.length} jobs to process`);

      // Group by baseId
      const groups = groupJobsByBase(jobs);
      console.log(`[GROUP] Organized into ${groups.length} message groups`);

      // Process in batches
      let processed = 0;
      while (processed < groups.length) {
        const batch = await buildBatch(groups.slice(processed), 10);

        if (batch.jobs.length === 0) {
          processed += 10; // Skip empty batch
          continue;
        }

        await sendBatch(batch);
        processed += 10;
      }

    } catch (error) {
      console.error('[LOOP ERROR]', error.message);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

// Graceful shutdown
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

// Start
main().catch(error => {
  console.error('[FATAL]', error);
  process.exit(1);
});