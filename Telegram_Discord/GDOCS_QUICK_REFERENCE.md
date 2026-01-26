# Google Docs Free Picks - Quick Reference Card

## 📱 Your Google Doc
**Link:** https://docs.google.com/document/d/1QAUgTvFZq3PlA25vznkly8CHb4uNsIRYEZ0oXCitKxo/edit

**Bookmark this on your phone!** ⭐

## ⏰ Update Schedule
- **Automatically updates:** Every hour at :00 (1:00, 2:00, 3:00, etc.)
- **Shows:** Only TODAY's picks (resets at midnight)
- **Channels included:** 4 free channels (42 picks today)

## 📊 Current Status
✅ **gdocs-exporter** - ONLINE (PM2 process #6)
✅ Runs hourly via cron: `0 * * * *`
✅ Last run: Successful (42 picks exported)

## 🔧 Quick Commands

### Check Status
```powershell
pm2 list
# Look for: gdocs-exporter (online)
```

### View Logs
```powershell
pm2 logs gdocs-exporter --lines 50
# Look for: "Export complete! X picks from Y channels"
```

### Manual Export (Don't Wait for Hourly)
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src\export_to_gdocs.py
```

### Restart Service
```powershell
pm2 restart gdocs-exporter
```

### Stop Service
```powershell
pm2 stop gdocs-exporter
```

### Start Service
```powershell
pm2 start gdocs-exporter
```

## 📱 Mobile Workflow

### Old Way (10 minutes):
1. Open Discord app
2. Navigate to 5 different channels
3. Copy each pick individually
4. Switch apps, paste, repeat
5. Miss picks buried in scrollback

### **NEW Way (30 seconds):** 🚀
1. Open Google Doc (bookmarked link)
2. Long press → **Select All**
3. **Copy**
4. Paste into consensus picks
5. **DONE!**

## 🎯 What Channels Are Included?

1. 🔥 **CAPPERS FREE💥** (8 picks today)
2. 💎 **Cappers Leaked** (0 picks today)
3. ✨ **Exclusive Cappers** (1 pick today)
4. 📊 **@splitthepicks on IG** (15 picks today)
5. 🆓 **New Free Channel** (18 picks today)

**Total:** 42 picks today

## 📁 File Locations

**Script:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\src\export_to_gdocs.py`

**Config:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.env`
- `GOOGLE_DOC_ID=1QAUgTvFZq3PlA25vznkly8CHb4uNsIRYEZ0oXCitKxo`
- `GOOGLE_CREDENTIALS_PATH=...\config\google_service_account.json`

**Credentials:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json`

**Logs:**
- PM2: `C:\Users\mpmmo\.pm2\logs\gdocs-exporter-*.log`
- Script: `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\logs\gdocs_exporter.log`

**PM2 Config:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\ecosystem.config.js`

## 🔄 How It Works

```
[Telegram] → [tg-collector] → [sent_archive/20251120/]
                                        ↓
                              [gdocs-exporter] (hourly)
                                        ↓
                                [Google Doc] (updates)
                                        ↓
                            📱 Open on phone → Copy all
```

## 🆘 Troubleshooting

### Document not updating?
```powershell
pm2 logs gdocs-exporter --lines 50
# Look for errors or "Export complete"
```

### Want to force an update now?
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src\export_to_gdocs.py
```

### Service crashed?
```powershell
pm2 restart gdocs-exporter
pm2 save
```

### Need to see what's in today's archive?
```powershell
ls C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\sent_archive\20251120
```

## 📅 Daily Behavior

**Today (Nov 20):**
- 1:00 PM → Doc shows 8 picks
- 2:00 PM → Doc updates with 15 picks (cumulative)
- 3:00 PM → Doc updates with 42 picks (cumulative)

**Tomorrow (Nov 21):**
- Midnight → Script reads NEW folder: `sent_archive/20251121/`
- Document **resets** and shows only Nov 21 picks
- Yesterday's picks still in archive, just not in doc

## ✅ Success Indicators

You know it's working when:
1. PM2 shows `gdocs-exporter` as **online**
2. Google Doc updates every hour
3. Logs show: `"Export complete! X picks from Y channels"`
4. You can copy all picks at once on mobile

## 🎉 Benefits

- ⏰ **Saves 10 minutes** per consensus (30 seconds vs 10 minutes)
- 📱 **Mobile friendly** (one tap to select all)
- ✅ **Never miss picks** (aggregates all 4 channels)
- 🔄 **Always current** (updates hourly automatically)
- 💯 **Zero maintenance** (runs forever via PM2)
- 🚫 **No rate limits** (uses local files, not Telegram API)

## 🔐 Security Notes

- Keep `google_service_account.json` **secret**
- Don't commit it to Git (already in `.gitignore`)
- Service account can ONLY access docs you share with it
- Your Google Doc link is private (only people with link can see)

## 📞 Need Help?

**Check logs first:**
```powershell
pm2 logs gdocs-exporter --lines 100
```

**Common log messages:**
- `✅ Authenticated with Google APIs` - Good!
- `✅ Loaded X picks from [channel]` - Good!
- `✅ Export complete!` - Good!
- `⚠️ No picks found for today` - Normal if early/no picks yet
- `❌ Error updating document` - Check permissions/doc ID

**Full documentation:** See `README_GDOCS_EXPORT.md`

---

**Your system is LIVE and working perfectly!** 🎉

Bookmark that Google Doc link on your phone and enjoy your new 30-second consensus workflow!
