/**
 * Centralized logging module with structured output
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

const LOG_LEVELS = {
  ERROR: 'ERROR',
  WARN: 'WARN',
  INFO: 'INFO',
  DEBUG: 'DEBUG'
};

class Logger {
  constructor(appName, options = {}) {
    this.appName = appName;
    this.logToFile = options.logToFile || false;
    this.logDir = options.logDir || '/var/log/bots';
    this.maxFileSize = options.maxFileSize || 10 * 1024 * 1024; // 10MB
    this.currentLogFile = null;
    this.currentFileStream = null;

    if (this.logToFile) {
      this.initFileLogging();
    }
  }

  initFileLogging() {
    try {
      if (!fs.existsSync(this.logDir)) {
        fs.mkdirSync(this.logDir, { recursive: true });
      }
      this.rotateLogIfNeeded();
    } catch (error) {
      console.error(`[LOGGER] Failed to init file logging: ${error.message}`);
      this.logToFile = false;
    }
  }

  rotateLogIfNeeded() {
    const logFile = path.join(this.logDir, `${this.appName}.log`);

    try {
      if (fs.existsSync(logFile)) {
        const stats = fs.statSync(logFile);
        if (stats.size > this.maxFileSize) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const rotatedFile = path.join(this.logDir, `${this.appName}_${timestamp}.log`);
          fs.renameSync(logFile, rotatedFile);
        }
      }

      if (this.currentFileStream) {
        this.currentFileStream.end();
      }

      this.currentLogFile = logFile;
      this.currentFileStream = fs.createWriteStream(logFile, { flags: 'a' });
    } catch (error) {
      console.error(`[LOGGER] Failed to rotate log: ${error.message}`);
      this.logToFile = false;
    }
  }

  formatMessage(level, message, metadata = {}) {
    const timestamp = new Date().toISOString();
    const metaStr = Object.keys(metadata).length > 0
      ? ` | ${JSON.stringify(metadata)}`
      : '';

    return `[${timestamp}] [${this.appName}] [${level}] ${message}${metaStr}`;
  }

  log(level, message, metadata = {}) {
    const formattedMessage = this.formatMessage(level, message, metadata);

    // Console output with colors
    switch (level) {
      case LOG_LEVELS.ERROR:
        console.error(`\\x1b[31m${formattedMessage}\\x1b[0m`);
        break;
      case LOG_LEVELS.WARN:
        console.warn(`\\x1b[33m${formattedMessage}\\x1b[0m`);
        break;
      case LOG_LEVELS.DEBUG:
        if (process.env.NODE_ENV === 'development') {
          console.log(`\\x1b[36m${formattedMessage}\\x1b[0m`);
        }
        break;
      default:
        console.log(formattedMessage);
    }

    // File output
    if (this.logToFile && this.currentFileStream) {
      this.currentFileStream.write(formattedMessage + '\\n');

      // Check for rotation
      if (this.currentFileStream.bytesWritten > this.maxFileSize) {
        this.rotateLogIfNeeded();
      }
    }
  }

  error(message, error = null) {
    const metadata = error ? {
      error: error.message,
      stack: error.stack
    } : {};
    this.log(LOG_LEVELS.ERROR, message, metadata);
  }

  warn(message, metadata = {}) {
    this.log(LOG_LEVELS.WARN, message, metadata);
  }

  info(message, metadata = {}) {
    this.log(LOG_LEVELS.INFO, message, metadata);
  }

  debug(message, metadata = {}) {
    this.log(LOG_LEVELS.DEBUG, message, metadata);
  }

  // For PM2 compatibility
  pm2Log(message) {
    // PM2 already handles timestamp, so just log the message
    console.log(`[${this.appName}] ${message}`);
  }

  close() {
    if (this.currentFileStream) {
      this.currentFileStream.end();
      this.currentFileStream = null;
    }
  }
}

// Export singleton factory
const loggers = {};

module.exports = {
  createLogger: (appName, options = {}) => {
    if (!loggers[appName]) {
      loggers[appName] = new Logger(appName, options);
    }
    return loggers[appName];
  },

  LOG_LEVELS,

  // Convenience method for PM2 apps
  pm2Logger: (appName) => {
    return module.exports.createLogger(appName, {
      logToFile: process.env.NODE_ENV === 'production'
    });
  }
};