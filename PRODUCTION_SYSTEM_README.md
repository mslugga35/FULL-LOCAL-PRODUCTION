# Telegram to Discord System Controller - Production Setup

## Overview

This is a comprehensive system controller that manages the complete Telegram to Discord pipeline using the updated `routing_config.json` structure. The system provides unified management, monitoring, and automated recovery for both Telegram message collection and Discord forwarding.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  System         │    │  Telegram       │    │  Discord        │
│  Controller     │←→  │  Collector      │    │  Forwarder      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Production     │    │  Message Queue  │    │  Discord API    │
│  Monitor        │    │  System         │    │  Integration    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Features

### 🎛️ System Controller (`system_controller.py`)
- **Unified Process Management**: Manages both Telegram collector and Discord forwarder
- **Health Monitoring**: Continuous health checks with automatic restarts
- **Configuration Integration**: Uses `routing_config.json` for all settings
- **Interactive Control**: Command-line interface for system management
- **Comprehensive Logging**: Detailed logging for all components

### 📡 Telegram Collector (`telegram_collector_updated.py`)
- **Dynamic Configuration**: Reads channel mappings from `routing_config.json`
- **Enhanced Routing**: Routes messages to correct queue directories
- **Media Handling**: Downloads and organizes media files
- **Error Recovery**: Robust error handling and reconnection logic

### 🚀 Discord Forwarder (`discord_forwarder_production.py`)
- **Queue Processing**: Monitors message queues for new content
- **Rate Limiting**: Built-in rate limiting for Discord API compliance
- **Format Integration**: Uses routing metadata for proper message formatting

### 📊 Production Monitor (`production_monitor.py`)
- **Real-time GUI**: Live monitoring dashboard
- **Health Checks**: System resource and process monitoring
- **Auto-restart**: Automatic recovery from failures
- **Log Analysis**: Real-time error detection and alerting

## Configuration Structure

The system uses `routing_config.json` with the following structure:

```json
{
  "version": "1.0",
  "windows_base_path": "C:\\Users\\mpmmo\\message_queue",
  "telegram_channels": {
    "-1002177758646": {
      "name": "UATB",
      "display_name": "🌐 UATB 🌐",
      "queue_path": "paid_uatb",
      "type": "paid",
      "enabled": true
    }
  },
  "discord_forwarder_integration": {
    "enabled": true,
    "message_format": {
      "include_routing_metadata": true
    }
  },
  "queue_management": {
    "create_media_subdirs": true,
    "auto_create_directories": true,
    "processed_folder": "processed",
    "failed_folder": "failed"
  }
}
```

## Quick Start

### 1. Validation
```bash
# Quick validation
QUICK_VALIDATE.bat

# Comprehensive testing
RUN_COMPLETE_SYSTEM_TEST.bat
```

### 2. Start System
```bash
# Start the complete system
START_SYSTEM_CONTROLLER.bat

# Or start with monitoring
START_PRODUCTION_MONITOR.bat
```

### 3. Monitor System
The system controller provides an interactive interface:
```
Commands: status, restart <component>, stop, help
system> status          # Show current status
system> restart telegram_collector  # Restart component
system> stop            # Stop system
```

## File Structure

```
FULL-LOCAL-PRODUCTION/
├── system_controller.py           # Main system controller
├── telegram_collector_updated.py  # Updated Telegram collector
├── discord_forwarder_production.py # Production Discord forwarder
├── production_monitor.py          # GUI monitoring system
├── routing_config.json            # System configuration
├── .env                           # Environment variables
│
├── START_SYSTEM_CONTROLLER.bat    # Main startup script
├── START_PRODUCTION_MONITOR.bat   # Monitor startup
├── RUN_COMPLETE_SYSTEM_TEST.bat   # Comprehensive testing
├── QUICK_VALIDATE.bat             # Quick validation
│
├── test_system_integration.py     # Integration tests
├── validate_config.py             # Configuration validator
│
├── logs/                          # System logs
│   ├── system_controller.log
│   ├── telegram_collector.log
│   ├── discord_forwarder_production.log
│   └── production_monitor.log
│
└── message_queue/                 # Message routing directories
    ├── paid_uatb/
    ├── paid_diamond/
    └── free_cappers/
        ├── cappers_free/
        ├── cappers_leaked/
        └── exclusive_cappers/
```

## Environment Variables

Required in `.env` file:
```env
# Telegram Configuration
TELEGRAM_STRING_SESSION=your_session_string
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token

# Optional
DISCORD_WEBHOOK_URL=your_webhook_url
```

## System Controller Commands

### Interactive Mode
- `status` - Show complete system status
- `restart telegram_collector` - Restart Telegram component
- `restart discord_forwarder` - Restart Discord component
- `stop` - Graceful system shutdown
- `help` - Show available commands

### Status Information
- Process health and resource usage
- Message queue activity
- Error counts and recent issues
- Channel configuration status

## Monitoring Features

### Health Checks
- Process availability monitoring
- Resource usage tracking (CPU, memory, disk)
- Message queue activity detection
- Log file error analysis

### Auto-Recovery
- Automatic process restart on failure
- Rate-limited restart attempts
- Critical error detection and alerting
- System resource threshold monitoring

### GUI Dashboard
- Real-time system status display
- Log file monitoring
- Statistics and performance metrics
- Manual control buttons

## Production Deployment

### 1. Pre-deployment Testing
```bash
# Run all tests
RUN_COMPLETE_SYSTEM_TEST.bat

# Validate configuration
python validate_config.py

# Test individual components
python test_system_integration.py
```

### 2. System Startup
```bash
# Recommended: Start with monitoring
START_PRODUCTION_MONITOR.bat

# Alternative: Direct system start
START_SYSTEM_CONTROLLER.bat
```

### 3. Monitoring and Maintenance
- Monitor GUI dashboard for real-time status
- Check log files regularly for errors
- Review message queue activity
- Monitor system resource usage

## Troubleshooting

### Common Issues

#### System Controller Won't Start
1. Check configuration file: `python validate_config.py`
2. Verify environment variables in `.env`
3. Check Python dependencies: `pip install -r requirements_production.txt`
4. Review logs: `logs/system_controller.log`

#### Telegram Collector Issues
1. Verify session string in environment
2. Check channel access permissions
3. Review Telegram API credentials
4. Check logs: `logs/telegram_collector.log`

#### Discord Forwarder Issues
1. Verify Discord bot token
2. Check webhook URLs (if used)
3. Review message queue permissions
4. Check logs: `logs/discord_forwarder_production.log`

#### Message Queue Problems
1. Verify base path exists and is writable
2. Check directory permissions
3. Review routing configuration
4. Monitor disk space usage

### Log Analysis
- **ERROR** level: Critical issues requiring immediate attention
- **WARNING** level: Issues that may affect operation
- **INFO** level: Normal operational messages

### Performance Optimization
- Monitor memory usage for long-running processes
- Review message processing rates
- Check disk space for message queue storage
- Optimize restart frequency based on error patterns

## API Rate Limits

### Telegram API
- Default flood control handling
- Automatic retry with exponential backoff
- Session persistence for reliability

### Discord API
- Built-in rate limiting (50 requests/second)
- Queue-based message processing
- Webhook fallback for high-volume scenarios

## Security Considerations

- Store credentials in `.env` file only
- Restrict file system permissions for message queue
- Monitor log files for sensitive information exposure
- Regular session string rotation recommended

## Support and Maintenance

### Regular Maintenance Tasks
1. Monitor log file sizes and rotate as needed
2. Check message queue disk usage
3. Review error patterns and adjust configurations
4. Update dependencies periodically

### Backup Considerations
- Back up `routing_config.json` and `.env` files
- Consider message queue backup strategy
- Document custom configuration changes

---

## Quick Reference

### Start System
```bash
START_SYSTEM_CONTROLLER.bat
```

### Monitor System
```bash
START_PRODUCTION_MONITOR.bat
```

### Validate Setup
```bash
QUICK_VALIDATE.bat
```

### Test Everything
```bash
RUN_COMPLETE_SYSTEM_TEST.bat
```

### Emergency Stop
- Press `Ctrl+C` in system controller console
- Or use `stop` command in interactive mode
- GUI monitor: Close window or click stop button

For detailed troubleshooting and advanced configuration, refer to the individual component documentation and log files.