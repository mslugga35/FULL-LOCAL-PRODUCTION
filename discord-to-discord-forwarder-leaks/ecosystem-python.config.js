module.exports = {
  apps: [
    {
      name: 'discord-forwarder-python',
      script: 'python',
      args: 'forwarder.py',
      cwd: 'C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\discord-forwarder',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};