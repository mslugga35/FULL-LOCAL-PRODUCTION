module.exports = {
  apps: [
    {
      name: 'tg-collector',
      script: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\.venv\\Scripts\\python.exe',
      args: 'src/telegram_collector.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
      interpreter: null,
      env: {
        PYTHONPATH: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
        PYTHONUNBUFFERED: '1'
      },
      // Auto-restart configuration
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '1G',
      kill_timeout: 5000,
      restart_delay: 4000,
      exp_backoff_restart_delay: 100,
      // Logging
      error_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\tg-collector-error.log',
      out_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\tg-collector-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      // Monitoring
      instance_var: 'INSTANCE_ID',
      instances: 1,
      exec_mode: 'fork'
    },
    {
      name: 'router',
      script: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\.venv\\Scripts\\python.exe',
      args: 'src/router.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
      interpreter: null,
      env: {
        PYTHONPATH: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
        PYTHONUNBUFFERED: '1'
      },
      // Auto-restart configuration
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '1G',
      kill_timeout: 5000,
      restart_delay: 4000,
      exp_backoff_restart_delay: 100,
      // Logging
      error_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\router-error.log',
      out_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\router-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      // Monitoring
      instance_var: 'INSTANCE_ID',
      instances: 1,
      exec_mode: 'fork'
    },
    {
      name: 'forwarder',
      script: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\.venv\\Scripts\\python.exe',
      args: 'src/forwarder.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
      interpreter: null,
      env: {
        PYTHONPATH: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
        PYTHONUNBUFFERED: '1'
      },
      // Auto-restart configuration
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '1G',
      kill_timeout: 5000,
      restart_delay: 4000,
      exp_backoff_restart_delay: 100,
      // Logging
      error_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\forwarder-error.log',
      out_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\forwarder-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      // Monitoring
      instance_var: 'INSTANCE_ID',
      instances: 1,
      exec_mode: 'fork'
    },
    {
      name: 'vision-service',
      script: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\.venv\\Scripts\\python.exe',
      args: 'src/vision_service.py --queue free_cappers',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
      interpreter: null,
      env: {
        PYTHONPATH: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
        PYTHONUNBUFFERED: '1',
        OPENAI_API_KEY: process.env.OPENAI_API_KEY
      },
      // Auto-restart configuration
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '1G',
      kill_timeout: 10000,  // Longer timeout to finish API calls
      restart_delay: 5000,
      exp_backoff_restart_delay: 100,
      // Logging
      error_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\vision-service-error.log',
      out_file: 'C:\\Users\\mpmmo\\.pm2\\logs\\vision-service-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: false,
      // Monitoring
      instance_var: 'INSTANCE_ID',
      instances: 1,
      exec_mode: 'fork'
    }
  ],

  // Deploy configuration (optional)
  deploy: {
    production: {
      user: 'mpmmo',
      host: 'localhost',
      ref: 'origin/master',
      repo: '',
      path: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord',
      'post-deploy': 'pm2 reload ecosystem.config.js --env production'
    }
  }
};