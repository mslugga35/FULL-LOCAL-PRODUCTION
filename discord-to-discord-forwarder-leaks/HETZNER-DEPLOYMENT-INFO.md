# 🚨 IMPORTANT: HETZNER DEPLOYMENT INFO

## ✅ THIS BOT IS DEPLOYED ON HETZNER AS:

### **PM2 Process Name:** `telegram-forwarder`
### **Server:** 95.217.152.205
### **Location:** `/root/bots/forwarder.py`

---

## ⚠️ NAMING CLARIFICATION

**Despite the confusing name `telegram-forwarder`, this is actually the DISCORD-TO-DISCORD bot!**

- **What it does:** Forwards messages from Discord channels to Discord webhooks
- **Channels monitored:** 49 Discord channels
- **NOT Telegram related** - the name is misleading!

---

## 📊 CURRENT STATUS ON HETZNER

```bash
Name: telegram-forwarder
Status: ONLINE ✅
Uptime: 9+ hours
Restarts: 0
Memory: ~33 MB
Script: /root/bots/forwarder.py
Config: /root/bots/config.json
```

---

## 🔧 MANAGEMENT COMMANDS

### Check Status:
```bash
ssh root@95.217.152.205 "pm2 status telegram-forwarder"
```

### View Logs:
```bash
ssh root@95.217.152.205 "pm2 logs telegram-forwarder --lines 50"
```

### Restart:
```bash
ssh root@95.217.152.205 "pm2 restart telegram-forwarder"
```

### Stop:
```bash
ssh root@95.217.152.205 "pm2 stop telegram-forwarder"
```

### Start:
```bash
ssh root@95.217.152.205 "pm2 start telegram-forwarder"
```

---

## 📁 FILES ON HETZNER

- **Script:** `/root/bots/forwarder.py` (Discord-to-Discord forwarder)
- **Config:** `/root/bots/config.json` (49 channel mappings)
- **Logs:** `/root/.pm2/logs/telegram-forwarder-*.log`
- **Last Messages:** `/root/bots/last_messages.json`

---

## ⚡ RECENT ACTIVITY

Last confirmed working: September 14, 2025 at 8:25 AM
- Forwarding from VIP PICKS channel
- Forwarding from LEAKS channel
- All 49 channel mappings active

---

## 🎯 REMEMBER

**This is the DISCORD-TO-DISCORD bot, NOT a Telegram bot!**
**PM2 name on Hetzner: `telegram-forwarder`**