#!/bin/bash
echo '===================================='
echo 'RESENDING PAID UATB ONLY'
echo '===================================='
DATE=$(date +%Y%m%d)
cd /root/bots/message_queue
COUNT=0
for file in archived_${DATE}/*uatb*.json archived_${DATE}/*_18076_*.json; do
  if [ -f "$file" ]; then
    cp "$file" paid_uatb/
    # Also copy any associated images
    BASE=$(basename "$file" .json)
    if [ -f "archived_${DATE}/${BASE}.jpg" ]; then
      cp "archived_${DATE}/${BASE}.jpg" paid_uatb/
    fi
    if [ -f "archived_${DATE}/${BASE}.png" ]; then
      cp "archived_${DATE}/${BASE}.png" paid_uatb/
    fi
    COUNT=$((COUNT+1))
  fi
done
echo "Copied $COUNT UATB messages (with images)"
pm2 restart discord-sender
echo 'Check UATB/Diamond channel in Discord'
