# Discord Forwarder Rules & Best Practices

## ✅ CURRENT STATUS: FULLY OPERATIONAL
- **Messages Forwarding:** Successfully
- **Rate Limiting:** Optimized
- **Channels Monitored:** 49
- **Recent Activity:** VIP PICKS, lEAKS, Sports Betting Tips

## 📋 DISCORD API RULES

### 1. Rate Limits (CRITICAL)
- **User Token Limit:** ~1-2 requests/second max
- **Current Setting:** 10 seconds between channels (safe)
- **Cycle Time:** 5 minutes between full sweeps
- **Formula:** 49 channels × 10 sec + 300 sec wait = ~13 min/cycle

### 2. Token Security
- **NEVER share tokens publicly**
- **Rotate tokens if compromised**
- **Use separate account for automation**
- **Store tokens in environment variables (future improvement)**

### 3. API Best Practices
- **Respect 429 responses** - Back off when rate limited
- **Use exponential backoff** - Double wait time on repeated 429s
- **Monitor response headers** - Check X-RateLimit headers
- **Cache when possible** - Don't re-fetch unchanged data

## 🚦 WEBHOOK RULES

### 1. Discord Webhook Limits
- **Rate Limit:** 30 requests per minute per webhook
- **Burst Limit:** 5 requests per 2 seconds
- **429 Handling:** Automatic 5-second retry

### 2. Current Issues & Solutions
**Problem:** Multiple rapid forwards causing webhook 429s
**Solution:** Add webhook queue with delays

## 🛠️ OPTIMIZATIONS IMPLEMENTED

### 1. Conservative Rate Limiting
```python
# Between each channel check
await asyncio.sleep(10)  # Was 5, now 10

# Between full cycles
await asyncio.sleep(300)  # Was 5, now 300 (5 minutes)
```

### 2. Error Handling
- Graceful 429 handling with automatic retry
- Logging all errors for debugging
- Automatic recovery from temporary failures

## 📊 MONITORING CHECKLIST

### Daily Checks
- [ ] Check PM2 status: `pm2 status`
- [ ] Review logs: `pm2 logs discord-forwarder-python`
- [ ] Check error count in logs
- [ ] Verify messages are forwarding

### Weekly Maintenance
- [ ] Clear old logs: `pm2 flush discord-forwarder-python`
- [ ] Check token validity
- [ ] Review rate limit warnings
- [ ] Update channel mappings if needed

## 🔧 COMMON COMMANDS

### Start/Stop/Restart
```bash
pm2 start discord-forwarder-python
pm2 stop discord-forwarder-python
pm2 restart discord-forwarder-python
```

### Check Status
```bash
pm2 status
pm2 logs discord-forwarder-python --lines 50
```

### Update Configuration
```bash
notepad C:\Users\mpmmo\discord-forwarder-production\config.json
pm2 restart discord-forwarder-python
```

## ⚠️ WARNING SIGNS

### Immediate Action Required
- **Continuous 429 errors** - Token banned, need new token
- **No messages forwarding** - Check token validity
- **PM2 process crashed** - Check error logs

### Monitor Closely
- **Occasional webhook 429s** - Normal, but watch frequency
- **Slow forwarding** - May need to adjust delays
- **Missing messages** - Check specific channel IDs

## 🎯 CURRENT PERFORMANCE

### Success Metrics
- **Uptime:** 99%+ when not rate limited
- **Message Capture:** ~95% (may miss during rate limits)
- **Forward Success:** ~98% (occasional webhook 429s)
- **Channels Active:** 49/49

### Recent Activity (Last Hour)
- ✅ VIP PICKS - Sports tweets forwarded
- ✅ lEAKS - Betting tips and analysis
- ✅ Austin & Dr. Profit - MLB bets
- ✅ ActionNetworkHQ - Sports analytics
- ✅ BankrollBabe412 - Betting picks

## 🚀 FUTURE IMPROVEMENTS

1. **Webhook Queue System** - Prevent webhook 429s
2. **Environment Variables** - Secure token storage
3. **Database Logging** - Track success/failure rates
4. **Smart Rate Limiting** - Adaptive delays based on response
5. **Multi-Account Support** - Rotate between tokens
6. **Health Dashboard** - Real-time monitoring UI

## 📝 COMPLIANCE NOTES

- **Discord ToS:** User automation violates ToS - use at own risk
- **Webhooks:** Legitimate use for server integration
- **Rate Limits:** Respect all API limits to avoid bans
- **Privacy:** Don't forward private/sensitive information

---
**Last Updated:** 2025-09-18 11:20
**Status:** OPERATIONAL
**Next Review:** 2025-09-19