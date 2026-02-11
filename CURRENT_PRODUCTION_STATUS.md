# FULL-LOCAL-PRODUCTION — Current Status
> Last Updated: 2026-02-11

## Architecture
Telegram → Discord relay system running locally via PM2. Isolated from Supabase.

## PM2 Services

| Service | Script | Purpose |
|---------|--------|---------|
| tg-collector | src/telegram_collector.py | Polls 8 Telegram channels, saves to inbox/ |
| router | src/router.py | Routes messages from inbox to message_queue/{channel}/ |
| forwarder | src/forwarder.py | Sends to Discord via bot/webhook, deduplicates, archives |

## Data Flow
```
Telegram Channels (8) → tg-collector → inbox/
→ router → message_queue/{channel}/
→ forwarder → Discord + sent_archive/
→ export_to_gdocs.py → Google Doc (free picks only)
```

## Additional Features
- **Smart Recap Filter:** Filters out result/recap posts (checkmarks, scores)
- **Google Docs Export:** Free picks exported to shared Google Doc for n8n consumption
- **Consensus Pipeline:** Detects multi-capper agreement (consensus_scheduler.py)
- **Vision Service:** OCR processing via OpenAI Vision (free_cappers only)

## Config Files
- `config/discord_targets.yaml` — Discord channel targets
- `config/settings.yaml` — OCR settings, paths, forwarder behavior
- `config/channel_routing_map.py` — Telegram → queue routing
- `.env` — API keys (Telegram, Discord, Google)

## Startup
```bash
cd Telegram_Discord
pm2 start ecosystem.config.js
pm2 save
```
