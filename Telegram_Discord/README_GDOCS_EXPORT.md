# Free Picks → Google Docs Exporter

## 🎯 What This Does

Automatically aggregates all your free picks from 5 Telegram channels into a single Google Doc that updates every hour. Perfect for easy copy/paste on mobile when building consensus picks.

### Free Channels Included
- 🔥 **CAPPERS FREE💥**
- 💎 **Cappers Leaked**
- ✨ **Exclusive Cappers**
- 📊 **@splitthepicks on IG**
- 🆓 **New Free Channel**

## 📱 Mobile Workflow

1. Open Google Doc on your phone (or browser)
2. Select All → Copy
3. Paste into your consensus picks
4. Done! No more copying individual picks.

## 🚀 Quick Start

### Step 1: Google Cloud Setup (5 minutes)
Follow the detailed guide:
```
GOOGLE_DOCS_SETUP.md
```

This will help you:
1. Create Google Cloud project
2. Enable Google Docs API
3. Create service account
4. Download credentials JSON
5. Share your Google Doc with the service account

### Step 2: Install Dependencies
Run the installation script:
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
.\install_gdocs_exporter.ps1
```

This installs:
- `google-api-python-client` - Google Docs API
- `google-auth` - Authentication
- `pytz` - Timezone handling

### Step 3: Configure Environment Variables
Edit `.env` and add:
```env
# Google Docs Export
GOOGLE_DOC_ID=your_document_id_here
GOOGLE_CREDENTIALS_PATH=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json
TIMEZONE=America/New_York
```

### Step 4: Test Manually
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src/export_to_gdocs.py
```

Check your Google Doc - you should see today's picks!

### Step 5: Start Automatic Hourly Updates
```powershell
pm2 restart ecosystem.config.js
pm2 save
```

The exporter will now run automatically every hour at :00 (1:00, 2:00, 3:00, etc.)

## 📊 How It Works

```
[Telegram Channels]
        ↓
[tg-collector] (already running)
        ↓
[sent_archive/YYYYMMDD/]
        ↓
[gdocs-exporter] ← NEW (runs hourly)
        ↓
[Google Doc] ← Opens on mobile
```

### Data Flow
1. **Telegram → Local Storage** (existing system)
   - Your `tg-collector` bot already saves messages to `sent_archive/`
   - Organized by date: `sent_archive/20251120/`

2. **Local Storage → Google Docs** (new script)
   - Reads all JSON files from today's date
   - Parses text and timestamps
   - Formats as clean, readable document
   - Updates Google Doc via API

3. **Google Docs → Mobile** (your workflow)
   - Open doc on phone
   - Copy all text
   - Paste into consensus

## 📄 Document Format

```
FREE PICKS - November 20, 2025
Last updated: 3:00 PM EST
═══════════════════════════════════════

🔥 CAPPERS FREE💥 (5 picks)
───────────────────────────────────────
[1:18 PM] VEGASMIRABET - ✅
[1:22 PM] Another pick here...
[2:05 PM] And another...

💎 Cappers Leaked (3 picks)
───────────────────────────────────────
[2:30 PM] Pick text...

✨ Exclusive Cappers (2 picks)
───────────────────────────────────────
[3:00 PM] Pick text...

📊 @splitthepicks on IG (1 pick)
───────────────────────────────────────
[12:45 PM] Pick text...

🆓 New Free Channel (0 picks)
───────────────────────────────────────
No picks yet today.

═══════════════════════════════════════
Total picks today: 11
```

## 🔧 Management

### Check Status
```powershell
pm2 list
```

You should see:
- ✅ tg-collector (online)
- ✅ router (online)
- ✅ forwarder (online)
- ✅ gdocs-exporter (online)

### View Logs
```powershell
# Real-time logs
pm2 logs gdocs-exporter

# Last 50 lines
pm2 logs gdocs-exporter --lines 50

# Error logs only
pm2 logs gdocs-exporter --err

# Log file location
C:\Users\mpmmo\.pm2\logs\gdocs-exporter-out.log
C:\Users\mpmmo\.pm2\logs\gdocs-exporter-error.log
```

### Manual Export
Run export on-demand (doesn't wait for hourly schedule):
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src/export_to_gdocs.py
```

### Restart Service
```powershell
pm2 restart gdocs-exporter
```

### Stop Service
```powershell
pm2 stop gdocs-exporter
```

## 🛠️ Configuration

### Change Update Frequency
Edit `ecosystem.config.js`, find the `gdocs-exporter` section:

```javascript
// Every hour (default)
cron_restart: '0 * * * *'

// Every 30 minutes
cron_restart: '*/30 * * * *'

// Every 15 minutes
cron_restart: '*/15 * * * *'

// Twice a day (noon and 6pm)
cron_restart: '0 12,18 * * *'
```

Then restart:
```powershell
pm2 restart ecosystem.config.js
pm2 save
```

### Change Timezone
Edit `.env`:
```env
TIMEZONE=America/New_York    # Eastern Time
TIMEZONE=America/Chicago     # Central Time
TIMEZONE=America/Denver      # Mountain Time
TIMEZONE=America/Los_Angeles # Pacific Time
```

### Add/Remove Channels
Edit `src/export_to_gdocs.py`, modify the `FREE_CHANNELS` dictionary:

```python
FREE_CHANNELS = {
    "free_cappers": {
        "name": "CAPPERS FREE💥",
        "emoji": "🔥",
        "folder": "free_cappers"
    },
    # Add your new channel here...
}
```

## 🐛 Troubleshooting

### "Permission denied" Error
**Problem:** Service account doesn't have access to Google Doc

**Solution:**
1. Open your Google Doc
2. Click "Share" button
3. Add the service account email (from `google_service_account.json` → `client_email`)
4. Set permission to "Editor"
5. Click "Send"

### "No picks found" Warning
**Problem:** Script can't find today's picks

**Possible causes:**
- It's early and no picks posted yet today → Normal, wait for picks
- `sent_archive/YYYYMMDD/` folder doesn't exist → Check if collector is running
- Wrong timezone in `.env` → Verify `TIMEZONE` setting

**Check:**
```powershell
# View today's archive folder
ls C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\sent_archive\20251120

# Check if collector is running
pm2 list
pm2 logs tg-collector --lines 20
```

### "Credentials file not found"
**Problem:** Script can't find `google_service_account.json`

**Solution:**
1. Verify file exists: `config\google_service_account.json`
2. Check `.env` file has correct path:
   ```env
   GOOGLE_CREDENTIALS_PATH=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json
   ```

### "Invalid document ID"
**Problem:** Wrong Google Doc ID in `.env`

**Solution:**
1. Open your Google Doc
2. Copy ID from URL: `https://docs.google.com/document/d/ABC123XYZ/edit`
3. ID is `ABC123XYZ` (the part between `/d/` and `/edit`)
4. Update `.env`:
   ```env
   GOOGLE_DOC_ID=ABC123XYZ
   ```

### PM2 Process Not Running
**Problem:** `pm2 list` doesn't show `gdocs-exporter`

**Solution:**
```powershell
# Reload ecosystem config
pm2 delete gdocs-exporter
pm2 start ecosystem.config.js --only gdocs-exporter
pm2 save
```

## 📁 File Structure

```
Telegram_Discord/
├── src/
│   └── export_to_gdocs.py           ← Main export script
├── config/
│   └── google_service_account.json  ← Google credentials (keep secret!)
├── logs/
│   └── gdocs_exporter.log           ← Application logs
├── sent_archive/
│   └── YYYYMMDD/                    ← Daily picks (read from here)
│       ├── free_cappers/
│       ├── cappers_leaked/
│       ├── exclusive_cappers/
│       ├── splitthepicks/
│       └── new_free_channel/
├── .env                             ← Configuration
├── ecosystem.config.js              ← PM2 config (hourly cron)
├── GOOGLE_DOCS_SETUP.md            ← Setup guide
├── README_GDOCS_EXPORT.md          ← This file
└── install_gdocs_exporter.ps1      ← Installation script
```

## 🔐 Security Notes

- **Keep `google_service_account.json` secret!** It's like a password.
- Don't commit it to Git (already in `.gitignore`)
- Only share Google Doc with the service account (not your whole workspace)
- The service account can only access docs you explicitly share with it

## 🎉 Success Indicators

You'll know it's working when:
1. ✅ PM2 shows `gdocs-exporter` as "online"
2. ✅ Google Doc updates every hour
3. ✅ Logs show: "✅ Export complete! X picks from Y channels"
4. ✅ You can open doc on mobile and copy all picks at once

## 📞 Support

Check logs for detailed error messages:
```powershell
pm2 logs gdocs-exporter --lines 100
```

Common log messages:
- `✅ Authenticated with Google APIs` - Good! Authentication working
- `✅ Loaded X picks from [channel]` - Good! Found picks
- `✅ Export complete!` - Good! Document updated successfully
- `⚠️ No picks found for today` - Normal if it's early/no picks yet
- `❌ Error updating document` - Check permissions/document ID
- `❌ Fatal error` - Check logs for details

## 🔄 Daily Workflow

### Morning (Start of Day)
- System automatically creates today's folder in `sent_archive/`
- First picks start arriving from Telegram
- First hourly export runs, creates initial document

### Throughout Day
- Every hour at :00, script runs automatically
- Reads all picks from `sent_archive/YYYYMMDD/`
- Updates Google Doc with latest picks
- Document grows throughout the day

### When You Need Picks
1. Open Google Doc on phone
2. See all free picks aggregated
3. Select All → Copy
4. Paste into consensus picks
5. Done in seconds!

### End of Day
- Final export includes all picks from the day
- Tomorrow, new `sent_archive/YYYYMMDD/` folder starts fresh
- Old folders preserved for history

## 🎯 Why This Works Better

**Before:**
- ❌ Open Discord app
- ❌ Navigate to free channels (5 different channels!)
- ❌ Copy pick 1, switch to notes, paste
- ❌ Back to Discord, copy pick 2, switch, paste
- ❌ Repeat 10-20 times
- ❌ Miss picks buried in scroll
- ❌ Takes 5-10 minutes

**After:**
- ✅ Open one Google Doc
- ✅ Select All → Copy
- ✅ Paste into consensus
- ✅ Done in 30 seconds
- ✅ All picks guaranteed included
- ✅ Organized by channel
- ✅ Sorted by time

## 🚀 Future Enhancements

Possible additions (not implemented yet):
- Filter by specific cappers/keywords
- Export to Google Sheets for better organization
- Include media/screenshots as links
- Historical view (yesterday's picks, etc.)
- SMS/email notifications when new picks arrive
- Integration with your consensus pick builder

---

**Enjoy your streamlined free picks workflow!** 🎉
