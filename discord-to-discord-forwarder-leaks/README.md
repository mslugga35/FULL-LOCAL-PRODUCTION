# 🤖 Discord Forwarder Bot - Production

## ✅ ACTIVE BOT
- **Script:** `forwarder.py` (Python)
- **Config:** `config.json` (49 channels)
- **Server:** Hetzner 95.217.152.205
- **PM2 Name:** `discord-forwarder-bot`

## 📚 DOCUMENTATION

### For Adding Channels:
→ See **[QUICK_CHANNEL_UPDATE.md](QUICK_CHANNEL_UPDATE.md)** (2-minute guide)

### For Complete Info:
→ See **[MASTER_BOT_INFO.md](MASTER_BOT_INFO.md)** (everything about the bot)

### For Current Status:
→ See **[MEMORY_NOTES.md](MEMORY_NOTES.md)** (history and notes)

## ⚡ QUICK COMMANDS

### Deploy Changes:
```bash
C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat
```

### Check Status:
```bash
ssh root@95.217.152.205 "pm2 status discord-forwarder-bot"
```

### View Logs:
```bash
ssh root@95.217.152.205 "pm2 logs discord-forwarder-bot --lines 20"
```

## 📁 ESSENTIAL FILES

| File | Purpose | Edit? |
|------|---------|-------|
| `forwarder.py` | Main bot script (Python) | ❌ |
| `config.json` | Channel mappings & token - EDIT THIS | ✅ |
| `last_messages.json` | Duplicate prevention | ❌ |
| `forwarder.log` | Local activity log | View only |
| `start_forwarder.bat` | Local startup script | ❌ |
| `requirements.txt` | Python dependencies | ❌ |

---

## ⚙️ CONFIGURATION (config.json)

### What Each Setting Does:

```json
{
  "user_token": "YOUR_TOKEN",              // Your Discord user token
  "fetch_history_on_start": false,         // Set to true to load today's messages on startup
  "channel_mappings": {
    "SOURCE_CHANNEL_ID": "WEBHOOK_URL"     // Each line = one channel pair
  }
}
```

### Current Setup:
- **Total Channels:** 49 active mappings
- **Last Updated:** September 12, 2025
- See `config.json` for all channel mappings

---

## 🔧 TROUBLESHOOTING

### Bot Not Starting:
1. Check `forwarder.log` for errors
2. Make sure Python is installed: `python --version`
3. Make sure packages installed: `pip install aiohttp`

### Messages Not Forwarding:
1. Check `forwarder.log` - it shows every message
2. Look for "Forwarded:" entries
3. Look for "Error:" entries
4. Common issues:
   - Invalid user token (401 error)
   - No access to channel (403 error)
   - Rate limited (429 error - wait)
   - Webhook deleted (404 error)

### To Test A Specific Channel:
Run: `python test_channel.py CHANNEL_ID`

### To View Logs:
- Live logs: Look at the command window
- Full logs: Open `forwarder.log` in Notepad

---

## 🔄 AUTO-START WITH WINDOWS

### Option 1: Task Scheduler (Recommended)
1. Double-click `setup_autostart.bat`
2. Bot will start automatically when Windows starts
3. To disable: Run `disable_autostart.bat`

### Option 2: Startup Folder
1. Copy `start_forwarder.bat` to:
   `C:\Users\mpmmo\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

---

## 📊 MONITORING

### Check If Bot Is Running:
- Look for Python in Task Manager
- Check `forwarder.log` - last entry shows if active
- New messages appear with timestamps

### Daily Stats:
The log shows:
- Messages forwarded count
- Error count
- Runtime duration

---

## 🛑 BOT IS ALREADY RUNNING 24/7

**Current Setup:** Bot runs on Hetzner server (95.217.152.205)
- Managed by PM2 process manager
- Auto-restarts if crashes
- Running 24/7 independently of your PC

---

## 📝 MAINTENANCE

### To Update Token:
1. Edit `config.json`
2. Change `user_token` value
3. Restart bot

### To Add/Remove Channels:
1. Edit `config.json`
2. Add/remove lines in `channel_mappings`
3. Restart bot

### To Clear Logs:
Delete `forwarder.log` (new one created automatically)

---

## ⚠️ IMPORTANT NOTES

1. **User Token:** Never share your user token!
2. **Rate Limits:** Bot respects Discord's limits automatically
3. **ToS:** Using user tokens violates Discord ToS - use at own risk
4. **Backup:** Keep a copy of `config.json` somewhere safe

---

## 🆘 EMERGENCY COMMANDS

### Force Stop Bot:
```
taskkill /F /IM python.exe
```

### Test Configuration:
```
python -c "import json; json.load(open('config.json'))"
```

### Check Python Packages:
```
pip list | findstr aiohttp
```

---

## 📞 SUPPORT

If bot stops working:
1. Check Discord still works normally
2. Check `forwarder.log` for errors
3. Try regenerating webhooks if needed
4. Update user token if expired