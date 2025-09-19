#!/bin/bash
echo '===================================='
echo 'RESENDING PAID DIAMOND/CHAMBA ONLY'
echo '===================================='
DATE=$(date +%Y%m%d)
cd /root/bots/message_queue
COUNT=0
for file in archived_${DATE}/*diamond*.json archived_${DATE}/*chamba*.json archived_${DATE}/*_18078_*.json archived_${DATE}/*_18077_*.json; do
  if [ -f "$file" ]; then
    if [[ "$file" == *"diamond"* ]]; then
      cp "$file" paid_diamond/
      # Copy associated images
      BASE=$(basename "$file" .json)
      [ -f "archived_${DATE}/${BASE}.jpg" ] && cp "archived_${DATE}/${BASE}.jpg" paid_diamond/
      [ -f "archived_${DATE}/${BASE}.png" ] && cp "archived_${DATE}/${BASE}.png" paid_diamond/
    elif [[ "$file" == *"chamba"* ]]; then
      cp "$file" paid_chamba/
      # Copy associated images
      BASE=$(basename "$file" .json)
      [ -f "archived_${DATE}/${BASE}.jpg" ] && cp "archived_${DATE}/${BASE}.jpg" paid_chamba/
      [ -f "archived_${DATE}/${BASE}.png" ] && cp "archived_${DATE}/${BASE}.png" paid_chamba/
    fi
    COUNT=$((COUNT+1))
  fi
done
echo "Copied $COUNT Diamond/Chamba messages (with images)"
pm2 restart discord-sender
echo 'Check Diamond channel in Discord'
