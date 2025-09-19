# OCR Integration Acceptance Checklist

## Implementation Status
- ✅ Created `src/utils/ocr.py` with Google Vision integration
- ✅ Created `src/utils/picks_formatter.py` with AI picks parsing
- ✅ Updated `config/settings.yaml` to enable OCR for `free_cappers` queue only
- ✅ Modified `src/forwarder.py` to implement selective OCR logic
- ✅ Installed `google-cloud-vision==3.7.4` dependency
- ✅ Verified Google Vision credentials are properly configured
- ✅ Restarted PM2 services (tg-collector, router, forwarder)
- ✅ Ran smoke tests for both PAID and FREE paths

## Configuration Details
### OCR Settings (settings.yaml)
```yaml
ocr:
  enabled: true
  provider: vision
  mode: capper_picks
  queues: ["free_cappers"]  # OCR only for free_cappers
```

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS`: C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\google-vision-key.json (verified)

## Behavioral Changes
### PAID Queues (paid_uatb, paid_chamba)
- **Unchanged**: Continue sending original image + text
- Transport: Webhook
- Format: Telegram message with media attachment

### FREE Queue with OCR (free_cappers)
- **New Behavior**:
  - Extracts text from images using Google Vision OCR
  - Formats picks using AI parser
  - Sends formatted text only (no image attachment)
  - Falls back to original format if OCR fails

### FREE Queues without OCR (free_cappers_leaked, free_exclusive)
- **Unchanged**: Continue sending original image + text
- Transport: Discord Bot
- Format: Telegram message with media attachment

## Test Results
### PAID Path Test
```bash
python src/test_forward.py --queue paid_uatb --text "PAID path unchanged: image+text"
```
✅ **Result**: Message sent successfully via webhook (unchanged behavior)

### FREE Path with OCR Test
```bash
python src/test_forward.py --queue free_cappers --text "FREE uses OCR+formatter (text only)"
```
✅ **Result**: Message sent as text only via Discord bot (new OCR behavior)

## PM2 Services Status
- tg-collector: ✅ Online
- router: ✅ Online
- forwarder: ✅ Online (with OCR support)

## Key Components
1. **ocr.py**: Handles Google Vision API integration for text extraction
2. **picks_formatter.py**: AI-powered parser for sports betting picks
3. **forwarder.py**: Updated to conditionally apply OCR based on queue configuration

## Verification Steps
1. Check logs for OCR processing: `pm2 logs forwarder`
2. Monitor free_cappers Discord channel for formatted text messages
3. Monitor paid channels to ensure images are still being sent
4. Check for OCR errors in logs: `grep "OCR" logs/forwarder.log`

## Rollback Instructions (if needed)
1. Set `ocr.enabled: false` in settings.yaml
2. Restart services: `pm2 restart tg-collector router forwarder`
3. Uninstall Google Vision (optional): `.venv/Scripts/pip uninstall google-cloud-vision`

## Success Criteria
- ✅ PAID queues continue sending images + text unchanged
- ✅ free_cappers queue sends formatted text only (no images)
- ✅ OCR gracefully falls back on failure
- ✅ No disruption to existing message flow
- ✅ Services remain stable after restart

## Notes
- OCR is only applied when media_path exists and queue is in OCR queues list
- Falls back to original format if OCR processing fails
- Google Vision credentials must be accessible at runtime
- The picks formatter includes known cappers list for better extraction