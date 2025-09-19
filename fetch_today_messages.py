#!/usr/bin/env python3
"""
Fetch all messages from today from all accessible channels
"""
import os
import sys
import asyncio
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
SESSION_STRING = "1AZWarzkBu6DecBYr_WGn2OhJ82zbJANYjaS3RCJEQZu96w-6v6OXFoGtg-KsomiMtevVzIMjyo7bMqqAY_4qA4mAr4KXTpMCqSIuAahKFKhSQj-nmEDgONexQpVh2EEbyIUVbUhQ03kPZ2mTyklCo2K8lDRAlprat0oLPyxgWox3Q4O2hsNnSA-2UurCu2S1s036o3drscyG1qMD_Uu1sxF5NCk_zhC8rwgtM-eURPNr86a3m0vaeOuqmIrCi-A9tVtVGB1nIsV4-WCdmBYgmnE2cohm59DFhfEIR3VnJ5XAOI7o71GGnsl6oCPVDB6XFiu_3MxoRKkV_WppBJ6JGzrKFRLWpaY="
INBOX = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\today_messages"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Target channels (both IDs and usernames)
CHANNELS = [
    -1002177758646,  # UATB
    -1002470080886,  # Diamond/Chamba
    -1002592669126,  # Cappers Free
    -1001560546587,  # Cappers Leaked
    -1002608783933,  # Exclusive Cappers
    "uatb",           # UATB username
    "diamond",        # Diamond username
]

# Create output directory
os.makedirs(INBOX, exist_ok=True)
os.makedirs(os.path.join(INBOX, "media"), exist_ok=True)

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

async def fetch_today_messages():
    """Fetch all messages from today"""
    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

    safe_print("=" * 60)
    safe_print("FETCHING TODAY'S MESSAGES")
    safe_print("=" * 60)

    await client.start()
    me = await client.get_me()
    safe_print(f"Connected as: {me.first_name} (@{me.username})")

    # Get today's date at midnight
    today = datetime.now()
    today_start = datetime(today.year, today.month, today.day)

    safe_print(f"Fetching messages from: {today_start.strftime('%Y-%m-%d')}")
    safe_print("")

    total_messages = 0
    channel_stats = {}

    # Process all accessible dialogs
    safe_print("Checking all accessible channels...")
    async for dialog in client.iter_dialogs():
        try:
            # Get channel/group details
            chat = dialog.entity
            chat_title = getattr(chat, 'title', dialog.name)

            if not chat_title:
                continue

            messages_count = 0

            # Iterate through messages from today
            async for message in client.iter_messages(chat, offset_date=today_start + timedelta(days=1), reverse=True):
                # Check if message is from today
                if message.date.replace(tzinfo=None) < today_start:
                    break

                messages_count += 1
                total_messages += 1

                # Save message data
                msg_data = {
                    "timestamp": message.date.isoformat(),
                    "channel": chat_title,
                    "message_id": message.id,
                    "text": message.message or "[no text]",
                    "sender": message.sender_id,
                    "has_media": bool(message.media)
                }

                # Handle media
                if message.media:
                    try:
                        media_folder = os.path.join(INBOX, "media")
                        base_filename = f"{message.date.strftime('%Y%m%d_%H%M%S')}_{chat_title.replace(' ', '_')}_{message.id}"

                        # Download media
                        file_path = os.path.join(media_folder, base_filename)
                        downloaded = await message.download_media(file=file_path)

                        if downloaded:
                            msg_data["media_file"] = os.path.basename(downloaded)
                    except Exception as e:
                        msg_data["media_error"] = str(e)

                # Save JSON
                json_filename = f"{message.date.strftime('%Y%m%d_%H%M%S')}_{chat_title.replace(' ', '_')}_{message.id}.json"
                json_path = os.path.join(INBOX, json_filename)

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(msg_data, f, ensure_ascii=False, indent=2)

            if messages_count > 0:
                channel_stats[chat_title] = messages_count
                safe_print(f"[FOUND] {chat_title}: {messages_count} messages")

        except Exception as e:
            safe_print(f"[ERROR] Failed to process {dialog.name}: {e}")

    safe_print("")
    safe_print("=" * 60)
    safe_print("SUMMARY")
    safe_print("=" * 60)
    safe_print(f"Total messages from today: {total_messages}")
    safe_print(f"Channels with messages: {len(channel_stats)}")
    safe_print("")

    if channel_stats:
        safe_print("Breakdown by channel:")
        for channel, count in sorted(channel_stats.items(), key=lambda x: x[1], reverse=True):
            safe_print(f"  - {channel}: {count} messages")

    safe_print("")
    safe_print(f"Messages saved to: {INBOX}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(fetch_today_messages())