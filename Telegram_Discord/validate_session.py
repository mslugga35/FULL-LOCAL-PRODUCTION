#!/usr/bin/env python3
"""
Validate current Telegram session string
"""
import asyncio
import os
import sys
import io
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Fix Windows Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment
BASE_PATH = Path(__file__).parent
load_dotenv(BASE_PATH / ".env")

async def validate_session():
    """Validate the current session string"""
    print("=" * 50)
    print("Validating Telegram Session")
    print("=" * 50)

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_string = os.getenv("TELEGRAM_SESSION_STRING")

    if not api_id or not api_hash:
        print("✗ Missing API credentials in .env")
        return False

    if not session_string:
        print("✗ No session string found in .env")
        return False

    print(f"API ID: {api_id}")
    print(f"Session length: {len(session_string)} chars")

    try:
        # Create client with string session
        client = TelegramClient(StringSession(session_string), int(api_id), api_hash)

        # Test connection
        await client.start()
        print("✓ Successfully connected to Telegram")

        # Get user info
        me = await client.get_me()
        print(f"✓ Logged in as: {me.username or me.first_name} ({me.phone})")

        # Test that we can access our channels
        channels = [-1002177758646, -1002470080886, -1002592669126, -1001560546587, -1002608783933]
        working_channels = 0

        for chat_id in channels:
            try:
                chat = await client.get_entity(chat_id)
                chat_name = getattr(chat, 'title', f'Chat {chat_id}')
                print(f"✓ Can access: {chat_name}")
                working_channels += 1
            except Exception as e:
                print(f"✗ Cannot access channel {chat_id}: {e}")

        await client.disconnect()

        if working_channels == len(channels):
            print(f"\n✅ Session is valid! Can access all {working_channels} channels")
            return True
        else:
            print(f"\n⚠️  Session partially working: {working_channels}/{len(channels)} channels accessible")
            return False

    except Exception as e:
        print(f"✗ Session validation failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(validate_session())
    if result:
        print("\n✓ Your session is working correctly!")
        print("The issue may be with the collector process itself.")
    else:
        print("\n✗ Session needs to be regenerated")
    sys.exit(0 if result else 1)