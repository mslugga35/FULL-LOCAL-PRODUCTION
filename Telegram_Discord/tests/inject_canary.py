import argparse, json, os, shutil, uuid, datetime, sys

# ---- CONFIG: paths (match your pipeline)
BASE = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\Telegram_Discord"
INBOX = os.path.join(BASE, "inbox")

# ---- Channel -> chat_id map (from your docs)
CHANNEL_MAP = {
    "DIAMOND 💎 VIP PACKAGE": -1002470080886,
    "UATB 🌐": -1002177758646,
    "CAPPERS FREE💥": -1002592669126,
    "Cappers leaked ‼️": -1001560546587,
    "Exclusive Cappers 👑": -1002608783933,
}

def now_stamp():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def main():
    parser = argparse.ArgumentParser(description="Inject a canary message into inbox/")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--channel", choices=list(CHANNEL_MAP.keys()),
                   help="Friendly channel name from map")
    g.add_argument("--chat-id", type=int,
                   help="Numeric Telegram chat_id (overrides channel)")
    parser.add_argument("--text", default="[TEST][CANARY] Canary check",
                        help="Text content for the message")
    parser.add_argument("--image", help="Path to an image to attach (optional)")
    parser.add_argument("--message-id", type=int, default=None,
                        help="Optional explicit message_id (default: random)")
    parser.add_argument("--timestamp", default=None,
                        help="Optional timestamp like 20250131_120000 (default: now UTC)")
    args = parser.parse_args()

    os.makedirs(INBOX, exist_ok=True)

    # Determine chat_id
    if args.chat_id is not None:
        chat_id = args.chat_id
        channel_name = None
    else:
        channel_name = args.channel
        chat_id = CHANNEL_MAP[channel_name]

    # Prepare media if provided
    has_media = False
    media_path = None
    if args.image:
        if not os.path.isfile(args.image):
            print(f"[ERROR] Image not found: {args.image}")
            sys.exit(1)
        # Copy into inbox for realism (collector normally downloads there)
        img_ext = os.path.splitext(args.image)[1].lower() or ".jpg"
        copied_name = f"canary_{now_stamp()}_{uuid.uuid4().hex}{img_ext}"
        dst = os.path.join(INBOX, copied_name)
        shutil.copy2(args.image, dst)
        has_media = True
        media_path = dst

    # Build message JSON (mirrors collector output fields your router expects)
    stamp = args.timestamp or now_stamp()
    msg_id = args.message_id or int(uuid.uuid4().int % 10**6)

    payload = {
        "channel": channel_name or "",
        "chat_id": chat_id,
        "message_id": msg_id,
        "message": args.text,
        "has_media": has_media,
        "media_path": media_path,
        "timestamp": stamp
    }

    # Filename pattern like your recovered files
    safe_chan = (channel_name or str(chat_id)).replace(" ", "_").replace(":", "_")
    json_name = f"{stamp}_{safe_chan}_{msg_id}.json"
    json_path = os.path.join(INBOX, json_name)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("[OK] Canary JSON written:")
    print(" ", json_path)
    if has_media:
        print("[OK] Canary image copied:")
        print(" ", media_path)
    print("\nNext:")
    print("  pm2 logs router    --lines 60 --nostream | findstr /i Routed")
    print("  pm2 logs forwarder --lines 80 --nostream | findstr /i \"Sent 429\"")
    print("  dir " + os.path.join(BASE, "message_queue", "unrouted"))
    print("\nExpect: SAVED (collector not used for this canary), Routed, Sent; no files in unrouted/.")

if __name__ == "__main__":
    main()
