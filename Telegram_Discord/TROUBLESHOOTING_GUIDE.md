# Telegram-Discord Pipeline Troubleshooting Guide

## Quick Status Check Commands

```bash
# Check all services
pm2 list

# Check specific service logs
pm2 logs tg-collector --lines 50
pm2 logs router --lines 50
pm2 logs forwarder --lines 50

# Monitor real-time logs
pm2 logs --lines 100

# Check message flow
ls -la /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/inbox/
ls -la /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/
ls -la /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/sent_archive/
```

## Common Issues & Solutions

### 1. Service Not Starting
**Symptoms:** PM2 shows service as "stopped" or "errored"

**Solutions:**
```bash
# Check error logs
pm2 logs [service-name] --err --lines 100

# Restart with clean state
pm2 delete [service-name]
pm2 start ecosystem.config.js --only [service-name]

# Check Python environment
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord
./.venv/Scripts/python.exe --version
./.venv/Scripts/pip.exe list
```

### 2. Telegram Not Collecting Messages
**Symptoms:** No new files in inbox directory

**Checks:**
```bash
# Test Telegram connection
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord
PYTHONPATH=. ./.venv/Scripts/python.exe -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f'API_ID: {os.getenv(\"TELEGRAM_API_ID\")}'); print(f'Session: {os.getenv(\"TELEGRAM_SESSION\")[:20]}...')"

# Manually fetch messages
PYTHONPATH=. ./.venv/Scripts/python.exe fetch_today.py

# Check collector health
pm2 logs tg-collector --lines 50 | grep -E "(ERROR|WARNING|Connected)"
```

**Common Fixes:**
- Check `.env` file has correct TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION
- Verify session is still valid (may need re-auth)
- Check internet connectivity

### 3. Messages Not Routing to Queues
**Symptoms:** Messages in inbox but not in message_queue folders

**Checks:**
```bash
# Check routing configuration
cat config/routing_map.yaml

# Check router logs for errors
pm2 logs router --err --lines 100

# Manually test routing
PYTHONPATH=. ./.venv/Scripts/python.exe src/test_router.py
```

**Common Fixes:**
- Verify channel IDs match in routing_map.yaml
- Check queue directories exist and have write permissions
- Restart router: `pm2 restart router`

### 4. Discord Rate Limiting
**Symptoms:** "Rate limited" or "429" errors in logs

**Checks:**
```bash
# Check rate limit status
pm2 logs forwarder --lines 20 | grep -i "rate"

# Check Discord credentials
grep -E "DISCORD_WEBHOOK|DISCORD_BOT" .env
```

**Solutions:**
- Wait for rate limit to expire (check retry_after in logs)
- Reduce batch_size in settings.yaml (default is 1)
- Implement exponential backoff (already configured)
- For persistent issues, rotate webhooks or use multiple bot tokens

### 5. OCR Not Working
**Symptoms:** Free_cappers messages not showing formatted text

**Checks:**
```bash
# Verify Google Vision credentials
ls -la /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/google-vision-key.json
grep GOOGLE_APPLICATION_CREDENTIALS .env

# Test OCR directly
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord
PYTHONPATH=. ./.venv/Scripts/python.exe -c "from src.utils.ocr import ocr_enabled; print(f'OCR Enabled: {ocr_enabled()}')"

# Check OCR configuration
grep -A 4 "ocr:" config/settings.yaml
```

**Common Fixes:**
- Ensure google-cloud-vision is installed: `./.venv/Scripts/pip.exe install google-cloud-vision==3.7.4`
- Verify GOOGLE_APPLICATION_CREDENTIALS path is correct
- Check Google Cloud project has Vision API enabled
- Verify service account has necessary permissions

### 6. Messages Stuck in Queue
**Symptoms:** Messages accumulating in message_queue folders

**Checks:**
```bash
# Count messages in each queue
for dir in /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/; do
  echo "$(basename $dir): $(ls $dir 2>/dev/null | wc -l) messages"
done

# Check forwarder status
pm2 logs forwarder --lines 50 | grep -E "(Sent|ERROR|Rate)"

# Check Discord target configuration
cat config/discord_targets.yaml
```

**Common Fixes:**
- Verify Discord channel IDs and webhook URLs in discord_targets.yaml
- Check bot has permissions in Discord channels
- Clear rate limits by waiting or using different credentials
- Manually move stuck messages: `mv message_queue/*/failed/* message_queue/*/`

## Service Dependencies

### Required Environment Variables
```bash
# Telegram
TELEGRAM_API_ID=29479443
TELEGRAM_API_HASH=[your_hash]
TELEGRAM_SESSION=[session_string]

# Discord
DISCORD_WEBHOOK_PAID=[webhook_url]
DISCORD_BOT_TOKEN_FREE=[bot_token]

# Google Vision (for OCR)
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\google-vision-key.json
```

### Python Dependencies
```bash
# Check all dependencies
./.venv/Scripts/pip.exe list

# Reinstall if needed
./.venv/Scripts/pip.exe install -r requirements.txt
./.venv/Scripts/pip.exe install google-cloud-vision==3.7.4
```

## PM2 Management

### Start All Services
```bash
pm2 start ecosystem.config.js
```

### Stop All Services
```bash
pm2 stop all
```

### Restart Specific Service
```bash
pm2 restart tg-collector
pm2 restart router
pm2 restart forwarder
```

### Save PM2 Configuration
```bash
pm2 save
pm2 startup  # For auto-start on boot
```

### Reset Service (Clear Logs & Restart)
```bash
pm2 delete [service-name]
pm2 start ecosystem.config.js --only [service-name]
```

## Testing Commands

### Test Telegram Collection
```bash
# Fetch all messages from today
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord
PYTHONPATH=. ./.venv/Scripts/python.exe fetch_today.py
```

### Test Message Forwarding
```bash
# Test PAID queue (image + text)
PYTHONPATH=. ./.venv/Scripts/python.exe src/test_forward.py --queue paid_uatb --text "Test PAID message"

# Test FREE queue with OCR (text only)
PYTHONPATH=. ./.venv/Scripts/python.exe src/test_forward.py --queue free_cappers --text "Test FREE OCR message"
```

### Test OCR Functionality
```bash
# Test OCR on an image
PYTHONPATH=. ./.venv/Scripts/python.exe -c "
from src.utils.ocr import extract_text_from_image
result = extract_text_from_image('/path/to/test/image.jpg')
print(f'OCR Result: {result}')
"
```

## Log File Locations

- **PM2 Logs:** `C:\Users\mpmmo\.pm2\logs\`
  - `tg-collector-out.log` / `tg-collector-error.log`
  - `router-out.log` / `router-error.log`
  - `forwarder-out.log` / `forwarder-error.log`

- **Application Logs:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\logs\`
  - `telegram_collector.log`
  - `router.log`
  - `forwarder.log`

## Emergency Recovery

### Full Pipeline Reset
```bash
# Stop everything
pm2 stop all

# Clear queues (backup first!)
mkdir -p /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/backup
mv /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/*.json /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/backup/

# Clear logs
pm2 flush

# Restart everything
pm2 start ecosystem.config.js

# Monitor
pm2 logs --lines 100
```

### Rollback OCR Changes
```bash
# Disable OCR in settings
cd /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord
sed -i 's/enabled: true/enabled: false/' config/settings.yaml

# Restart forwarder
pm2 restart forwarder
```

## Performance Monitoring

### Check Resource Usage
```bash
# PM2 monitoring
pm2 monit

# Check message throughput
watch -n 5 'for dir in /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/; do echo "$(basename $dir): $(ls $dir 2>/dev/null | wc -l)"; done'
```

### Health Check Endpoints
```bash
# Check service health in logs
pm2 logs | grep HEALTH
```

## Contact & Escalation

1. **Check Logs First** - Most issues are visible in PM2 logs
2. **Verify Configuration** - Ensure all YAML files are valid
3. **Test Components Individually** - Use test scripts to isolate issues
4. **Rate Limits** - Discord has strict limits; be patient
5. **Session Expiry** - Telegram sessions may expire; re-authenticate if needed

## Quick Diagnostics Script

Create `diagnose.sh`:
```bash
#!/bin/bash
echo "=== PIPELINE DIAGNOSTICS ==="
echo ""
echo "1. SERVICE STATUS:"
pm2 list | grep -E "(tg-collector|router|forwarder)"
echo ""
echo "2. MESSAGE FLOW:"
echo "Inbox: $(ls /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/inbox/ | wc -l) messages"
for dir in /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/; do
  echo "Queue $(basename $dir): $(ls $dir 2>/dev/null | wc -l) messages"
done
echo "Archive: $(find /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/sent_archive/ -name "*.json" | wc -l) sent"
echo ""
echo "3. RECENT ERRORS:"
pm2 logs --err --nostream --lines 10
echo ""
echo "4. RATE LIMITS:"
pm2 logs forwarder --nostream --lines 5 | grep -i rate || echo "No recent rate limits"
```

Run with: `bash diagnose.sh`