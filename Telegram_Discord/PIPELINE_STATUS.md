# Telegram-Discord Pipeline Status

## Current Status: ✅ OPERATIONAL

**All systems functioning normally - messages flowing smoothly**

### Last Updated: September 19, 2025 08:13 AM

## System Overview

### 🟢 Services Running
- **tg-collector**: Collecting from Telegram
- **router**: Routing messages to queues
- **forwarder**: Sending to Discord channels
- **discord_to_discord_forwarder_leaks**: Cross-Discord forwarding

### 📊 Queue Status
| Queue | Pending | Status |
|-------|---------|--------|
| paid_uatb | 0 | ✅ Clear |
| paid_diamond | 0 | ✅ Clear |
| free_cappers | 0 | ✅ Clear |
| cappers_leaked | 0 | ✅ Clear |
| exclusive_cappers | 0 | ✅ Clear |

## Recent Changes & Fixes

### What Was Changed
1. **Switched from Webhook to Bot Transport for Paid Channels**
   - Previously: Used webhooks which got severely rate limited
   - Now: Using bot API with same token for all channels
   - Result: More reliable delivery, better rate limit handling

2. **Implemented Per-Queue Rate Limiting**
   - Each queue has independent cooldowns
   - One rate-limited queue won't block others
   - 30-second cooldowns instead of 12+ hour blocks

### Configuration Changes

#### discord_targets.yaml
```yaml
# OLD (webhook-based):
paid_uatb:
  transport: webhook
  webhook_env: DISCORD_WEBHOOK_PAID

# NEW (bot-based):
paid_uatb:
  transport: bot
  channel_id: 1403837637730762875

paid_diamond:
  transport: bot
  channel_id: 1403837637730762875
```

#### settings.yaml - Rate Limiting
```yaml
forwarder:
  per_queue_min_interval_seconds:
    paid_uatb: 0.6          # Minimum 0.6s between messages
    paid_diamond: 0.6       # Minimum 0.6s between messages
    free_cappers: 0.3       # Minimum 0.3s between messages
    default: 0.5            # Default for other queues
  on_429_cooldown_seconds: 30   # Cool down for 30s on rate limit
  max_retry_after_seconds: 60   # Cap Discord's retry-after to 60s
```

## How It Works Now

### Message Flow
1. **Telegram Collection** → Messages collected from Telegram channels
2. **Routing** → Messages routed to appropriate queues based on chat
3. **OCR Processing** → Free queues get OCR text extraction (no images sent)
4. **Discord Forwarding** → Bot API sends to Discord channels
5. **Rate Management** → Per-queue throttling prevents overload

### Transport Methods
| Queue Type | Transport | Method | Channel |
|------------|-----------|--------|---------|
| Paid (UATB, Diamond) | Bot API | Text + Images | 1403837637730762875 |
| Free (Cappers) | Bot API | OCR Text Only | 1403894557615325216 |
| Leaks | Bot API | Text + Images | 1403894596186017962 |
| Exclusive | Bot API | Text + Images | 1403894653660692500 |

### Rate Limit Handling
- **Per-Queue Cooldowns**: Each queue tracks its own rate limits
- **Smart Backoff**: 30-second cooldowns on 429 errors
- **Non-Blocking**: One queue's rate limit doesn't affect others
- **Auto-Recovery**: Automatically resumes after cooldown

## Key Features

### ✅ Working
- Telegram message collection
- Message routing by chat
- OCR for free_cappers queue
- Discord forwarding via bot API
- Per-queue rate limiting
- Automatic error recovery
- Message archiving

### 🔧 Configuration
- **Bot Token**: `DISCORD_BOT_TOKEN_FREE` (single bot for all)
- **Paid Channel**: 1403837637730762875
- **Free Channel**: 1403894557615325216
- **OCR Enabled**: Only for free_cappers queue

## Monitoring Commands

```bash
# Check service status
pm2 status

# View recent logs
pm2 logs forwarder --lines 50

# Check queue sizes
for dir in /c/Users/mpmmo/FULL-LOCAL-PRODUCTION/Telegram_Discord/message_queue/*/; do
  echo "$(basename $dir): $(ls $dir/*.json 2>/dev/null | wc -l)"
done

# Watch for sent messages
pm2 logs forwarder --lines 100 | grep "Sent"

# Check for errors
pm2 logs forwarder --lines 100 | grep -E "ERROR|Failed"
```

## Troubleshooting

### If Messages Stop Flowing
1. Check PM2 status: `pm2 status`
2. Check for rate limits: `pm2 logs forwarder | grep "Rate limit"`
3. Verify bot token: `grep DISCORD_BOT_TOKEN_FREE .env`
4. Test bot manually: Use the test script in docs

### Common Issues & Fixes
| Issue | Cause | Solution |
|-------|-------|----------|
| 429 Rate Limits | Too many requests | Wait 30s (auto-recovery) |
| 403 Forbidden | Bot missing permissions | Re-invite bot to server |
| Cloudflare Block | IP-level rate limit | Wait 6-24 hours or use VPN |
| Messages Stuck | Service crashed | `pm2 restart forwarder` |

## Summary

The pipeline is now fully operational using **bot transport** for all channels instead of webhooks. This provides:
- ✅ Better rate limit handling
- ✅ Faster recovery from 429 errors
- ✅ More reliable message delivery
- ✅ Single bot token for all channels

The key change was switching from webhook transport (which got severely rate limited) to bot API transport with proper per-queue rate limiting. Messages now flow smoothly with automatic 30-second cooldowns when hitting rate limits instead of 12+ hour blocks.

---
*Generated: September 19, 2025 08:13 AM*
*Pipeline Version: 2.0 (Bot Transport)*
*Status: Fully Operational*