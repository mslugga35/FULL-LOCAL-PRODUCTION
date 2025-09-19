// FIXED ECOSYSTEM FOR WINDOWS - ALL BOTS
module.exports = {
  apps: [
    // DISCORD SENDER (Works fine)
    {
      name: 'discord-sender',
      script: './discord_sender.js',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      env: {
        DISCORD_WEBHOOK_URL: 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
        BOT_USERNAME: 'Sports Bot',
        TEXT_BATCH_SIZE: '10',
        FILE_BATCH_SIZE: '10',
        FLOOR_DELAY_MS: '250',
        QUEUE_DIRS: './message_queue/uatb,./message_queue/paid_uatb,./message_queue/diamond,./message_queue/paid_diamond,./message_queue/paid_chamba'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/discord-error.log',
      out_file: './logs/discord-out.log'
    },

    // WATCHDOG (Works fine)
    {
      name: 'watchdog',
      script: './scripts/watchdog.js',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      env: {
        CHECK_INTERVAL: '60000',
        RESTART_THRESHOLD: '3'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/watchdog-error.log',
      out_file: './logs/watchdog-out.log'
    }

    // Python scripts removed - will run separately
  ]
};