// COMPLETE LOCAL ECOSYSTEM - ALL BOTS
// Everything runs locally - NO Hetzner
module.exports = {
  apps: [
    // 1. TELEGRAM COLLECTOR
    {
      name: 'telegram-collector',
      script: 'python',
      args: './python/telegram_to_discord.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        SESSION_FILE: './python/telegram_session.session',
        OUTPUT_DIR: './inbox'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/telegram-error.log',
      out_file: './logs/telegram-out.log'
    },

    // 2. MESSAGE PROCESSOR
    {
      name: 'message-processor',
      script: 'python',
      args: './python/process_telegram_messages.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        INBOX_DIR: './inbox',
        QUEUE_DIR: './message_queue'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/processor-error.log',
      out_file: './logs/processor-out.log'
    },

    // 3. DISCORD SENDER
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

    // 4. OCR PROCESSOR (Google Vision)
    {
      name: 'ocr-processor',
      script: 'python',
      args: './python/google_vision_ocr.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1',
        GOOGLE_APPLICATION_CREDENTIALS: './config/google-vision-key.json',
        OCR_INPUT_DIR: './message_queue',
        OCR_OUTPUT_DIR: './message_queue'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/ocr-error.log',
      out_file: './logs/ocr-out.log'
    },

    // 5. WATCHDOG
    {
      name: 'watchdog',
      script: './scripts/watchdog.js',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
      env: {
        CHECK_INTERVAL: '60000', // Check every minute
        RESTART_THRESHOLD: '3'
      },
      autorestart: true,
      max_restarts: 10,
      error_file: './logs/watchdog-error.log',
      out_file: './logs/watchdog-out.log'
    }
  ]
};