#!/usr/bin/env python3
"""
SIMPLE MESSAGE FETCHER - Fetch today's messages from all channels
"""
import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

# CHANNELS TO MONITOR
CHANNELS = {
    -1002177758646: 'UATB',
    -1002470080886: 'Diamond',
    -1002592669126: 'Cappers_Free',
    -1001560546587: 'Cappers_Leaked',
    -1002608783933: 'Exclusive_Cappers'
}

async def main():
    print("=" * 50)
    print("FETCHING TODAY'S MESSAGES")
    print("=" * 50)

    # Check for session
    if os.path.exists('NEW_SESSION_STRING.txt'):
        with open('NEW_SESSION_STRING.txt', 'r') as f:
            session = f.read().strip()
        print("Using NEW session string")
    elif os.path.exists('telegram_session.session'):
        print("Using session file")
        client = TelegramClient('telegram_session', 29479443, "e3a7a7226cf446bbfd5366f7da75cdfa")
    else:
        print("ERROR: No session found! Run TELEGRAM_AUTH_NEW.py first")
        return

    if 'session' in locals():
        client = TelegramClient(StringSession(session), 29479443, "e3a7a7226cf446bbfd5366f7da75cdfa")

    await client.start()
    print("✅ Connected to Telegram\n")

    # Get today's messages
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    total_saved = 0

    for channel_id, name in CHANNELS.items():
        print(f"Fetching {name}...")
        try:
            entity = await client.get_entity(channel_id)
            count = 0

            async for msg in client.iter_messages(entity, offset_date=datetime.now(timezone.utc), reverse=False):
                if msg.date.replace(tzinfo=timezone.utc) < today:
                    continue

                # Save to inbox
                timestamp = msg.date.strftime("%Y%m%d_%H%M%S")
                filename = f"inbox/{name}_{timestamp}_{msg.id}.json"

                data = {
                    "channel_id": channel_id,
                    "channel_name": name,
                    "message_id": msg.id,
                    "timestamp": msg.date.isoformat(),
                    "text": msg.text or "",
                    "has_media": msg.media is not None
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

                count += 1
                total_saved += 1

                # Show preview
                preview = (msg.text[:50] if msg.text else "[Media]").replace('\n', ' ')
                print(f"  [{msg.date.strftime('%H:%M')}] {preview}")

                if count >= 20:  # Limit per channel
                    break

            print(f"  ✓ Saved {count} messages\n")

        except Exception as e:
            print(f"  ❌ Error: {e}\n")

    print(f"=" * 50)
    print(f"TOTAL: {total_saved} messages saved to inbox/")

    await client.disconnect()

if __name__ == "__main__":
    # Create inbox if doesn't exist
    os.makedirs('inbox', exist_ok=True)
    asyncio.run(main())