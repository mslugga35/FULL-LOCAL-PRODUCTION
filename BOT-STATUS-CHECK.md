# Bot Status Quick Check Reference
**Location:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\BOT-STATUS-CHECK.md`
**Last Updated:** December 30, 2025

---

## Quick Commands to Run

### 1. Check PM2 Status
```bash
pm2 list
```

### 2. Start All Bots (if not running)
```bash
# Telegram-Discord Pipeline
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord && pm2 start ecosystem.config.js

# Discord-to-Discord Forwarder
cd /c/Users/mpmmo/discord-to-discord-forwarder-leaks && pm2 start ecosystem-python.config.js

# Save config
pm2 save --force
```

### 3. Check Logs
```bash
pm2 logs --lines 10 --nostream
```

---

## Expected Running Services (4 Total)

| ID | Service Name | Purpose | Config Location |
|----|-------------|---------|-----------------|
| 0 | `tg-collector` | Collects from 9 Telegram channels | `FULL-LOCAL-PRODUCTION/Telegram_Discord/ecosystem.config.js` |
| 1 | `router` | Routes messages to Discord queues | `FULL-LOCAL-PRODUCTION/Telegram_Discord/ecosystem.config.js` |
| 2 | `forwarder` | Sends to Discord webhooks | `FULL-LOCAL-PRODUCTION/Telegram_Discord/ecosystem.config.js` |
| 3 | `discord-forwarder-python` | Discord-to-Discord (91 channels) | `discord-to-discord-forwarder-leaks/ecosystem-python.config.js` |

---

## Key Paths

| Item | Path |
|------|------|
| Main Production | `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION` |
| Telegram Pipeline | `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord` |
| Discord Forwarder | `C:\Users\mpmmo\discord-to-discord-forwarder-leaks` |
| PM2 Logs | `C:\Users\mpmmo\.pm2\logs\` |
| PM2 Dump | `C:\Users\mpmmo\.pm2\dump.pm2` |

---

## Troubleshooting

### PM2 Shows Empty After Check
PM2 daemon may have restarted. Run the start commands above.

### "wmic ENOENT" Errors in Logs
This is cosmetic only (Windows limitation). Bots work fine.

### Bot Crashed/Restarting
```bash
pm2 logs [service-name] --lines 50
pm2 restart [service-name]
```

### Full Restart
```bash
pm2 kill
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord && pm2 start ecosystem.config.js
cd /c/Users/mpmmo/discord-to-discord-forwarder-leaks && pm2 start ecosystem-python.config.js
pm2 save --force
```

---

## System Flow

```
TELEGRAM (9 channels)
    ↓
tg-collector → inbox/
    ↓
router → message_queue/
    ↓
forwarder → DISCORD WEBHOOKS
    ↓
(triggers) → Google Docs Export (for free_cappers only)


DISCORD (91 source channels)
    ↓
discord-forwarder-python → DISCORD (destination channels)
```

---

## Google Docs Export (Free Picks)

### What It Does
Exports picks from **free_cappers** Telegram channel to a Google Doc for the n8n workflow to read.

### Key Files & Locations

| Item | Path |
|------|------|
| **Export Script** | `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\src\export_to_gdocs.py` |
| **Config (.env)** | `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.env` |
| **Google Credentials** | `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json` |
| **Source Data** | `Telegram_Discord\message_queue\free_cappers\` and `Telegram_Discord\sent_archive\YYYYMMDD\free_cappers\` |

### Google Doc Being Updated
- **Document ID:** `<GOOGLE_DOC_ID - see .env>`
- **URL:** `<GOOGLE_DOC_URL - see .env>`

### Environment Variables (in .env)
```
GOOGLE_DOC_ID=<GOOGLE_DOC_ID - see .env>
GOOGLE_CREDENTIALS_PATH=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json
GOOGLE_AI_API_KEY=<GOOGLE_AI_API_KEY - see .env>
TIMEZONE=America/New_York
```

### How It Runs
1. **Automatic:** The `forwarder.py` triggers `export_to_gdocs.py` after sending free_cappers messages
2. **Manual:** Run the command below

### Manual Export Command
```bash
cd "C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord"
.venv/Scripts/python.exe src/export_to_gdocs.py
```

### What It Exports
- Only **free_cappers** channel picks (Telegram ID: -1002592669126)
- Uses **Gemini AI OCR** to extract text from images
- Formats picks with timestamps
- Updates Google Doc with today's picks

### n8n Workflow That Reads This Doc
- **Workflow:** "DailyAI Betting - Master Picks (Webhook)"
- **Workflow ID:** `MInpXFItYWBsrlFz`
- **Status:** Active on https://mslugga35.app.n8n.cloud

### Troubleshooting Google Docs Export

**Doc not updating?**
1. Check if free_cappers has data: `ls Telegram_Discord/sent_archive/YYYYMMDD/free_cappers/`
2. Run manual export and check for errors
3. Verify Google credentials file exists

**No picks showing?**
- Only `free_cappers` channel is exported to Google Docs
- Other channels (cappers_leaked, exclusive_cappers, etc.) go to Discord only

---

## Auto-Start After Reboot

PM2 does NOT auto-start on Windows. Options:

1. **Windows Startup Folder:**
   - Press `Win + R` → `shell:startup`
   - Add shortcut to `START_ALL_BOTS.bat`

2. **Manual after reboot:**
   ```bash
   C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\START_ALL_BOTS.bat
   ```

---

## Health Check Indicators

When running `pm2 logs --lines 5 --nostream`, look for:

- `tg-collector`: "Telegram collector started. Monitoring X chats"
- `router`: "Configured routes: X"
- `forwarder`: "Forwarder started with channel-based rate limiting"
- `discord-forwarder-python`: "Monitoring X channels"
