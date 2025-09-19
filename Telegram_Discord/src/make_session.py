#!/usr/bin/env python3
"""
Telethon StringSession Creator
Creates a StringSession for Telegram API authentication
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

async def create_session():
    """Create a new Telethon StringSession"""

    # Load environment variables
    load_dotenv()

    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')

    if not api_id or not api_hash:
        print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        return

    print("Creating Telegram session...")
    print("You will need to enter your phone number and verification code.")
    print()

    # Create client with StringSession
    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        await client.start()

        # Get the session string
        session_string = client.session.save()

        print()
        print("SUCCESS! Your session string is:")
        print("=" * 50)
        print(session_string)
        print("=" * 50)
        print()
        print("Add this to your .env file as:")
        print(f"TELEGRAM_SESSION_STRING={session_string}")
        print()
        print("Keep this session string secure - it provides access to your Telegram account!")

    except Exception as e:
        print(f"ERROR creating session: {e}")

    finally:
        await client.disconnect()

def main():
    """Main entry point"""
    try:
        asyncio.run(create_session())
    except KeyboardInterrupt:
        print("\nSession creation cancelled by user")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()