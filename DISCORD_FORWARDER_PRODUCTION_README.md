# Discord Forwarder Production

A production-ready Discord forwarder that reads from `routing_config.json` and implements exact routing between Telegram message queues and Discord channels using both webhook and bot transport methods.

## Features

- **Dual Transport Methods**: Supports both Discord webhooks and bot API
- **Configuration-Driven**: All routing defined in `routing_config.json`
- **Rate Limiting**: Built-in rate limiting to avoid Discord API limits
- **Error Handling**: Comprehensive error handling and logging
- **File Processing**: Processes JSON message files from queue directories
- **Automatic Cleanup**: Moves processed files to avoid duplicates
- **Windows Path Support**: Correctly handles Windows path separators

## File Structure

```
C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\
├── discord_forwarder_production.py          # Main forwarder application
├── test_discord_forwarder_production.py     # Test suite
├── START_DISCORD_FORWARDER_PRODUCTION.bat   # Windows startup script
├── routing_config.json                      # Routing configuration
├── .env                                     # Environment variables
├── requirements_production.txt              # Python dependencies
├── message_queue/                           # Input message queues
│   ├── paid_uatb/                          # UATB paid messages
│   ├── paid_diamond/                       # Diamond paid messages
│   └── free_cappers/                       # Free capper messages
│       ├── cappers_free/
│       ├── cappers_leaked/
│       └── exclusive_cappers/
├── processed_messages/                      # Processed message archive
├── logs/                                   # Application logs
└── DISCORD_FORWARDER_PRODUCTION_README.md  # This documentation
```

## Routing Configuration

The forwarder implements these exact routes from `routing_config.json`:

### Webhook Transport (Paid Channels)
- `paid_uatb` → Discord channel `1403837637730762875` (webhook)
- `paid_diamond` → Discord channel `1403837637730762875` (webhook)

### Bot Transport (Free Channels)
- `free_cappers\cappers_free` → Discord channel `1403894557615325216` (bot)
- `free_cappers\cappers_leaked` → Discord channel `1403894596186017962` (bot)
- `free_cappers\exclusive_cappers` → Discord channel `1403894653660692500` (bot)

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_production.txt
   ```

2. **Verify Environment**:
   - Ensure `.env` file contains `DISCORD_BOT_TOKEN`
   - Ensure `routing_config.json` exists with proper configuration

3. **Run Tests**:
   ```bash
   python test_discord_forwarder_production.py
   ```

## Usage

### Quick Start (Windows)
```cmd
START_DISCORD_FORWARDER_PRODUCTION.bat
```

### Manual Start
```bash
python discord_forwarder_production.py
```

### Testing
```bash
# Run configuration tests
python test_discord_forwarder_production.py

# Check test messages were created
dir message_queue\paid_uatb\test_message_*.json

# Start forwarder to process test messages
python discord_forwarder_production.py
```

## Configuration Details

### Environment Variables (.env)
```
DISCORD_BOT_TOKEN=your_bot_token_here
```

### Routing Configuration (routing_config.json)
```json
{
  "discord_channels": {
    "1403837637730762875": {
      "transport": "webhook",
      "webhook_url": "https://discord.com/api/webhooks/..."
    },
    "1403894557615325216": {
      "transport": "bot"
    }
  },
  "queue_to_discord_routing": {
    "paid_uatb": {
      "destination_channel": "1403837637730762875",
      "transport": "webhook"
    },
    "free_cappers\\cappers_free": {
      "destination_channel": "1403894557615325216",
      "transport": "bot"
    }
  }
}
```

## Message Processing

### Input Format
Messages in queue directories should be JSON files with structure:
```json
{
  "text": "Message content",
  "sender_name": "Sender Name",
  "date": "2024-01-01T12:00:00Z",
  "message_id": "unique_id",
  "channel_title": "Source Channel"
}
```

### Processing Flow
1. **Scan**: Continuously scans all queue directories for `.json` files
2. **Route**: Determines destination channel and transport method
3. **Format**: Formats message content for Discord
4. **Send**: Sends via webhook or bot API with rate limiting
5. **Archive**: Moves processed files to `processed_messages/`

### Rate Limiting
- **Webhooks**: 0.5 second delay between messages
- **Bot Messages**: 0.5 second delay between messages
- **Message Length**: Truncated to 2000 characters (Discord limit)

## Logging

### Log Files
- `logs/discord_forwarder_production.log`: Main application log
- Console output: Real-time status and errors

### Log Levels
- **INFO**: Normal operation, successful sends
- **WARNING**: Non-critical issues, truncated messages
- **ERROR**: Failed sends, configuration errors
- **DEBUG**: Detailed processing information

## Error Handling

### Common Issues

1. **Bot Token Invalid**
   - Check `.env` file contains valid `DISCORD_BOT_TOKEN`
   - Verify bot has permissions in target Discord servers

2. **Webhook URL Invalid**
   - Check webhook URLs in `routing_config.json`
   - Verify webhooks are active in Discord

3. **Queue Directory Missing**
   - Ensure all queue directories exist under `message_queue/`
   - Test script will create missing directories

4. **Message Processing Fails**
   - Check JSON file format is valid
   - Verify file permissions
   - Review logs for specific errors

### Recovery Mechanisms
- **Retry Logic**: Failed messages remain in queue for retry
- **File Safety**: Files only moved after successful send
- **Graceful Shutdown**: Ctrl+C stops processing safely

## Monitoring

### Health Checks
```bash
# Check if forwarder is running
tasklist | findstr python

# Check recent log entries
tail -f logs/discord_forwarder_production.log

# Check for unprocessed messages
dir /s message_queue\*.json

# Check processed message archive
dir /s processed_messages\*.json
```

### Performance Metrics
- **Processing Rate**: ~2 messages per second (with rate limiting)
- **Memory Usage**: Typically <50MB
- **CPU Usage**: Very low during normal operation

## Security Considerations

1. **Bot Token**: Keep `DISCORD_BOT_TOKEN` secure and never commit to version control
2. **Webhook URLs**: Treat webhook URLs as sensitive credentials
3. **File Permissions**: Ensure only authorized users can write to message_queue/
4. **Network**: Consider firewall rules for Discord API access

## Troubleshooting

### Discord API Errors
- **401 Unauthorized**: Invalid bot token
- **403 Forbidden**: Bot lacks channel permissions
- **429 Too Many Requests**: Rate limit exceeded (handled automatically)

### File Processing Errors
- **JSON Parse Error**: Invalid message file format
- **Permission Denied**: File system permissions issue
- **File Not Found**: Race condition during processing

### Network Issues
- **Connection Timeout**: Discord API unreachable
- **DNS Resolution**: Network configuration issue

## Production Deployment

### Recommended Setup
1. **Service Management**: Use Windows Task Scheduler or service wrapper
2. **Log Rotation**: Implement log rotation for long-term operation
3. **Monitoring**: Set up alerts for error conditions
4. **Backup**: Regular backup of configuration files

### Scaling Considerations
- **Multiple Instances**: Can run multiple instances for different route groups
- **Load Balancing**: Distribute queue processing across instances
- **Database**: Consider database for large-scale message tracking

## Support

For issues or questions:
1. Check logs in `logs/discord_forwarder_production.log`
2. Run test suite: `python test_discord_forwarder_production.py`
3. Verify configuration with routing test scripts
4. Review this documentation for common solutions

## Changelog

- **v1.0**: Initial production release
  - Dual transport support (webhook/bot)
  - Configuration-driven routing
  - Comprehensive error handling
  - Windows path support
  - Rate limiting and logging