#!/bin/bash
set -euo pipefail

echo "======================================"
echo "Webhook Routing Verification"
echo "======================================"
echo ""

ENV_FILE="/root/bots/.env"
OUT_LOG="/root/.pm2/logs/paid-webhook-out.log"
OCR_LOG="/root/.pm2/logs/ocr-processor-out.log"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[RED] .env not found at $ENV_FILE"
  exit 1
fi

source "$ENV_FILE"

mask() { sed -E 's,(webhooks/[0-9]+)/[A-Za-z0-9_\-]+,\1/REDACTED,g'; }

echo "• Env loaded:"
{ echo "  UATB_WEBHOOK=${UATB_WEBHOOK:-MISSING}"
  echo "  DIAMOND_WEBHOOK=${DIAMOND_WEBHOOK:-MISSING}"
  echo "  UATB_EXPECTED_CHANNEL_ID=${UATB_EXPECTED_CHANNEL_ID:-MISSING}"
  echo "  DIAMOND_EXPECTED_CHANNEL_ID=${DIAMOND_EXPECTED_CHANNEL_ID:-MISSING}"
} | mask

fail=0

check_webhook() {
  local name="$1" url="$2" expected="$3"
  if [[ -z "${url:-}" ]]; then
    echo "[RED] $name webhook missing"
    fail=1; return
  fi
  local chan
  chan=$(curl -s "$url" | jq -r '.channel_id // empty') || true
  local url_masked
  url_masked=$(echo "$url" | mask)
  if [[ -z "$chan" ]]; then
    echo "[RED] $name webhook GET failed → $url_masked"
    fail=1
  elif [[ -n "${expected:-}" && "$chan" != "$expected" ]]; then
    echo "[RED] $name webhook targets channel_id=$chan but expected=$expected → $url_masked"
    fail=1
  else
    echo "[GREEN] $name webhook OK → channel_id=$chan"
  fi
}

echo ""
echo "• Validating webhooks → channel_id..."
check_webhook "UATB"    "${UATB_WEBHOOK:-}"    "${UATB_EXPECTED_CHANNEL_ID:-}"
check_webhook "DIAMOND" "${DIAMOND_WEBHOOK:-}" "${DIAMOND_EXPECTED_CHANNEL_ID:-}"

echo ""
echo "• Folder ownership (ensure only paid-webhook handles these):"
grep -nE "paid_uatb|paid_chamba|paid_diamond" /root/bots/discord_sender.js /root/bots/paid_webhook_sender.js 2>/dev/null || true

echo ""
echo "• Pending queue (should drain over time):"
for f in paid_uatb paid_diamond paid_chamba; do
  c=$(ls -1 /root/bots/message_queue/$f/*.json 2>/dev/null | wc -l | tr -d ' ')
  printf "  %-12s : %s\n" "$f" "$c"
done

echo ""
echo "• Last webhook sends:"
grep -a "\[UATB\] sent\|\[DIAMOND\] sent" "$OUT_LOG" 2>/dev/null | tail -n 10 || echo "  (no recent send lines)"

echo ""
echo "• OCR signal (recent FOUND lines):"
grep -a "\[FOUND\].*TESSERACT\|\[FOUND\].*GCV" "$OCR_LOG" 2>/dev/null | tail -n 10 || echo "  (no recent OCR lines)"

echo ""
if [[ $fail -eq 0 ]]; then
  echo "✅ VERIFIED: webhooks point to the correct channel and logs look healthy."
  exit 0
else
  echo "❌ ACTION NEEDED: see red lines above (fix .env or recreate webhook in the right channel)."
  exit 2
fi
