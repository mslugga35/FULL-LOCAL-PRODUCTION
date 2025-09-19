#!/bin/bash
echo '===================================='
echo 'RESENDING EXCLUSIVE CAPPERS ONLY'
echo '===================================='
DATE=$(date +%Y%m%d)
cd /root/bots/message_queue
COUNT=0
for file in archived_${DATE}/*exclusive*.json archived_${DATE}/*_17985_*.json; do
  if [ -f "$file" ]; then
    cp "$file" exclusive_cappers/
    COUNT=$((COUNT+1))
  fi
done
echo "Copied $COUNT exclusive messages"
pm2 restart discord-sender
echo 'Check #exclusive-cappers channel in Discord'
