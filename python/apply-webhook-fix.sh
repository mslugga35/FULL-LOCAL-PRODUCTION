#!/bin/bash
set -euo pipefail

echo "🚀 Applying UATB/Diamond webhook fix…"
ENV_FILE="/root/bots/.env"
PAID="/root/bots/paid_webhook_sender.js"
SENDER="/root/bots/discord_sender.js"

# 1) Ensure .env contains your values (only appends if keys missing)
ensure_kv () {
  local key="$1" val="$2"
  grep -q "^${key}=" "$ENV_FILE" 2>/dev/null || echo "${key}=${val}" >> "$ENV_FILE"
}

touch "$ENV_FILE"
chmod 640 "$ENV_FILE"

ensure_kv "TARGET_GUILD_ID" "675908407617650697"
ensure_kv "UATB_EXPECTED_CHANNEL_ID" "1403837637730762875"
ensure_kv "DIAMOND_EXPECTED_CHANNEL_ID" "1403837637730762875"

# NOTE: keep the full URLs; do NOT redact in the file
ensure_kv "UATB_WEBHOOK" "https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN"
ensure_kv "DIAMOND_WEBHOOK" "https://discord.com/api/webhooks/1403837691807924294/_wwVsXOAldM4mPDxltGipB0eYYNBlkDZJzG0x6jWEbwSiGUeuUOfI3Y858YY9MYEQ8GN"

# 2) Quick validate webhooks (prints channel_id)
source "$ENV_FILE"
echo "→ Validating webhooks (should return channel_id=1403837637730762875)…"
for w in "$UATB_WEBHOOK" "$DIAMOND_WEBHOOK"; do
  curl -s "$w" | jq .id,.channel_id
done

# 3) Restart paid-webhook
pm2 restart paid-webhook --update-env 2>/dev/null || echo "paid-webhook not running yet"
sleep 3

# 4) Optional: ensure discord_sender.js does NOT process paid_* (comment out if you want bot path)
if grep -q "paid_uatb" "$SENDER" 2>/dev/null; then
  cp "$SENDER" "$SENDER.backup.$(date +%s)" || true
  # remove folders from scan array if present (best-effort)
  sed -i 's/"paid_uatb"//g; s/'"'"'paid_uatb'"'"'//g; s/"paid_diamond"//g; s/'"'"'paid_diamond'"'"'//g; s/"paid_chamba"//g; s/'"'"'paid_chamba'"'"'//g' "$SENDER" || true
  pm2 restart discord-sender || true
fi

# 5) Proof lines
echo "=== PROOF (paid-webhook logs) ==="
pm2 logs paid-webhook --lines 120 --nostream 2>/dev/null | tail -n 20 | sed 's/\(webhooks\/[0-9]\+\/\)[A-Za-z0-9_\-]\{20,\}/\1REDACTED/g' || echo "No paid-webhook logs yet"

echo "✅ Done."
