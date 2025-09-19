# Signal Integration Setup Guide

## Overview
The Signal integration allows forwarding betting picks to Signal groups/contacts using either Signal CLI or Signal REST API.

## Setup Options

### Option 1: Signal CLI (Recommended)

1. **Install Signal CLI**
   ```bash
   # Download from: https://github.com/AsamK/signal-cli/releases
   # Extract to a folder in your PATH or specify full path in .env
   ```

2. **Register Phone Number**
   ```bash
   signal-cli -a +1234567890 register
   signal-cli -a +1234567890 verify CODE_FROM_SMS
   ```

3. **Environment Variables**
   Add to your `.env` file:
   ```
   SIGNAL_CLI_PATH=signal-cli  # or full path like C:\signal-cli\bin\signal-cli.bat
   SIGNAL_PHONE_NUMBER=+1234567890
   ```

### Option 2: Signal REST API

1. **Environment Variables**
   Add to your `.env` file:
   ```
   SIGNAL_API_URL=http://localhost:8080  # Your Signal API server
   SIGNAL_API_TOKEN=your_api_token
   SIGNAL_PHONE_NUMBER=+1234567890
   ```

## Configuration

### 1. Get Signal Group ID
```bash
# List your Signal groups
signal-cli -a +1234567890 listGroups

# Output will show group IDs like:
# Group: group.abcd1234... Name: "My Betting Group"
```

### 2. Update Configuration
Edit `config/discord_targets.yaml`:
```yaml
signal_picks:
  transport: signal
  recipient_id: group.abcd1234efgh5678  # Your actual group ID

# Or for individual contact:
signal_picks:
  transport: signal
  recipient_id: +1987654321  # Phone number
```

### 3. Set Up Message Routing
Edit `config/channel_routing_map.py` to route messages to `signal_picks`:
```python
ROUTING_MAP = {
    -1002592669126: "signal_picks",  # Route free_cappers to Signal
    # ... other routes
}
```

## Testing

### Test Signal CLI
```bash
signal-cli -a +1234567890 send -g group.YOUR_GROUP_ID -m "Test message from Signal CLI"
```

### Test Integration
1. Create a test message file:
   ```bash
   echo '{"text":"Test pick: Lakers ML -150 2u","chat_title":"Test","sender_name":"TestUser","timestamp":"2025-09-19"}' > message_queue/signal_picks/test.json
   ```

2. Watch logs:
   ```bash
   pm2 logs forwarder --lines 20
   ```

3. Restart forwarder:
   ```bash
   pm2 restart forwarder
   ```

## Features

- ✅ Text message forwarding
- ✅ Image/media forwarding (via Signal CLI)
- ✅ Clean pick formatting using updated formatter
- ✅ Rate limiting (1 second between messages)
- ✅ Error handling and retries
- ✅ Archive system for sent messages

## Troubleshooting

### Signal CLI Issues
- Make sure phone number is properly registered
- Check Signal CLI path in environment variables
- Ensure Signal CLI has proper permissions

### Group Permission Issues
- Make sure your Signal account is admin of the group
- Verify group ID is correct (starts with `group.`)

### Rate Limiting
- Signal has built-in rate limits
- System waits 1 second between Signal messages
- Failures trigger cooldown periods

## Current Status
- ✅ Signal client implemented
- ✅ Forwarder updated to handle Signal transport
- ✅ Configuration files updated
- ⏳ **Need your Signal group ID to complete setup**

## Next Steps
1. Install Signal CLI or set up REST API
2. Get your Signal group ID
3. Update `recipient_id` in `discord_targets.yaml`
4. Test the integration
5. Set up routing in `channel_routing_map.py`