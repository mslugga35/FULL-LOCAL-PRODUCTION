#!/usr/bin/env python3
"""Catch up on missed messages from last 3 hours"""
import os
import sys
import json
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Configuration
INBOX = BASE_DIR / "inbox"
INBOX.mkdir(exist_ok=True)

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

# Channels to catchup (all paid channels)
CHANNELS = [
    -1002470080886,   # Diamond/Hchamba (Paid Picks) - PRIORITY
    -1002177758646,   # UATB (Paid Picks)
    -1002452200409,   # New Paid Channel
    -1002592669126,   # Cappers Free
    -1001560546587,   # Cappers Leaked
    -1002608783933,   # Exclusive Cappers
    -1002337803032,   # SplitThePicks
    -1002601732910,   # New Free Channel
]

async def main():
    print(f"📥 Catching up messages from last 24 hours")
    print(f"Inbox: {INBOX}")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Not authorized!")
            return

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        print(f"⏰ Getting messages since: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        total = 0
        for channel_id in CHANNELS:
            try:
                entity = await client.get_entity(channel_id)
                channel_name = entity.title
                print(f"\n📢 Checking: {channel_name}")

                count = 0
                async for message in client.iter_messages(entity, limit=100):
                    print(f"  DEBUG: msg {message.id} at {message.date} UTC")
                    if message.date < since:
                        print(f"    (too old, skipping)")
                        continue

                    # Create message data
                    msg_data = {
                        "chat_id": channel_id,
                        "channel": channel_name,
                        "message_id": message.id,
                        "text": message.text or "",
                        "date": message.date.isoformat(),
                        "has_media": message.media is not None
                    }

                    # Save to inbox
                    timestamp = message.date.strftime("%H%M%S")
                    filename = f"{channel_id}_{message.id}_{timestamp}.json"
                    filepath = INBOX / filename

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(msg_data, f, indent=2, ensure_ascii=False)

                    count += 1
                    total += 1
                    print(f"  ✅ Message {message.id} - {message.date.strftime('%H:%M:%S')}")

                print(f"  Total: {count} messages")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        print(f"\n✅ Done! Collected {total} messages total")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())