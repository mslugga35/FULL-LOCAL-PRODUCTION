// FULL LOCAL PRODUCTION ECOSYSTEM - WINDOWS OPTIMIZED
// Fixed paths and components for complete message pipeline
module.exports = {
  apps: [
    // 1. Telegram Message Collector
    {
      name: 'telegram-collector',
      script: 'python',
      args: './telegram_production_collector.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8'
      },
      restart_delay: 10000,
      autorestart: true,
      max_restarts: 5,
      min_uptime: '60s',
      error_file: './logs/telegram-collector-error.log',
      out_file: './logs/telegram-collector-out.log',
      time: true
    },

    // 2. Message Processor (recent_messages -> message_queue)
    {
      name: 'message-processor',
      script: 'python',
      args: './message_processor_windows.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8'
      },
      restart_delay: 5000,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '30s',
      error_file: './logs/message-processor-error.log',
      out_file: './logs/message-processor-out.log',
      time: true
    },

    // 3. Discord Sender (message_queue -> Discord webhooks)
    {
      name: 'discord-sender',
      script: './discord_sender.js',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      env: {
        DISCORD_WEBHOOK_URL: 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
        BOT_USERNAME: 'Sports Bot',
        TEXT_BATCH_SIZE: '5',
        FILE_BATCH_SIZE: '3',
        FLOOR_DELAY_MS: '500',
        PROCESS_NAME: 'discord-sender-main',
        QUEUE_DIRS: './message_queue/uatb,./message_queue/paid_uatb,./message_queue/diamond,./message_queue/paid_diamond,./message_queue/paid_chamba'
      },
      restart_delay: 5000,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '30s',
      error_file: './logs/discord-sender-error.log',
      out_file: './logs/discord-sender-out.log',
      time: true
    },

    // 4. Discord Forwarder (Discord-to-Discord)
    {
      name: 'discord-forwarder',
      script: 'python',
      args: './discord-forwarder/forwarder.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8'
      },
      restart_delay: 10000,
      autorestart: true,
      max_restarts: 5,
      min_uptime: '60s',
      error_file: './logs/discord-forwarder-error.log',
      out_file: './logs/discord-forwarder-out.log',
      time: true
    }
  ]
};