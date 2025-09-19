#\!/bin/bash
# Send today's picks to Discord to show improved OCR

echo "==========================================="
echo "SENDING TODAY'S PICKS TO DISCORD"
echo "==========================================="

TODAY=$(date +%Y%m%d)
echo "Looking for today's messages: $TODAY"

# Find all today's messages in inbox
INBOX_COUNT=$(find /root/inbox -name "${TODAY}_*.jpg" 2>/dev/null | wc -l)
echo "Found $INBOX_COUNT images in inbox from today"

# Process them through the router
if [ $INBOX_COUNT -gt 0 ]; then
    echo "Processing inbox images..."
    cd /root/bots && node message_router.js
fi

# Check queue folders for today's messages
echo ""
echo "Checking queue folders..."
for folder in free_cappers leaked_cappers exclusive_cappers paid_uatb paid_diamond; do
    COUNT=$(find /root/bots/message_queue/$folder -name "${TODAY}_*.json" 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        echo "  $folder: $COUNT messages"
    fi
done

# Trigger Discord sender
echo ""
echo "Triggering Discord sender..."
pm2 restart discord-sender

# Also restart the OCR cleaner to process any messages
pm2 restart ocr-cleaner

echo ""
echo "Messages are being sent to Discord\!"
echo "Check the Discord channels for improved OCR text"
