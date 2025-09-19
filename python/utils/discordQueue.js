/**
 * Discord API rate limiting queue
 * Implements proper rate limiting per Discord's guidelines
 */

const axios = require('axios');
const { createLogger } = require('../logger');

const logger = createLogger('discord-queue');

class DiscordQueue {
  constructor(options = {}) {
    // Discord rate limits: 5 requests per 5 seconds per channel
    this.maxRequestsPerInterval = options.maxRequests || 5;
    this.intervalMs = options.intervalMs || 5000;
    this.retryAfterBuffer = options.retryAfterBuffer || 1000; // Extra buffer for 429s

    // Queue management
    this.queue = [];
    this.processing = false;
    this.requestCounts = new Map(); // Track per-channel rates
    this.globalRateLimitUntil = null;

    // Statistics
    this.stats = {
      sent: 0,
      dropped: 0,
      retries: 0,
      errors: 0,
      queueSize: 0
    };

    // Start processor
    this.startProcessor();
  }

  /**
   * Add a webhook message to the queue
   */
  async enqueue(webhookUrl, payload, options = {}) {
    const request = {
      id: Date.now() + Math.random(),
      webhookUrl,
      payload,
      priority: options.priority || 0,
      retries: 0,
      maxRetries: options.maxRetries || 3,
      createdAt: Date.now(),
      callback: options.callback || null
    };

    // Check queue size limits
    if (this.queue.length > 100) {
      logger.warn('Queue full, dropping oldest messages', {
        queueSize: this.queue.length
      });
      this.queue.splice(0, 10); // Remove oldest 10
      this.stats.dropped += 10;
    }

    this.queue.push(request);
    this.queue.sort((a, b) => b.priority - a.priority); // Higher priority first
    this.stats.queueSize = this.queue.length;

    logger.debug('Message queued', {
      id: request.id,
      queueSize: this.queue.length
    });

    return request.id;
  }

  /**
   * Process queue items
   */
  async startProcessor() {
    if (this.processing) return;
    this.processing = true;

    while (this.processing) {
      try {
        await this.processNext();
      } catch (error) {
        logger.error('Queue processor error', error);
      }
      await this.sleep(100); // Check every 100ms
    }
  }

  /**
   * Process next item in queue
   */
  async processNext() {
    // Check global rate limit
    if (this.globalRateLimitUntil && Date.now() < this.globalRateLimitUntil) {
      return;
    }

    // Get next item
    const request = this.queue.shift();
    if (!request) return;

    this.stats.queueSize = this.queue.length;

    // Check per-webhook rate limit
    const webhookKey = this.getWebhookKey(request.webhookUrl);
    if (!this.canSendToWebhook(webhookKey)) {
      // Re-queue for later
      this.queue.unshift(request);
      return;
    }

    // Send the request
    try {
      await this.sendRequest(request);
    } catch (error) {
      await this.handleError(error, request);
    }
  }

  /**
   * Check if we can send to this webhook (rate limiting)
   */
  canSendToWebhook(webhookKey) {
    const now = Date.now();
    const counts = this.requestCounts.get(webhookKey) || [];

    // Remove old entries
    const recentCounts = counts.filter(t => now - t < this.intervalMs);

    if (recentCounts.length >= this.maxRequestsPerInterval) {
      return false;
    }

    return true;
  }

  /**
   * Send webhook request
   */
  async sendRequest(request) {
    const webhookKey = this.getWebhookKey(request.webhookUrl);

    // Validate payload
    if (!request.payload.content && !request.payload.embeds) {
      throw new Error('Message must have content or embeds');
    }

    // Truncate content if too long
    if (request.payload.content && request.payload.content.length > 2000) {
      request.payload.content = request.payload.content.substring(0, 1997) + '...';
    }

    // Send request
    const response = await axios.post(request.webhookUrl, request.payload, {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot (Custom Webhook Sender, 1.0)'
      },
      timeout: 10000,
      validateStatus: null // Don't throw on 4xx/5xx
    });

    // Handle response
    if (response.status === 204) {
      // Success
      this.recordRequest(webhookKey);
      this.stats.sent++;

      logger.info('Message sent successfully', {
        id: request.id,
        webhookId: webhookKey
      });

      if (request.callback) {
        request.callback(null, { id: request.id, status: 'sent' });
      }
    } else if (response.status === 429) {
      // Rate limited
      const retryAfter = response.headers['retry-after'] || response.data?.retry_after;
      await this.handleRateLimit(retryAfter, request);
    } else if (response.status >= 500) {
      // Server error - retry
      throw new Error(`Discord server error: ${response.status}`);
    } else {
      // Client error - don't retry
      throw new Error(`Discord rejected message: ${response.status} - ${JSON.stringify(response.data)}`);
    }
  }

  /**
   * Handle rate limiting
   */
  async handleRateLimit(retryAfter, request) {
    const delayMs = (parseInt(retryAfter) || 5) * 1000 + this.retryAfterBuffer;

    logger.warn('Rate limited by Discord', {
      retryAfter: delayMs,
      webhookId: this.getWebhookKey(request.webhookUrl)
    });

    // Set global rate limit if it's a global limit
    if (retryAfter > 10) {
      this.globalRateLimitUntil = Date.now() + delayMs;
    }

    // Re-queue with higher priority
    request.priority = 10;
    this.queue.unshift(request);
    this.stats.retries++;
  }

  /**
   * Handle send errors
   */
  async handleError(error, request) {
    logger.error('Failed to send message', error);
    this.stats.errors++;

    request.retries++;

    if (request.retries < request.maxRetries) {
      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, request.retries), 30000);

      logger.info('Retrying message', {
        id: request.id,
        attempt: request.retries,
        delay
      });

      setTimeout(() => {
        this.queue.push(request);
      }, delay);
    } else {
      logger.error('Message dropped after max retries', {
        id: request.id,
        error: error.message
      });

      this.stats.dropped++;

      if (request.callback) {
        request.callback(error, { id: request.id, status: 'failed' });
      }
    }
  }

  /**
   * Record successful request for rate limiting
   */
  recordRequest(webhookKey) {
    const counts = this.requestCounts.get(webhookKey) || [];
    counts.push(Date.now());

    // Keep only recent entries
    const now = Date.now();
    const recentCounts = counts.filter(t => now - t < this.intervalMs * 2);
    this.requestCounts.set(webhookKey, recentCounts);
  }

  /**
   * Get webhook identifier from URL
   */
  getWebhookKey(webhookUrl) {
    const match = webhookUrl.match(/webhooks\\/(\\d+)\\/([\\w-]+)/);
    return match ? match[1] : webhookUrl;
  }

  /**
   * Get queue statistics
   */
  getStats() {
    return {
      ...this.stats,
      queueSize: this.queue.length,
      processing: this.processing,
      globalRateLimit: this.globalRateLimitUntil > Date.now()
    };
  }

  /**
   * Stop processing
   */
  stop() {
    this.processing = false;
    logger.info('Queue processor stopped', this.stats);
  }

  /**
   * Sleep helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton
let instance = null;

module.exports = {
  getInstance: (options = {}) => {
    if (!instance) {
      instance = new DiscordQueue(options);
    }
    return instance;
  },

  DiscordQueue
};