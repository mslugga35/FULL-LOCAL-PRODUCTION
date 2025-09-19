#!/usr/bin/env python3
"""
Single Telegram Producer - Monitors 5 channels and writes to inbox
No duplicate sessions - this is the ONLY Telegram client
"""

import os
import asyncio
import json
import time
import pathlib
import requests
from telethon import TelegramClient, events
from datetime import datetime

# Configuration from environment - force Windows paths
import platform
if platform.system() == "Windows":
    INBOX = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\inbox"
    session_file = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\telegram_session"
else:
    INBOX = os.getenv("INBOX_DIR", "/root/inbox")
    session_file = os.getenv("TG_SESSION_FILE", "/root/telegram_session.session")

api_id = int(os.getenv("TG_API_ID", "29479443"))
api_hash = os.getenv("TG_API_HASH", "e3a7a7226cf446bbfd5366f7da75cdfa")

# The 5 channels to monitor (use channel usernames or IDs)
CHANNELS_TO_MONITOR = [
    -1002592669126,      # Cappers Free
    -1001560546587,    # Cappers Leaked  
    -1002608783933, # Exclusive Cappers
    -1002177758646,            # UATB
    -1002470080886,         # Diamond/Chamba
]

# Discord webhook mappings - PAID CHANNELS ONLY
DISCORD_WEBHOOKS = {
    # FREE CHANNELS REMOVED - NO WEBHOOKS FOR FREE CONTENT
    # -1002592669126: REMOVED (CAPPERS_FREE - uses bot)
    # -1001560546587: REMOVED (CAPPERS_LEAKED - uses bot)
    # -1002608783933: REMOVED (EXCLUSIVE - uses bot)

    # PAID CHANNELS ONLY
    -1002177758646: os.getenv("WEBHOOK_UATB"),
    -1002470080886: os.getenv("WEBHOOK_DIAMOND"),
}

# Ensure directories exist
pathlib.Path(INBOX).mkdir(parents=True, exist_ok=True)
pathlib.Path(pathlib.Path(session_file).parent).mkdir(parents=True, exist_ok=True)

# Initialize client
client = TelegramClient(session_file, api_id, api_hash)

def save_to_inbox(payload, media_path=None):
    """Save message to inbox for Discord bots to consume"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    msg_id = payload.get("message_id", int(time.time() * 1000))
    key = f"{ts}_{msg_id}"
    json_path = f"{INBOX}/{key}.json"
    
    # Add media reference if exists
    if media_path:
        payload["media_file"] = os.path.basename(media_path)
    
    # Write JSON metadata
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVED] {json_path}")
    return json_path

def post_to_discord_webhook(webhook_url, text, file_path=None):
    """Optional: Direct post to Discord webhook"""
    if not webhook_url:
        return
    
    try:
        data = {"content": text[:2000] if text else ""}
        files = {}
        
        if file_path and os.path.exists(file_path):
            files["file"] = open(file_path, "rb")
        
        response = requests.post(webhook_url, data=data, files=files, timeout=10)
        
        if response.status_code == 204:
            print(f"[WEBHOOK] Posted to Discord")
        else:
            print(f"[WEBHOOK] Error: {response.status_code}")
            
    except Exception as e:
        print(f"[WEBHOOK] Exception: {e}")
    finally:
        if "file" in files:
            files["file"].close()

@client.on(events.NewMessage(chats=CHANNELS_TO_MONITOR))
async def handle_new_message(event):
    """Handle new messages from monitored channels"""
    try:
        # Get chat info
        chat = await event.get_chat()
        chat_id = chat.id if chat else None
        chat_title = getattr(chat, "title", str(chat_id))
        chat_username = getattr(chat, "username", "")
        
        # Get message info
        text = event.message.message or ""
        message_id = event.message.id

        # Clean text for Windows console output
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(f"\n[NEW] {chat_title}: {clean_text[:50]}...")
        
        # Download media if exists
        media_path = None
        if event.photo or event.document:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            media_filename = f"{ts}_{message_id}"
            media_path = f"{INBOX}/{media_filename}"
            media_path = await event.download_media(file=media_path)
            print(f"[MEDIA] Downloaded: {media_path}")
        
        # Create payload for inbox
        payload = {
            "source": "telegram",
            "channel": "telegram",
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "message_id": message_id,
            "text": text,
            "has_media": bool(media_path),
            "needs_ocr": bool(event.photo),  # Photos likely need OCR
            "timestamp": datetime.now().isoformat(),
            "created_utc": int(time.time())
        }
        
        # Save to inbox
        save_to_inbox(payload, media_path)
        
        # Optional: Also post directly to Discord webhook
        webhook_url = DISCORD_WEBHOOKS.get(chat_id) if chat_id else None
        if webhook_url:
            formatted_text = f"**[{chat_title}]**\n{text}"
            post_to_discord_webhook(webhook_url, formatted_text, media_path)
        
    except Exception as e:
        print(f"[ERROR] Handler exception: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    print("=" * 50)
    print("TELEGRAM PRODUCER - SINGLE CLIENT")
    print("=" * 50)
    print(f"Session: {session_file}")
    print(f"Inbox: {INBOX}")
    print(f"Monitoring {len(CHANNELS_TO_MONITOR)} channels")
    print("=" * 50)
    
    # Start client
    await client.start()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} ({me.username})")
    
    # List monitored channels
    print("\nMonitored Channels:")
    for channel in CHANNELS_TO_MONITOR:
        try:
            entity = await client.get_entity(channel)
            print(f"  [OK] {entity.title} (@{getattr(entity, 'username', channel)})")
        except Exception as e:
            print(f"  [ERROR] {channel}: {e}")
    
    print("\n[READY] Listening for messages...")
    print("=" * 50)
    
    # Run until disconnected
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User interrupted")
    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()