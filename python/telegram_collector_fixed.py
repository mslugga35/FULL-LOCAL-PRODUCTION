#!/usr/bin/env python3
"""
Enhanced Telegram Producer - Monitors channels by both ID and username
Handles Windows encoding issues and provides robust error handling
"""

import os
import sys
import asyncio
import json
import time
import pathlib
import platform
from telethon import TelegramClient, events
from datetime import datetime

# Force UTF-8 encoding for Windows
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration - Windows paths
INBOX = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\inbox"
session_file = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\telegram_session"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Monitor channels by BOTH ID and username for redundancy
CHANNELS_BY_ID = {
    -1002592669126: {"name": "Cappers Free", "username": "cappersfree"},
    -1001560546587: {"name": "Cappers Leaked", "username": "cappersleaked"},
    -1002608783933: {"name": "Exclusive Cappers", "username": "exclusivecappers"},
    -1002177758646: {"name": "UATB", "username": "uatb"},
    -1002470080886: {"name": "Diamond/Chamba", "username": "diamond"},
}

# Also monitor by username as fallback
CHANNELS_BY_USERNAME = [
    "cappersfree",
    "cappersleaked",
    "exclusivecappers",
    "uatb",
    "diamond"
]

# Combined list for event handler
ALL_CHANNELS = list(CHANNELS_BY_ID.keys()) + CHANNELS_BY_USERNAME

# Ensure directories exist
pathlib.Path(INBOX).mkdir(parents=True, exist_ok=True)
pathlib.Path(os.path.dirname(session_file)).mkdir(parents=True, exist_ok=True)

# Initialize client
client = TelegramClient(session_file, api_id, api_hash)

def safe_print(message):
    """Print with fallback for Windows encoding issues"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII representation
        safe_msg = message.encode('ascii', 'replace').decode('ascii')
        print(safe_msg)

def save_to_inbox(payload, media_path=None):
    """Save message to inbox for Discord bots to consume"""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]  # Include microseconds
        msg_id = payload.get("message_id", int(time.time() * 1000000))
        channel_name = payload.get("chat_title", "unknown").replace(" ", "_").replace("/", "_")
        key = f"{ts}_{channel_name}_{msg_id}"
        json_path = os.path.join(INBOX, f"{key}.json")

        # Add media reference if exists
        if media_path:
            payload["media_file"] = os.path.basename(media_path)

        # Add timestamp for tracking
        payload["saved_at"] = datetime.now().isoformat()

        # Write JSON metadata
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        safe_print(f"[SAVED] {json_path}")
        return json_path
    except Exception as e:
        safe_print(f"[ERROR] Failed to save message: {e}")
        return None

@client.on(events.NewMessage(chats=ALL_CHANNELS))
async def handle_new_message(event):
    """Handle new messages from monitored channels"""
    try:
        # Get chat info
        chat = await event.get_chat()
        chat_id = chat.id if chat else None
        chat_title = getattr(chat, "title", str(chat_id))
        chat_username = getattr(chat, "username", "")

        # Try to match with our known channels
        channel_info = CHANNELS_BY_ID.get(chat_id, {})
        if channel_info:
            channel_display = channel_info.get("name", chat_title)
        else:
            channel_display = chat_title

        # Get message info
        text = event.message.message or ""
        message_id = event.message.id

        # Safe print for Windows
        preview = text[:100].replace('\n', ' ')
        safe_print(f"\n[NEW MSG] {channel_display}: {preview}...")

        # Download media if exists
        media_path = None
        has_media = False
        needs_ocr = False

        if event.message.photo:
            has_media = True
            needs_ocr = True  # Photos likely contain text needing OCR
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
            media_filename = f"{ts}_{channel_display.replace(' ', '_')}_{message_id}.jpg"
            media_path = os.path.join(INBOX, media_filename)
            try:
                downloaded = await event.message.download_media(file=media_path)
                if downloaded:
                    safe_print(f"[MEDIA] Downloaded photo: {media_filename}")
                    media_path = downloaded
            except Exception as e:
                safe_print(f"[ERROR] Failed to download photo: {e}")

        elif event.message.document:
            has_media = True
            # Check if it's an image document
            if hasattr(event.message.document, 'mime_type'):
                mime = event.message.document.mime_type
                if mime and 'image' in mime:
                    needs_ocr = True

            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
            media_filename = f"{ts}_{channel_display.replace(' ', '_')}_{message_id}"
            media_path = os.path.join(INBOX, media_filename)
            try:
                downloaded = await event.message.download_media(file=media_path)
                if downloaded:
                    safe_print(f"[MEDIA] Downloaded document: {os.path.basename(downloaded)}")
                    media_path = downloaded
            except Exception as e:
                safe_print(f"[ERROR] Failed to download document: {e}")

        # Create payload for inbox
        payload = {
            "source": "telegram",
            "channel": channel_display,
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "message_id": message_id,
            "text": text,
            "has_media": has_media,
            "needs_ocr": needs_ocr,
            "timestamp": datetime.now().isoformat(),
            "created_utc": int(time.time())
        }

        # Save to inbox
        saved_path = save_to_inbox(payload, media_path)
        if saved_path:
            safe_print(f"[SUCCESS] Message saved for channel: {channel_display}")

    except Exception as e:
        safe_print(f"[ERROR] Handler exception: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    safe_print("=" * 60)
    safe_print("TELEGRAM COLLECTOR - ENHANCED VERSION")
    safe_print("=" * 60)
    safe_print(f"Session: {session_file}")
    safe_print(f"Inbox: {INBOX}")
    safe_print(f"Monitoring {len(CHANNELS_BY_ID)} channels by ID")
    safe_print(f"Monitoring {len(CHANNELS_BY_USERNAME)} channels by username")
    safe_print("=" * 60)

    # Start client
    await client.start()
    me = await client.get_me()
    safe_print(f"Logged in as: {me.first_name} (@{me.username})")

    # List monitored channels - try both ID and username
    safe_print("\nMonitored Channels:")

    # Try by ID first
    for channel_id, info in CHANNELS_BY_ID.items():
        try:
            entity = await client.get_entity(channel_id)
            safe_print(f"  [OK] {info['name']} (ID: {channel_id})")
        except Exception as e:
            # Try by username as fallback
            try:
                username = info.get('username')
                if username:
                    entity = await client.get_entity(username)
                    safe_print(f"  [OK] {info['name']} (Username: @{username})")
                else:
                    safe_print(f"  [FAIL] {info['name']}: {str(e)[:50]}")
            except Exception as e2:
                safe_print(f"  [FAIL] {info['name']}: Cannot access")

    safe_print("\n[READY] Listening for messages...")
    safe_print("=" * 60)

    # Keep alive message every 5 minutes
    async def keep_alive():
        while True:
            await asyncio.sleep(300)  # 5 minutes
            safe_print(f"[ALIVE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Still monitoring...")

    # Start keep-alive task
    asyncio.create_task(keep_alive())

    # Run until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\n[STOPPED] User interrupted")
    except Exception as e:
        safe_print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()