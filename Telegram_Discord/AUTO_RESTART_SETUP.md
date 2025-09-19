# Auto-Restart & Auto-Start Setup Guide

## Overview
This pipeline is configured to automatically:
1. **Restart services** if they crash (PM2 auto-restart)
2. **Start on boot** when Windows starts (Task Scheduler)
3. **Monitor and recover** from failures (Watchdog)

## Components Installed

### 1. PM2 Auto-Restart Configuration
**File:** `ecosystem.config.js`
- Services configured with `autorestart: true`
- Max 10 restart attempts
- Exponential backoff on failures
- Memory limit protection (1GB)

### 2. Windows Startup Script
**File:** `start-pipeline.bat`
- Starts all services on system boot
- Waits for system stabilization
- Resurrects saved PM2 processes

### 3. Task Scheduler Integration
**File:** `pipeline-autostart-task.xml`
- Triggers on system boot (30s delay)
- Triggers on user login (10s delay)
- Retries on failure (3 times, 5min interval)

### 4. Watchdog Script
**File:** `watchdog.bat`
- Continuously monitors services
- Restarts stopped services
- Checks every 60 seconds

## Installation Steps

### Step 1: Save PM2 Configuration
```bash
pm2 save --force
```
✅ **Status:** Completed - Configuration saved to `C:\Users\mpmmo\.pm2\dump.pm2`

### Step 2: Install Windows Task Scheduler Task

#### Option A: Automatic Installation (Recommended)
1. Open Command Prompt as **Administrator**
2. Navigate to pipeline directory:
   ```cmd
   cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
   ```
3. Run installation script:
   ```cmd
   install-autostart.bat
   ```

#### Option B: Manual Installation
1. Open Task Scheduler (`Win + R`, type `taskschd.msc`)
2. Click "Import Task" in Actions panel
3. Select `pipeline-autostart-task.xml`
4. Click OK

### Step 3: Test Auto-Start
```cmd
schtasks /run /tn "TelegramDiscordPipeline"
```

## Verification Commands

### Check Task Scheduler Status
```cmd
schtasks /query /tn "TelegramDiscordPipeline" /v
```

### Check PM2 Services
```bash
pm2 list
pm2 show tg-collector
pm2 show router
pm2 show forwarder
```

### Monitor Auto-Restart
```bash
# Watch restart counter
pm2 describe tg-collector | grep restart

# Monitor logs for crashes
pm2 logs --lines 50
```

## Service Recovery Behavior

### When a Service Crashes
1. PM2 immediately attempts restart
2. Uses exponential backoff (100ms → 200ms → 400ms...)
3. Maximum 10 restart attempts
4. If max reached, service stops

### When Windows Restarts
1. Task Scheduler waits 30 seconds
2. Runs `start-pipeline.bat`
3. PM2 resurrects saved processes
4. Services start automatically

### When PM2 Daemon Dies
1. Watchdog detects within 60 seconds
2. Resurrects PM2 daemon
3. Restarts all services

## Manual Controls

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

### Disable Auto-Start
```cmd
schtasks /change /tn "TelegramDiscordPipeline" /disable
```

### Enable Auto-Start
```cmd
schtasks /change /tn "TelegramDiscordPipeline" /enable
```

### Remove Auto-Start Completely
```cmd
schtasks /delete /tn "TelegramDiscordPipeline" /f
```

## Troubleshooting

### Services Not Starting on Boot
1. Check Task Scheduler:
   ```cmd
   schtasks /query /tn "TelegramDiscordPipeline"
   ```
2. Check Task History in Task Scheduler GUI
3. Review startup log:
   ```cmd
   type C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\startup.log
   ```

### Services Keep Crashing
1. Check error logs:
   ```bash
   pm2 logs --err --lines 100
   ```
2. Check restart count:
   ```bash
   pm2 describe [service-name] | grep restart
   ```
3. Reset restart counter:
   ```bash
   pm2 reset [service-name]
   ```

### PM2 Not Found After Reboot
1. Ensure Node.js is in system PATH
2. Reinstall PM2 globally:
   ```bash
   npm install -g pm2
   ```

## Monitoring Dashboard

### Real-time Monitoring
```bash
pm2 monit
```

### Web Dashboard (Optional)
```bash
pm2 plus
```

## Log Locations

- **PM2 Logs:** `C:\Users\mpmmo\.pm2\logs\`
- **Startup Log:** `C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord\startup.log`
- **Task Scheduler Logs:** Event Viewer → Windows Logs → System

## Best Practices

1. **Regular Monitoring**
   - Check `pm2 list` daily
   - Review logs weekly
   - Monitor restart counts

2. **Maintenance**
   - Clear old logs monthly: `pm2 flush`
   - Update PM2 quarterly: `npm update -g pm2`
   - Test auto-start after Windows updates

3. **Backup**
   - Keep copy of `ecosystem.config.js`
   - Export Task Scheduler task regularly
   - Document any configuration changes

## Emergency Recovery

If everything fails:
```bash
# Kill all PM2 processes
pm2 kill

# Clear PM2 data
rm -rf ~/.pm2

# Reinstall PM2
npm install -g pm2

# Start fresh
cd C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord
pm2 start ecosystem.config.js
pm2 save
```

## Status Summary

✅ **PM2 Auto-Restart:** Configured and Active
✅ **Windows Auto-Start:** Task Scheduler ready (run `install-autostart.bat` as Admin)
✅ **Watchdog Monitoring:** Script available
✅ **Process Persistence:** Saved to PM2 dump
✅ **Recovery Scripts:** All created and ready

The pipeline is now configured for maximum uptime with automatic recovery from:
- Process crashes
- System reboots
- PM2 daemon failures
- Unexpected shutdowns

---
*Last Updated: September 18, 2025*
*Auto-restart configured with PM2 v5.3.0*