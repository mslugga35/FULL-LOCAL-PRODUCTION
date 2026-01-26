#!/usr/bin/env python
"""
Get Telegram channel/chat IDs for configuration
"""
import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

async def get_channel_ids():
    """List all accessible channels and their IDs"""

    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')

    if not api_id or not api_hash:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        return

    client = TelegramClient('telegram_session', api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("Session is not authorized. Please run the session validator first.")
            return

        print("=" * 60)
        print("YOUR TELEGRAM CHANNELS/CHATS")
        print("=" * 60)

        # Get all dialogs (chats)
        dialogs = await client.get_dialogs()

        test_channels = []
        other_channels = []

        for dialog in dialogs:
            chat = dialog.entity

            # Check if it's a channel or group
            if hasattr(chat, 'broadcast') or hasattr(chat, 'megagroup') or hasattr(chat, 'gigagroup'):
                channel_info = {
                    'title': dialog.title,
                    'id': chat.id,
                    'type': 'Channel' if getattr(chat, 'broadcast', False) else 'Group'
                }

                # Separate test channels
                if 'test' in dialog.title.lower():
                    test_channels.append(channel_info)
                else:
                    other_channels.append(channel_info)

        # Show test channels first
        if test_channels:
            print("\n🧪 TEST CHANNELS:")
            print("-" * 40)
            for ch in test_channels:
                # Telegram IDs need to be prefixed with -100 for supergroups/channels
                full_id = f"-100{ch['id']}" if ch['id'] > 0 else str(ch['id'])
                print(f"  {ch['title']}")
                print(f"  ID: {full_id}")
                print(f"  Type: {ch['type']}")
                print()

        # Show other channels
        if other_channels:
            print("\n📢 OTHER CHANNELS:")
            print("-" * 40)
            for ch in other_channels[:10]:  # Show first 10
                full_id = f"-100{ch['id']}" if ch['id'] > 0 else str(ch['id'])
                print(f"  {ch['title']}")
                print(f"  ID: {full_id}")
                print(f"  Type: {ch['type']}")
                print()

        print("=" * 60)
        print("Copy the ID of your test channel to add it to the configuration")
        print("=" * 60)

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_channel_ids())