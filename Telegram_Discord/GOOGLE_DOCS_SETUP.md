# Google Docs Free Picks Exporter - Setup Guide

## Overview
This system automatically exports your 5 free picks channels to a Google Doc every hour, making it easy to copy all picks at once on your mobile device.

## Quick Setup (5 minutes)

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it: `free-picks-exporter`
4. Click "Create"

### Step 2: Enable Google Docs API

1. In your new project, go to: https://console.cloud.google.com/apis/library
2. Search for "Google Docs API"
3. Click "Enable"
4. Also enable "Google Drive API" (needed to create/share docs)

### Step 3: Create Service Account

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Name: `picks-exporter-bot`
4. Description: `Automated free picks to Google Docs`
5. Click "Create and Continue"
6. Skip role assignment (click "Continue" → "Done")

### Step 4: Create JSON Key

1. Click on your new service account email (picks-exporter-bot@...)
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create" - a JSON file will download

### Step 5: Save Credentials

1. Rename the downloaded file to: `google_service_account.json`
2. Move it to: `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\`
3. Keep this file secret (it's like a password)

### Step 6: Create Your Google Doc

1. Go to https://docs.google.com/
2. Create a new document
3. Name it: `Free Picks - Daily Export`
4. Click "Share" button (top right)
5. In "Add people and groups", paste your service account email:
   - Find it in `google_service_account.json` → `client_email` field
   - Should look like: `picks-exporter-bot@free-picks-exporter.iam.gserviceaccount.com`
6. Set permission to "Editor"
7. Click "Send"
8. Copy the document ID from the URL:
   - URL looks like: `https://docs.google.com/document/d/ABC123XYZ/edit`
   - Document ID is: `ABC123XYZ`
9. Save this ID - you'll need it in the next step

### Step 7: Configure the Script

1. Open: `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.env`
2. Add these lines:
   ```
   # Google Docs Export
   GOOGLE_DOC_ID=ABC123XYZ
   GOOGLE_CREDENTIALS_PATH=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\config\google_service_account.json
   ```
3. Replace `ABC123XYZ` with your actual document ID
4. Save the file

## That's it! Setup complete.

## Testing

Run manually to test:
```powershell
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src/export_to_gdocs.py
```

Check your Google Doc - it should now have today's picks!

## Automation

The script will run automatically every hour via PM2. Check status:
```powershell
pm2 list
pm2 logs gdocs-exporter
```

## Mobile Access

1. Open Google Docs app on phone (or browser)
2. Find "Free Picks - Daily Export" document
3. Select all text (long press → Select All)
4. Copy
5. Paste into your consensus picks!

## Troubleshooting

### "Permission denied" error
- Make sure you shared the Google Doc with the service account email
- Check the email in `google_service_account.json` → `client_email`

### "File not found" error
- Verify `GOOGLE_CREDENTIALS_PATH` in `.env` points to the JSON file
- Check that `google_service_account.json` exists in the config folder

### "Invalid document ID" error
- Double-check `GOOGLE_DOC_ID` in `.env`
- Make sure you copied just the ID, not the full URL

### No picks showing up
- Check that `sent_archive/YYYYMMDD/` has files for today
- Run `pm2 logs gdocs-exporter` to see detailed logs

## Manual Commands

```powershell
# Run export now
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python src/export_to_gdocs.py

# Check PM2 status
pm2 list

# View logs
pm2 logs gdocs-exporter --lines 50

# Restart service
pm2 restart gdocs-exporter

# Stop service
pm2 stop gdocs-exporter
```

## Configuration

Edit `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\.env`:

```env
# Update frequency (cron format, default: every hour)
EXPORT_CRON=0 * * * *

# Timezone for timestamps
TIMEZONE=America/New_York

# Channels to include (comma-separated)
FREE_CHANNELS=free_cappers,cappers_leaked,exclusive_cappers,splitthepicks,new_free_channel
```

## Document Format

The exported document will look like:

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

## Support

Check logs if something goes wrong:
```powershell
pm2 logs gdocs-exporter --lines 100
```

The script logs:
- ✅ Number of picks found per channel
- ✅ Document update success/failure
- ✅ Any errors with file paths or API calls
