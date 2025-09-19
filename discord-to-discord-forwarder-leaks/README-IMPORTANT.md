# ⚠️ IMPORTANT: THIS BOT RUNS ON HETZNER

## 📍 DEPLOYMENT LOCATION

**This bot is deployed on HETZNER SERVER, not locally!**

- **Server:** 95.217.152.205
- **PM2 Process Name:** `telegram-forwarder` (confusing name, but it's Discord-to-Discord)
- **Script Location:** `/root/bots/forwarder.py`
- **Config Location:** `/root/bots/config.json`

---

## 🔧 HOW TO MANAGE THIS BOT

### Check Status:
```bash
ssh root@95.217.152.205 "pm2 status telegram-forwarder"
```

### View Logs:
```bash
ssh root@95.217.152.205 "pm2 logs telegram-forwarder --lines 50"
```

### Restart Bot:
```bash
ssh root@95.217.152.205 "pm2 restart telegram-forwarder"
```

### Stop Bot:
```bash
ssh root@95.217.152.205 "pm2 stop telegram-forwarder"
```

### Start Bot:
```bash
ssh root@95.217.152.205 "pm2 start telegram-forwarder"
```

---

## 📊 WHAT THIS BOT DOES

- Monitors 49 Discord channels
- Forwards messages to Discord webhooks
- Does NOT involve Telegram (despite the name)
- Runs 24/7 on Hetzner server

---

## ⚠️ DO NOT RUN LOCALLY

This folder contains backup/reference code only.
The production bot runs on Hetzner server.
Do NOT run `python forwarder.py` locally!

---

## 📝 LAST KNOWN STATUS

- **Status:** ONLINE ✅
- **Last Checked:** September 14, 2025
- **Uptime:** 9+ hours
- **Memory:** ~33 MB
- **Restarts:** 0 (stable)

---

## 🚨 TROUBLESHOOTING

If bot is not working:

1. Check if it's running: `ssh root@95.217.152.205 "pm2 list"`
2. Look for `telegram-forwarder` in the list
3. If status is "stopped", start it: `ssh root@95.217.152.205 "pm2 start telegram-forwarder"`
4. Check logs for errors: `ssh root@95.217.152.205 "pm2 logs telegram-forwarder --err"`

---

**Remember: This is Discord-to-Discord, NOT Telegram related!**