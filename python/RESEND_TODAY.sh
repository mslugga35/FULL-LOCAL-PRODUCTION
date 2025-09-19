#!/bin/bash
echo '===================================='
echo 'RESENDING ALL TODAY MESSAGES'
echo '===================================='

# Get today's date
DATE=20250916
ARCHIVE_DIR="/root/bots/message_queue/archived_${DATE}"

echo "Processing messages from: $ARCHIVE_DIR"

# Count messages
TOTAL=0
echo "Found $TOTAL messages from today"

# Copy all messages back to their queues
echo "Copying messages back to queues..."
cd /root/bots/message_queue

for file in archived_${DATE}/*.json; do
  if [ -f "$file" ]; then
    # Determine which queue based on filename
    if [[ "$file" == *"free_cappers"* ]]; then
      cp "$file" free_cappers/
    elif [[ "$file" == *"leaked_cappers"* ]]; then
      cp "$file" leaked_cappers/
    elif [[ "$file" == *"exclusive_cappers"* ]]; then
      cp "$file" exclusive_cappers/
    elif [[ "$file" == *"paid_uatb"* ]]; then
      cp "$file" paid_uatb/
    elif [[ "$file" == *"paid_diamond"* ]]; then
      cp "$file" paid_diamond/
    elif [[ "$file" == *"paid_chamba"* ]]; then
      cp "$file" paid_chamba/
    else
      # Default to free if can't determine
      cp "$file" free_cappers/
    fi
  fi
done

echo "Messages queued for processing!"

# Restart Discord sender to process immediately
echo "Restarting Discord sender..."
pm2 restart discord-sender

echo '===================================='
echo 'RESEND INITIATED!'
echo 'Check Discord channels in 1-2 minutes'
echo '===================================='
