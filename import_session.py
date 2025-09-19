#!/usr/bin/env python3
"""
Import existing Telegram session from string format
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
import sys

# Force UTF-8 for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# The session string from your working setup
SESSION_STRING = "1AQAOMTQ5LjE1NC4xNzUuNTcBu2g+yaG4eWVh5epPtcgWfQTPkqasIdvsxCj68U7clUx9mn3LsVTRIXr/0xJoWABsu/2Khznce7EyhPh0wMw4aFTKllNmUA+iJsGib4sQfpd5dMcg0Ua3BR9JCx596L7qNzAhSda7R2grZFv5cnyx5oT39iXIA3edgHUpf0n+0XwfFFwK8oIqoJgPvoThCpwPit2iCXGM1LERLzssLErvGYzUeAklhKBvle3OJJRFPz4GQIkSRiVQLutLHHXUh3uLws7Pauq/fuhTbd8KxQ5987wcrXlwGI7iUOskQkc+vGlDuXUr3pgbsRHZ5qnIycCnWE3GhO/ns5OtXvJ8PbvkMjQ="

# Configuration
api_id = 29479443
api_hash = "e3a7a7226cf446bbfd5366f7da75cdfa"

async def main():
    print("=" * 60)
    print("IMPORTING TELEGRAM SESSION")
    print("=" * 60)

    # Create client from string session
    client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

    await client.connect()

    if await client.is_user_authorized():
        print("[SUCCESS] Session is valid and authorized!")

        me = await client.get_me()
        print(f"\nLogged in as: {me.first_name} (@{me.username})")
        print(f"Phone: {me.phone}")

        # Save to local file session
        local_session_file = "C:\\Users\\mpmmo\\FULL-LOCAL-PRODUCTION\\telegram_session"
        local_client = TelegramClient(local_session_file, api_id, api_hash)

        # Export session to file
        session_str = StringSession.save(client.session)

        # Now test access to channels
        print("\nTesting channel access:")
        test_channels = [
            (-1002177758646, "UATB"),
            (-1002470080886, "Diamond/Chamba"),
            (-1002592669126, "Cappers Free"),
            (-1001560546587, "Cappers Leaked"),
            (-1002608783933, "Exclusive Cappers")
        ]

        for channel_id, name in test_channels:
            try:
                entity = await client.get_entity(channel_id)
                print(f"  [OK] {name} - Can access")
            except Exception as e:
                print(f"  [FAIL] {name} - {str(e)[:50]}")

        # Also try by username
        print("\nTrying by username:")
        usernames = ["uatb", "diamond", "cappersfree", "cappersleaked"]
        for username in usernames:
            try:
                entity = await client.get_entity(username)
                title = getattr(entity, 'title', username)
                print(f"  [OK] @{username} => {title}")
            except Exception as e:
                print(f"  [FAIL] @{username} - Cannot access")
    else:
        print("[ERROR] Session is not authorized!")

    await client.disconnect()
    print("\n[DONE] You can now run the collector with the string session")

if __name__ == "__main__":
    asyncio.run(main())