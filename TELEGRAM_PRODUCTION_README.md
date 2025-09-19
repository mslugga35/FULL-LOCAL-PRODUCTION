# Telegram Production Collection System

## Overview

This is a complete, production-ready Telegram message collection system that:
- ✅ Uses proper single-instance locking (no multiple instances)
- ✅ Handles session authentication without hanging
- ✅ Captures ALL message types from specific channels
- ✅ Saves messages to structured inbox folder
- ✅ Forwards summaries to validation number
- ✅ Uses StringSession for seamless authentication
- ✅ Includes comprehensive error handling and recovery
- ✅ Production-ready logging and monitoring

## Target Channels

The system monitors these 5 channels:
1. **UATB** (-1002177758646)
2. **Diamond/Chamba** (-1002470080886)
3. **Cappers Free** (-1002592669126)
4. **Cappers Leaked** (-1001560546587)
5. **Exclusive Cappers** (-1002608783933)

## Quick Start

### 1. Initial Setup
```batch
# Run the complete setup
SETUP_PRODUCTION_TELEGRAM.bat
```

### 2. Authentication (First Time Only)
```batch
# Set up Telegram session
python auth_session_production.py
```

### 3. Test Connection
```batch
# Verify everything works
python test_telegram_connection.py
```

### 4. Start Collection
```batch
# Start the production collector
START_TELEGRAM_PRODUCTION.bat
```

## File Structure

```
FULL-LOCAL-PRODUCTION/
├── telegram_production_collector.py    # Main collector (production-ready)
├── auth_session_production.py          # Authentication setup
├── test_telegram_connection.py         # Connection testing
├── START_TELEGRAM_PRODUCTION.bat       # Start script
├── STOP_TELEGRAM_PRODUCTION.bat        # Stop script
├── MONITOR_TELEGRAM_PRODUCTION.bat     # Monitor script
├── SETUP_PRODUCTION_TELEGRAM.bat       # Complete setup
├── requirements_production.txt         # Python dependencies
├── .env                                # Environment configuration
├── inbox/                              # Message storage
│   ├── media/                          # Downloaded media files
│   └── *.json                          # Message metadata
└── logs/                               # Application logs
    └── telegram_collector_YYYYMMDD.log
```

## Key Features

### 🔒 Single Instance Protection
- Uses robust PID-based locking
- Prevents multiple instances running simultaneously
- Automatic cleanup of stale lock files

### 🔐 Authentication Management
- Non-blocking session authentication
- Proper timeout handling (30 seconds)
- StringSession for persistent authentication
- No interactive prompts during operation

### 📨 Message Processing
- Captures ALL message types (text, photos, videos, documents, stickers, audio)
- Handles grouped media (albums)
- Preserves original filenames when possible
- Structured JSON metadata for each message

### 🔄 Connection Reliability
- Automatic reconnection with exponential backoff
- Health checks every 5 minutes
- Graceful handling of network interruptions
- Connection timeout protection

### 📊 Monitoring & Logging
- Comprehensive logging to files and console
- Real-time status monitoring
- Periodic summary reports (+3212629156)
- Process monitoring and management

### 🎯 Channel-Specific Targeting
- Only monitors specified channels (reduces noise)
- Channel name mapping for easy identification
- Access verification on startup

## Configuration

### Environment Variables (.env file)
```bash
# Required: Telegram session string (set by auth script)
TELEGRAM_STRING_SESSION=your_session_string_here

# Optional: Other Discord/OCR tokens (inherited from existing setup)
DISCORD_BOT_TOKEN=...
DISCORD_OCR_BOT_TOKEN=...
# ... etc
```

### API Configuration (hardcoded)
```python
API_ID = 29479443
API_HASH = "e3a7a7226cf446bbfd5366f7da75cdfa"
VALIDATION_NUMBER = "+3212629156"
```

## Operation Scripts

### Start the Collector
```batch
START_TELEGRAM_PRODUCTION.bat
```
- Checks dependencies
- Verifies authentication
- Handles lock files
- Starts collector with error handling

### Stop the Collector
```batch
STOP_TELEGRAM_PRODUCTION.bat
```
- Graceful termination (SIGTERM)
- Force kill if needed (SIGKILL)
- Cleanup lock files
- Process verification

### Monitor Operation
```batch
MONITOR_TELEGRAM_PRODUCTION.bat
```
- Real-time status display
- Log file viewing
- Process management
- Inbox statistics

## Message Storage Format

### JSON Metadata (`inbox/*.json`)
```json
{
  "timestamp": "2025-09-18T10:30:45.123456",
  "source": "UATB",
  "channel_id": -1002177758646,
  "message_id": 12345,
  "text": "Message content here...",
  "media_type": "photo",
  "media_info": {
    "filename": "20250918_103045_12345.jpg",
    "mime_type": "image/jpeg",
    "size": 245760
  },
  "files_saved": ["20250918_103045_12345.jpg"],
  "processing_status": "success"
}
```

### Media Files (`inbox/media/`)
- Original filenames preserved when possible
- Timestamp-based naming for unnamed files
- All file types supported (images, videos, documents, audio, stickers)

## Summary Reports

Every 10 messages, a summary is sent to `+3212629156`:

```
📊 TELEGRAM CAPTURE SUMMARY
Total captured: 150
Recent batch: 10

🎯 UATB (6 messages)
  • Today's picks: Yankees vs Red Sox...
    📎 2 files
  • Late addition: Dodgers +1.5...
  • Weather update for tonight's games...

🎯 Diamond/Chamba (4 messages)
  • Premium lock: Warriors -3.5...
    📎 1 files
  • VIP members exclusive...

⏰ 2025-09-18 10:30:45
```

## Error Handling

### Connection Issues
- Automatic reconnection with exponential backoff
- Maximum 3 retry attempts per connection failure
- Health checks every 5 minutes
- Graceful degradation during network issues

### Authentication Problems
- Clear error messages with resolution steps
- No hanging on authentication failures
- Session validation on startup
- Automatic session refresh when needed

### Media Download Failures
- Individual file failure doesn't stop processing
- Partial success tracking in metadata
- Retry logic for temporary failures
- Error logging for debugging

## Troubleshooting

### Common Issues

**1. "Another instance is running"**
```batch
# Stop any existing instances
STOP_TELEGRAM_PRODUCTION.bat

# Check for stale processes
tasklist | findstr python
```

**2. "Session not authorized"**
```batch
# Re-run authentication
python auth_session_production.py
```

**3. "Connection timeout"**
- Check internet connection
- Verify firewall settings
- Try VPN if blocked

**4. "No channels accessible"**
- Verify account has access to target channels
- Check if account is banned/restricted
- Confirm channel IDs are correct

### Log Analysis
```batch
# View today's logs
notepad logs\telegram_collector_20250918.log

# Monitor real-time
tail -f logs\telegram_collector_20250918.log
```

### Manual Testing
```batch
# Test connection only
python test_telegram_connection.py

# Test specific channel
python -c "
import asyncio
from telegram_production_collector import TelegramCollector
# ... custom test code
"
```

## Performance Considerations

### Resource Usage
- **Memory**: ~50-100MB typical
- **CPU**: Low (event-driven)
- **Disk**: Depends on media volume
- **Network**: Minimal (except media downloads)

### Scaling Limits
- **Messages**: No practical limit
- **Media**: Limited by disk space
- **Channels**: Currently 5 (easily expandable)
- **Concurrent**: Single instance only

### Optimization Tips
- Regular cleanup of old files
- Monitor disk space usage
- Archive old logs periodically
- Consider media compression for long-term storage

## Security Considerations

### Session Protection
- StringSession stored in .env (not in code)
- Session string is encrypted by Telegram
- No plaintext credentials in logs
- Lock file prevents unauthorized access

### File Permissions
- Inbox directory should be protected
- Log files may contain sensitive info
- Media files inherit original permissions
- Environment file should be secured

### Network Security
- All connections use Telegram's encryption
- No custom protocols or servers
- Standard HTTPS/TLS for all communications
- No data transmitted to third parties (except summaries)

## Maintenance

### Daily Tasks
- Check collector status
- Monitor disk space
- Review error logs
- Verify summary delivery

### Weekly Tasks
- Archive old logs
- Clean up old media files
- Update dependencies if needed
- Backup configuration files

### Monthly Tasks
- Review channel access
- Update target channels if needed
- Performance analysis
- Security review

## Support

### Log Files
All issues should include relevant log entries from:
```
logs\telegram_collector_YYYYMMDD.log
```

### Configuration Check
Before reporting issues, run:
```batch
python test_telegram_connection.py
```

### Common Solutions
1. **Restart the service**: `STOP_TELEGRAM_PRODUCTION.bat` → `START_TELEGRAM_PRODUCTION.bat`
2. **Re-authenticate**: `python auth_session_production.py`
3. **Check dependencies**: `pip install -r requirements_production.txt`
4. **Verify permissions**: Ensure account can access target channels

---

## Technical Architecture

### Design Principles
- **Single Responsibility**: One process, one purpose
- **Fail-Safe**: Graceful degradation on errors
- **Observable**: Comprehensive logging and monitoring
- **Recoverable**: Automatic reconnection and retry
- **Maintainable**: Clear code structure and documentation

### Key Components
1. **SingletonLock**: Process-level locking mechanism
2. **TelegramCollector**: Main collection engine
3. **Event Handlers**: Message and media processing
4. **Health Monitor**: Connection and system health
5. **Summary Reporter**: Periodic status updates

This system is designed for 24/7 operation with minimal manual intervention.