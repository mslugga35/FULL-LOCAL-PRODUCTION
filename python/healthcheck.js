/**
 * Health check HTTP server
 * Provides monitoring endpoints for external services
 */

const http = require('http');
const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const config = require('./config');
const { createLogger } = require('./logger');

const execAsync = promisify(exec);
const logger = createLogger('healthcheck');

class HealthCheckServer {
  constructor(port = 3000) {
    this.port = port;
    this.server = null;
    this.startTime = Date.now();
    this.requestCount = 0;
    this.checks = new Map();

    // Register default checks
    this.registerCheck('pm2', this.checkPM2.bind(this));
    this.registerCheck('queues', this.checkQueues.bind(this));
    this.registerCheck('disk', this.checkDiskSpace.bind(this));
    this.registerCheck('memory', this.checkMemory.bind(this));
  }

  /**
   * Start the health check server
   */
  start() {
    this.server = http.createServer(this.handleRequest.bind(this));

    this.server.listen(this.port, () => {
      logger.info(`Health check server listening on port ${this.port}`);
    });

    // Handle errors
    this.server.on('error', (error) => {
      logger.error('Health check server error', error);
    });

    return this.server;
  }

  /**
   * Handle HTTP requests
   */
  async handleRequest(req, res) {
    this.requestCount++;

    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');

    try {
      const url = new URL(req.url, `http://localhost:${this.port}`);

      switch (url.pathname) {
        case '/health':
          await this.handleHealthCheck(req, res);
          break;

        case '/status':
          await this.handleStatus(req, res);
          break;

        case '/metrics':
          await this.handleMetrics(req, res);
          break;

        case '/ready':
          await this.handleReadiness(req, res);
          break;

        case '/live':
          await this.handleLiveness(req, res);
          break;

        default:
          res.writeHead(404);
          res.end(JSON.stringify({ error: 'Not found' }));
      }
    } catch (error) {
      logger.error('Request handler error', error);
      res.writeHead(500);
      res.end(JSON.stringify({
        status: 'error',
        error: error.message
      }));
    }
  }

  /**
   * Main health check endpoint
   */
  async handleHealthCheck(req, res) {
    const results = {};
    let overallStatus = 'healthy';

    // Run all registered checks
    for (const [name, checkFn] of this.checks) {
      try {
        const result = await checkFn();
        results[name] = result;

        if (result.status !== 'healthy') {
          overallStatus = result.status === 'degraded' && overallStatus === 'healthy'
            ? 'degraded'
            : 'unhealthy';
        }
      } catch (error) {
        results[name] = {
          status: 'error',
          error: error.message
        };
        overallStatus = 'unhealthy';
      }
    }

    const statusCode = overallStatus === 'healthy' ? 200 :
                       overallStatus === 'degraded' ? 200 : 503;

    res.writeHead(statusCode);
    res.end(JSON.stringify({
      status: overallStatus,
      timestamp: new Date().toISOString(),
      checks: results
    }));
  }

  /**
   * Status endpoint with detailed info
   */
  async handleStatus(req, res) {
    try {
      const { stdout } = await execAsync('pm2 jlist', { timeout: 5000 });
      const processes = JSON.parse(stdout);

      const status = {
        uptime: Math.floor((Date.now() - this.startTime) / 1000),
        processes: processes.map(p => ({
          name: p.name,
          status: p.pm2_env.status,
          restarts: p.pm2_env.restart_time,
          uptime: p.pm2_env.pm_uptime,
          cpu: p.monit.cpu,
          memory: Math.round(p.monit.memory / 1024 / 1024) + 'MB'
        }))
      };

      res.writeHead(200);
      res.end(JSON.stringify(status));
    } catch (error) {
      res.writeHead(500);
      res.end(JSON.stringify({ error: error.message }));
    }
  }

  /**
   * Metrics endpoint for monitoring
   */
  async handleMetrics(req, res) {
    const metrics = await this.collectMetrics();

    // Prometheus format
    const promFormat = this.formatPrometheus(metrics);

    res.setHeader('Content-Type', 'text/plain');
    res.writeHead(200);
    res.end(promFormat);
  }

  /**
   * Kubernetes readiness probe
   */
  async handleReadiness(req, res) {
    // Check if all critical services are ready
    const pm2Check = await this.checkPM2();
    const queueCheck = await this.checkQueues();

    if (pm2Check.status === 'healthy' && queueCheck.status === 'healthy') {
      res.writeHead(200);
      res.end(JSON.stringify({ ready: true }));
    } else {
      res.writeHead(503);
      res.end(JSON.stringify({ ready: false }));
    }
  }

  /**
   * Kubernetes liveness probe
   */
  async handleLiveness(req, res) {
    // Simple liveness check
    res.writeHead(200);
    res.end(JSON.stringify({ alive: true }));
  }

  /**
   * Register a health check
   */
  registerCheck(name, checkFn) {
    this.checks.set(name, checkFn);
  }

  /**
   * Check PM2 processes
   */
  async checkPM2() {
    try {
      const { stdout } = await execAsync('pm2 jlist', { timeout: 5000 });
      const processes = JSON.parse(stdout);

      const critical = [
        config.pm2.router,
        config.pm2.paidWebhook
      ];

      let unhealthyCount = 0;
      let degradedCount = 0;

      for (const proc of processes) {
        if (proc.pm2_env.status !== 'online') {
          if (critical.includes(proc.name)) {
            unhealthyCount++;
          } else {
            degradedCount++;
          }
        }

        // High restart count
        if (proc.pm2_env.restart_time > 50) {
          degradedCount++;
        }
      }

      if (unhealthyCount > 0) {
        return { status: 'unhealthy', unhealthy: unhealthyCount };
      } else if (degradedCount > 0) {
        return { status: 'degraded', degraded: degradedCount };
      }

      return { status: 'healthy', processes: processes.length };
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  }

  /**
   * Check message queues
   */
  async checkQueues() {
    try {
      const queueDir = config.dirs.queue;
      const folders = ['uatb_expected', 'diamond_expected', 'free_cappers'];
      let totalMessages = 0;
      let oldestMessage = 0;

      for (const folder of folders) {
        try {
          const folderPath = path.join(queueDir, folder);
          const files = await fs.readdir(folderPath);
          const jsonFiles = files.filter(f => f.endsWith('.json'));

          totalMessages += jsonFiles.length;

          if (jsonFiles.length > 0) {
            const firstFile = path.join(folderPath, jsonFiles[0]);
            const stats = await fs.stat(firstFile);
            const age = Date.now() - stats.mtime.getTime();
            oldestMessage = Math.max(oldestMessage, age);
          }
        } catch (error) {
          // Folder doesn't exist, skip
        }
      }

      // Check thresholds
      if (totalMessages > 50) {
        return { status: 'degraded', backlog: totalMessages };
      } else if (oldestMessage > 300000) { // 5 minutes
        return { status: 'degraded', oldest: Math.round(oldestMessage / 1000) + 's' };
      }

      return { status: 'healthy', messages: totalMessages };
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  }

  /**
   * Check disk space
   */
  async checkDiskSpace() {
    try {
      const { stdout } = await execAsync('df -h /', { timeout: 5000 });
      const lines = stdout.split('\\n');
      const dataLine = lines[1];

      if (dataLine) {
        const parts = dataLine.split(/\\s+/);
        const usePercent = parseInt(parts[4]);

        if (usePercent > 90) {
          return { status: 'unhealthy', usage: usePercent + '%' };
        } else if (usePercent > 80) {
          return { status: 'degraded', usage: usePercent + '%' };
        }

        return { status: 'healthy', usage: usePercent + '%' };
      }
    } catch (error) {
      return { status: 'error', error: error.message };
    }

    return { status: 'unknown' };
  }

  /**
   * Check system memory
   */
  async checkMemory() {
    try {
      const { stdout } = await execAsync('free -m', { timeout: 5000 });
      const lines = stdout.split('\\n');
      const memLine = lines[1];

      if (memLine) {
        const parts = memLine.split(/\\s+/);
        const total = parseInt(parts[1]);
        const used = parseInt(parts[2]);
        const usePercent = Math.round((used / total) * 100);

        if (usePercent > 90) {
          return { status: 'unhealthy', usage: usePercent + '%' };
        } else if (usePercent > 80) {
          return { status: 'degraded', usage: usePercent + '%' };
        }

        return { status: 'healthy', usage: usePercent + '%' };
      }
    } catch (error) {
      return { status: 'error', error: error.message };
    }

    return { status: 'unknown' };
  }

  /**
   * Collect all metrics
   */
  async collectMetrics() {
    const metrics = {
      healthcheck_uptime_seconds: (Date.now() - this.startTime) / 1000,
      healthcheck_requests_total: this.requestCount
    };

    // Get PM2 metrics
    try {
      const { stdout } = await execAsync('pm2 jlist', { timeout: 5000 });
      const processes = JSON.parse(stdout);

      for (const proc of processes) {
        const name = proc.name.replace(/-/g, '_');
        metrics[`process_restarts_total{name="${proc.name}"}`] = proc.pm2_env.restart_time;
        metrics[`process_memory_bytes{name="${proc.name}"}`] = proc.monit.memory;
        metrics[`process_cpu_percent{name="${proc.name}"}`] = proc.monit.cpu;
      }
    } catch (error) {
      logger.error('Failed to get PM2 metrics', error);
    }

    return metrics;
  }

  /**
   * Format metrics in Prometheus format
   */
  formatPrometheus(metrics) {
    let output = '';

    for (const [key, value] of Object.entries(metrics)) {
      output += `# TYPE ${key.split('{')[0]} gauge\\n`;
      output += `${key} ${value}\\n`;
    }

    return output;
  }

  /**
   * Stop the server
   */
  stop() {
    if (this.server) {
      this.server.close();
      logger.info('Health check server stopped');
    }
  }
}

// Start if run directly
if (require.main === module) {
  const port = process.env.HEALTH_PORT || 3000;
  const server = new HealthCheckServer(port);
  server.start();

  // Graceful shutdown
  process.on('SIGINT', () => {
    logger.info('Shutting down health check server...');
    server.stop();
    process.exit(0);
  });
}

module.exports = HealthCheckServer;