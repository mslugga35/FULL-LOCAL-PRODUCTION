# Test Channel Setup Guide

## How to Get Your Test Channel ID

### Method 1: Using Telegram Web (Easiest)
1. Open https://web.telegram.org
2. Navigate to your test channel
3. Look at the URL - it will show something like:
   - `https://web.telegram.org/k/#-1234567890`
4. Copy the number INCLUDING the minus sign

### Method 2: Using Telegram Desktop
1. Right-click on your test channel
2. Select "Copy Link"
3. The link will be like: `https://t.me/c/1234567890`
4. Add `-100` before the number: `-1001234567890`

### Method 3: Forward a Message
1. Forward any message from your test channel to @userinfobot
2. The bot will reply with the channel ID

## Adding Your Test Channel

Run this command to add your channel:
```bash
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
python add_test_channel.py
```

Or manually edit `config/channel_routing_map.py` and add your channel:

```python
ROUTING_MAP = {
    -1002177758646: "paid_uatb",
    -1002470080886: "paid_diamond",
    -1002592669126: "free_cappers",
    -1001560546587: "cappers_leaked",
    -1002608783933: "exclusive_cappers",
    -100XXXXXXXXXX: "test_channel",      # <-- Add your test channel here
}
```

## After Adding Your Channel

1. Restart the collector:
   ```bash
   pm2 restart tg-collector
   ```

2. Send a test message in your Telegram channel

3. Check if message arrived:
   ```bash
   # Check inbox for new messages
   ls -la C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\inbox\

   # Check if routed to queue
   ls -la C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\message_queue\test_channel\
   ```

4. Monitor logs:
   ```bash
   pm2 logs tg-collector --lines 50
   ```

## Testing With Different Content

Send these test messages in your channel:

1. **Text only**: "Test message 123"
2. **With image**: Send any image with caption "Test with image"
3. **Media only**: Send image without text
4. **Multiple images**: Send 2+ images in one message

## Troubleshooting

If messages aren't appearing:

1. Check collector is running:
   ```bash
   pm2 status tg-collector
   ```

2. Verify session is valid:
   ```bash
   cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
   python validate_session.py
   ```

3. Check collector logs for errors:
   ```bash
   pm2 logs tg-collector --lines 100
   ```

4. Make sure your bot/user account is a member of the test channel

## Current Discord Mapping

Your test messages will be sent to the same Discord channel as `free_cappers`:
- Discord Channel ID: `1403894557615325216`
- This is for testing purposes
- You can change this in `config/discord_targets.yaml`