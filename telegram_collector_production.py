#!/usr/bin/env python3
"""
PRODUCTION Telegram Collector - Uses existing session string
Monitors 5 channels and writes messages to inbox
"""
import os
import sys
import asyncio
import json
import time
import pathlib
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime

# Basic logging so you see what's happening
logging.basicConfig(level=logging.INFO)

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# PRODUCTION SESSION STRING (from your working setup)
SESSION_STRING = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="

# Configuration
INBOX = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\inbox"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Channels to monitor (both ID and username)
CHANNELS = [
    -1002592669126,  # Cappers Free
    -1001560546587,  # Cappers Leaked
    -1002608783933,  # Exclusive Cappers
    -1002177758646,  # UATB
    -1002470080886,  # Diamond/Chamba
    "cappersfree",
    "cappersleaked",
    "exclusivecappers",
    "uatb",
    "diamond"
]

# Ensure inbox exists
pathlib.Path(INBOX).mkdir(parents=True, exist_ok=True)

# Initialize client with string session
client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

def save_message(channel_name, text, message_id, has_media=False, media_path=None):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        safe_name = channel_name.replace(" ", "_").replace("/", "_")
        filename = f"{ts}_{safe_name}_{message_id}.json"
        filepath = os.path.join(INBOX, filename)

        payload = {
            "source": "telegram",
            "channel": channel_name,
            "message_id": message_id,
            "text": text,
            "has_media": has_media,
            "media_file": os.path.basename(media_path) if media_path else None,
            "timestamp": datetime.now().isoformat(),
            "created_utc": int(time.time())
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        safe_print(f"[SAVED] {filename}")
        return True
    except Exception as e:
        safe_print(f"[ERROR] Save failed: {e}")
        return False

@client.on(events.NewMessage(chats=CHANNELS))
async def handle_message(event):
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", "Unknown")

        text = event.message.message or ""
        message_id = event.message.id

        preview = text[:80].replace('\n', ' ')
        safe_print(f"\n[NEW] {chat_title}: {preview}...")

        media_path = None
        if event.message.photo or event.message.document:
            try:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                media_file = f"{ts}_{message_id}"
                media_path = os.path.join(INBOX, media_file)
                downloaded = await event.message.download_media(file=media_path)
                if downloaded:
                    safe_print(f"[MEDIA] Downloaded: {os.path.basename(downloaded)}")
                    media_path = downloaded
            except Exception as e:
                safe_print(f"[MEDIA] Download failed: {e}")

        save_message(
            chat_title,
            text,
            message_id,
            has_media=bool(media_path),
            media_path=media_path
        )
    except Exception as e:
        safe_print(f"[ERROR] Handler error: {e}")

async def main():
    safe_print("=" * 60)
    safe_print("TELEGRAM COLLECTOR - PRODUCTION")
    safe_print("=" * 60)
    safe_print(f"Inbox: {INBOX}")
    safe_print(f"Monitoring {len(CHANNELS)} channels/IDs")
    safe_print("=" * 60)

    await client.connect()

    if await client.is_user_authorized():
        safe_print("[OK] Session authorized!")

        me = await client.get_me()
        safe_print(f"User: {me.first_name} (@{me.username})")

        safe_print("\nChannel Access:")
        for ch in [-1002177758646, -1002470080886]:
            try:
                entity = await client.get_entity(ch)
                safe_print(f"  [OK] {entity.title}")
            except:
                safe_print(f"  [FAIL] Channel ID {ch}")

        safe_print("\n[READY] Listening for messages...")
        safe_print("=" * 60)

        await client.run_until_disconnected()
    else:
        safe_print("[ERROR] Session not authorized!")
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\n[STOPPED]")
    except Exception as e:
        safe_print(f"[FATAL] {e}")