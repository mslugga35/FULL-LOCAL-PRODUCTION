# 🔧 TROUBLESHOOTING GUIDE

## QUICK DIAGNOSIS FLOWCHART

```
Bot not working?
    ↓
Is python.exe in Task Manager?
    ├─ NO → Bot not running → Run start_forwarder.bat
    └─ YES → Bot running but not forwarding
              ↓
         Check forwarder.log
              ↓
         Look for ERROR lines
```

---

## 🔴 COMMON PROBLEMS & FIXES

### 1. "Bot isn't forwarding messages"

**Check #1: Is it running?**
- Open Task Manager
- Look for `python.exe`
- If missing → Double-click `start_forwarder.bat`

**Check #2: Look at the log**
- Open `forwarder.log`
- Find the last timestamp
- If old → Bot crashed
- If recent → Check for ERROR messages

**Check #3: Test a webhook**
```python
# Save as test.py and run
import requests
webhook = "YOUR_WEBHOOK_URL_HERE"
requests.post(webhook, json={"content": "Test"})
```

**Check #4: Multi-server issues**
- Bot now monitors 14 channels across 2 servers
- Check you have access to BOTH servers
- Some channels may work (Server 1) while others don't (Server 2)

---

### 2. "ERROR: 401 Unauthorized"

**Problem:** Your user token expired or is wrong

**Fix:**
1. Get new token from Discord (F12 → Network → Authorization header)
2. Edit `config.json`
3. Replace old token with new one
4. Restart bot

---

### 3. "ERROR: 403 Forbidden"

**Problem:** No access to channel

**Possible causes:**
- You're not in one of the servers (now monitoring 2 servers)
- Channel was deleted
- You were removed from channel
- Private channel you don't have access to

**Fix:**
1. Check you're still in BOTH servers:
   - Server 1: 1402442728091943134
   - Server 2: 1264133755115933717
2. Check channel still exists
3. Remove channel from config.json if deleted
4. Verify you have read permissions in all 14 channels

---

### 4. "ERROR: 404 Not Found"

**Problem:** Webhook was deleted

**Fix:**
1. Go to Server 2 channel
2. Create new webhook
3. Copy new webhook URL
4. Update in `config.json`
5. Restart bot

---

### 5. "ERROR: 429 Too Many Requests"

**Problem:** Rate limited by Discord

**Fix:**
- This is normal, bot handles it automatically
- Just wait, it will resume
- If constant, reduce check interval

---

### 6. "Bot crashes on startup"

**Check Python:**
```
python --version
```
Should show Python 3.8 or higher

**Check packages:**
```
pip install aiohttp
```

**Check config.json:**
```
python -c "import json; json.load(open('config.json'))"
```
If error → Fix JSON syntax

---

## 📝 LOG FILE MESSAGES EXPLAINED

| Log Message | Meaning | Action Needed |
|------------|---------|---------------|
| `INFO - Discord Forwarder Started` | Bot started successfully | None |
| `INFO - Monitoring 14 channels` | Loaded configuration | None |
| `INFO - Forwarded: Username` | Message sent successfully | None |
| `ERROR - 401` | Invalid token | Update token |
| `ERROR - 403` | No channel access | Check permissions |
| `ERROR - 404` | Webhook deleted | Create new webhook |
| `ERROR - 429` | Rate limited | Wait (automatic) |
| `ERROR - Fatal error` | Bot crashed | Check error, restart |

---

## 🛠️ FIXES BY SYMPTOM

### "Messages forward but delayed"
- Normal - checks every 5 seconds
- Live enough for most uses
- Can't be faster (Discord limits)

### "Only some channels work"
1. Check each webhook is valid
2. Test each webhook individually  
3. Check you have access to all source channels
4. **Multi-server check:** Some channels are in different servers
   - First 9 channels: Server 1402442728091943134
   - Last 5 channels: Server 1264133755115933717
   - Make sure you're in BOTH servers

### "Bot runs but log is empty"
- Delete `forwarder.log`
- Restart bot
- New log will be created

### "Windows starts but bot doesn't"
1. Run as Administrator: `setup_autostart.bat`
2. Check Task Scheduler
3. Look for "DiscordForwarder" task
4. Should be set to "Run at log on"

---

## 🔄 COMPLETE RESET PROCEDURE

If nothing else works:

1. **Stop everything:**
   ```
   taskkill /F /IM python.exe
   ```

2. **Clean up:**
   - Delete `forwarder.log`
   - Run `disable_autostart.bat`

3. **Fresh start:**
   - Run `start_forwarder.bat` manually
   - Watch for errors
   - If works, run `setup_autostart.bat`

---

## 📊 PERFORMANCE CHECK

Run this to see if bot is healthy:

1. Check log file size:
   - Under 10MB = Good
   - Over 100MB = Delete and restart

2. Check message rate:
   - Open `forwarder.log`
   - Count "Forwarded" in last hour
   - Should match Discord activity

3. Check errors:
   - Search log for "ERROR"
   - Occasional = OK
   - Constant = Problem

---

## 💡 PREVENTION TIPS

1. **Weekly:** Check log for errors
2. **Monthly:** Delete old log file
3. **Keep backup:** Save config.json copy
4. **Document changes:** Note any webhook updates

---

## 🚨 EMERGENCY CONTACTS

If completely broken:

1. **Regenerate all webhooks** in Server 2
2. **Get fresh user token** from Discord
3. **Start fresh** with new config
4. **Test one channel** first, then add others

## 📋 CURRENT CONFIGURATION

**Bot monitors 35 channels across 3 servers:**

**Server 1 (ID: 1402442728091943134) - 9 channels**
**Server 2 (ID: 1264133755115933717) - 21 channels**
**Server 3 (ID: 1386004250781552700) - 5 channels**

All forward to webhooks in destination server (ID: 675908407617650697)

**Total Active Channels: 35**

---

## TEST COMMANDS

### Test if Python works:
```
python --version
```

### Test if config is valid:
```
python -c "import json; print('OK') if json.load(open('config.json')) else 'ERROR')"
```

### Test if bot can start:
```
python forwarder.py
```
(Should see "Discord Forwarder Started")

### Force stop all Python:
```
taskkill /F /IM python.exe
```