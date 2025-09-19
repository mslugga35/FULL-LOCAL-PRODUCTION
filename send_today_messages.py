#!/usr/bin/env python3
"""
Pull all messages from today and send to validation number
"""
import os
import sys
import asyncio
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timedelta

# Force UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Your session and config
SESSION_STRING = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"
VALIDATION_NUMBER = "+3212629156"

# Channels to pull from
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

client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

def safe_print(msg):
    try:
        print(msg, flush=True)
    except:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

async def pull_today_messages():
    """Pull all messages from today from monitored channels"""
    safe_print("=" * 60)
    safe_print("PULLING TODAY'S MESSAGES FOR VALIDATION")
    safe_print("=" * 60)

    await client.start()
    me = await client.get_me()
    safe_print(f"Connected as: {me.first_name} (@{me.username})")

    # Get today's date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    safe_print(f"Pulling messages from: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"To: {tomorrow.strftime('%Y-%m-%d %H:%M:%S')}")

    all_messages = []

    for channel in CHANNELS:
        try:
            safe_print(f"\n[CHECKING] {channel}")

            # Get channel entity
            entity = await client.get_entity(channel)
            channel_name = getattr(entity, 'title', str(channel))
            safe_print(f"[OK] Found: {channel_name}")

            # Get messages from today
            messages = []
            async for message in client.iter_messages(entity, offset_date=tomorrow, limit=None):
                if message.date < today:
                    break

                text = message.message or "[no text]"
                msg_data = {
                    "channel": channel_name,
                    "time": message.date.strftime("%H:%M:%S"),
                    "text": text[:200] + ("..." if len(text) > 200 else ""),
                    "has_media": bool(message.photo or message.document)
                }
                messages.append(msg_data)

            if messages:
                safe_print(f"[FOUND] {len(messages)} messages from {channel_name}")
                all_messages.extend(messages)
            else:
                safe_print(f"[EMPTY] No messages today from {channel_name}")

        except Exception as e:
            safe_print(f"[ERROR] Failed to check {channel}: {e}")

    return all_messages

async def send_validation_summary(messages):
    """Send summary to validation number"""
    if not messages:
        summary = "🔍 NO MESSAGES FOUND TODAY\n\nNo messages were found in any monitored channels for today."
    else:
        # Group by channel
        by_channel = {}
        for msg in messages:
            channel = msg["channel"]
            if channel not in by_channel:
                by_channel[channel] = []
            by_channel[channel].append(msg)

        # Create summary
        summary = f"📊 TODAY'S TELEGRAM SUMMARY ({len(messages)} total)\n\n"

        for channel, msgs in by_channel.items():
            summary += f"📢 {channel} ({len(msgs)} messages)\n"
            for msg in msgs[-3:]:  # Last 3 messages
                media_icon = "📎" if msg["has_media"] else ""
                summary += f"  {msg['time']} {media_icon} {msg['text'][:100]}\n"
            if len(msgs) > 3:
                summary += f"  ... and {len(msgs)-3} more\n"
            summary += "\n"

    try:
        # Send to validation number
        await client.send_message(VALIDATION_NUMBER, summary)
        safe_print(f"[SENT] Validation summary sent to {VALIDATION_NUMBER}")
        return True
    except Exception as e:
        safe_print(f"[ERROR] Failed to send to {VALIDATION_NUMBER}: {e}")
        return False

async def main():
    """Main function"""
    try:
        # Pull today's messages
        messages = await pull_today_messages()

        # Send validation summary
        await send_validation_summary(messages)

        safe_print(f"\n[COMPLETE] Found {len(messages)} messages total")
        safe_print("=" * 60)

    except Exception as e:
        safe_print(f"[FATAL] {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\n[STOPPED]")
    except Exception as e:
        safe_print(f"[ERROR] {e}")