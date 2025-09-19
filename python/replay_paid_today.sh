#!/bin/bash
set -euo pipefail

SINCE="today 00:00"
QUEUES=(/root/bots/message_queue/paid_uatb /root/bots/message_queue/paid_diamond /root/bots/message_queue/paid_chamba)

replay_for_queue() {
  local Q="$1"
  mkdir -p "$Q"
  cd "$Q"

  # Find most recent image or media
  local LAST_IMG
  LAST_IMG=$(find . -maxdepth 1 -type f \( -name "*_media.*" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" -o -name "*.gif" \) -newermt "$SINCE" 2>/dev/null | sort | tail -1 || true)
  
  local LAST_ANY=""
  if [ -z "$LAST_IMG" ]; then
    LAST_ANY=$(find . -maxdepth 1 -type f \( -name "*_media.*" -o -name "*.mp4" -o -name "*.mov" \) -newermt "$SINCE" 2>/dev/null | sort | tail -1 || true)
  fi

  local PICK="${LAST_IMG:-$LAST_ANY}"
  if [ -z "$PICK" ]; then
    echo "[SKIP] ${Q##*/}: no media found since $SINCE"
    return 0
  fi

  # Build matching JSON
  local BASE FILE
  FILE=$(basename "$PICK")
  BASE=${FILE%.*}
  BASE=${BASE%_media*}

  # Create JSON
  cat > "$BASE.json" <<JSON
{ "caption": "INLINE TEST: replaying from ${Q##*/}", "has_media": true }
JSON

  ls -l "$BASE".*
  echo "[QUEUED] ${Q##*/}: $BASE.json with $FILE"
}

for Q in "${QUEUES[@]}"; do
  replay_for_queue "$Q"
done

echo ""
echo "Run: pm2 logs paid-webhook -f"
