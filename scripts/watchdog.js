// LOCAL WATCHDOG - Monitors and restarts crashed services
const { exec } = require('child_process');
const fs = require('fs');

const CHECK_INTERVAL = parseInt(process.env.CHECK_INTERVAL) || 60000; // 1 minute
const RESTART_THRESHOLD = parseInt(process.env.RESTART_THRESHOLD) || 3;

// Services to monitor
const CRITICAL_SERVICES = [
  'telegram-collector',
  'message-processor',
  'discord-sender'
];

let restartCounts = {};

async function checkServices() {
  console.log(`[${new Date().toISOString()}] Checking services...`);

  exec('pm2 jlist', (error, stdout, stderr) => {
    if (error) {
      console.error(`Error checking PM2: ${error}`);
      return;
    }

    try {
      const processes = JSON.parse(stdout);

      for (const service of CRITICAL_SERVICES) {
        const proc = processes.find(p => p.name === service);

        if (!proc) {
          console.log(`[WATCHDOG] ${service} not found! Starting...`);
          exec(`pm2 start ecosystem-complete.config.js --only ${service}`, (err) => {
            if (err) console.error(`Failed to start ${service}: ${err}`);
            else console.log(`[WATCHDOG] Started ${service}`);
          });
        } else if (proc.pm2_env.status === 'stopped' || proc.pm2_env.status === 'errored') {
          // Track restart attempts
          restartCounts[service] = (restartCounts[service] || 0) + 1;

          if (restartCounts[service] <= RESTART_THRESHOLD) {
            console.log(`[WATCHDOG] ${service} is ${proc.pm2_env.status}! Restarting... (attempt ${restartCounts[service]})`);
            exec(`pm2 restart ${service}`, (err) => {
              if (err) console.error(`Failed to restart ${service}: ${err}`);
              else console.log(`[WATCHDOG] Restarted ${service}`);
            });
          } else {
            console.error(`[WATCHDOG] ${service} has failed ${restartCounts[service]} times. Manual intervention needed!`);
          }
        } else if (proc.pm2_env.status === 'online') {
          // Reset counter if service is healthy
          if (restartCounts[service] > 0) {
            console.log(`[WATCHDOG] ${service} recovered. Resetting counter.`);
            restartCounts[service] = 0;
          }
        }
      }

      // Log status
      const status = processes.map(p => `${p.name}: ${p.pm2_env.status}`).join(', ');
      console.log(`[WATCHDOG] Status: ${status}`);

    } catch (parseError) {
      console.error(`Error parsing PM2 output: ${parseError}`);
    }
  });
}

// Main loop
console.log('=========================================');
console.log('LOCAL WATCHDOG - Started');
console.log(`Monitoring: ${CRITICAL_SERVICES.join(', ')}`);
console.log(`Check interval: ${CHECK_INTERVAL}ms`);
console.log('=========================================');

// Initial check
checkServices();

// Schedule regular checks
setInterval(checkServices, CHECK_INTERVAL);

// Handle shutdown
process.on('SIGINT', () => {
  console.log('\n[WATCHDOG] Shutting down...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n[WATCHDOG] Shutting down...');
  process.exit(0);
});