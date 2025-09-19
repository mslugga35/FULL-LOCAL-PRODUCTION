// FULL LOCAL PRODUCTION ECOSYSTEM
// Everything runs locally - no Hetzner dependency
module.exports = {
  apps: [
    // Telegram Collector
    {
      name: 'tg-collector',
      script: 'python',
      args: './python/telegram_to_discord.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      restart_delay: 5000,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '30s',
      error_file: './logs/tg-collector-error.log',
      out_file: './logs/tg-collector-out.log',
      time: true
    },

    // Message Processor
    {
      name: 'msg-processor',
      script: 'python',
      args: './python/process_telegram_messages.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        INBOX_PATH: './inbox',
        QUEUE_PATH: './message_queue'
      },
      restart_delay: 5000,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '30s',
      error_file: './logs/msg-processor-error.log',
      out_file: './logs/msg-processor-out.log',
      time: true
    },

    // Discord Sender
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
      restart_delay: 5000,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '30s',
      error_file: './logs/discord-sender-error.log',
      out_file: './logs/discord-sender-out.log',
      time: true
    }
  ]
};