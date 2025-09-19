# 🧠 MEMORY NOTES - Discord Forwarder Bot

## PROJECT HISTORY

### Initial Problem:
- User needed to forward messages from servers where they couldn't add bots
- Had to use user token to read messages from Server 1
- Forward to Server 2 where they have webhook access

### Evolution:
1. Started with 9 channels from Server 1
2. Added 5 channels from Server 2 (first batch)
3. Added 16 more channels from Server 2 (second batch) 
4. Fixed duplicate channel IDs (lawdtp-tennis and balesjustin)
5. Added 5 channels from Server 3
6. Added 14 channels from Server 1264133755115933717 (September 12, 2025)
7. **Current Total: 53 channels**

### Key Problems Solved:
1. **@everyone mentions** - Now replaced with `@everyone` (no pings)
2. **Duplicate messages on restart** - Added last_messages.json persistence
3. **Auto-start** - Configured Windows Task Scheduler
4. **Log management** - Auto-archives on restart
5. **Multi-server support** - Handles 3 different source servers

---

## TECHNICAL DETAILS

### Architecture:
- **Language:** Python 3.12
- **Library:** aiohttp for async HTTP requests
- **Method:** User token for reading, webhooks for sending
- **Interval:** Checks every 5 seconds
- **Logging:** Comprehensive file logging

### File Structure:
```
LOCAL (C:\Users\mpmmo\discord-forwarder-production\):
├── forwarder.py              # Main bot code (Python)
├── config.json               # Channel mappings & token
├── last_messages.json        # Persistence file
├── forwarder.log            # Activity log
├── MASTER_BOT_INFO.md       # Complete bot documentation
├── QUICK_CHANNEL_UPDATE.md  # Quick guide for adding channels
└── start_forwarder.bat      # Local startup script

SERVER (95.217.152.205 - /root/bots/discord-forwarder-bot/):
├── forwarder.py             # ACTIVE BOT (Python)
├── config.json              # Live configuration
├── last_messages.json       # Message tracking
└── [many old JS files]      # IGNORE - Not used
```

### Deployment:
- **Server:** Hetzner (95.217.152.205)
- **Process Manager:** PM2
- **PM2 Name:** discord-forwarder-bot
- **Deploy Script:** C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat

### Security Considerations:
- Uses user token (Discord ToS violation risk)
- Token stored in plain text config
- No encryption on webhook URLs
- Logs may contain message content

---

## COMMON TASKS

### Add New Channels:
```json
// Add to config.json before last brace:
"CHANNEL_ID": "WEBHOOK_URL",
```

### Update User Token:
```json
// In config.json:
"user_token": "NEW_TOKEN_HERE",
```

### Reset Message History:
```bash
# Delete this file:
last_messages.json
```

### Check Bot Status:
```bash
# Look for python.exe in:
tasklist | findstr python
```

---

## IMPORTANT REMINDERS

1. **ALWAYS restart bot after config changes**
2. **Bot shows "Monitoring X channels" on start** - Verify correct count
3. **@everyone is intentionally shown as `@everyone`** - This is working correctly
4. **Duplicate prevention via last_messages.json** - Don't delete unless you want to reprocess
5. **User token can expire** - Usually lasts weeks/months but may need updating
6. **Webhooks are permanent** - Unless manually deleted in Discord

---

## CONTACT POINTS

- **Main Folder:** `C:\Users\mpmmo\discord-forwarder-production\`
- **Total Channels:** 53
- **Servers Monitored:** 4 (including 1264133755115933717)
- **Destination Server:** 675908407617650697
- **Auto-Start:** ENABLED
- **@everyone Protection:** ACTIVE

---

## NEXT TIME SETUP

When returning to this project:

1. **Check if running:** Look for python.exe in Task Manager
2. **View current status:** Check last lines of forwarder.log
3. **To add channels:** Edit config.json, add new mappings, restart
4. **If not working:** Check TROUBLESHOOTING.md
5. **For full details:** Read COMPLETE_SETUP_GUIDE.md

---

*Last configured: September 12, 2025 - 53 channels active*

### Latest Addition (September 12, 2025):
Added 14 channels from server 1264133755115933717:
- kims-picks (1388290916237840415)
- chillibets (1406555021037932686)
- parlaytravy (1414494319871655936)
- bet2survive (1414494356437471294)
- prizepickvalue (1339353002368172146)
- razz (1336611883272245280)
- brickspicks (1380057752134484008)
- propzzeekgreek (1341231378469097542)
- wyzebets (1336611913500721164)
- prizepicksplug (1413721616910778418)
- cush (1412279849216639027)
- jags (1413766698003333150)
- ptd-prestige (1389114842253754510)
- capper-potds (1323502454461042838)