# Google Docs Export - Quick Start Checklist

Complete these steps to get your free picks flowing to Google Docs!

## ☑️ Checklist

### [ ] Step 1: Google Cloud Setup (5 minutes)
1. [ ] Go to https://console.cloud.google.com/
2. [ ] Create new project: "free-picks-exporter"
3. [ ] Enable "Google Docs API"
4. [ ] Enable "Google Drive API"
5. [ ] Create service account: "picks-exporter-bot"
6. [ ] Create JSON key → Download
7. [ ] Rename to `google_service_account.json`
8. [ ] Move to `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\`

**Detailed guide:** See `GOOGLE_DOCS_SETUP.md`

### [ ] Step 2: Create Google Doc
1. [ ] Go to https://docs.google.com/
2. [ ] Create new document
3. [ ] Name it: "Free Picks - Daily Export"
4. [ ] Copy document ID from URL:
   - URL: `https://docs.google.com/document/d/ABC123XYZ/edit`
   - ID: `ABC123XYZ`
5. [ ] Save this ID for next step

### [ ] Step 3: Share Doc with Service Account
1. [ ] Click "Share" button in Google Doc
2. [ ] Open `config\google_service_account.json` in notepad
3. [ ] Find `"client_email"` field (looks like: `picks-exporter-bot@...`)
4. [ ] Copy that email
5. [ ] Paste into "Add people and groups" in Google Doc
6. [ ] Set permission to "Editor"
7. [ ] Click "Send"

### [ ] Step 4: Configure Environment
1. [ ] Open `.env` file in notepad
2. [ ] Find the `GOOGLE DOCS EXPORT` section
3. [ ] Replace `YOUR_DOCUMENT_ID_HERE` with your actual document ID
4. [ ] Verify `GOOGLE_CREDENTIALS_PATH` points to your JSON file
5. [ ] Save `.env`

Example:
```env
GOOGLE_DOC_ID=1a2b3c4d5e6f7g8h9i0j
GOOGLE_CREDENTIALS_PATH=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json
TIMEZONE=America/New_York
```

### [ ] Step 5: Install Dependencies
Run in PowerShell:
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
.\install_gdocs_exporter.ps1
```

This script will:
- ✅ Check virtual environment
- ✅ Install Google API libraries
- ✅ Verify configuration
- ✅ Create logs directory

### [ ] Step 6: Test Manually
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src/export_to_gdocs.py
```

Expected output:
```
🚀 Starting Google Docs export...
✅ Authenticated with Google APIs
✅ Loaded X picks from CAPPERS FREE💥
✅ Loaded X picks from Cappers Leaked
...
✅ Export complete! X picks from Y channels
📄 View document: https://docs.google.com/document/d/...
```

### [ ] Step 7: Verify Google Doc
1. [ ] Open your Google Doc
2. [ ] Should see today's picks formatted nicely
3. [ ] Try selecting all text and copying
4. [ ] If you see picks, it works! 🎉

### [ ] Step 8: Start Automatic Updates
```powershell
pm2 restart ecosystem.config.js
pm2 save
```

Check status:
```powershell
pm2 list
```

Should show:
- ✅ tg-collector (online)
- ✅ router (online)
- ✅ forwarder (online)
- ✅ gdocs-exporter (online) ← NEW!

### [ ] Step 9: Test Hourly Updates
Wait for next hour (e.g., if it's 3:15 PM, wait until 4:00 PM) and check:

```powershell
pm2 logs gdocs-exporter --lines 20
```

Should see:
```
[4:00:00 PM] ✅ Export complete! X picks from Y channels
```

### [ ] Step 10: Mobile Access
1. [ ] Open Google Docs app on phone (or browser)
2. [ ] Find "Free Picks - Daily Export"
3. [ ] Long press → Select All → Copy
4. [ ] Paste into your consensus picks
5. [ ] Success! 🎉

---

## ✅ All Done!

Your free picks are now auto-exporting to Google Docs every hour!

### What Happens Next?
- ⏰ Every hour at :00, script runs automatically
- 📄 Google Doc updates with latest picks
- 📱 Open on mobile anytime to copy all picks
- 🎯 Build consensus picks faster than ever

### Quick Commands
```powershell
# Check status
pm2 list

# View logs
pm2 logs gdocs-exporter

# Manual export now
python src/export_to_gdocs.py

# Restart service
pm2 restart gdocs-exporter
```

### Troubleshooting
If something doesn't work, see:
- `README_GDOCS_EXPORT.md` - Full documentation
- `GOOGLE_DOCS_SETUP.md` - Detailed setup guide

Common issues:
- "Permission denied" → Share doc with service account
- "File not found" → Check credentials path in `.env`
- "No picks found" → Normal if early in day, wait for picks

---

## 📱 Your New Workflow

**Before:**
1. Open Discord
2. Navigate to 5 different channels
3. Copy each pick individually
4. Switch to notes, paste
5. Repeat 10-20 times
6. Takes 5-10 minutes

**After:**
1. Open one Google Doc
2. Select All → Copy
3. Paste in consensus
4. Done in 30 seconds! 🚀

Enjoy your streamlined free picks workflow!
