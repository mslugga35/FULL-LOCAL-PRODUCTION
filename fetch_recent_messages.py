#!/usr/bin/env python3
"""
Fetch recent messages (last 7 days) from all accessible channels
Shows what messages are available for troubleshooting
"""
import os
import sys
import asyncio
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
SESSION_STRING = "1AZWarzkBu6DecBYr_WGn2OhJ82zbJANYjaS3RCJEQZu96w-6v6OXFoGtg-KsomiMtevVzIMjyo7bMqqAY_4qA4mAr4KXTpMCqSIuAahKFKhSQj-nmEDgONexQpVh2EEbyIUVbUhQ03kPZ2mTyklCo2K8lDRAlprat0oLPyxgWox3Q4O2hsNnSA-2UurCu2S1s036o3drscyG1qMD_Uu1sxF5NCk_zhC8rwgtM-eURPNr86a3m0vaeOuqmIrCi-A9tVtVGB1nIsV4-WCdmBYgmnE2cohm59DFhfEIR3VnJ5XAOI7o71GGnsl6oCPVDB6XFiu_3MxoRKkV_WppBJ6JGzrKFRLWpaY="
INBOX = r"C:\Users\mpmmo\FULL-LOCAL-PRODUCTION\recent_messages"
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

# Create output directory
os.makedirs(INBOX, exist_ok=True)
os.makedirs(os.path.join(INBOX, "media"), exist_ok=True)

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

async def fetch_recent_messages():
    """Fetch messages from last 7 days"""
    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

    safe_print("=" * 60)
    safe_print("FETCHING RECENT MESSAGES (LAST 7 DAYS)")
    safe_print("=" * 60)

    await client.start()
    me = await client.get_me()
    safe_print(f"Connected as: {me.first_name} (@{me.username})")

    # Get date range
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    safe_print(f"Date range: {seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    safe_print("")

    total_messages = 0
    channel_stats = {}
    daily_stats = {}

    # Initialize daily stats
    for i in range(8):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_stats[date] = 0

    # Process priority channels first
    priority_channels = [
        "UATB",
        "DIAMOND",
        "Cappers Free",
        "Cappers Leaked",
        "Exclusive Cappers"
    ]

    safe_print("Checking channels...")
    safe_print("")

    # Process all accessible dialogs
    async for dialog in client.iter_dialogs(limit=50):
        try:
            # Get channel/group details
            chat = dialog.entity
            chat_title = getattr(chat, 'title', dialog.name)

            if not chat_title:
                continue

            messages_count = 0
            latest_message_date = None
            sample_messages = []

            # Get last 100 messages or messages from last 7 days
            async for message in client.iter_messages(chat, limit=100):
                # Skip if older than 7 days
                if message.date.replace(tzinfo=None) < seven_days_ago:
                    break

                messages_count += 1
                total_messages += 1

                # Track daily stats
                msg_date = message.date.strftime('%Y-%m-%d')
                if msg_date in daily_stats:
                    daily_stats[msg_date] += 1

                # Keep track of latest message
                if not latest_message_date:
                    latest_message_date = message.date

                # Save first 3 messages as samples
                if len(sample_messages) < 3:
                    sample_messages.append({
                        "date": message.date.strftime('%Y-%m-%d %H:%M'),
                        "text": (message.message or "[no text]")[:100]
                    })

                # Save message data
                msg_data = {
                    "timestamp": message.date.isoformat(),
                    "channel": chat_title,
                    "message_id": message.id,
                    "text": message.message or "[no text]",
                    "sender": message.sender_id,
                    "has_media": bool(message.media)
                }

                # Save JSON
                json_filename = f"{message.date.strftime('%Y%m%d_%H%M%S')}_{chat_title.replace(' ', '_')[:20]}_{message.id}.json"
                json_path = os.path.join(INBOX, json_filename)

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(msg_data, f, ensure_ascii=False, indent=2)

            if messages_count > 0:
                channel_stats[chat_title] = {
                    "count": messages_count,
                    "latest": latest_message_date.strftime('%Y-%m-%d %H:%M') if latest_message_date else "N/A",
                    "samples": sample_messages,
                    "is_priority": any(p.upper() in chat_title.upper() for p in priority_channels)
                }

                # Show priority channels immediately
                if channel_stats[chat_title]["is_priority"]:
                    safe_print(f"[PRIORITY] {chat_title}: {messages_count} messages")
                    safe_print(f"  Latest: {channel_stats[chat_title]['latest']}")
                    if sample_messages:
                        safe_print("  Sample messages:")
                        for sample in sample_messages[:2]:
                            safe_print(f"    - {sample['date']}: {sample['text'][:50]}...")

        except Exception as e:
            safe_print(f"[ERROR] Failed to process {dialog.name}: {e}")

    safe_print("")
    safe_print("=" * 60)
    safe_print("SUMMARY")
    safe_print("=" * 60)
    safe_print(f"Total messages from last 7 days: {total_messages}")
    safe_print(f"Channels with messages: {len(channel_stats)}")
    safe_print("")

    # Show daily breakdown
    safe_print("Messages by day:")
    for date in sorted(daily_stats.keys(), reverse=True):
        count = daily_stats[date]
        bar = "█" * min(50, count // 2) if count > 0 else "-"
        safe_print(f"  {date}: {count:4d} {bar}")

    safe_print("")

    # Show all channels
    if channel_stats:
        safe_print("All channels with recent messages:")

        # Sort by priority first, then by count
        sorted_channels = sorted(
            channel_stats.items(),
            key=lambda x: (x[1]["is_priority"], x[1]["count"]),
            reverse=True
        )

        for channel, stats in sorted_channels:
            prefix = "[P]" if stats["is_priority"] else "   "
            safe_print(f"{prefix} {channel}: {stats['count']} messages (latest: {stats['latest']})")

    safe_print("")
    safe_print(f"Messages saved to: {INBOX}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(fetch_recent_messages())