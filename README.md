# Full Local Production Setup

## Overview
All services previously running on Hetzner are now running locally.

## Services

### 1. Telegram → Discord Pipeline
- **Telegram Collector** (`python/telegram_to_discord.py`)
  - Monitors 5 Telegram channels:
    - Cappers Free (-1002592669126)
    - Cappers Leaked (-1001560546587)
    - Exclusive Cappers (-1002608783933)
    - UATB (-1002177758646)
    - Diamond/Chamba (-1002470080886)
  - Saves messages to `inbox/` folder
  - Uses session: `telegram_session.session`

### 2. Message Processor
- Processes messages from inbox
- Handles OCR if needed
- Sends to message queues

### 3. Discord Sender (`discord_sender.js`)
- Sends messages from queues to Discord webhook
- Includes Cloudflare protection (rate limiting)
- Webhook: Configured in PM2 ecosystem

### 4. Discord-to-Discord Forwarder (`discord-forwarder/forwarder.py`)
- Monitors 49 Discord channels
- Acts as your user account (self-bot)
- Forwards messages to configured webhooks
- Config: `discord-forwarder/config.json`

### 5. Watchdog (`scripts/watchdog.js`)
- Monitors all services
- Auto-restarts failed services
- Check interval: 60 seconds

## Directory Structure
```
FULL-LOCAL-PRODUCTION/
├── discord_sender.js          # Discord webhook sender
├── inbox/                      # Telegram messages land here
├── message_queue/              # Processed messages by channel
│   ├── uatb/
│   ├── paid_uatb/
│   ├── diamond/
│   ├── paid_diamond/
│   ├── paid_chamba/
│   └── free_cappers/
├── python/
│   └── telegram_to_discord.py # Telegram collector
├── discord-forwarder/
│   ├── forwarder.py           # Discord-to-Discord forwarder
│   └── config.json            # Channel mappings & token
├── scripts/
│   └── watchdog.js            # Service monitor
└── logs/                       # All service logs
```

## Configuration Files

### Telegram Session
- File: `telegram_session.session`
- Phone: +3212629156
- Username: @mslugga

### Discord User Token
- Location: `discord-forwarder/config.json`
- Field: `user_token`
- To update: Get new token from Discord browser console

## Starting Services

### Quick Start All
```batch
START_ALL_SERVICES.bat
```

### Individual Services
```batch
# Discord Sender
pm2 start discord_sender.js --name discord-sender

# Watchdog
pm2 start scripts/watchdog.js --name watchdog

# Telegram Collector
python python/telegram_to_discord.py

# Discord Forwarder
cd discord-forwarder && python forwarder.py
```

## Monitoring

### Check Status
```batch
pm2 list
```

### View Logs
```batch
pm2 logs
pm2 logs discord-sender
pm2 logs watchdog
```

### Check Python Processes
```batch
tasklist | findstr python
```

## Troubleshooting

### Discord Token Invalid
1. Open Discord in browser
2. Press F12 → Console
3. Run: `(webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()`
4. Update token in `discord-forwarder/config.json`

### Telegram Session Expired
1. Run: `python setup_telegram_auth.py`
2. Enter phone verification code

### Service Not Starting
1. Check logs: `pm2 logs [service-name]`
2. Check if port is in use
3. Verify dependencies installed

## Dependencies

### Node.js
- discord.js
- express
- bottleneck
- fs-extra

### Python
- telethon
- aiohttp
- discord.py-self

## Notes
- All services run locally on Windows
- Hetzner server has been shut down
- Cloudflare protection built into Discord sender
- Python processes show as "online" in PM2 but with N/A PID (Windows limitation)