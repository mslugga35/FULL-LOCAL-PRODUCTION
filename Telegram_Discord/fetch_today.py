#!/usr/bin/env python
"""
Fetch all messages from today from monitored Telegram channels
"""
import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load environment
load_dotenv()

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION = os.getenv("TELEGRAM_SESSION")

# Channels to fetch from
CHANNELS = {
    -1002177758646: "UATB",
    -1002470080886: "Diamond/Chamba",
    -1002592669126: "Cappers Free",
    -1001560546587: "Cappers Leaked",
    -1002608783933: "Exclusive Cappers"
}

# Output directory
INBOX_DIR = Path("C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\Telegram_Discord\\inbox")
INBOX_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_today_messages():
    """Fetch all messages from today"""
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

    await client.start()
    print("Connected to Telegram")

    # Get today's date at midnight UTC
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_messages = 0

    for channel_id, channel_name in CHANNELS.items():
        print(f"\nFetching from {channel_name} ({channel_id})...")

        try:
            # Get entity
            entity = await client.get_entity(channel_id)

            # Fetch messages from today
            messages = []
            async for message in client.iter_messages(entity, offset_date=datetime.now(timezone.utc), reverse=False):
                # Check if message is from today
                if message.date < today:
                    break
                messages.append(message)

            print(f"  Found {len(messages)} messages from today")

            # Save each message
            for msg in messages:
                # Create message data
                msg_data = {
                    "id": msg.id,
                    "chat_id": channel_id,
                    "chat_title": channel_name,
                    "sender_id": msg.sender_id,
                    "type": "text",
                    "text": msg.message or "",
                    "media_path": None,
                    "ts_iso": msg.date.isoformat() + "Z",
                    "has_media": bool(msg.media),
                    "raw": msg.to_dict()
                }

                # Save to inbox
                filename = f"{channel_id}_{msg.id}_{datetime.now().strftime('%H%M%S')}.json"
                filepath = INBOX_DIR / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(msg_data, f, ensure_ascii=False, indent=2, default=str)

                print(f"    Saved: {filename}")
                total_messages += 1

                # Download media if present
                if msg.media and msg.photo:
                    try:
                        media_dir = INBOX_DIR / "media" / datetime.now().strftime("%Y%m%d")
                        media_dir.mkdir(parents=True, exist_ok=True)

                        media_path = await client.download_media(
                            msg.media,
                            file=str(media_dir / f"{channel_id}_{msg.id}")
                        )

                        if media_path:
                            # Update message data with media path
                            msg_data["media_path"] = media_path
                            msg_data["type"] = "photo"

                            with open(filepath, 'w', encoding='utf-8') as f:
                                json.dump(msg_data, f, ensure_ascii=False, indent=2, default=str)

                            print(f"      Downloaded media: {Path(media_path).name}")
                    except Exception as e:
                        print(f"      Failed to download media: {e}")

        except Exception as e:
            print(f"  Error fetching from {channel_name}: {e}")

    print(f"\n{'='*50}")
    print(f"Total messages fetched: {total_messages}")
    print(f"Messages saved to: {INBOX_DIR}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(fetch_today_messages())