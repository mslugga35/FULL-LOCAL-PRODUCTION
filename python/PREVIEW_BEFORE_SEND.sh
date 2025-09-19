#!/bin/bash
# This script processes images and saves preview to file BEFORE sending

TODAY=$(date +%Y%m%d)
PREVIEW_FILE="/root/bots/discord_preview_${TODAY}.txt"

echo "Preview for $(date)" > $PREVIEW_FILE
echo "==========================================" >> $PREVIEW_FILE

for img in /root/inbox/${TODAY}*.jpg; do
  if [ -f "$img" ]; then
    echo "Processing: $(basename $img)" >> $PREVIEW_FILE
    # Process with Google Vision and save preview
    node /root/bots/test_clean_sender.js >> $PREVIEW_FILE 2>&1
  fi
done

echo "" >> $PREVIEW_FILE
echo "Preview saved to: $PREVIEW_FILE"
echo "Review this file BEFORE approving Discord send"
cat $PREVIEW_FILE
