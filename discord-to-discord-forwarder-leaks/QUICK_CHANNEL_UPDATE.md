# ⚡ QUICK GUIDE - ADD NEW CHANNELS IN 2 MINUTES

## 🎯 YOU ONLY NEED 2 THINGS:
1. **Channel ID** from Discord
2. **Webhook URL** where to forward messages

---

## 📝 STEP 1: Add Channels to Config

Open this file:
```
C:\Users\mpmmo\discord-forwarder-production\config.json
```

Find the last channel (currently line 39) and add your new channels:
```json
    "1323502454461042838": "https://discord.com/api/webhooks/...",
    "NEW_CHANNEL_ID": "NEW_WEBHOOK_URL",
    "ANOTHER_CHANNEL_ID": "ANOTHER_WEBHOOK_URL"
```

⚠️ **IMPORTANT:** 
- Add comma after the previous line
- NO comma after the last channel
- Keep the quotes around IDs and URLs

---

## 🚀 STEP 2: Deploy to Server

Double-click this file:
```
C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat
```

Or run in terminal:
```bash
cd C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts
DEPLOY_FORWARDER_UPDATE.bat
```

---

## ✅ STEP 3: Verify It's Working

The deployment script will show you the status. To double-check:

```bash
ssh root@95.217.152.205 "pm2 logs discord-forwarder-bot --lines 10"
```

You should see your new channels being monitored!

---

## 🔍 HOW TO GET CHANNEL IDs

### In Discord:
1. Enable Developer Mode (Settings → Advanced → Developer Mode)
2. Right-click any channel
3. Click "Copy Channel ID"

### From a Message Link:
If you have a Discord message link like:
```
https://discord.com/channels/1264133755115933717/1388290916237840415/123456789
```
The channel ID is: `1388290916237840415`

---

## 🔗 HOW TO CREATE WEBHOOKS

1. Go to your destination Discord server
2. Right-click the channel where you want messages
3. Edit Channel → Integrations → Webhooks
4. Click "New Webhook"
5. Name it (e.g., "kims-picks-forward")
6. Copy the Webhook URL

---

## 📊 EXAMPLE: Adding 3 New Channels

Before:
```json
    "1323502454461042838": "https://discord.com/api/webhooks/lastchannel"
  }
}
```

After:
```json
    "1323502454461042838": "https://discord.com/api/webhooks/lastchannel",
    "1234567890123456789": "https://discord.com/api/webhooks/newchannel1/token",
    "9876543210987654321": "https://discord.com/api/webhooks/newchannel2/token",
    "1122334455667788990": "https://discord.com/api/webhooks/newchannel3/token"
  }
}
```

---

## 🆘 COMMON ISSUES

### "Invalid JSON" Error?
- Check your commas - need comma after each line except the last
- Make sure all quotes are straight quotes `"` not smart quotes `"`
- Use a JSON validator: https://jsonlint.com

### Bot Not Picking Up New Channels?
- Did you run the deployment script?
- Check logs: `pm2 logs discord-forwarder-bot`
- Make sure webhook URL is complete (includes token)

### Webhook Not Working?
- Test the webhook in Discord first
- Make sure the webhook channel still exists
- Webhooks expire if deleted from Discord

---

## 📱 QUICK COMMANDS REFERENCE

```bash
# Deploy changes
C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat

# Check status
ssh root@95.217.152.205 "pm2 status"

# View logs
ssh root@95.217.152.205 "pm2 logs discord-forwarder-bot"

# Restart bot
ssh root@95.217.152.205 "pm2 restart discord-forwarder-bot"
```

---

## 📁 FILES YOU'RE EDITING

**Local Config:** `C:\Users\mpmmo\discord-forwarder-production\config.json`
**Deployment Script:** `C:\Users\mpmmo\BOT-OPERATIONS-CENTER\deployment-scripts\DEPLOY_FORWARDER_UPDATE.bat`

That's it! Just edit config.json and run the deployment script! 🎉