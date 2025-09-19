# 🤖 DISCORD FORWARDER BOT - MASTER DOCUMENTATION

## ⚡ QUICK INFO - WHAT'S RUNNING NOW

### 🏃 CURRENT LIVE BOT
- **Bot Type:** Python Script (`forwarder.py`)
- **Location on Server:** `/root/bots/discord-forwarder-bot/forwarder.py`
- **Config File:** `config.json` (same directory)
- **PM2 Process Name:** `discord-forwarder-bot`
- **Server:** Hetzner - 95.217.152.205
- **Channels Monitored:** 49 channels
- **Last Updated:** September 12, 2025

---

## 📁 WHERE EVERYTHING IS

### 💻 LOCAL (Your PC)
```
C:\Users\mpmmo\discord-forwarder-production\
├── forwarder.py          ← THE MAIN BOT (Python)
├── config.json           ← CHANNEL MAPPINGS (Edit this to add channels)
├── last_messages.json    ← Tracking file (prevents duplicates)
└── MASTER_BOT_INFO.md    ← THIS FILE
```

### ☁️ SERVER (Hetzner)
```
/root/bots/discord-forwarder-bot/
├── forwarder.py          ← RUNNING BOT (Python version)
├── config.json           ← LIVE CONFIG (must match local)
├── last_messages.json    ← Message tracking
└── [many old JS files]   ← IGNORE THESE - Not used anymore
```

---

## 🎯 HOW TO ADD NEW CHANNELS

### Step 1: Edit Local Config
```bash
# Open config.json in C:\Users\mpmmo\discord-forwarder-production\
# Add new channel before the last closing brace:
"CHANNEL_ID_HERE": "WEBHOOK_URL_HERE",
```

### Step 2: Deploy to Server
```bash
# Run this from BOT-OPERATIONS-CENTER:
cd C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts
DEPLOY_FORWARDER_UPDATE.bat
```

### Step 3: Verify It's Working
```bash
# Check the logs:
ssh root@95.217.152.205 "pm2 logs discord-forwarder-bot --lines 20"
```

---

## 🔧 COMMON COMMANDS

### Check Bot Status
```bash
ssh root@95.217.152.205 "pm2 status discord-forwarder-bot"
```

### View Live Logs
```bash
ssh root@95.217.152.205 "pm2 logs discord-forwarder-bot --lines 50"
```

### Restart Bot
```bash
ssh root@95.217.152.205 "pm2 restart discord-forwarder-bot"
```

### Stop Bot
```bash
ssh root@95.217.152.205 "pm2 stop discord-forwarder-bot"
```

### Start Bot
```bash
ssh root@95.217.152.205 "pm2 start discord-forwarder-bot"
```

---

## 📊 CURRENT CONFIGURATION

### Bot Details
- **Language:** Python 3.12
- **Main Library:** aiohttp
- **Check Interval:** 5 seconds
- **User Token:** Stored in config.json
- **Webhook URLs:** 49 mapped channels

### What It Does
1. Reads messages from Discord channels (using user token)
2. Forwards to webhooks in destination server
3. Tracks sent messages to prevent duplicates
4. Replaces @everyone mentions with `@everyone` (no ping)

---

## ⚠️ IMPORTANT NOTES

### NAMING CONFUSION - READ THIS!
There are MANY files in the server directory with similar names:
- `production-bot.js` - OLD JavaScript bot (NOT USED)
- `forwarder.py` - ✅ **THIS IS THE ACTIVE BOT**
- `index.js`, `discord-forwarder-fixed.js`, etc. - ALL OLD (NOT USED)

**ONLY `forwarder.py` MATTERS!**

### Files That Matter
1. **forwarder.py** - The actual bot script
2. **config.json** - Channel mappings
3. **last_messages.json** - Duplicate prevention

### Server Has Many Bots
The server runs multiple bots. When using PM2 commands, always specify:
- `discord-forwarder-bot` - This is YOUR forwarder bot
- Other bots like `discord-sender`, `fetch-today-bot` are different projects

---

## 🚀 DEPLOYMENT SCRIPT LOCATION

The deployment script is here:
```
C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat
```

This script:
1. Uploads config.json
2. Uploads forwarder.py
3. Restarts the bot
4. Shows you the status

---

## 📝 LAST 14 CHANNELS ADDED (Sept 12, 2025)

From server 1264133755115933717:
1. kims-picks (1388290916237840415)
2. chillibets (1406555021037932686)
3. parlaytravy (1414494319871655936)
4. bet2survive (1414494356437471294)
5. prizepickvalue (1339353002368172146)
6. razz (1336611883272245280)
7. brickspicks (1380057752134484008)
8. propzzeekgreek (1341231378469097542)
9. wyzebets (1336611913500721164)
10. prizepicksplug (1413721616910778418)
11. cush (1412279849216639027)
12. jags (1413766698003333150)
13. ptd-prestige (1389114842253754510)
14. capper-potds (1323502454461042838)

---

## 🆘 TROUBLESHOOTING

### Bot Not Forwarding?
1. Check if it's running: `pm2 status`
2. Check logs for errors: `pm2 logs discord-forwarder-bot --err`
3. Verify token is valid in config.json
4. Make sure webhooks are still active

### Need to Update Token?
1. Edit `config.json` locally
2. Run deployment script
3. Bot will restart automatically

### Bot Keeps Restarting?
- Check error logs
- Likely token expired or rate limited
- May need new user token

---

## 📞 QUICK REFERENCE

**Local Folder:** `C:\Users\mpmmo\discord-forwarder-production\`
**Server Location:** `/root/bots/discord-forwarder-bot/`
**Bot Script:** `forwarder.py` (Python)
**Config:** `config.json`
**PM2 Name:** `discord-forwarder-bot`
**Deploy Script:** `C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat`

---

**Remember:** When in doubt, `forwarder.py` is the ONLY bot file that matters!