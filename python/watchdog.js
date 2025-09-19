/**
 * PM2 Process Watchdog
 * Monitors and auto-restarts failed processes with intelligent backoff
 */

const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const config = require('./config');
const { createLogger } = require('./logger');

const execAsync = promisify(exec);
const logger = createLogger('watchdog', { logToFile: true });

class ProcessWatchdog {
  constructor() {
    this.pollInterval = config.watchdog.pollMs;
    this.staleThreshold = config.watchdog.staleMs;
    this.largeBacklogThreshold = config.watchdog.largeBacklog;
    this.ignoreProcesses = config.watchdog.ignoreProcs;

    // Track restart attempts per process
    this.restartAttempts = new Map();
    this.lastHealthCheck = new Map();
    this.processStats = new Map();

    // Circuit breaker for each process
    this.circuitBreakers = new Map();
  }

  /**
   * Start monitoring
   */
  async start() {
    logger.info('Watchdog starting', {
      pollInterval: this.pollInterval,
      staleThreshold: this.staleThreshold,
      ignoreProcesses: this.ignoreProcesses
    });

    // Initial check
    await this.checkProcesses();

    // Schedule regular checks
    setInterval(() => {
      this.checkProcesses().catch(error => {
        logger.error('Watchdog check failed', error);
      });
    }, this.pollInterval);

    // Monitor webhook if configured
    if (config.discord.monitorWebhook) {
      this.sendMonitorNotification('🐕 Watchdog Started', {
        color: 0x00ff00,
        fields: [
          { name: 'Poll Interval', value: `${this.pollInterval}ms`, inline: true },
          { name: 'Stale Threshold', value: `${this.staleThreshold}ms`, inline: true }
        ]
      });
    }
  }

  /**
   * Check all PM2 processes
   */
  async checkProcesses() {
    try {
      const processes = await this.getPM2List();

      for (const proc of processes) {
        if (this.ignoreProcesses.includes(proc.name)) {
          continue;
        }

        await this.checkProcess(proc);
      }

      // Check for queue backlogs
      await this.checkQueues();

      // Update health metrics
      this.updateHealthMetrics();
    } catch (error) {
      logger.error('Failed to check processes', error);
    }
  }

  /**
   * Get PM2 process list
   */
  async getPM2List() {
    try {
      const { stdout } = await execAsync('pm2 jlist', {
        timeout: 10000
      });

      const processes = JSON.parse(stdout);
      return processes.map(p => ({
        name: p.name,
        pm_id: p.pm_id,
        status: p.pm2_env.status,
        restarts: p.pm2_env.restart_time,
        cpu: p.monit.cpu,
        memory: p.monit.memory,
        uptime: Date.now() - p.pm2_env.pm_uptime
      }));
    } catch (error) {
      logger.error('Failed to get PM2 list', error);
      return [];
    }
  }

  /**
   * Check individual process health
   */
  async checkProcess(proc) {
    const breaker = this.getCircuitBreaker(proc.name);

    // Skip if circuit breaker is open
    if (breaker.isOpen()) {
      logger.debug(`Circuit breaker open for ${proc.name}`, {
        resetTime: breaker.resetTime
      });
      return;
    }

    // Check process status
    if (proc.status !== 'online') {
      await this.handleOfflineProcess(proc);
      return;
    }

    // Check for high restart count
    if (proc.restarts > 50) {
      await this.handleHighRestarts(proc);
    }

    // Check for memory issues
    if (proc.memory > 500 * 1024 * 1024) { // 500MB
      await this.handleHighMemory(proc);
    }

    // Check for CPU issues
    if (proc.cpu > 80) {
      logger.warn(`High CPU usage for ${proc.name}`, {
        cpu: proc.cpu
      });
    }

    // Update last health check
    this.lastHealthCheck.set(proc.name, Date.now());
  }

  /**
   * Handle offline process
   */
  async handleOfflineProcess(proc) {
    const attempts = this.restartAttempts.get(proc.name) || 0;

    if (attempts >= 5) {
      logger.error(`Process ${proc.name} failed after 5 restart attempts`, {
        status: proc.status
      });

      // Open circuit breaker
      const breaker = this.getCircuitBreaker(proc.name);
      breaker.open();

      // Send alert
      await this.sendAlert(`Process ${proc.name} is down`, {
        status: proc.status,
        attempts: attempts
      });

      return;
    }

    logger.warn(`Restarting offline process ${proc.name}`, {
      status: proc.status,
      attempt: attempts + 1
    });

    try {
      await execAsync(`pm2 restart ${proc.name}`, {
        timeout: 15000
      });

      this.restartAttempts.set(proc.name, attempts + 1);

      // Reset attempts after successful restart
      setTimeout(() => {
        this.restartAttempts.set(proc.name, 0);
      }, 60000); // Reset after 1 minute of stability
    } catch (error) {
      logger.error(`Failed to restart ${proc.name}`, error);
    }
  }

  /**
   * Handle process with high restart count
   */
  async handleHighRestarts(proc) {
    logger.warn(`High restart count for ${proc.name}`, {
      restarts: proc.restarts
    });

    // Check if it's the OCR processor (known issue)
    if (proc.name === config.pm2.ocr && proc.restarts > 75) {
      logger.info('Resetting OCR processor due to high restarts');

      try {
        await execAsync(`pm2 delete ${proc.name}`, { timeout: 10000 });
        await execAsync(`pm2 start ecosystem.config.js --only ${proc.name}`, {
          timeout: 15000
        });
      } catch (error) {
        logger.error('Failed to reset OCR processor', error);
      }
    }
  }

  /**
   * Handle high memory usage
   */
  async handleHighMemory(proc) {
    logger.warn(`High memory usage for ${proc.name}`, {
      memory: Math.round(proc.memory / 1024 / 1024) + 'MB'
    });

    // Graceful restart for memory issues
    try {
      await execAsync(`pm2 reload ${proc.name}`, {
        timeout: 20000
      });
      logger.info(`Reloaded ${proc.name} due to high memory`);
    } catch (error) {
      logger.error(`Failed to reload ${proc.name}`, error);
    }
  }

  /**
   * Check message queues for backlogs
   */
  async checkQueues() {
    try {
      const queueDir = config.dirs.queue;
      const folders = ['uatb_expected', 'diamond_expected', 'free_cappers'];

      for (const folder of folders) {
        const folderPath = path.join(queueDir, folder);

        try {
          const files = await fs.readdir(folderPath);
          const jsonFiles = files.filter(f => f.endsWith('.json'));

          if (jsonFiles.length > this.largeBacklogThreshold) {
            logger.warn(`Large backlog in ${folder}`, {
              count: jsonFiles.length
            });

            // Check if messages are stale
            const oldestFile = jsonFiles[0];
            const filePath = path.join(folderPath, oldestFile);
            const stats = await fs.stat(filePath);
            const age = Date.now() - stats.mtime.getTime();

            if (age > this.staleThreshold) {
              logger.error(`Stale messages in ${folder}`, {
                age: Math.round(age / 1000) + 's',
                count: jsonFiles.length
              });

              await this.sendAlert(`Queue backlog in ${folder}`, {
                count: jsonFiles.length,
                oldest: Math.round(age / 1000) + 's'
              });
            }
          }
        } catch (error) {
          // Queue folder doesn't exist, that's okay
        }
      }
    } catch (error) {
      logger.error('Failed to check queues', error);
    }
  }

  /**
   * Circuit breaker for process restarts
   */
  getCircuitBreaker(processName) {
    if (!this.circuitBreakers.has(processName)) {
      this.circuitBreakers.set(processName, {
        isOpen: false,
        failures: 0,
        resetTime: null,
        open: function() {
          this.isOpen = true;
          this.resetTime = Date.now() + 300000; // 5 minutes
          logger.warn(`Circuit breaker opened for ${processName}`);
        },
        close: function() {
          this.isOpen = false;
          this.failures = 0;
          this.resetTime = null;
          logger.info(`Circuit breaker closed for ${processName}`);
        },
        isOpen: function() {
          if (this.isOpen && Date.now() > this.resetTime) {
            this.close();
          }
          return this.isOpen;
        }
      });
    }

    return this.circuitBreakers.get(processName);
  }

  /**
   * Update health metrics
   */
  updateHealthMetrics() {
    const now = Date.now();
    const metrics = {
      healthy: 0,
      unhealthy: 0,
      restarting: 0
    };

    for (const [name, lastCheck] of this.lastHealthCheck) {
      if (now - lastCheck < this.pollInterval * 2) {
        metrics.healthy++;
      } else {
        metrics.unhealthy++;
      }
    }

    for (const attempts of this.restartAttempts.values()) {
      if (attempts > 0) {
        metrics.restarting++;
      }
    }

    logger.debug('Health metrics', metrics);
  }

  /**
   * Send alert to Discord webhook
   */
  async sendAlert(title, details) {
    if (!config.discord.monitorWebhook) {
      return;
    }

    try {
      await this.sendMonitorNotification(`⚠️ ${title}`, {
        color: 0xff0000,
        fields: Object.entries(details).map(([key, value]) => ({
          name: key,
          value: String(value),
          inline: true
        }))
      });
    } catch (error) {
      logger.error('Failed to send alert', error);
    }
  }

  /**
   * Send notification to monitor webhook
   */
  async sendMonitorNotification(title, embed) {
    const axios = require('axios');

    try {
      await axios.post(config.discord.monitorWebhook, {
        embeds: [{
          title,
          timestamp: new Date().toISOString(),
          ...embed
        }]
      });
    } catch (error) {
      logger.error('Failed to send monitor notification', error);
    }
  }
}

// Start watchdog if running as main module
if (require.main === module) {
  const watchdog = new ProcessWatchdog();
  watchdog.start().catch(error => {
    logger.error('Failed to start watchdog', error);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGINT', () => {
    logger.info('Watchdog shutting down...');
    process.exit(0);
  });
}

module.exports = ProcessWatchdog;