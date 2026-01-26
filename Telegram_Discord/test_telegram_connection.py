#!/usr/bin/env python3
"""
Test Telegram connection and list recent messages from monitored channels
"""
import asyncio
import os
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Fix Windows Unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.telegram_client import build_client
from config.channel_routing_map import ROUTING_MAP

# Load environment
BASE_PATH = Path(__file__).parent
load_dotenv(BASE_PATH / ".env")

async def test_connection():
    """Test Telegram connection and fetch recent messages"""
    print("=" * 60)
    print("Testing Telegram Connection")
    print("=" * 60)

    # Build client
    try:
        client = build_client()
        print("✓ Client created successfully")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return

    # Connect
    try:
        await client.start()
        print("✓ Connected to Telegram")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return

    # Get user info
    try:
        me = await client.get_me()
        print(f"✓ Logged in as: {me.username or me.phone}")
    except Exception as e:
        print(f"✗ Failed to get user info: {e}")

    # Check monitored channels
    print("\n" + "=" * 60)
    print("Checking Monitored Channels")
    print("=" * 60)

    channels = list(ROUTING_MAP.keys())
    print(f"Monitoring {len(channels)} channels:")

    # Get recent messages from each channel
    for chat_id in channels:
        try:
            # Get chat info
            chat = await client.get_entity(chat_id)
            chat_name = getattr(chat, 'title', f'Chat {chat_id}')
            print(f"\n📢 {chat_name} (ID: {chat_id})")

            # Get recent messages (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            messages = []
            async for msg in client.iter_messages(chat_id, limit=10, offset_date=yesterday):
                messages.append(msg)

            if messages:
                print(f"  ✓ Found {len(messages)} recent messages")
                # Show last message time
                last_msg = messages[0]
                time_diff = datetime.now(timezone.utc) - last_msg.date
                hours = time_diff.total_seconds() / 3600
                print(f"  📝 Last message: {hours:.1f} hours ago")
                print(f"     Preview: {last_msg.text[:50] if last_msg.text else '[Media]'}...")
            else:
                print(f"  ⚠️ No messages in last 24 hours")

        except Exception as e:
            print(f"  ✗ Error accessing channel: {e}")

    # Test if we can receive new messages
    print("\n" + "=" * 60)
    print("Testing Message Reception")
    print("=" * 60)
    print("Waiting 10 seconds for new messages...")

    received_count = 0

    @client.on(client.events.NewMessage(chats=channels))
    async def handler(event):
        nonlocal received_count
        received_count += 1
        chat_name = getattr(event.chat, 'title', 'Unknown')
        print(f"  📨 New message from {chat_name}: {event.message.text[:50] if event.message.text else '[Media]'}...")

    # Wait for messages
    await asyncio.sleep(10)

    if received_count > 0:
        print(f"✓ Received {received_count} messages during test")
    else:
        print("⚠️ No new messages received during test period")

    await client.disconnect()
    print("\n✓ Test complete")

if __name__ == "__main__":
    asyncio.run(test_connection())