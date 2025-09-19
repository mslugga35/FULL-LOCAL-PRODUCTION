module.exports = {
  apps: [{
    name: 'discord-sender-safe',
    script: 'discord_sender_safe.js',
    cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION',
    interpreter: 'node',
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    restart_delay: 5000,
    env: {
      NODE_ENV: 'production',
      DISCORD_WEBHOOK_URL: 'https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN',
      BOT_USERNAME: 'Safe Sports Bot',
      PROCESS_NAME: 'discord-sender-safe'
    },
    error_file: './logs/discord-sender-safe-error.log',
    out_file: './logs/discord-sender-safe-out.log',
    log_file: './logs/discord-sender-safe-combined.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};