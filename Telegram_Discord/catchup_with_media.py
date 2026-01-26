#!/usr/bin/env python3
"""Catch up on missed messages with MEDIA DOWNLOAD"""
import os
import sys
import json
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
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

# Channels to catchup
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

# Parse hours from command line
HOURS = int(sys.argv[1]) if len(sys.argv) > 1 else 5


async def download_media(client, message, inbox_dir):
    """Download media from message"""
    if not message.media:
        return None

    try:
        # Create filename based on message
        timestamp = message.date.strftime("%H%M%S")

        if isinstance(message.media, MessageMediaPhoto):
            ext = "jpg"
        elif isinstance(message.media, MessageMediaDocument):
            # Try to get extension from document attributes
            ext = "bin"
            if hasattr(message.media.document, 'mime_type'):
                mime = message.media.document.mime_type
                if 'jpeg' in mime or 'jpg' in mime:
                    ext = "jpg"
                elif 'png' in mime:
                    ext = "png"
                elif 'gif' in mime:
                    ext = "gif"
                elif 'mp4' in mime or 'video' in mime:
                    ext = "mp4"
        else:
            ext = "bin"

        filename = f"{message.chat_id}_{message.id}_{timestamp}.{ext}"
        filepath = inbox_dir / filename

        # Download
        await client.download_media(message, file=str(filepath))
        return str(filepath)

    except Exception as e:
        print(f"    Media download error: {e}")
        return None


async def main():
    print(f"📥 Catching up messages from last {HOURS} hours (WITH MEDIA)")
    print(f"Inbox: {INBOX}")

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Not authorized!")
            return

        since = datetime.now(timezone.utc) - timedelta(hours=HOURS)
        print(f"⏰ Getting messages since: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        total = 0
        for channel_id in CHANNELS:
            try:
                entity = await client.get_entity(channel_id)
                channel_name = entity.title
                print(f"\n📢 Checking: {channel_name}")

                count = 0
                async for message in client.iter_messages(entity, limit=100):
                    if message.date < since:
                        break  # Messages are in reverse chronological order

                    # Determine media type
                    media_type = "text"
                    media_path = None

                    if isinstance(message.media, MessageMediaPhoto):
                        media_type = "photo"
                    elif isinstance(message.media, MessageMediaDocument):
                        media_type = "document"
                    elif message.media:
                        media_type = "other_media"

                    # Download media if present
                    if message.media:
                        print(f"  📷 Downloading media for msg {message.id}...")
                        media_path = await download_media(client, message, INBOX)

                    # Create message data (matching collector format)
                    msg_data = {
                        "id": message.id,
                        "chat_id": channel_id,
                        "chat_title": channel_name,
                        "sender_id": message.sender_id,
                        "type": media_type,
                        "text": message.text or "",
                        "media_path": media_path,
                        "ts_iso": message.date.isoformat(),
                        "has_media": message.media is not None,
                    }

                    # Save to inbox
                    timestamp = message.date.strftime("%H%M%S")
                    filename = f"{channel_id}_{message.id}_{timestamp}.json"
                    filepath = INBOX / filename

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(msg_data, f, indent=2, ensure_ascii=False)

                    count += 1
                    total += 1
                    status = "📷" if media_path else "📝"
                    print(f"  {status} Message {message.id} - {message.date.strftime('%H:%M:%S')}")

                print(f"  Total: {count} messages")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        print(f"\n✅ Done! Collected {total} messages total (with media)")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
