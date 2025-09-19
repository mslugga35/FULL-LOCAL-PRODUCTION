/**
 * Centralized configuration management
 * All environment variables and defaults in one place
 */

require('dotenv').config({ path: process.env.ENV_PATH || '.env' });

function getEnv(key, defaultValue) {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    console.error(`[CONFIG] Required environment variable ${key} is not set`);
    process.exit(1);
  }
  return value !== undefined ? value : defaultValue;
}

function getNumericEnv(key, defaultValue) {
  const value = getEnv(key, defaultValue);
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    console.error(`[CONFIG] Environment variable ${key} must be numeric, got: ${value}`);
    process.exit(1);
  }
  return parsed;
}

function getBooleanEnv(key, defaultValue) {
  const value = getEnv(key, defaultValue?.toString());
  return value === 'true' || value === '1';
}

const config = {
  // Discord Configuration
  discord: {
    botToken: getEnv('DISCORD_BOT_TOKEN', null),
    paidWebhookUrl: getEnv('PAID_WEBHOOK_URL', null),
    freeWebhookUrl: getEnv('FREE_WEBHOOK_URL', null),
    monitorWebhook: getEnv('MONITOR_WEBHOOK', ''),
    guildId: getEnv('TARGET_GUILD_ID', '675908407617650697'),
    channels: {
      uatbExpected: getEnv('UATB_EXPECTED_CHANNEL_ID', '1403837637730762875'),
      diamondExpected: getEnv('DIAMOND_EXPECTED_CHANNEL_ID', '1403837637730762875'),
      freeCappers: getEnv('CH_FREE', '1403894557615325216'),
      leakedCappers: getEnv('CH_LEAKED', '1403894596186017962'),
      exclusiveCappers: getEnv('CH_EXCLUSIVE', '1403894653660692500')
    }
  },

  // Rate Limiting
  rateLimit: {
    intervalMs: getNumericEnv('RATE_LIMIT_INTERVAL_MS', 5000),
    cap: getNumericEnv('RATE_LIMIT_CAP', 5),
    msgMaxLen: getNumericEnv('MSG_MAX_LEN', 1800)
  },

  // Watchdog Configuration
  watchdog: {
    pollMs: getNumericEnv('WATCHDOG_POLL_MS', 60000),
    staleMs: getNumericEnv('WATCHDOG_STALE_MS', 180000),
    largeBacklog: getNumericEnv('WATCHDOG_LARGE_BACKLOG', 25),
    ignoreProcs: (getEnv('WATCHDOG_IGNORE_PROCS', 'discord-sender') || '').split(',').map(s => s.trim())
  },

  // OCR Configuration
  ocr: {
    maxConcurrent: getNumericEnv('OCR_MAX_CONCURRENT', 2),
    timeoutMs: getNumericEnv('OCR_TIMEOUT_MS', 30000),
    maxMemoryMb: getNumericEnv('OCR_MAX_MEMORY_MB', 100)
  },

  // Directories
  dirs: {
    queue: getEnv('QUEUE_DIR', '/root/bots/message_queue'),
    processed: getEnv('PROCESSED_DIR', '/root/bots/message_queue/processed'),
    inbox: getEnv('INBOX_DIR', '/root/inbox')
  },

  // PM2 App Names
  pm2: {
    tgProducer: getEnv('PM2_TG_PRODUCER', 'tg-producer'),
    ocr: getEnv('PM2_OCR', 'ocr-processor'),
    sender: getEnv('PM2_SENDER', 'discord-sender'),
    router: getEnv('PM2_ROUTER', 'message-router'),
    forwarder: getEnv('PM2_FORWARDER', 'telegram-forwarder'),
    paidWebhook: getEnv('PM2_PAID_WEBHOOK', 'paid-webhook')
  },

  // Node environment
  env: process.env.NODE_ENV || 'production',
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV !== 'development'
};

// Validate critical configs at startup
function validateConfig() {
  const errors = [];

  // Only validate if the value is explicitly null or undefined
  // Allow placeholder values like "YOUR_" to pass
  if (!config.discord.paidWebhookUrl || config.discord.paidWebhookUrl.includes('YOUR_')) {
    console.warn('[CONFIG] Warning: PAID_WEBHOOK_URL not properly configured');
  }

  if (!config.discord.freeWebhookUrl || config.discord.freeWebhookUrl.includes('YOUR_')) {
    console.warn('[CONFIG] Warning: FREE_WEBHOOK_URL not properly configured');
  }

  if (!config.discord.botToken || config.discord.botToken.includes('YOUR_')) {
    console.warn('[CONFIG] Warning: DISCORD_BOT_TOKEN not properly configured');
  }

  // Only fail on truly critical missing configs
  if (!config.discord.paidWebhookUrl && !config.discord.freeWebhookUrl) {
    errors.push('At least one webhook URL must be configured');
  }

  if (errors.length > 0) {
    console.error('[CONFIG] Validation failed:');
    errors.forEach(err => console.error(`  - ${err}`));
    if (config.isProduction) {
      // Don't exit, just warn - let the service decide
      console.error('[CONFIG] Running with incomplete configuration');
    }
  }
}

validateConfig();

module.exports = config;