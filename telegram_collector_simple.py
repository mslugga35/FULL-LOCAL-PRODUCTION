#!/usr/bin/env python3
"""
Simple Telegram Collector - Just captures messages to inbox
No phone forwarding, no complex features - just works
"""
import os
import sys
import asyncio
import json
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
SESSION_STRING = "1AZWarzkBu6DecBYr_WGn2OhJ82zbJANYjaS3RCJEQZu96w-6v6OXFoGtg-KsomiMtevVzIMjyo7bMqqAY_4qA4mAr4KXTpMCqSIuAahKFKhSQj-nmEDgONexQpVh2EEbyIUVbUhQ03kPZ2mTyklCo2K8lDRAlprat0oLPyxgWox3Q4O2hsNnSA-2UurCu2S1s036o3drscyG1qMD_Uu1sxF5NCk_zhC8rwgtM-eURPNr86a3m0vaeOuqmIrCi-A9tVtVGB1nIsV4-WCdmBYgmnE2cohm59DFhfEIR3VnJ5XAOI7o71GGnsl6oCPVDB6XFiu_3MxoRKkV_WppBJ6JGzrKFRLWpaY="
INBOX = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\inbox"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Target channels
CHANNELS = [
    -1002177758646,  # UATB
    -1002470080886,  # Diamond/Chamba
    -1002592669126,  # Cappers Free
    -1001560546587,  # Cappers Leaked
    -1002608783933,  # Exclusive Cappers
]

# Create directories
os.makedirs(INBOX, exist_ok=True)
os.makedirs(os.path.join(INBOX, "media"), exist_ok=True)

client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)
message_count = 0

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

@client.on(events.NewMessage(chats=CHANNELS))
async def capture_message(event):
    """Capture messages from target channels"""
    global message_count

    try:
        message_count += 1

        # Get channel info
        chat = await event.get_chat()
        channel_name = getattr(chat, 'title', str(chat.id))

        # Message details
        message_text = event.message.message or "[no text]"
        message_id = event.message.id
        timestamp = datetime.now()

        safe_print(f"[{message_count}] {channel_name}: {message_text[:80]}...")

        # Save message data
        msg_data = {
            "timestamp": timestamp.isoformat(),
            "channel": channel_name,
            "message_id": message_id,
            "text": message_text,
            "has_media": False
        }

        # Handle media if present
        if event.message.media:
            msg_data["has_media"] = True
            try:
                media_folder = os.path.join(INBOX, "media")
                base_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{message_id}"

                # Download media
                file_path = os.path.join(media_folder, base_filename)
                downloaded = await event.message.download_media(file=file_path)

                if downloaded:
                    msg_data["media_file"] = os.path.basename(downloaded)
                    safe_print(f"    [SAVED] Media: {os.path.basename(downloaded)}")
            except Exception as e:
                safe_print(f"    [ERROR] Media download failed: {e}")

        # Save JSON metadata
        json_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{channel_name.replace(' ', '_')}_{message_id}.json"
        json_path = os.path.join(INBOX, json_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(msg_data, f, ensure_ascii=False, indent=2)

        safe_print(f"    [SAVED] {json_filename}")

    except Exception as e:
        safe_print(f"[ERROR] Failed to capture message: {e}")

async def main():
    """Main function"""
    safe_print("=" * 60)
    safe_print("TELEGRAM COLLECTOR - SIMPLE VERSION")
    safe_print("=" * 60)

    safe_print("Connecting...")

    try:
        await client.start()
        me = await client.get_me()
        safe_print(f"Connected as: {me.first_name} (@{me.username})")
    except Exception as e:
        safe_print(f"[ERROR] Failed to connect: {e}")
        safe_print("[INFO] Session may be expired. You need to authenticate.")
        return

    safe_print(f"Monitoring {len(CHANNELS)} channels")
    safe_print(f"Saving to: {INBOX}")
    safe_print("=" * 60)
    safe_print("Waiting for messages... (Press Ctrl+C to stop)")

    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        safe_print("\n[STOPPED] User interrupted")
    except Exception as e:
        safe_print(f"[ERROR] {e}")
    finally:
        safe_print(f"[STATS] Captured {message_count} messages")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        safe_print(f"[FATAL] {e}")