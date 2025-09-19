// Rate limiting utility for Discord API
const sleep = ms => new Promise(r => setTimeout(r, ms));

class RateLimiter {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 5;
    this.baseDelay = options.baseDelay || 1000;
    this.maxDelay = options.maxDelay || 60000;
  }

  async execute(fn, context = {}) {
    let lastError;
    
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const result = await fn();
        return result;
      } catch (error) {
        lastError = error;
        
        // Handle Discord rate limits
        if (error.response && error.response.status === 429) {
          const retryAfter = error.response.headers['retry-after'] || error.response.headers['x-ratelimit-reset-after'];
          const delay = retryAfter ? Number(retryAfter) * 1000 : Math.min(this.baseDelay * Math.pow(2, attempt), this.maxDelay);
          
          console.log(`[RATE LIMIT] Waiting ${delay}ms before retry (attempt ${attempt + 1}/${this.maxRetries})`);
          await sleep(delay);
          continue;
        }
        
        // Handle other retryable errors
        if (error.response && error.response.status >= 500) {
          const delay = Math.min(this.baseDelay * Math.pow(2, attempt), this.maxDelay);
          console.log(`[ERROR ${error.response.status}] Retrying in ${delay}ms (attempt ${attempt + 1}/${this.maxRetries})`);
          await sleep(delay);
          continue;
        }
        
        // Non-retryable error
        throw error;
      }
    }
    
    throw lastError || new Error('Max retries exceeded');
  }
}

// Timestamp normalization utility
function toISO(input) {
  if (input == null) return null;
  
  const s = String(input).trim();
  
  // Check for ISO format
  const iso = /^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?)?(?:Z|[+\-]\d{2}:?\d{2})?$/;
  
  // Check for epoch milliseconds
  const epoch = /^\d{10,13}$/;
  
  let d;
  if (epoch.test(s)) {
    d = new Date(Number(s));
  } else if (iso.test(s)) {
    d = new Date(s);
  } else {
    return null; // Invalid format
  }
  
  return isNaN(+d) ? null : d.toISOString();
}

// Message deduplication
class MessageDeduplicator {
  constructor(ttl = 3600000) { // 1 hour default TTL
    this.seen = new Map();
    this.ttl = ttl;
    
    // Clean up old entries periodically
    setInterval(() => this.cleanup(), ttl / 2);
  }
  
  generateKey(message) {
    // Create unique key from platform + message ID or content hash
    const platform = message.platform || 'unknown';
    const id = message.id || message.message_id || this.hash(JSON.stringify(message));
    return `${platform}:${id}`;
  }
  
  hash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(36);
  }
  
  isDuplicate(message) {
    const key = this.generateKey(message);
    const now = Date.now();
    
    if (this.seen.has(key)) {
      const timestamp = this.seen.get(key);
      if (now - timestamp < this.ttl) {
        return true;
      }
    }
    
    this.seen.set(key, now);
    return false;
  }
  
  cleanup() {
    const now = Date.now();
    for (const [key, timestamp] of this.seen.entries()) {
      if (now - timestamp > this.ttl) {
        this.seen.delete(key);
      }
    }
  }
}

module.exports = {
  RateLimiter,
  toISO,
  MessageDeduplicator,
  sleep
};
