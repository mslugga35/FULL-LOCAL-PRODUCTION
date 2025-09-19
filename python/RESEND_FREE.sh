#!/bin/bash
echo '===================================='
echo 'RESENDING FREE CAPPERS ONLY'
echo '===================================='
DATE=$(date +%Y%m%d)
cd /root/bots/message_queue
COUNT=0
for file in archived_${DATE}/*free*.json archived_${DATE}/*_17849_*.json; do
  if [ -f "$file" ]; then
    cp "$file" free_cappers/
    COUNT=$((COUNT+1))
  fi
done
echo "Copied $COUNT free messages"
pm2 restart discord-sender
echo 'Check #leaks channel in Discord'
