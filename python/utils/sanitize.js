/**
 * Message sanitization utility
 * Prevents injection attacks and removes sensitive data
 */

const crypto = require('crypto');

const SENSITIVE_PATTERNS = [
  // API Keys and Tokens
  /sk-[a-zA-Z0-9]{48}/gi, // OpenAI API keys
  /Bot\s+[a-zA-Z0-9\-._]{59}/gi, // Discord bot tokens
  /[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, // UUIDs that might be tokens
  /Bearer\s+[a-zA-Z0-9\-._]+/gi, // Bearer tokens

  // Webhooks
  /https:\/\/discord\.com\/api\/webhooks\/\d+\/[\w-]+/gi,
  /https:\/\/hooks\.slack\.com\/services\/[\w\/]+/gi,

  // Email addresses (optional - uncomment if needed)
  // /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,

  // Credit card numbers (basic pattern)
  /\b(?:\d[ -]*?){13,16}\b/g,

  // Social Security Numbers (US)
  /\b\d{3}-\d{2}-\d{4}\b/g,

  // Private IP addresses
  /\b(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b/g,
];

const DISCORD_INJECTION_PATTERNS = [
  /@everyone/gi,
  /@here/gi,
  /<@&?\d+>/g, // User and role mentions
];

class MessageSanitizer {
  constructor(options = {}) {
    this.removeSensitive = options.removeSensitive !== false;
    this.preventMentions = options.preventMentions !== false;
    this.maxLength = options.maxLength || 2000;
    this.hashSensitive = options.hashSensitive || false;
    this.customPatterns = options.customPatterns || [];
    this.allowedDomains = options.allowedDomains || [];
  }

  /**
   * Sanitize a message for Discord
   */
  sanitize(text) {
    if (!text || typeof text !== 'string') {
      return '';
    }

    let sanitized = text;

    // Remove sensitive data
    if (this.removeSensitive) {
      sanitized = this.removeSensitiveData(sanitized);
    }

    // Prevent Discord injection
    if (this.preventMentions) {
      sanitized = this.preventDiscordInjection(sanitized);
    }

    // Remove zero-width characters and other Unicode tricks
    sanitized = this.removeInvisibleChars(sanitized);

    // Truncate if too long
    if (sanitized.length > this.maxLength) {
      sanitized = this.truncate(sanitized, this.maxLength);
    }

    // Final validation
    sanitized = this.validateText(sanitized);

    return sanitized;
  }

  /**
   * Remove sensitive data from text
   */
  removeSensitiveData(text) {
    let sanitized = text;

    // Apply built-in patterns
    for (const pattern of SENSITIVE_PATTERNS) {
      if (this.hashSensitive) {
        // Replace with hash for debugging
        sanitized = sanitized.replace(pattern, (match) => {
          const hash = crypto.createHash('sha256')
            .update(match)
            .digest('hex')
            .substring(0, 8);
          return `[REDACTED:${hash}]`;
        });
      } else {
        // Complete removal
        sanitized = sanitized.replace(pattern, '[REDACTED]');
      }
    }

    // Apply custom patterns
    for (const pattern of this.customPatterns) {
      sanitized = sanitized.replace(pattern, '[REDACTED]');
    }

    return sanitized;
  }

  /**
   * Prevent Discord mention injection
   */
  preventDiscordInjection(text) {
    let sanitized = text;

    for (const pattern of DISCORD_INJECTION_PATTERNS) {
      sanitized = sanitized.replace(pattern, (match) => {
        // Replace @ with a similar looking character
        return match.replace('@', '\\@');
      });
    }

    // Escape Discord formatting characters if they're being abused
    // But preserve legitimate formatting
    sanitized = this.escapeDiscordFormatting(sanitized);

    return sanitized;
  }

  /**
   * Escape Discord formatting to prevent abuse
   */
  escapeDiscordFormatting(text) {
    // Only escape if there's excessive use (potential abuse)
    const formatChars = ['*', '_', '~', '`', '|', '>'];

    for (const char of formatChars) {
      const count = (text.match(new RegExp('\\' + char, 'g')) || []).length;

      // If there are too many format characters, it might be abuse
      if (count > 20) {
        text = text.replace(new RegExp('\\' + char, 'g'), '\\' + char);
      }
    }

    return text;
  }

  /**
   * Remove invisible and zero-width characters
   */
  removeInvisibleChars(text) {
    // Remove zero-width characters
    const invisibleChars = [
      '\\u200B', // Zero-width space
      '\\u200C', // Zero-width non-joiner
      '\\u200D', // Zero-width joiner
      '\\u2060', // Word joiner
      '\\uFEFF', // Zero-width no-break space
      '\\u180E', // Mongolian vowel separator
      '\\u2000-\\u200F', // Various spaces and formatting marks
      '\\u202A-\\u202F', // Directional formatting
      '\\u2061-\\u2064', // Invisible math operators
    ];

    let pattern = new RegExp('[' + invisibleChars.join('') + ']', 'g');
    return text.replace(pattern, '');
  }

  /**
   * Truncate text intelligently
   */
  truncate(text, maxLength) {
    if (text.length <= maxLength) {
      return text;
    }

    // Try to truncate at a word boundary
    const truncated = text.substring(0, maxLength - 3);
    const lastSpace = truncated.lastIndexOf(' ');

    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...';
    }

    return truncated + '...';
  }

  /**
   * Final validation and cleanup
   */
  validateText(text) {
    // Remove null bytes
    text = text.replace(/\\0/g, '');

    // Normalize whitespace
    text = text.replace(/\\s+/g, ' ').trim();

    // Remove control characters except newlines and tabs
    text = text.replace(/[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]/g, '');

    return text;
  }

  /**
   * Check if text contains sensitive data
   */
  containsSensitiveData(text) {
    if (!text) return false;

    for (const pattern of SENSITIVE_PATTERNS) {
      if (pattern.test(text)) {
        return true;
      }
    }

    for (const pattern of this.customPatterns) {
      if (pattern.test(text)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Sanitize a Discord embed object
   */
  sanitizeEmbed(embed) {
    if (!embed || typeof embed !== 'object') {
      return null;
    }

    const sanitized = {};

    // Sanitize each field
    if (embed.title) {
      sanitized.title = this.sanitize(embed.title);
    }

    if (embed.description) {
      sanitized.description = this.sanitize(embed.description);
    }

    if (embed.url && this.isValidUrl(embed.url)) {
      sanitized.url = embed.url;
    }

    if (embed.color && typeof embed.color === 'number') {
      sanitized.color = embed.color;
    }

    if (embed.fields && Array.isArray(embed.fields)) {
      sanitized.fields = embed.fields.map(field => ({
        name: this.sanitize(field.name || ''),
        value: this.sanitize(field.value || ''),
        inline: Boolean(field.inline)
      })).slice(0, 25); // Discord limit
    }

    if (embed.footer) {
      sanitized.footer = {
        text: this.sanitize(embed.footer.text || '')
      };
    }

    if (embed.author) {
      sanitized.author = {
        name: this.sanitize(embed.author.name || '')
      };
    }

    return sanitized;
  }

  /**
   * Validate URL
   */
  isValidUrl(url) {
    try {
      const parsed = new URL(url);

      // Check if domain is allowed
      if (this.allowedDomains.length > 0) {
        const domain = parsed.hostname.toLowerCase();
        return this.allowedDomains.some(allowed =>
          domain === allowed || domain.endsWith('.' + allowed)
        );
      }

      // Basic validation
      return ['http:', 'https:'].includes(parsed.protocol);
    } catch {
      return false;
    }
  }
}

// Export singleton factory
module.exports = {
  createSanitizer: (options = {}) => {
    return new MessageSanitizer(options);
  },

  // Default sanitizer instance
  default: new MessageSanitizer(),

  // Utility functions
  containsSensitiveData: (text) => {
    const sanitizer = new MessageSanitizer();
    return sanitizer.containsSensitiveData(text);
  },

  sanitize: (text, options = {}) => {
    const sanitizer = new MessageSanitizer(options);
    return sanitizer.sanitize(text);
  }
};