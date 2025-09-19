#!/bin/bash
echo '===================================='
echo 'RESENDING LEAKED CAPPERS ONLY'
echo '===================================='
DATE=$(date +%Y%m%d)
cd /root/bots/message_queue
COUNT=0
for file in archived_${DATE}/*leaked*.json archived_${DATE}/*_17848_*.json; do
  if [ -f "$file" ]; then
    cp "$file" leaked_cappers/
    COUNT=$((COUNT+1))
  fi
done
echo "Copied $COUNT leaked messages"
pm2 restart discord-sender
echo 'Check #cappers-leaked channel in Discord'
