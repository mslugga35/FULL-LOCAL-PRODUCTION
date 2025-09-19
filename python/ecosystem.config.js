module.exports = {
  apps: [
    {
      name: 'telegram-forwarder',
      script: '/root/bots/telegram_forwarder.js',
      max_memory_restart: '250M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/telegram-forwarder-error.log',
      out_file: '/root/.pm2/logs/telegram-forwarder-out.log',
      merge_logs: true,
      time: true
    },
    {
      name: 'tg-producer',
      script: '/root/bots/tg_producer.js',
      max_memory_restart: '250M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/tg-producer-error.log',
      out_file: '/root/.pm2/logs/tg-producer-out.log',
      merge_logs: true,
      time: true
    },
    {
      name: 'ocr-processor',
      script: '/root/bots/ocr-folder-processor.js',
      max_memory_restart: '400M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/ocr-processor-error.log',
      out_file: '/root/.pm2/logs/ocr-processor-out.log',
      merge_logs: true,
      time: true,
      env: {
        GOOGLE_APPLICATION_CREDENTIALS: '/root/bots/google-vision-key.json'
      }
    },
    {
      name: 'message-router',
      script: '/root/bots/message_router.js',
      max_memory_restart: '300M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/message-router-error.log',
      out_file: '/root/.pm2/logs/message-router-out.log',
      merge_logs: true,
      time: true
    },
    {
      name: 'discord-sender',
      script: '/root/bots/discord_sender.js',
      max_memory_restart: '300M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/discord-sender-error.log',
      out_file: '/root/.pm2/logs/discord-sender-out.log',
      merge_logs: true,
      time: true,
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'production',
        RATE_LIMIT_ENABLED: 'true'
      }
    },
    {
      name: 'paid-webhook',
      script: '/root/bots/paid_webhook.js',
      max_memory_restart: '250M',
      min_uptime: '30s',
      max_restarts: 5,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/paid-webhook-error.log',
      out_file: '/root/.pm2/logs/paid-webhook-out.log',
      merge_logs: true,
      time: true
    },
    {
      name: 'watchdog-pro',
      script: '/root/bots/watchdog_pro.js',
      max_memory_restart: '200M',
      min_uptime: '60s',
      max_restarts: 3,
      kill_timeout: 5000,
      error_file: '/root/.pm2/logs/watchdog-pro-error.log',
      out_file: '/root/.pm2/logs/watchdog-pro-out.log',
      merge_logs: true,
      time: true,
      cron_restart: '0 */6 * * *'  // Restart every 6 hours to prevent memory leaks
    }
  ],

  // Deploy configuration (optional)
  deploy: {
    production: {
      user: 'root',
      host: 'localhost',
      ref: 'origin/master',
      repo: 'git@github.com:yourusername/yourrepo.git',
      path: '/root/bots',
      'post-deploy': 'npm install && pm2 reload ecosystem.config.js --env production'
    }
  }
};
