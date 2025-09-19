#!/bin/bash
# Quick bot status checker

echo "=== BOT STATUS CHECK ==="
echo "Date: $(date)"
echo ""

# Check critical bots
BOTS=("discord-sender" "paid-webhook" "message-router" "tg-producer" "ocr-processor")

for bot in "${BOTS[@]}"; do
    status=$(pm2 list | grep "$bot" | awk '{print $10}')
    if [ -z "$status" ]; then
        echo "❌ $bot: NOT RUNNING - Starting..."
        case $bot in
            "message-router")
                pm2 start /root/bots/message_router.js --name message-router
                ;;
            *)
                pm2 restart "$bot" 2>/dev/null || echo "   Failed to restart $bot"
                ;;
        esac
    else
        echo "✅ $bot: $status"
    fi
done

echo ""
echo "=== MESSAGE COUNTS ==="
echo "Inbox: $(ls -1 /root/inbox/*.json 2>/dev/null | wc -l)"
echo "Free: $(ls -1 /root/bots/message_queue/free_cappers/*.json 2>/dev/null | wc -l)"
echo "Leaked: $(ls -1 /root/bots/message_queue/leaked_cappers/*.json 2>/dev/null | wc -l)"
echo "Exclusive: $(ls -1 /root/bots/message_queue/exclusive_cappers/*.json 2>/dev/null | wc -l)"
echo "UATB: $(ls -1 /root/bots/message_queue/paid_uatb/*.json 2>/dev/null | wc -l)"
echo "Diamond: $(ls -1 /root/bots/message_queue/paid_diamond/*.json 2>/dev/null | wc -l)"

echo ""
echo "All bots checked and started if needed!"